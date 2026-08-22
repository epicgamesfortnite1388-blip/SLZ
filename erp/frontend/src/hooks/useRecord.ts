/**
 * Generic single-record fetching hook for detail screens.
 *
 * Mirrors {@link useCollection} but for one object retrieved from a REST detail
 * endpoint (e.g. `/partners/partners/{id}/`). Owns loading/error/data state,
 * cancels stale responses on unmount / param change, and exposes `reload` for
 * retry-after-error. Pass `path = null` to hold off fetching (e.g. while a route
 * param is still resolving).
 */
import { useCallback, useEffect, useRef, useState } from 'react';
import { apiClient } from '@/api/client';
import { ApiError } from '@/api/types';

export interface UseRecordResult<T> {
  data: T | null;
  loading: boolean;
  error: ApiError | null;
  reload: () => void;
}

export function useRecord<T>(path: string | null): UseRecordResult<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(path !== null);
  const [error, setError] = useState<ApiError | null>(null);
  const [nonce, setNonce] = useState(0);

  const requestId = useRef(0);

  const load = useCallback(() => {
    if (path === null) {
      setData(null);
      setLoading(false);
      setError(null);
      return;
    }
    const id = ++requestId.current;
    setLoading(true);
    setError(null);
    apiClient
      .get<T>(path)
      .then((result) => {
        if (id === requestId.current) setData(result);
      })
      .catch((err: unknown) => {
        if (id !== requestId.current) return;
        setError(
          err instanceof ApiError
            ? err
            : new ApiError({
                type: 'SystemError',
                message: 'Unexpected error',
                correlationId: '',
                status: 0,
              }),
        );
      })
      .finally(() => {
        if (id === requestId.current) setLoading(false);
      });
  }, [path]);

  useEffect(() => {
    load();
    return () => {
      // Invalidate any in-flight request tied to the previous params.
      requestId.current += 1;
    };
  }, [load, nonce]);

  const reload = useCallback(() => setNonce((n) => n + 1), []);

  return { data, loading, error, reload };
}
