import * as React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";

import { ListRow } from "@shared/ui/ListRow";

describe("ListRow", () => {
  it("renders title and subtitle", () => {
    render(<ListRow title="My Thesis" subtitle="Ana Perez · 2026-04-01" />);
    expect(screen.getByText("My Thesis")).toBeDefined();
    expect(screen.getByText(/Ana Perez/)).toBeDefined();
  });

  it("shows violet type pill for TEG", () => {
    const { container } = render(<ListRow title="T" type="tesis" />);
    const pill = container.querySelector("[data-slot='list-row-type']");
    expect(pill).not.toBeNull();
    expect((pill as HTMLElement).className).toContain("bg-[var(--accent-teg-soft-bg)]");
  });

  it("shows blue type pill for PTEG", () => {
    const { container } = render(<ListRow title="P" type="proyecto" />);
    const pill = container.querySelector("[data-slot='list-row-type']");
    expect((pill as HTMLElement).className).toContain("bg-[var(--accent-pteg-soft-bg)]");
  });

  it("renders status chip with matching label", () => {
    render(<ListRow title="P" status="rejected" />);
    expect(screen.getByText(/rechazado/i)).toBeDefined();
  });

  it("calls onClick when action button clicked", () => {
    const onClick = vi.fn();
    render(<ListRow title="P" onClick={onClick} />);
    fireEvent.click(screen.getByRole("button", { name: /abrir/i }));
    expect(onClick).toHaveBeenCalledOnce();
  });
});
