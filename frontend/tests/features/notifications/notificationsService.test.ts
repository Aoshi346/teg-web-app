import { describe, it, expect, vi, beforeEach } from "vitest";
import { api } from "@shared/api/api";
import {
  listNotifications,
  getUnreadCount,
  markRead,
  markAllRead,
} from "@features/notifications/api/notificationsService";

vi.mock("@shared/api/api", () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

const mockApi = api as { get: ReturnType<typeof vi.fn>; post: ReturnType<typeof vi.fn> };

beforeEach(() => {
  vi.clearAllMocks();
});

describe("notificationsService", () => {
  describe("listNotifications", () => {
    it("GETs /api/notifications/?page=1 and returns paginated result", async () => {
      const payload = {
        count: 3,
        next: null,
        previous: null,
        results: [
          {
            id: 1,
            kind: "evaluation_received",
            title: "Evaluación recibida",
            body: "Tu proyecto fue evaluado.",
            payload: {},
            link_url: "/dashboard/proyectos/1",
            read_at: null,
            created_at: "2026-04-25T10:00:00Z",
          },
        ],
      };
      mockApi.get.mockResolvedValueOnce(payload);

      const result = await listNotifications(1);

      expect(mockApi.get).toHaveBeenCalledWith("/notifications/?page=1");
      expect(result).toEqual(payload);
      expect(result.count).toBe(3);
      expect(result.results).toHaveLength(1);
    });
  });

  describe("getUnreadCount", () => {
    it("GETs /api/notifications/unread_count/ and returns {count: number}", async () => {
      mockApi.get.mockResolvedValueOnce({ count: 5 });

      const result = await getUnreadCount();

      expect(mockApi.get).toHaveBeenCalledWith("/notifications/unread_count/");
      expect(result).toEqual({ count: 5 });
    });
  });

  describe("markRead", () => {
    it("POSTs to /api/notifications/{id}/mark_read/ and returns updated unread count", async () => {
      mockApi.post.mockResolvedValueOnce({ count: 4 });

      const result = await markRead(7);

      expect(mockApi.post).toHaveBeenCalledWith("/notifications/7/mark_read/", {});
      expect(result).toEqual({ count: 4 });
    });

    it("propagates a 404 error when the notification does not belong to the user", async () => {
      mockApi.post.mockRejectedValueOnce(new Error("Not found"));

      await expect(markRead(999)).rejects.toThrow("Not found");
    });
  });

  describe("markAllRead", () => {
    it("POSTs to /api/notifications/mark_all_read/ and returns {count: 0}", async () => {
      mockApi.post.mockResolvedValueOnce({ count: 0 });

      const result = await markAllRead();

      expect(mockApi.post).toHaveBeenCalledWith("/notifications/mark_all_read/", {});
      expect(result).toEqual({ count: 0 });
    });
  });

  describe("network error handling", () => {
    it("surfaces a normalized error when the network fails", async () => {
      mockApi.get.mockRejectedValueOnce(new Error("Network Error"));

      await expect(getUnreadCount()).rejects.toThrow("Network Error");
    });
  });
});
