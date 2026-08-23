/**
 * Shared API types that mirror the SLZ ERP backend contract.
 */

/** Language codes supported by the app / backend. */
export type Language = 'fa' | 'en';

/** Permission codes follow `module.resource.action`, e.g. `organization.company.view`. */
export type PermissionCode = string;

/** Role codes, e.g. `admin`, `operator`. */
export type RoleCode = string;

/** Authenticated user, as returned by `/auth/login/` and `/auth/me/`. */
export interface User {
  id: number | string;
  email: string;
  full_name: string;
  language: Language;
  timezone: string;
  is_superuser: boolean;
  roles: RoleCode[];
  permissions: PermissionCode[];
  /** Company IDs this user is a member of (Q-055). */
  companies: string[];
  /** Per-company permission breakdown (from /auth/me/). */
  permissions_by_company?: Record<string, PermissionCode[]>;
  /** Active company from the X-SLZ-Company header (mirrored by /auth/me/). */
  active_company_id?: string | null;
}

/** Successful login response payload. */
export interface LoginResponse {
  access: string;
  refresh: string;
  user: User;
}

/** Refresh response payload. */
export interface RefreshResponse {
  access: string;
}

/** Error types emitted by the backend error envelope. */
export type ApiErrorType =
  | 'ValidationError'
  | 'AuthenticationError'
  | 'AuthorizationError'
  | 'NotFoundError'
  | 'ConflictError'
  | 'BusinessRuleError'
  | 'ThrottledError'
  | 'SystemError';

/** Raw error envelope shape returned by the backend on failure. */
export interface ApiErrorEnvelope {
  error: {
    type: ApiErrorType;
    message: string;
    details?: unknown;
    code?: string | null;
    correlation_id?: string;
  };
}

/**
 * Typed error thrown by the API client on any non-2xx response.
 * Carries the parsed error envelope plus the HTTP status and correlation id.
 */
export class ApiError extends Error {
  readonly type: ApiErrorType;
  readonly details: unknown;
  readonly code: string | null;
  readonly correlationId: string;
  readonly status: number;

  constructor(params: {
    type: ApiErrorType;
    message: string;
    details?: unknown;
    code?: string | null;
    correlationId: string;
    status: number;
  }) {
    super(params.message);
    this.name = 'ApiError';
    this.type = params.type;
    this.details = params.details ?? null;
    this.code = params.code ?? null;
    this.correlationId = params.correlationId;
    this.status = params.status;
    // Restore prototype chain (TS + extending built-ins).
    Object.setPrototypeOf(this, ApiError.prototype);
  }
}

/** Type guard for {@link ApiError}. */
export function isApiError(value: unknown): value is ApiError {
  return value instanceof ApiError;
}
