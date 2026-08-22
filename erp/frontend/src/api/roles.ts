/**
 * Identity RBAC administration API layer: platform **roles**.
 *
 * Mirrors ``apps.identity.serializers.RoleSerializer``. Both reading and
 * writing roles require ``identity.role.manage`` server-side (the catalogue is
 * platform configuration, not business data). ``permission_codes`` is
 * read-only on the wire for now — role-permission assignment UI is a follow-up
 * slice and must not be assumed writable here.
 */
import { apiClient } from './client';
import type { Paginated } from './masterData';

/** A named bundle of permission codes assignable to users. */
export interface Role {
  id: string;
  code: string;
  name_en: string;
  name_fa: string;
  description: string;
  is_system: boolean;
  /** Granted permission codes (read-only projection of the m2m). */
  permission_codes: string[];
}

/** Paginated role list (`GET /auth/roles/`). */
export async function fetchRoles(page = 1, pageSize = 25): Promise<Paginated<Role>> {
  return apiClient.get<Paginated<Role>>(`/auth/roles/?page=${page}&page_size=${pageSize}`);
}

/** Create a role (audited write path; requires ``identity.role.manage``). */
export function createRole(payload: {
  code: string;
  name_en?: string;
  name_fa?: string;
  description?: string;
}): Promise<Role> {
  return apiClient.post<Role>('/auth/roles/', payload);
}
