/**
 * Auth-related API calls, matching the SLZ ERP backend contract.
 */
import { apiClient } from './client';
import type { LoginResponse, RefreshResponse, User } from './types';

export interface LoginCredentials {
  email: string;
  password: string;
}

/** POST /auth/login/ → { access, refresh, user } */
export function login(credentials: LoginCredentials): Promise<LoginResponse> {
  return apiClient.post<LoginResponse>('/auth/login/', credentials, {
    auth: false,
  });
}

/** POST /auth/refresh/ → { access } */
export function refresh(refreshToken: string): Promise<RefreshResponse> {
  return apiClient.post<RefreshResponse>(
    '/auth/refresh/',
    { refresh: refreshToken },
    { auth: false },
  );
}

/** POST /auth/logout/ (Bearer) → 205 */
export function logout(refreshToken: string): Promise<void> {
  return apiClient.post<void>('/auth/logout/', { refresh: refreshToken });
}

/** GET /auth/me/ (Bearer) → user object */
export function getMe(): Promise<User> {
  return apiClient.get<User>('/auth/me/');
}

export const authApi = { login, refresh, logout, getMe };
