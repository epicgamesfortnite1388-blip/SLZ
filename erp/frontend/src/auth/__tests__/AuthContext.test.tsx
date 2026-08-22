import { describe, it, expect, beforeEach, vi } from 'vitest';
import { act, renderHook, waitFor } from '@testing-library/react';
import type { ReactNode } from 'react';
import { AuthProvider, useAuth } from '../AuthContext';
import type { User } from '@/api/types';

function jsonResponse(status: number, body?: unknown): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    text: async () => (body === undefined ? '' : JSON.stringify(body)),
  } as unknown as Response;
}

function makeUser(overrides: Partial<User> = {}): User {
  return {
    id: 1,
    email: 'operator@example.com',
    full_name: 'Test Operator',
    language: 'en',
    timezone: 'Asia/Tehran',
    is_superuser: false,
    roles: ['operator'],
    permissions: ['organization.company.view'],
    ...overrides,
  };
}

const wrapper = ({ children }: { children: ReactNode }): JSX.Element => (
  <AuthProvider>{children}</AuthProvider>
);

beforeEach(() => {
  window.localStorage.clear();
});

describe('AuthContext', () => {
  it('starts unauthenticated once session restore settles', async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal('fetch', fetchMock);

    const { result } = renderHook(() => useAuth(), { wrapper });

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.user).toBeNull();
    // No refresh token persisted → no network call attempted.
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('login sets the user, isAuthenticated, and permission checks', async () => {
    const user = makeUser();
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes('/auth/login/')) {
        return jsonResponse(200, {
          access: 'access-token',
          refresh: 'refresh-token',
          user,
        });
      }
      throw new Error(`Unexpected fetch: ${url}`);
    });
    vi.stubGlobal('fetch', fetchMock);

    const { result } = renderHook(() => useAuth(), { wrapper });
    await waitFor(() => expect(result.current.loading).toBe(false));

    await act(async () => {
      await result.current.login('operator@example.com', 'secret');
    });

    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.user?.email).toBe('operator@example.com');

    // Permission present in the user's list.
    expect(result.current.hasPermission('organization.company.view')).toBe(true);
    // Permission absent from the list.
    expect(result.current.hasPermission('organization.company.delete')).toBe(
      false,
    );
  });

  it('grants every permission to a superuser (bypass)', async () => {
    const superuser = makeUser({
      is_superuser: true,
      permissions: [],
      email: 'admin@example.com',
    });
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes('/auth/login/')) {
        return jsonResponse(200, {
          access: 'access-token',
          refresh: 'refresh-token',
          user: superuser,
        });
      }
      throw new Error(`Unexpected fetch: ${url}`);
    });
    vi.stubGlobal('fetch', fetchMock);

    const { result } = renderHook(() => useAuth(), { wrapper });
    await waitFor(() => expect(result.current.loading).toBe(false));

    await act(async () => {
      await result.current.login('admin@example.com', 'secret');
    });

    expect(result.current.isAuthenticated).toBe(true);
    expect(result.current.hasPermission('anything.at.all')).toBe(true);
  });

  it('surfaces an ApiError on failed login', async () => {
    const fetchMock = vi.fn(async () =>
      jsonResponse(401, {
        error: {
          type: 'AuthenticationError',
          message: 'Invalid credentials',
          code: null,
          correlation_id: 'test-corr-id',
        },
      }),
    );
    vi.stubGlobal('fetch', fetchMock);

    const { result } = renderHook(() => useAuth(), { wrapper });
    await waitFor(() => expect(result.current.loading).toBe(false));

    await expect(
      act(async () => {
        await result.current.login('bad@example.com', 'nope');
      }),
    ).rejects.toMatchObject({
      name: 'ApiError',
      status: 401,
      type: 'AuthenticationError',
      message: 'Invalid credentials',
    });

    expect(result.current.isAuthenticated).toBe(false);
  });
});
