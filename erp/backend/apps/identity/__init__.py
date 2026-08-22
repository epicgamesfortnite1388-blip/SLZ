"""Identity, authentication and RBAC.

Roles and permissions are DATA, never hard-coded. A permission code follows the
``module.resource.action`` convention (e.g. ``sales.order.approve``) so future
business modules can declare their own permissions without touching this app.
"""
