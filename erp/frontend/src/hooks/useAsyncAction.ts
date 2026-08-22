/**
 * Shared runner for row-level actions (status transitions, retire/reactivate,
 * approval steps…). Tracks which row/action is busy and captures any thrown
 * {@link ApiError} so callers can render it inline.
 *
 * The point of this hook is that `run` NEVER rejects: list pages call it with
 * `void run(...)` from onClick handlers, so an uncaught rejection would fail
 * silently and leave the user wondering why nothing happened.
 */
import { useCallback, useRef, useState } from 'react';
import { ApiError } from '@/api/types';

export interface UseAsyncActionResult {
  /** `"rowId:action"` while that action is in flight, else null. */
  busy: string | null;
  /** The captured failure of the most recent run, if any. */
  error: ApiError | null;
  /**
   * Run `fn` under `key`. Resolves to `true` on success, `false` on failure
   * (the failure is available via {@link error}). Never throws.
   */
  run: (key: string, fn: () => Promise<unknown>) => Promise<boolean>;
  clearError: () => void;
}

export function useAsyncAction(): UseAsyncActionResult {
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const requestId = useRef(0);

  const run = useCallback(async (key: string, fn: () => Promise<unknown>) => {
    const id = ++requestId.current;
    setBusy(key);
    setError(null);
    try {
      await fn();
      return true;
    } catch (err) {
      // Only the latest run may report its failure.
      if (id === requestId.current) {
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
      }
      return false;
    } finally {
      if (id === requestId.current) setBusy(null);
    }
  }, []);

  const clearError = useCallback(() => setError(null), []);

  return { busy, error, run, clearError };
}
