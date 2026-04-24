import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { StatTile } from "@shared/ui/StatTile";

describe("StatTile", () => {
  it("renders hero tone with chips", () => {
    render(
      <StatTile
        tone="hero"
        label="Proyectos PTEG"
        value="12"
        chips={[
          { label: "Rev 1", count: 5, href: "/dashboard/proyectos?state=pending_review_1" },
          { label: "Defensa", count: 3, href: "/dashboard/proyectos?state=pending_defense" },
        ]}
      />,
    );
    expect(screen.getByText("Proyectos PTEG")).toBeInTheDocument();
    expect(screen.getByText("12")).toBeInTheDocument();
    expect(screen.getByText("Rev 1")).toBeInTheDocument();
    expect(screen.getByText("5")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Rev 1/i })).toHaveAttribute(
      "href",
      "/dashboard/proyectos?state=pending_review_1",
    );
  });

  it("renders secondary tone with urgent pulse dot", () => {
    const { container } = render(
      <StatTile tone="amber" label="Tu acción" value="5" urgent />,
    );
    expect(screen.getByText("Tu acción")).toBeInTheDocument();
    expect(container.querySelector(".pulse-soft")).not.toBeNull();
  });

  it("renders secondary tone without urgent dot when flag absent", () => {
    const { container } = render(<StatTile tone="green" label="Aprobados" value="3" />);
    expect(container.querySelector(".pulse-soft")).toBeNull();
  });

  it("wraps in Link when href provided and no chips", () => {
    render(<StatTile tone="blue" label="Tesis" value="7" href="/dashboard/tesis" />);
    expect(screen.getByRole("link")).toHaveAttribute("href", "/dashboard/tesis");
  });
});
