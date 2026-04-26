import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import type { Project } from "@features/projects/types/project";
import { cardAction } from "@features/projects/lib/cardAction";
import { seguimientoColumnsFor } from "@features/projects/lib/seguimientoColumns";
import SeguimientoTable from "./SeguimientoTable";

// ---------------------------------------------------------------------------
// Fixture factory
// ---------------------------------------------------------------------------

function makeProject(overrides: Partial<Project> = {}): Project {
  return {
    id: 1,
    title: "Sistema de Gestión Académica",
    student: "Ana Pérez",
    advisorNames: ["Prof. Gómez"],
    reviewer: 42,
    reviewerName: "Dr. Torres",
    submittedDate: "2026-03-10",
    state: "pending_review_1",
    period: "2026-01",
    type: "proyecto",
    ...overrides,
  };
}

// Three canonical fixtures used across multiple tests.
// PTEG pending_review_1 with reviewer assigned.
const ptegPending = makeProject({
  id: 1,
  type: "proyecto",
  state: "pending_review_1",
  reviewer: 42,
  reviewerName: "Dr. Torres",
});

// TEG pending_entrega with no reviewer.
const tegNoReviewer = makeProject({
  id: 2,
  title: "Tesis sobre redes neuronales",
  student: "Carlos Díaz",
  type: "tesis",
  state: "pending_entrega",
  reviewer: null,
  reviewerName: null,
});

// PTEG approved (terminal).
const ptegApproved = makeProject({
  id: 3,
  title: "Análisis de datos financieros",
  student: "Lucía Vargas",
  type: "proyecto",
  state: "approved",
  reviewer: 42,
  reviewerName: "Dr. Torres",
});

// ---------------------------------------------------------------------------
// Column header label map (mirrors the component's expected render text).
// ---------------------------------------------------------------------------

const COLUMN_HEADER: Record<string, string> = {
  title:           "Trabajo",
  estudiante:      "Estudiante",
  tutorJurado:     "Tutor / Jurado",
  jurado:          "Jurado",
  estado:          "Estado",
  fase:            "Fase",
  ultimaActividad: "Última actividad",
  recibido:        "Recibido",
};

// ---------------------------------------------------------------------------
// Helper: render with a default pagination stub.
// ---------------------------------------------------------------------------

function renderTable(
  items: Project[],
  role: "Administrador" | "Jurado" | "Tutor",
  opts: {
    viewerId?: number;
    currentPage?: number;
    totalPages?: number;
    onPageChange?: ReturnType<typeof vi.fn>;
  } = {},
) {
  const onPageChange = opts.onPageChange ?? vi.fn();
  return render(
    <SeguimientoTable
      items={items}
      role={role}
      viewerId={opts.viewerId}
      pagination={{
        currentPage: opts.currentPage ?? 1,
        totalPages: opts.totalPages ?? 1,
        onPageChange,
      }}
    />,
  );
}

// ---------------------------------------------------------------------------
// 1. Column visibility per role
// ---------------------------------------------------------------------------

describe("SeguimientoTable — column visibility", () => {
  it("admin sees all expected column headers", () => {
    renderTable([ptegPending], "Administrador");
    const cols = seguimientoColumnsFor("Administrador").filter((c) => c !== "action");
    for (const key of cols) {
      const header = COLUMN_HEADER[key];
      expect(screen.getByText(header), `Expected header "${header}" to be present for admin`).toBeTruthy();
    }
  });

  it("admin does NOT see 'Jurado' standalone column", () => {
    renderTable([ptegPending], "Administrador");
    // Admin has tutorJurado, not a separate jurado column.
    const adminCols = seguimientoColumnsFor("Administrador");
    if (!adminCols.includes("jurado")) {
      expect(screen.queryByRole("columnheader", { name: "Jurado" })).toBeNull();
    }
  });

  it("jurado sees 'Tutor / Jurado' column header", () => {
    renderTable([ptegPending], "Jurado");
    expect(screen.getByText("Tutor / Jurado")).toBeTruthy();
  });

  it("jurado does NOT see 'Fase' column header", () => {
    renderTable([ptegPending], "Jurado");
    const juradoCols = seguimientoColumnsFor("Jurado");
    if (!juradoCols.includes("fase")) {
      expect(screen.queryByText("Fase")).toBeNull();
    }
  });

  it("tutor sees 'Jurado' column header instead of 'Tutor / Jurado'", () => {
    renderTable([ptegPending], "Tutor");
    expect(screen.getByText("Jurado")).toBeTruthy();
    expect(screen.queryByText("Tutor / Jurado")).toBeNull();
  });

  it("tutor sees 'Última actividad' column header", () => {
    renderTable([ptegPending], "Tutor");
    expect(screen.getByText("Última actividad")).toBeTruthy();
  });

  it("tutor does NOT see 'Fase' column header", () => {
    renderTable([ptegPending], "Tutor");
    const tutorCols = seguimientoColumnsFor("Tutor");
    if (!tutorCols.includes("fase")) {
      expect(screen.queryByText("Fase")).toBeNull();
    }
  });
});

// ---------------------------------------------------------------------------
// 2. StatePill renders once per row
// Judgment call: assert via the `.spill` class, which StatePill always applies.
// `data-testid` is not set on StatePill, and `.spill` is guaranteed by the
// component (it's the base class applied unconditionally in StatePill.tsx:57).
// ---------------------------------------------------------------------------

describe("SeguimientoTable — StatePill per row", () => {
  it("renders one StatePill per item (single item)", () => {
    const { container } = renderTable([ptegPending], "Administrador");
    expect(container.querySelectorAll(".spill")).toHaveLength(1);
  });

  it("renders one StatePill per item (multiple items)", () => {
    const { container } = renderTable([ptegPending, tegNoReviewer, ptegApproved], "Administrador");
    expect(container.querySelectorAll(".spill")).toHaveLength(3);
  });
});

