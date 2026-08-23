"""Authentication and identity API views."""

from __future__ import annotations

from zoneinfo import available_timezones

from django.contrib.auth import get_user_model
from rest_framework import mixins, serializers, status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.audit.services import record_audit
from apps.core.exceptions import AuthenticationError, ValidationError
from apps.identity.models import Language, Permission, Role
from apps.identity.permissions import require_permission
from apps.identity.serializers import PermissionSerializer, RoleSerializer, UserSerializer

User = get_user_model()


class MeUpdateSerializer(serializers.ModelSerializer):
    """Validated self-profile update (language / timezone / full name).

    Replaces the previous unchecked ``setattr`` loop: an over-long value or an
    unknown language code used to surface as a 500 (DB DataError) or silently
    persist state the locale layer could not render.
    """

    class Meta:
        model = User
        fields = ["full_name", "language", "timezone"]

    def validate_language(self, value):
        # Model choices are not enforced on .save(); enforce them here.
        valid = {code for code, _label in Language.choices}
        if value not in valid:
            raise serializers.ValidationError(
                f"'{value}' is not a supported language.",
                code="invalid_choice",
            )
        return value

    def validate_timezone(self, value):
        if value not in available_timezones():
            raise serializers.ValidationError(
                f"'{value}' is not a valid IANA time zone.",
                code="invalid_timezone",
            )
        return value


class AuthAnonThrottle(AnonRateThrottle):
    """Per-IP rate limit for unauthenticated auth endpoints.

    Login and token refresh are the platform's brute-force surface; this adds
    baseline resistance without any business policy. The rate lives in
    ``REST_FRAMEWORK['DEFAULT_THROTTLE_RATES']['auth']`` (env-tunable).
    """

    scope = "auth"


class LoginView(TokenObtainPairView):
    """Obtain JWT access/refresh tokens; records a LOGIN audit entry."""

    permission_classes = [AllowAny]
    throttle_classes = [AuthAnonThrottle]

    def post(self, request, *args, **kwargs):
        serializer = TokenObtainPairSerializer(data=request.data)
        if not serializer.is_valid():
            raise AuthenticationError("Invalid credentials.")
        data = serializer.validated_data
        user = serializer.user
        record_audit(
            action="LOGIN",
            entity_type="identity.User",
            entity_id=str(user.pk),
            actor=user,
        )
        data["user"] = UserSerializer(user).data
        return Response(data, status=status.HTTP_200_OK)


class RefreshView(TokenRefreshView):
    permission_classes = [AllowAny]
    throttle_classes = [AuthAnonThrottle]


class LogoutView(APIView):
    """Blacklist the supplied refresh token and record a LOGOUT audit entry."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        token = request.data.get("refresh")
        if not token:
            raise ValidationError("A 'refresh' token is required.")
        try:
            RefreshToken(token).blacklist()
        except Exception as exc:  # invalid/expired token
            raise ValidationError("Invalid refresh token.") from exc
        record_audit(
            action="LOGOUT",
            entity_type="identity.User",
            entity_id=str(request.user.pk),
            actor=request.user,
        )
        return Response(status=status.HTTP_205_RESET_CONTENT)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = UserSerializer(request.user).data
        # Augment with per-company permission breakdown so the frontend can
        # show the right UI for the active company (Q-055).
        data["permissions_by_company"] = {
            str(cid): sorted(request.user.permission_codes(company_id=str(cid)))
            for cid in request.user.company_memberships.values_list("company_id", flat=True)
        }
        data["active_company_id"] = getattr(request, "company_id", None)
        return Response(data)

    def patch(self, request):
        # Users may update their own locale preferences only — validated, so a
        # bad value is a clean 400 instead of a 500 or silently-broken state.
        serializer = MeUpdateSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(request.user).data)


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating users via the API.

    Password is write-only. Roles and companies are accepted as FK lists.
    """

    password = serializers.CharField(write_only=True, required=False, min_length=8)
    roles = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Role.objects.all(), required=False,
    )
    company_ids = serializers.ListField(
        child=serializers.UUIDField(), write_only=True, required=False,
    )

    class Meta:
        model = User
        fields = [
            "email", "username", "full_name", "password",
            "is_active", "language", "timezone", "roles", "company_ids",
        ]

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        roles = validated_data.pop("roles", [])
        company_ids = validated_data.pop("company_ids", [])
        user = User.objects.create_user(**validated_data)
        if password:
            user.set_password(password)
            user.save(update_fields=["password"])
        if roles:
            from apps.identity.models import UserRole
            for role in roles:
                UserRole.objects.get_or_create(user=user, role=role)
        if company_ids:
            from apps.identity.models import CompanyMembership
            from apps.organization.models import Company
            for cid in company_ids:
                CompanyMembership.objects.get_or_create(user=user, company_id=cid)
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        roles = validated_data.pop("roles", None)
        company_ids = validated_data.pop("company_ids", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        if roles is not None:
            from apps.identity.models import UserRole
            UserRole.objects.filter(user=instance).delete()
            for role in roles:
                UserRole.objects.get_or_create(user=instance, role=role)
        if company_ids is not None:
            from apps.identity.models import CompanyMembership
            CompanyMembership.objects.filter(user=instance).delete()
            for cid in company_ids:
                CompanyMembership.objects.get_or_create(user=instance, company_id=cid)
        return instance


class PermissionViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    # Explicitly gated: the permission catalogue is platform configuration and
    # must not be enumerable by every authenticated user.
    permission_classes = [require_permission("identity.permission.view")]
    filterset_fields = ["module"]
    search_fields = ["code", "description_en", "description_fa"]


class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all().prefetch_related("permissions")
    serializer_class = RoleSerializer
    permission_classes = [require_permission("identity.role.manage")]
    search_fields = ["code", "name_en", "name_fa"]


class UserViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    queryset = User.objects.all().prefetch_related("roles")
    serializer_class = UserSerializer
    permission_classes = [require_permission("identity.user.view")]
    permission_map = {
        "POST": "identity.user.manage",
        "PUT": "identity.user.manage",
        "PATCH": "identity.user.manage",
    }
    filterset_fields = ["is_active", "language"]
    search_fields = ["email", "username", "full_name"]

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return UserCreateSerializer
        return UserSerializer
