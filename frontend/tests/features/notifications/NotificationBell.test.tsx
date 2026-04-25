import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { NotificationBell } from "@features/notifications/components/NotificationBell";

vi.mock("@features/notifications/hooks/useNotifications", () => ({
  useNotifications: vi.fn(() => ({
    unreadCount: 0,
    notifications: [],
    markRead: vi.fn(),
    markAllRead: vi.fn(),
    openDropdown: vi.fn(),
  })),
}));

import { useNotifications } from "@features/notifications/hooks/useNotifications";

const mockUseNotifications = useNotifications as ReturnType<typeof vi.fn>;

describe("NotificationBell", () => {
  it("renders a Bell icon button", () => {
    mockUseNotifications.mockReturnValue({
      unreadCount: 0,
      notifications: [],
      markRead: vi.fn(),
      markAllRead: vi.fn(),
      openDropdown: vi.fn(),
    });

    render(<NotificationBell />);

    const button = screen.getByRole("button");
    expect(button).toBeInTheDocument();
  });

  it("does not show a badge when unreadCount is 0", () => {
    mockUseNotifications.mockReturnValue({
      unreadCount: 0,
      notifications: [],
      markRead: vi.fn(),
      markAllRead: vi.fn(),
      openDropdown: vi.fn(),
    });

    const { container } = render(<NotificationBell />);

    expect(container.querySelector("[data-testid='notification-badge']")).toBeNull();
  });

  it("shows a badge with the count when unreadCount is greater than 0", () => {
    mockUseNotifications.mockReturnValue({
      unreadCount: 3,
      notifications: [],
      markRead: vi.fn(),
      markAllRead: vi.fn(),
      openDropdown: vi.fn(),
    });

    render(<NotificationBell />);

    const badge = screen.getByTestId("notification-badge");
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveTextContent("3");
  });

  it("toggles the dropdown open and closed when the bell is clicked", async () => {
    mockUseNotifications.mockReturnValue({
      unreadCount: 1,
      notifications: [],
      markRead: vi.fn(),
      markAllRead: vi.fn(),
      openDropdown: vi.fn(),
    });

    const user = userEvent.setup();

    render(<NotificationBell />);

    const button = screen.getByRole("button");

    await user.click(button);
    expect(screen.getByRole("menu")).toBeInTheDocument();

    await user.click(button);
    expect(screen.queryByRole("menu")).toBeNull();
  });
});
