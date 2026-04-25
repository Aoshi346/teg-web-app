import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { NotificationsDropdown } from "@features/notifications/components/NotificationsDropdown";

const makeNotification = (id: number, read = false) => ({
  id,
  kind: "evaluation_received" as const,
  title: `Notificación ${id}`,
  body: `Descripción de notificación ${id}`,
  payload: {},
  link_url: "",
  read_at: read ? "2026-04-25T10:00:00Z" : null,
  created_at: "2026-04-25T09:00:00Z",
});

describe("NotificationsDropdown", () => {
  it("is closed by default and opens when the trigger is clicked", async () => {
    const user = userEvent.setup();

    render(
      <NotificationsDropdown
        notifications={[makeNotification(1)]}
        unreadCount={1}
        onMarkRead={vi.fn()}
        onMarkAllRead={vi.fn()}
        onOpen={vi.fn()}
      />,
    );

    expect(screen.queryByRole("menu")).toBeNull();

    await user.click(screen.getByRole("button", { name: /notificaciones|bell/i }));

    expect(screen.getByRole("menu")).toBeInTheDocument();
  });

  it("shows empty state message when there are no notifications", async () => {
    const user = userEvent.setup();

    render(
      <NotificationsDropdown
        notifications={[]}
        unreadCount={0}
        onMarkRead={vi.fn()}
        onMarkAllRead={vi.fn()}
        onOpen={vi.fn()}
      />,
    );

    await user.click(screen.getByRole("button", { name: /notificaciones|bell/i }));

    expect(screen.getByText(/No tienes notificaciones/i)).toBeInTheDocument();
  });

  it("renders up to 10 notification items from the results array", async () => {
    const user = userEvent.setup();
    const notifications = Array.from({ length: 12 }, (_, i) => makeNotification(i + 1));

    render(
      <NotificationsDropdown
        notifications={notifications}
        unreadCount={12}
        onMarkRead={vi.fn()}
        onMarkAllRead={vi.fn()}
        onOpen={vi.fn()}
      />,
    );

    await user.click(screen.getByRole("button", { name: /notificaciones|bell/i }));

    const items = screen.getAllByText(/Notificación \d+/);
    expect(items.length).toBeLessThanOrEqual(10);
  });

  it("contains a footer link to the settings notifications tab", async () => {
    const user = userEvent.setup();

    render(
      <NotificationsDropdown
        notifications={[makeNotification(1)]}
        unreadCount={1}
        onMarkRead={vi.fn()}
        onMarkAllRead={vi.fn()}
        onOpen={vi.fn()}
      />,
    );

    await user.click(screen.getByRole("button", { name: /notificaciones|bell/i }));

    const footerLink = screen.getByRole("link", { name: /ver todas/i });
    expect(footerLink).toHaveAttribute("href", "/dashboard/settings#notifications");
  });

  it("calls onMarkAllRead when 'Marcar todas como leídas' button is clicked", async () => {
    const onMarkAllRead = vi.fn();
    const user = userEvent.setup();

    render(
      <NotificationsDropdown
        notifications={[makeNotification(1)]}
        unreadCount={1}
        onMarkRead={vi.fn()}
        onMarkAllRead={onMarkAllRead}
        onOpen={vi.fn()}
      />,
    );

    await user.click(screen.getByRole("button", { name: /notificaciones|bell/i }));
    await user.click(screen.getByRole("button", { name: /marcar todas como leídas/i }));

    expect(onMarkAllRead).toHaveBeenCalledTimes(1);
  });
});
