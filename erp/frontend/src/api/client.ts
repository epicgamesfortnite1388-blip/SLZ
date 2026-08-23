/**
 * Fetch-based API client for the SLZ ERP backend.
 *
 * Responsibilities:
 *  - Prefix requests with the configured base URL.
 *  - Inject the `Authorization: Bearer <access>` header.
 *  - Attach a fresh `X-Correlation-ID` (UUID) per request.
 *  - Parse JSON responses and throw a typed {@link ApiError} on non-2xx.
 *  - Transparently refresh the access token once on `401`, then retry.
 */
import { ApiError, type ApiErrorEnvelope, type ApiErrorType } from './types';

const DEFAULT_BASE_URL = 'http://localhost:8000/api/v1';

export function getBaseUrl(): string {
  const fromEnv = import.meta.env.VITE_API_BASE_URL;
  const base = (fromEnv && fromEnv.trim()) || DEFAULT_BASE_URL;
  return base.replace(/\/+$/, '');
}

/** Generate a RFC-4122-ish UUID, using the platform crypto when available. */
export function generateCorrelationId(): string {
  const cryptoObj = globalThis.crypto as Crypto | undefined;
  if (cryptoObj && typeof cryptoObj.randomUUID === 'function') {
    return cryptoObj.randomUUID();
  }
  // Fallback for environments without crypto.randomUUID.
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

/**
 * Callbacks the client uses to read/update auth state. Registered by the
 * auth layer via {@link configureTokenProvider} to avoid a circular import.
 */
export interface TokenProvider {
  getAccessToken(): string | null;
  getRefreshToken(): string | null;
  /** Persist a freshly-issued access token after a successful refresh. */
  onAccessTokenRefreshed(access: string): void;
  /** Called when refresh fails / session can no longer be recovered. */
  onAuthFailure(): void;
}

let tokenProvider: TokenProvider | null = null;

/** Active company ID set by AuthContext via configureActiveCompany. */
let activeCompanyId: string | null = null;

export function setActiveCompanyId(id: string | null): void {
  activeCompanyId = id;
}

export function getActiveCompanyId(): string | null {
  return activeCompanyId;
}

export function configureTokenProvider(provider: TokenProvider | null): void {
  tokenProvider = provider;
}

export interface RequestOptions extends Omit<RequestInit, 'body' | 'headers'> {
  /** JSON body — serialized automatically. */
  json?: unknown;
  /**
   * Multipart body (file uploads). When set, the browser sets the
   * `multipart/form-data` boundary itself, so we deliberately do NOT set a
   * `Content-Type` header for it.
   */
  form?: FormData;
  headers?: Record<string, string>;
  /** Send the Authorization header (default true). */
  auth?: boolean;
  /** Internal: prevents infinite refresh recursion. */
  _isRetry?: boolean;
}

function buildUrl(path: string): string {
  if (/^https?:\/\//i.test(path)) return path;
  const suffix = path.startsWith('/') ? path : `/${path}`;
  return `${getBaseUrl()}${suffix}`;
}

async function parseJsonSafe(response: Response): Promise<unknown> {
  const text = await response.text();
  if (!text) return null;
  try {
    return JSON.parse(text) as unknown;
  } catch {
    return text;
  }
}

function isErrorEnvelope(value: unknown): value is ApiErrorEnvelope {
  return (
    typeof value === 'object' &&
    value !== null &&
    'error' in value &&
    typeof (value as { error: unknown }).error === 'object' &&
    (value as { error: unknown }).error !== null
  );
}

const STATUS_TO_TYPE: Record<number, ApiErrorType> = {
  400: 'ValidationError',
  401: 'AuthenticationError',
  403: 'AuthorizationError',
  404: 'NotFoundError',
  409: 'ConflictError',
  422: 'ValidationError',
  429: 'ThrottledError',
  500: 'SystemError',
};

function toApiError(
  status: number,
  payload: unknown,
  correlationId: string,
): ApiError {
  if (isErrorEnvelope(payload)) {
    const env = payload.error;
    return new ApiError({
      type: env.type,
      message: env.message,
      details: env.details,
      code: env.code ?? null,
      correlationId: env.correlation_id ?? correlationId,
      status,
    });
  }
  const type = STATUS_TO_TYPE[status] ?? 'SystemError';
  const message =
    typeof payload === 'string' && payload
      ? payload
      : `Request failed with status ${status}`;
  return new ApiError({ type, message, correlationId, status });
}

// Single in-flight refresh shared across concurrent 401s.
let refreshInFlight: Promise<string | null> | null = null;

async function refreshAccessToken(): Promise<string | null> {
  if (!tokenProvider) return null;
  const refresh = tokenProvider.getRefreshToken();
  if (!refresh) return null;

  if (!refreshInFlight) {
    refreshInFlight = (async (): Promise<string | null> => {
      try {
        const res = await fetch(buildUrl('/auth/refresh/'), {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Accept: 'application/json',
            'X-Correlation-ID': generateCorrelationId(),
          },
          body: JSON.stringify({ refresh }),
        });
        if (!res.ok) {
          tokenProvider?.onAuthFailure();
          return null;
        }
        const data = (await parseJsonSafe(res)) as { access?: string } | null;
        const access = data?.access ?? null;
        if (access) {
          tokenProvider?.onAccessTokenRefreshed(access);
          return access;
        }
        tokenProvider?.onAuthFailure();
        return null;
      } catch {
        tokenProvider?.onAuthFailure();
        return null;
      } finally {
        refreshInFlight = null;
      }
    })();
  }
  return refreshInFlight;
}

/**
 * Perform a request and return the parsed JSON body typed as `T`.
 * Throws {@link ApiError} on any non-2xx response.
 */
export async function request<T = unknown>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const {
    json,
    form,
    headers: extraHeaders,
    auth = true,
    _isRetry = false,
    ...rest
  } = options;

  const correlationId = generateCorrelationId();
  const headers: Record<string, string> = {
    Accept: 'application/json',
    'X-Correlation-ID': correlationId,
    ...extraHeaders,
  };

  if (json !== undefined) {
    headers['Content-Type'] = 'application/json';
  }

  if (auth) {
    const access = tokenProvider?.getAccessToken();
    if (access) headers['Authorization'] = `Bearer ${access}`;
  }

  // Company-scoped RBAC (Q-055): attach X-SLZ-Company header when set.
  if (activeCompanyId) {
    headers['X-SLZ-Company'] = activeCompanyId;
  }

  const body =
    json !== undefined
      ? JSON.stringify(json)
      : form !== undefined
        ? form
        : (rest as RequestInit).body;

  const response = await fetch(buildUrl(path), {
    ...rest,
    headers,
    body,
  });

  // 401 → try a single refresh + retry (only for authed, non-retried requests).
  if (
    response.status === 401 &&
    auth &&
    !_isRetry &&
    tokenProvider?.getRefreshToken()
  ) {
    const newAccess = await refreshAccessToken();
    if (newAccess) {
      return request<T>(path, { ...options, _isRetry: true });
    }
  }

  if (!response.ok) {
    const payload = await parseJsonSafe(response);
    throw toApiError(response.status, payload, correlationId);
  }

  if (response.status === 204 || response.status === 205) {
    return undefined as T;
  }

  return (await parseJsonSafe(response)) as T;
}

