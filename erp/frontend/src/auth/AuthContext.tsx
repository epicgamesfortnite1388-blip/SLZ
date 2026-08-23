/**
 * Authentication context for the SLZ ERP frontend.
 *
 * - Access token is held in memory (a ref) for synchronous reads by the API client.
 * - Refresh token is persisted in localStorage so a reload can restore the session.
 * - On mount, if a refresh token exists, the session is restored via refresh + getMe.
 */
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react';
import { authApi } from '@/api/auth';
import { configureTokenProvider, setActiveCompanyId } from '@/api/client';
import type { PermissionCode, User } from '@/api/types';
import i18n from '@/i18n';

const REFRESH_STORAGE_KEY = 'slz_erp_refresh_token';

function readStoredRefreshToken(): string | null {
  try {
    return window.localStorage.getItem(REFRESH_STORAGE_KEY);
  } catch {
    return null;
  }
}

function writeStoredRefreshToken(token: string | null): void {
  try {
    if (token) {
      window.localStorage.setItem(REFRESH_STORAGE_KEY, token);
    } else {
      window.localStorage.removeItem(REFRESH_STORAGE_KEY);
    }
  } catch {
    /* localStorage unavailable — session simply won't persist. */
  }
}

export interface AuthContextValue {
  user: User | null;
  isAuthenticated: boolean;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  hasPermission: (code: PermissionCode) => boolean;
  /** Currently selected company ID (Q-055). */
  activeCompanyId: string | null;
  /** Switch the active company context (sends X-SLZ-Company header). */
  setActiveCompany: (companyId: string | null) => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }): JSX.Element {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeCompanyId, setActiveCompanyIdState] = useState<string | null>(null);

  // Tokens live in refs so the API client's TokenProvider can read them synchronously.
  const accessTokenRef = useRef<string | null>(null);
  const refreshTokenRef = useRef<string | null>(readStoredRefreshToken());

  const setRefreshToken = useCallback((token: string | null) => {
    refreshTokenRef.current = token;
    writeStoredRefreshToken(token);
  }, []);

  const clearSession = useCallback(() => {
    accessTokenRef.current = null;
    setRefreshToken(null);
    setUser(null);
  }, [setRefreshToken]);

  const applyLanguage = useCallback((lang: string | undefined) => {
    if (lang && (lang === 'fa' || lang === 'en') && i18n.language !== lang) {
      void i18n.changeLanguage(lang);
    }
  }, []);

  // Wire the API client to this context's token state.
  useEffect(() => {
    configureTokenProvider({
      getAccessToken: () => accessTokenRef.current,
      getRefreshToken: () => refreshTokenRef.current,
      onAccessTokenRefreshed: (access) => {
        accessTokenRef.current = access;
      },
      onAuthFailure: () => {
        clearSession();
      },
    });
    return () => configureTokenProvider(null);
  }, [clearSession]);

  // Restore session on mount from a persisted refresh token.
  useEffect(() => {
    let cancelled = false;

    async function restore(): Promise<void> {
      const storedRefresh = refreshTokenRef.current;
      if (!storedRefresh) {
        if (!cancelled) setLoading(false);
        return;
      }
      try {
        const { access } = await authApi.refresh(storedRefresh);
        accessTokenRef.current = access;
        const me = await authApi.getMe();
        if (cancelled) return;
        setUser(me);
        applyLanguage(me.language);
      } catch {
        if (!cancelled) clearSession();
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    void restore();
    return () => {
      cancelled = true;
    };
  }, [applyLanguage, clearSession]);

  const login = useCallback(
    async (email: string, password: string): Promise<void> => {
      const result = await authApi.login({ email, password });
      accessTokenRef.current = result.access;
      setRefreshToken(result.refresh);
      setUser(result.user);
      applyLanguage(result.user.language);
    },
    [applyLanguage, setRefreshToken],
  );

  const logout = useCallback(async (): Promise<void> => {
    const refreshToken = refreshTokenRef.current;
    try {
      if (refreshToken) {
        await authApi.logout(refreshToken);
      }
    } catch {
      /* Ignore network/logout errors — clear the session regardless. */
    } finally {
      clearSession();
    }
  }, [clearSession]);

  const hasPermission = useCallback(
    (code: PermissionCode): boolean => {
      if (!user) return false;
      if (user.is_superuser) return true;
      // When a company is selected, check per-company permissions.
      if (activeCompanyId && user.permissions_by_company?.[activeCompanyId]) {
        return user.permissions_by_company[activeCompanyId].includes(code);
      }
      return user.permissions.includes(code);
    },
    [user, activeCompanyId],
  );

  const setActiveCompany = useCallback((companyId: string | null) => {
    setActiveCompanyId(companyId);
    setActiveCompanyIdState(companyId);
    // Broadcast so every mounted collection/detail refetches in the new
    // company context — prevents stale cross-company data on screen.
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('slz:company-changed'));
    }
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isAuthenticated: user !== null,
      loading,
      login,
      logout,
      hasPermission,
      activeCompanyId,
      setActiveCompany,
    }),
    [user, loading, login, logout, hasPermission, activeCompanyId, setActiveCompany],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return ctx;
}
