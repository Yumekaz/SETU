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
      { timeout: 500 },
    );

    unmount();
  });

  it("manual refresh invokes fetcher again", async () => {
    const fetcher = vi.fn().mockResolvedValue({ ok: true });
    const { result, unmount } = renderHook(() => usePolling(fetcher, 999_999, true));

    await waitFor(() => expect(result.current.data).toEqual({ ok: true }));
    const before = fetcher.mock.calls.length;

    await act(async () => {
      result.current.refresh();
    });
    await waitFor(() => expect(fetcher.mock.calls.length).toBe(before + 1));

    unmount();
  });
});