/**
 * Perform an authenticated request and return the raw response body as a
 * {@link Blob}. Used for secure binary downloads (e.g. document attachments)
 * where an anchor `href` cannot carry the `Authorization` header.
 *
 * Mirrors {@link request}'s auth handling — Bearer token, correlation id, and a
 * single transparent 401→refresh→retry — but never JSON-parses the payload.
 * Throws {@link ApiError} on any non-2xx response.
 */
export async function requestBlob(
  path: string,
  options: RequestOptions = {},
): Promise<Blob> {
  const {
    headers: extraHeaders,
    auth = true,
    _isRetry = false,
    // json/form are meaningless for a download; ignore if passed.
    json: _json,
    form: _form,
    ...rest
  } = options;

  const correlationId = generateCorrelationId();
  const headers: Record<string, string> = {
    'X-Correlation-ID': correlationId,
    ...extraHeaders,
  };

  if (auth) {
    const access = tokenProvider?.getAccessToken();
    if (access) headers['Authorization'] = `Bearer ${access}`;
  }

  // Company-scoped RBAC (Q-055): attach X-SLZ-Company header when set.
  if (activeCompanyId) {
    headers['X-SLZ-Company'] = activeCompanyId;
  }

  const response = await fetch(buildUrl(path), { ...rest, headers });

  if (
    response.status === 401 &&
    auth &&
    !_isRetry &&
    tokenProvider?.getRefreshToken()
  ) {
    const newAccess = await refreshAccessToken();
    if (newAccess) {
      return requestBlob(path, { ...options, _isRetry: true });
    }
  }

  if (!response.ok) {
    const payload = await parseJsonSafe(response);
    throw toApiError(response.status, payload, correlationId);
  }

  return response.blob();
}

export const apiClient = {
  request,
  get: <T = unknown>(path: string, options?: RequestOptions) =>
    request<T>(path, { ...options, method: 'GET' }),
  post: <T = unknown>(path: string, json?: unknown, options?: RequestOptions) =>
    request<T>(path, { ...options, method: 'POST', json }),
  postForm: <T = unknown>(path: string, form: FormData, options?: RequestOptions) =>
    request<T>(path, { ...options, method: 'POST', form }),
  put: <T = unknown>(path: string, json?: unknown, options?: RequestOptions) =>
    request<T>(path, { ...options, method: 'PUT', json }),
  patch: <T = unknown>(path: string, json?: unknown, options?: RequestOptions) =>
    request<T>(path, { ...options, method: 'PATCH', json }),
  delete: <T = unknown>(path: string, options?: RequestOptions) =>
    request<T>(path, { ...options, method: 'DELETE' }),
  /** Fetch a binary resource (e.g. a secure file download) as a Blob. */
  getBlob: (path: string, options?: RequestOptions) =>
    requestBlob(path, { ...options, method: 'GET' }),
};
