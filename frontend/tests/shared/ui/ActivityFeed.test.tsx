import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ActivityFeed } from "@shared/ui/ActivityFeed";

describe("ActivityFeed (restyled)", () => {
  it("renders rounded-square icon blocks", () => {
    const { container } = render(
      <ActivityFeed
        items={[
          { id: 1, kind: "submitted", text: "Nueva entrega de María", time: "Hoy" },
          { id: 2, kind: "reviewed", text: "Aprobado Diego", time: "Ayer" },
        ]}
      />,
    );
    const icons = container.querySelectorAll("[data-slot='activity-icon']");
    expect(icons.length).toBe(2);
    icons.forEach((el) => {
      expect(el.className).toMatch(/rounded-\[10px\]/);
    });
  });

  it("renders empty state when no items", () => {
    render(<ActivityFeed items={[]} />);
    expect(screen.getByText(/Sin actividad/i)).toBeInTheDocument();
  });
});
