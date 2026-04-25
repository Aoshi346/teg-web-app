import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ListRow } from "@shared/ui/ListRow";

describe("ListRow (restyled)", () => {
  it("renders title, breadcrumb subtitle parts, and pending status badge", () => {
    render(
      <ListRow
        title="Sistema de gestión hospitalaria"
        subtitle="María Pérez · 22 abr · PTEG"
        state="pending_review_1"
        href="/dashboard/proyectos/1"
      />,
    );
    expect(screen.getByText("Sistema de gestión hospitalaria")).toBeInTheDocument();
    expect(screen.getByText(/María Pérez/)).toBeInTheDocument();
    expect(screen.getByText(/22 abr/)).toBeInTheDocument();
    expect(screen.getByText(/Pendiente|Revisión/i)).toBeInTheDocument();
  });

  it("renders ring indicator for status", () => {
    const { container } = render(
      <ListRow title="X" subtitle="y" state="failed_final" href="/x" />,
    );
    expect(container.querySelector("[data-slot='list-row-indicator']")).not.toBeNull();
  });
});
