/**
 * @vitest-environment jsdom
 */
import { act, renderHook, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { usePolling } from "./usePolling";

describe("usePolling", () => {
  it("fetches on mount and refreshes on interval", async () => {
    let callCount = 0;
    const fetcher = vi.fn(async () => ({ n: ++callCount }));

    const { result, unmount } = renderHook(() => usePolling(fetcher, 80, true));

    await waitFor(() => expect(result.current.data).not.toBeNull());
    const firstN = result.current.data!.n;
    expect(firstN).toBeGreaterThanOrEqual(1);

    await waitFor(
      () => expect(result.current.data!.n).toBeGreaterThan(firstN),
      { timeout: 2000 },
    );

    unmount();
  });

  it("manual refresh invokes fetcher again and updates data", async () => {
    const fetcher = vi
      .fn()
      .mockResolvedValueOnce({ n: 1 })
      .mockResolvedValueOnce({ n: 2 });
    const { result, unmount } = renderHook(() => usePolling(fetcher, 999_999, true));

    await waitFor(() => expect(result.current.data).toEqual({ n: 1 }));
    const before = fetcher.mock.calls.length;

    await act(async () => {
      result.current.refresh();
    });
    await waitFor(() => expect(fetcher.mock.calls.length).toBe(before + 1));
    await waitFor(() => expect(result.current.data).toEqual({ n: 2 }));

    unmount();
  });

  it("does not fetch when disabled, then fetches when enabled", async () => {
    const fetcher = vi.fn().mockResolvedValue({ ready: true });
    const { result, rerender, unmount } = renderHook(
      ({ enabled }) => usePolling(fetcher, 60_000, enabled),
      { initialProps: { enabled: false } },
    );

    await act(async () => {
      await new Promise((r) => setTimeout(r, 50));
    });
    expect(fetcher).not.toHaveBeenCalled();
    expect(result.current.data).toBeNull();

    rerender({ enabled: true });
    await waitFor(() => expect(result.current.data).toEqual({ ready: true }));
    expect(fetcher).toHaveBeenCalled();

    unmount();
  });

  it("surfaces fetch errors and clears loading", async () => {
    const fetcher = vi.fn().mockRejectedValue(new Error("network down"));
    const { result, unmount } = renderHook(() => usePolling(fetcher, 999_999, true));

    await waitFor(() => expect(result.current.error).toBe("network down"));
    expect(result.current.loading).toBe(false);
    expect(result.current.data).toBeNull();

    unmount();
  });

  it("sets loading during manual refresh", async () => {
    let resolveFetch: (v: { ok: boolean }) => void = () => {};
    const fetcher = vi.fn(
      () =>
        new Promise<{ ok: boolean }>((resolve) => {
          resolveFetch = resolve;
        }),
    );
    const { result, unmount } = renderHook(() => usePolling(fetcher, 999_999, true));

    await waitFor(() => expect(fetcher).toHaveBeenCalled());
    resolveFetch({ ok: true });
    await waitFor(() => expect(result.current.data).toEqual({ ok: true }));

    const pending = new Promise<{ ok: boolean }>((resolve) => {
      resolveFetch = resolve;
    });
    fetcher.mockReturnValueOnce(pending);

    act(() => {
      result.current.refresh();
    });
    expect(result.current.loading).toBe(true);

    await act(async () => {
      resolveFetch({ ok: true });
      await pending;
    });
    await waitFor(() => expect(result.current.loading).toBe(false));

    unmount();
  });

  it("stops interval polling after unmount", async () => {
    const fetcher = vi.fn().mockResolvedValue({ tick: 1 });
    const { unmount } = renderHook(() => usePolling(fetcher, 40, true));

    await waitFor(() => expect(fetcher.mock.calls.length).toBeGreaterThanOrEqual(1));
    const callsAtUnmount = fetcher.mock.calls.length;
    unmount();

    await act(async () => {
      await new Promise((r) => setTimeout(r, 120));
    });
    expect(fetcher.mock.calls.length).toBe(callsAtUnmount);
  });
});