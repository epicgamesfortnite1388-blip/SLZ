/**
* Identity administration API layer: users and permissions (read-only surfaces
* for identity administrators; mutation is through the seed/CLI tooling).
*
* The UserViewSet is gated by ``identity.user.view`` server-side. User mutation
* (creation, role assignment) is deliberately not exposed in the API — it is
* performed through ``manage.py`` / seed tooling until the final role catalogue
* (Q-053) is confirmed.
*/
import { apiClient } from './client';
import type { Paginated } from './masterData';

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
 companies: string[];
 date_joined: string;
}

/** Payload for creating or updating a user. */
export interface UserPayload {
 email: string;
 password?: string;
 full_name?: string;
 language?: string;
 timezone?: string;
 is_active?: boolean;
 roles?: string[];
 company_ids?: string[];
}

/** Create a user (requires ``identity.user.manage``). */
export function createUser(payload: UserPayload): Promise<PlatformUser> {
 return apiClient.post<PlatformUser>('/auth/users/', payload);
}

/** Update a user (requires ``identity.user.manage``). */
export function updateUser(id: string, payload: Partial<UserPayload>): Promise<PlatformUser> {
 return apiClient.patch<PlatformUser>(`/auth/users/${id}/`, payload);
}

/** Platform permission code (mirrors ``PermissionSerializer``). */
export interface PlatformPermission {
 id: string;
 code: string;
 module: string;
 description_en: string;
 description_fa: string;
}

/** Fetch all permissions (for role assignment UI). */
export async function fetchPermissions(): Promise<Paginated<PlatformPermission>> {
 return apiClient.get<Paginated<PlatformPermission>>('/auth/permissions/?page_size=200');
}

/** Fetch all roles (for user assignment). */
export async function fetchAllRoles(): Promise<{ results: { id: string; code: string }[] }> {
 return apiClient.get('/auth/roles/?page_size=200');
}

/** Fetch all companies (for membership assignment). */
export async function fetchAllCompanies(): Promise<{ results: { id: string; code: string; name_en: string; name_fa: string }[] }> {
 return apiClient.get('/organization/companies/?page_size=200');
}