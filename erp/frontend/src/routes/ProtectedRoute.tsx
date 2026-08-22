import type { ReactNode } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/auth/AuthContext';
import type { PermissionCode } from '@/api/types';
import { LoadingScreen } from '@/components/LoadingScreen';
import { ForbiddenPage } from '@/pages/ForbiddenPage';

export interface ProtectedRouteProps {
  children: ReactNode;
  /** If set, the user must hold this permission (superuser bypass applies). */
  requiredPermission?: PermissionCode;
}

/**
 * Route guard:
 *  - while the session is being restored, shows a loading screen;
 *  - if unauthenticated, redirects to /login (preserving the target location);
 *  - if authenticated but lacking `requiredPermission`, shows the 403 view.
 */
export function ProtectedRoute({
  children,
  requiredPermission,
}: ProtectedRouteProps): JSX.Element {
  const { isAuthenticated, loading, hasPermission } = useAuth();
  const location = useLocation();

  if (loading) {
    return <LoadingScreen />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  if (requiredPermission && !hasPermission(requiredPermission)) {
    return <ForbiddenPage />;
  }

  return <>{children}</>;
}
