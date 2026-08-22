from django.contrib import admin

from apps.identity.models import Permission, Role, User

admin.site.register(User)
admin.site.register(Role)
admin.site.register(Permission)
