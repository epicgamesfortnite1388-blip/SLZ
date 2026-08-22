import { renderHook, act, waitFor } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { useAsyncAction } from '../useAsyncAction';
import { ApiError } from '@/api/types';

describe('useAsyncAction', () => {
  it('reports success and clears the busy flag', async () => {
    const { result } = renderHook(() => useAsyncAction());
    let outcome: boolean | undefined;
    await act(async () => {
      outcome = await result.current.run('row1:retire', () => Promise.resolve('ok'));
    });
    expect(outcome).toBe(true);
    expect(result.current.busy).toBeNull();
    expect(result.current.error).toBeNull();
  });

  it('captures ApiError, never rejects, and exposes it to the caller', async () => {
    const { result } = renderHook(() => useAsyncAction());
    const failure = new ApiError({
      type: 'ConflictError',
      message: 'Illegal transition',
      correlationId: 'c-1',
      status: 409,
    });
    let outcome: boolean | undefined;
    await act(async () => {
      outcome = await result.current.run(
        'row2:approve',
        () => Promise.reject(failure),
      );
    });
    expect(outcome).toBe(false);
    expect(result.current.busy).toBeNull();
    expect(result.current.error).not.toBeNull();
    expect(result.current.error?.message).toBe('Illegal transition');
    // The error stays available for rendering until cleared.
    await waitFor(() => expect(result.current.error).not.toBeNull());
  });

  it('ignores a stale failure when a newer run started', async () => {
    const { result } = renderHook(() => useAsyncAction());
    const staleFailure = new ApiError({
      type: 'SystemError',
      message: 'stale',
      correlationId: '',
      status: 0,
    });
    let first: Promise<boolean> | undefined;
    act(() => {
      first = result.current.run('a', () => new Promise((_, reject) =>
        setTimeout(() => reject(staleFailure), 20),
      ));
    });
    await act(async () => {
      await result.current.run('b', () => Promise.resolve('ok'));
    });
    await act(async () => {
      await first;
    });
    // The slow first run failed after the second finished; its error must not
    // overwrite the clean state of the newer run.
    expect(result.current.busy).toBeNull();
    expect(result.current.error).toBeNull();
  });
});
