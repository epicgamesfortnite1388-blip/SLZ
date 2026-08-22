/**
 * Generic collection-fetching hook for master-data browse screens.
 *
 * Owns loading/error/data state, supports search + pagination, and exposes a
 * `reload` for retry-after-error. Cancels stale responses on unmount / param
 * change so a slow request can never overwrite fresher state.
 */
import { useCallback, useEffect, useRef, useState } from 'react';
import { fetchCollection, type CollectionQuery, type Paginated } from '@/api/masterData';
import { ApiError } from '@/api/types';

export interface UseCollectionResult<T> {
  data: Paginated<T> | null;
  loading: boolean;
  error: ApiError | null;
  page: number;
  search: string;
  setPage: (page: number) => void;
  setSearch: (search: string) => void;
  reload: () => void;
}

export function useCollection<T>(
  path: string,
  pageSize = 25,
): UseCollectionResult<T> {
  const [data, setData] = useState<Paginated<T> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);
  const [page, setPage] = useState(1);
  const [search, setSearchState] = useState('');
  const [nonce, setNonce] = useState(0);

  const requestId = useRef(0);

  const load = useCallback(
    (query: CollectionQuery) => {
      const id = ++requestId.current;
      setLoading(true);
      setError(null);
      fetchCollection<T>(path, query)
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
    },
    [path],
  );

  useEffect(() => {
    load({ page, pageSize, search });
    return () => {
      // Invalidate any in-flight request tied to the previous params.
      requestId.current += 1;
    };
  }, [load, page, pageSize, search, nonce]);

  const setSearch = useCallback((next: string) => {
    setSearchState(next);
    setPage(1);
  }, []);

  const reload = useCallback(() => setNonce((n) => n + 1), []);

  return { data, loading, error, page, search, setPage, setSearch, reload };
}
