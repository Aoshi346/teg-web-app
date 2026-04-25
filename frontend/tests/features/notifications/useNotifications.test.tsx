import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useNotifications } from "@features/notifications/hooks/useNotifications";
import * as notificationsService from "@features/notifications/api/notificationsService";

vi.mock("@features/notifications/api/notificationsService");

const mockedService = notificationsService as {
  listNotifications: ReturnType<typeof vi.fn>;
  getUnreadCount: ReturnType<typeof vi.fn>;
  markRead: ReturnType<typeof vi.fn>;
  markAllRead: ReturnType<typeof vi.fn>;
};

const makeNotification = (id: number, read = false) => ({
  id,
  kind: "evaluation_received",
  title: `Notificación ${id}`,
  body: "Descripción",
  payload: {},
  link_url: "",
  read_at: read ? "2026-04-25T10:00:00Z" : null,
  created_at: "2026-04-25T09:00:00Z",
});

const makeListResponse = (ids: number[]) => ({
  count: ids.length,
  next: null,
  previous: null,
  results: ids.map((id) => makeNotification(id)),
});

beforeEach(() => {
  vi.useFakeTimers();
  vi.clearAllMocks();
  mockedService.getUnreadCount.mockResolvedValue({ count: 2 });
  mockedService.listNotifications.mockResolvedValue(makeListResponse([1, 2]));
  mockedService.markRead.mockResolvedValue({ count: 1 });
  mockedService.markAllRead.mockResolvedValue({ count: 0 });
  Object.defineProperty(document, "visibilityState", {
    configurable: true,
    value: "visible",
  });
});

afterEach(() => {
  vi.useRealTimers();
});

describe("useNotifications", () => {
  it("fetches unread count and first page on initial mount", async () => {
    const { result } = renderHook(() => useNotifications());

    await act(async () => {
      await vi.runAllTimersAsync();
    });

    expect(mockedService.getUnreadCount).toHaveBeenCalledTimes(1);
    expect(mockedService.listNotifications).toHaveBeenCalledWith(1);
    expect(result.current.unreadCount).toBe(2);
    expect(result.current.notifications).toHaveLength(2);
  });

  it("polls getUnreadCount every 60 seconds", async () => {
    renderHook(() => useNotifications());

    await act(async () => {
      await vi.runAllTimersAsync();
    });

    mockedService.getUnreadCount.mockResolvedValue({ count: 3 });

    await act(async () => {
      vi.advanceTimersByTime(30_000);
      await vi.runAllTimersAsync();
    });

    expect(mockedService.getUnreadCount).toHaveBeenCalledTimes(2);
  });

  it("pauses polling when document.visibilityState is hidden", async () => {
    renderHook(() => useNotifications());

    await act(async () => {
      await vi.runAllTimersAsync();
    });

    const callCountAfterMount = mockedService.getUnreadCount.mock.calls.length;

    Object.defineProperty(document, "visibilityState", {
      configurable: true,
      value: "hidden",
    });
    document.dispatchEvent(new Event("visibilitychange"));

    await act(async () => {
      vi.advanceTimersByTime(30_000);
      await vi.runAllTimersAsync();
    });

    expect(mockedService.getUnreadCount.mock.calls.length).toBe(callCountAfterMount);
  });

  it("resumes polling when visibilityState returns to visible", async () => {
    renderHook(() => useNotifications());

    await act(async () => {
      await vi.runAllTimersAsync();
    });

    Object.defineProperty(document, "visibilityState", {
      configurable: true,
      value: "hidden",
    });
    document.dispatchEvent(new Event("visibilitychange"));

    await act(async () => {
      vi.advanceTimersByTime(30_000);
      await vi.runAllTimersAsync();
    });

    const callCountWhileHidden = mockedService.getUnreadCount.mock.calls.length;

    Object.defineProperty(document, "visibilityState", {
      configurable: true,
      value: "visible",
    });
    document.dispatchEvent(new Event("visibilitychange"));

    await act(async () => {
      await vi.runAllTimersAsync();
    });

    expect(mockedService.getUnreadCount.mock.calls.length).toBeGreaterThan(callCountWhileHidden);
  });

  it("openDropdown() triggers an immediate refetch of the notification list", async () => {
    const { result } = renderHook(() => useNotifications());

    await act(async () => {
      await vi.runAllTimersAsync();
    });

    const listCallsBefore = mockedService.listNotifications.mock.calls.length;

    await act(async () => {
      result.current.openDropdown();
      await vi.runAllTimersAsync();
    });

    expect(mockedService.listNotifications.mock.calls.length).toBeGreaterThan(listCallsBefore);
  });

  it("markRead(id) calls service, optimistically updates the row, decrements unread count", async () => {
    const { result } = renderHook(() => useNotifications());

    await act(async () => {
      await vi.runAllTimersAsync();
    });

    await act(async () => {
      await result.current.markRead(1);
    });

    expect(mockedService.markRead).toHaveBeenCalledWith(1);
    const updatedRow = result.current.notifications.find((n) => n.id === 1);
    expect(updatedRow?.read_at).not.toBeNull();
    expect(result.current.unreadCount).toBe(1);
  });

  it("markAllRead() calls service, sets all rows to read, sets unread to 0", async () => {
    const { result } = renderHook(() => useNotifications());

    await act(async () => {
      await vi.runAllTimersAsync();
    });

    await act(async () => {
      await result.current.markAllRead();
    });

    expect(mockedService.markAllRead).toHaveBeenCalledTimes(1);
    expect(result.current.unreadCount).toBe(0);
    result.current.notifications.forEach((n) => {
      expect(n.read_at).not.toBeNull();
    });
  });

  it("unmount clears the polling interval without console errors", async () => {
    const { unmount } = renderHook(() => useNotifications());

    await act(async () => {
      await vi.runAllTimersAsync();
    });

    const clearIntervalSpy = vi.spyOn(global, "clearInterval");

    unmount();

    expect(clearIntervalSpy).toHaveBeenCalled();
    clearIntervalSpy.mockRestore();
  });
});
