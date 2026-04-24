import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { SemesterRow } from "@features/settings/components/admin/semesters/SemesterRow";

describe("SemesterRow", () => {
  it("disables Activar and Eliminar for the active semester", () => {
    render(<SemesterRow
      semester={{ id: 1, period: "2026-01", start_month: 1, end_month: 6, is_active: true, label: "Enero 2026 – Junio 2026", project_count: 5, created_at: "2026-01-01" }}
      onActivate={vi.fn()} onDelete={vi.fn()}
    />);
    expect(screen.getByRole("button", { name: /✓ activo/i })).toBeDisabled();
    expect(screen.getByRole("button", { name: /eliminar/i })).toBeDisabled();
  });

  it("disables Eliminar when project_count > 0", () => {
    render(<SemesterRow
      semester={{ id: 2, period: "2025-02", start_month: 9, end_month: 1, is_active: false, label: "Septiembre 2025 – Enero 2026", project_count: 3, created_at: "2025-09-01" }}
      onActivate={vi.fn()} onDelete={vi.fn()}
    />);
    const del = screen.getByRole("button", { name: /eliminar/i });
    expect(del).toBeDisabled();
    expect(del.getAttribute("title")).toMatch(/3 proyectos/i);
  });

  it("enables Eliminar for inactive semesters with zero projects", () => {
    render(<SemesterRow
      semester={{ id: 3, period: "2026-02", start_month: 9, end_month: 1, is_active: false, label: "", project_count: 0, created_at: "2026-09-01" }}
      onActivate={vi.fn()} onDelete={vi.fn()}
    />);
    expect(screen.getByRole("button", { name: /eliminar/i })).not.toBeDisabled();
  });
});
