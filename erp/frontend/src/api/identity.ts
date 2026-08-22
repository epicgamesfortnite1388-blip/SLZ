/**
 * Identity administration API layer: users and permissions (read-only surfaces
 * for identity administrators; mutation is through the seed/CLI tooling).
 *
 * The UserViewSet is gated by ``identity.user.view`` server-side. User mutation
 * (creation, role assignment) is deliberately not exposed in the API — it is
 * performed through ``manage.py`` / seed tooling until the final role catalogue
 * (Q-053) is confirmed.
 */

/** Platform user (mirrors ``apps.identity.serializers.UserSerializer``). */
export interface PlatformUser {
  id: string;
  email: string;
  username: string;
  full_name: string;
  language: string;
  timezone: string;
  is_active: boolean;
  is_staff: boolean;
  is_superuser: boolean;
  roles: string[];
  permissions: string[];
  date_joined: string;
}

/** Platform permission code (mirrors ``PermissionSerializer``). */
export interface PlatformPermission {
  id: string;
  code: string;
  module: string;
  description_en: string;
  description_fa: string;
}