import * as React from "react";
import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";

import { StatTile } from "@shared/ui/StatTile";

describe("StatTile", () => {
  it("renders label, value, and breakdown", () => {
    render(
      <StatTile tone="primary" label="PTEG" value="12" breakdown="8 aprobados · 3 en revisión" />
    );
    expect(screen.getByText("PTEG")).toBeDefined();
    expect(screen.getByText("12")).toBeDefined();
    expect(screen.getByText(/8 aprobados/)).toBeDefined();
  });

  it("renders as an anchor when href is provided", () => {
    render(
      <StatTile tone="primary" label="PTEG" value="12" href="/dashboard/proyectos" />
    );
    const el = screen.getByRole("link", { name: /PTEG/i });
    expect(el).toBeDefined();
    expect((el as HTMLAnchorElement).getAttribute("href")).toBe("/dashboard/proyectos");
  });

  it("renders as a div when no href", () => {
    render(<StatTile tone="primary" label="PTEG" value="12" />);
    expect(screen.queryByRole("link")).toBeNull();
  });

  it("uses primary background for tone=primary", () => {
    const { container } = render(<StatTile tone="primary" label="X" value="1" />);
    const el = container.firstChild as HTMLElement;
    expect(el.className).toContain("bg-primary");
  });

  it("uses orange background for tone=accent", () => {
    const { container } = render(<StatTile tone="accent" label="X" value="1" />);
    const el = container.firstChild as HTMLElement;
    expect(el.className).toContain("bg-[var(--brand-orange)]");
  });
});
