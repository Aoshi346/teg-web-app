import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { NotificationItem } from "@features/notifications/components/NotificationItem";

const baseNotification = {
  id: 1,
  kind: "evaluation_received" as const,
  title: "Evaluación recibida",
  body: "Tu proyecto fue evaluado por el jurado.",
  payload: {},
  link_url: "",
  read_at: null,
  created_at: "2026-04-25T09:00:00Z",
};

describe("NotificationItem", () => {
  it("renders title, body, kind icon, and relative timestamp", () => {
    render(
      <NotificationItem
        notification={baseNotification}
        onMarkRead={vi.fn()}
        now={new Date("2026-04-25T09:05:00Z")}
      />,
    );

    expect(screen.getByText("Evaluación recibida")).toBeInTheDocument();
    expect(screen.getByText("Tu proyecto fue evaluado por el jurado.")).toBeInTheDocument();
    expect(screen.getByText(/hace \d+ minutos|hace unos segundos/i)).toBeInTheDocument();
  });

  it("shows the unread marker when notification is unread", () => {
    const { container } = render(
      <NotificationItem
        notification={{ ...baseNotification, read_at: null }}
        onMarkRead={vi.fn()}
        now={new Date("2026-04-25T09:05:00Z")}
      />,
    );

    expect(container.querySelector("[data-testid='notification-unread-marker']")).not.toBeNull();
  });

  it("does not show the unread marker when notification is read", () => {
    const { container } = render(
      <NotificationItem
        notification={{ ...baseNotification, read_at: "2026-04-25T10:00:00Z" }}
        onMarkRead={vi.fn()}
        now={new Date("2026-04-25T10:05:00Z")}
      />,
    );

    expect(container.querySelector("[data-testid='notification-unread-marker']")).toBeNull();
  });

  it("calls onMarkRead(id) when the item is clicked", async () => {
    const onMarkRead = vi.fn();
    const user = userEvent.setup();

    render(
      <NotificationItem
        notification={baseNotification}
        onMarkRead={onMarkRead}
        now={new Date("2026-04-25T09:05:00Z")}
      />,
    );

    await user.click(screen.getByText("Evaluación recibida"));

    expect(onMarkRead).toHaveBeenCalledWith(1);
  });

  it("renders as a link element when link_url is set", () => {
    render(
      <NotificationItem
        notification={{ ...baseNotification, link_url: "/dashboard/proyectos/1" }}
        onMarkRead={vi.fn()}
        now={new Date("2026-04-25T09:05:00Z")}
      />,
    );

    const link = screen.getByRole("link");
    expect(link).toHaveAttribute("href", "/dashboard/proyectos/1");
  });
});