// ---------------------------------------------------------------------------
// 3. Modality dot prefix in the title cell
// ---------------------------------------------------------------------------

describe("SeguimientoTable — modality dot prefix", () => {
  it("title cell has .tdot.pteg span for type='proyecto'", () => {
    const { container } = renderTable([ptegPending], "Administrador");
    expect(container.querySelector(".tdot.pteg")).not.toBeNull();
  });

  it("title cell has .tdot.teg span for type='tesis'", () => {
    const { container } = renderTable([tegNoReviewer], "Administrador");
    expect(container.querySelector(".tdot.teg")).not.toBeNull();
  });

  it("a table with both types renders both dot variants", () => {
    const { container } = renderTable([ptegPending, tegNoReviewer], "Administrador");
    expect(container.querySelector(".tdot.pteg")).not.toBeNull();
    expect(container.querySelector(".tdot.teg")).not.toBeNull();
  });
});

// ---------------------------------------------------------------------------
// 4. Action button label matches cardAction output
// ---------------------------------------------------------------------------

describe("SeguimientoTable — action button label", () => {
  it("admin sees 'Revisar' on a PTEG pending_review_1 project", () => {
    // cardAction("Administrador", ptegPending) → { label: "Revisar", ... }
    const expected = cardAction("Administrador", ptegPending).label;
    renderTable([ptegPending], "Administrador");
    expect(screen.getByRole("link", { name: new RegExp(expected, "i") })).toBeTruthy();
  });

  it("jurado assigned to project sees their action label on that project", () => {
    const viewerId = 42;
    const expected = cardAction("Jurado", ptegPending, viewerId).label;
    renderTable([ptegPending], "Jurado", { viewerId });
    expect(screen.getByRole("link", { name: new RegExp(expected, "i") })).toBeTruthy();
  });

  it("tutor sees 'Ver detalles' on any project", () => {
    const expected = cardAction("Tutor", ptegPending).label;
    renderTable([ptegPending], "Tutor");
    expect(screen.getByRole("link", { name: new RegExp(expected, "i") })).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// 5. "Sin asignar" fallback when reviewerName is null / undefined / empty
// Judgment call: assert with /sin asignar/i (case-insensitive regex).
// ---------------------------------------------------------------------------

describe("SeguimientoTable — Sin asignar fallback", () => {
  it("tutor view shows /sin asignar/i when reviewerName is null", () => {
    renderTable([makeProject({ reviewerName: null })], "Tutor");
    expect(screen.getByText(/sin asignar/i)).toBeTruthy();
  });

  it("tutor view shows /sin asignar/i when reviewerName is undefined", () => {
    renderTable([makeProject({ reviewerName: undefined })], "Tutor");
    expect(screen.getByText(/sin asignar/i)).toBeTruthy();
  });

  it("tutor view shows /sin asignar/i when reviewerName is empty string", () => {
    renderTable([makeProject({ reviewerName: "" })], "Tutor");
    expect(screen.getByText(/sin asignar/i)).toBeTruthy();
  });

  it("admin view shows /sin asignar/i in tutorJurado cell when reviewerName is null", () => {
    renderTable([makeProject({ reviewerName: null })], "Administrador");
    expect(screen.getByText(/sin asignar/i)).toBeTruthy();
  });

  it("admin view shows /sin asignar/i when reviewerName is undefined", () => {
    renderTable([makeProject({ reviewerName: undefined })], "Administrador");
    expect(screen.getByText(/sin asignar/i)).toBeTruthy();
  });

  it("admin view shows /sin asignar/i when reviewerName is empty string", () => {
    renderTable([makeProject({ reviewerName: "" })], "Administrador");
    expect(screen.getByText(/sin asignar/i)).toBeTruthy();
  });
});

// ---------------------------------------------------------------------------
// 6. Pagination
// ---------------------------------------------------------------------------

describe("SeguimientoTable — pagination", () => {
  it("clicking next-page button calls onPageChange(2) when currentPage=1 totalPages=3", () => {
    const onPageChange = vi.fn();
    renderTable([ptegPending], "Administrador", {
      currentPage: 1,
      totalPages: 3,
      onPageChange,
    });
    // The next-page button should be present and clickable.
    const nextBtn = screen.getByRole("button", { name: /siguiente|next|›|»|>/i });
    fireEvent.click(nextBtn);
    expect(onPageChange).toHaveBeenCalledWith(2);
  });

  it("previous-page button calls onPageChange(1) when currentPage=2", () => {
    const onPageChange = vi.fn();
    renderTable([ptegPending], "Administrador", {
      currentPage: 2,
      totalPages: 3,
      onPageChange,
    });
    const prevBtn = screen.getByRole("button", { name: /anterior|prev|‹|«|</i });
    fireEvent.click(prevBtn);
    expect(onPageChange).toHaveBeenCalledWith(1);
  });
});

// ---------------------------------------------------------------------------
// 7. Empty state
// Judgment call: empty state renders "Todo al día" text.
// Pagination footer is NOT rendered when items is empty.
// ---------------------------------------------------------------------------

describe("SeguimientoTable — empty state", () => {
  it("renders 'Todo al día' when items is empty", () => {
    renderTable([], "Administrador");
    expect(screen.getByText(/todo al día/i)).toBeTruthy();
  });

  it("does not render pagination when items is empty", () => {
    const onPageChange = vi.fn();
    renderTable([], "Administrador", {
      currentPage: 1,
      totalPages: 3,
      onPageChange,
    });
    expect(screen.queryByRole("button", { name: /siguiente|next|›|»|>/i })).toBeNull();
  });
});
