"use client";
import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor, act } from "@testing-library/react";
import type { Presentation } from "../types/planificacion";
import type { Project } from "@features/projects/types/project";

// ── Combobox mock — covers both the current path and any promoted @shared path.
// The mock renders a simple button that exposes the selected value and fires
// onChange synchronously when the data-testid trigger button is clicked.
vi.mock("@/app/dashboard/agregar/components/Combobox", () => ({
  default: vi.fn(({ placeholder, value, onChange, options, disabled }: {
    placeholder?: string;
    value?: number | "" | null;
    onChange: (v: number | "") => void;
    options: { id: number; label: string }[];
    disabled?: boolean;
  }) => {
    const selected = options?.find((o: { id: number; label: string }) => o.id === value);
    return (
      <div role="combobox" aria-label={placeholder ?? "combobox"}>
        <span data-testid="combobox-selected">{selected?.label ?? ""}</span>
        {options?.map((o: { id: number; label: string }) => (
          <button
            key={o.id}
            type="button"
            data-testid={`combobox-option-${o.id}`}
            disabled={disabled}
            onClick={() => onChange(o.id)}
          >
            {o.label}
          </button>
        ))}
      </div>
    );
  }),
}));

vi.mock("@shared/ui/Combobox", () => ({
  default: vi.fn(({ placeholder, value, onChange, options, disabled }: {
    placeholder?: string;
    value?: number | "" | null;
    onChange: (v: number | "") => void;
    options: { id: number; label: string }[];
    disabled?: boolean;
  }) => {
    const selected = options?.find((o: { id: number; label: string }) => o.id === value);
    return (
      <div role="combobox" aria-label={placeholder ?? "combobox"}>
        <span data-testid="combobox-selected">{selected?.label ?? ""}</span>
        {options?.map((o: { id: number; label: string }) => (
          <button
            key={o.id}
            type="button"
            data-testid={`combobox-option-${o.id}`}
            disabled={disabled}
            onClick={() => onChange(o.id)}
          >
            {o.label}
          </button>
        ))}
      </div>
    );
  }),
}));

// ── Project fixtures ──────────────────────────────────────────────────────────

const PROJECT_PTEG: Project = {
  id: 1,
  title: "Sistema de Inventario Inteligente",
  student: "Ana Pérez",
  advisors: [5],
  advisorNames: ["Prof. Ramírez"],
  reviewer: null,
  reviewerName: null,
  submittedDate: "2026-01-10",
  state: "pending_review_1",
  score: 0,
  diagramacionScore: 0,
  contenidoScore: 0,
  period: "2026-01",
  type: "proyecto",
};

const PROJECT_TEG: Project = {
  id: 2,
  title: "Análisis de Redes Neuronales Aplicadas",
  student: "Diego Torres",
  advisors: [7],
  advisorNames: ["Prof. Morales"],
  reviewer: null,
  reviewerName: null,
  submittedDate: "2026-01-15",
  state: "pending_articulo",
  score: 0,
  diagramacionScore: 0,
  contenidoScore: 0,
  period: "2026-01",
  type: "tesis",
};

const PROJECT_PTEG_NO_TUTOR: Project = {
  id: 3,
  title: "App Móvil de Gestión Estudiantil",
  student: "Carlos Mendoza",
  advisors: [],
  advisorNames: [],
  reviewer: null,
  reviewerName: null,
  submittedDate: "2026-02-01",
  state: "pending_review_1",
  score: 0,
  diagramacionScore: 0,
  contenidoScore: 0,
  period: "2026-01",
  type: "proyecto",
};

const ALL_PROJECTS: Project[] = [PROJECT_PTEG, PROJECT_TEG, PROJECT_PTEG_NO_TUTOR];

// ── Jurado fixtures ───────────────────────────────────────────────────────────

const JURADO_FIXTURES = [
  { id: 10, fullName: "Dr. Luis García", email: "l.garcia@test.com", role: "Jurado" as const, status: "active" as const },
  { id: 11, fullName: "Dra. Marina Flores", email: "m.flores@test.com", role: "Jurado" as const, status: "active" as const },
  { id: 12, fullName: "Prof. Roberto Salas", email: "r.salas@test.com", role: "Jurado" as const, status: "active" as const },
  { id: 13, fullName: "Ing. Patricia Vega", email: "p.vega@test.com", role: "Jurado" as const, status: "active" as const },
  { id: 14, fullName: "Lic. Jorge Núñez", email: "j.nunez@test.com", role: "Jurado" as const, status: "active" as const },
];

// ── Presentation fixture (edit mode) ─────────────────────────────────────────
// TEG project (id=2), student "Diego Torres", 3 jurados pre-filled

const EDIT_PRESENTATION: Presentation = {
  id: 99,
  day: 7,
  project: 2,
  project_title: "Análisis de Redes Neuronales Aplicadas",
  project_type: "tesis",
  student_name: "Diego Torres",
  student_email: "diego@test.com",
  tutor: 7,
  tutor_name: "Prof. Morales",
  jurado: [10, 11, 12],
  jurado_names: ["Dr. Luis García", "Dra. Marina Flores", "Prof. Roberto Salas"],
  start_time: "14:30",
  duration_minutes: 45,
  order: 1,
};

// ── Service mocks ─────────────────────────────────────────────────────────────

vi.mock("@features/projects/api/projectService", () => ({
  getAllProjects: vi.fn(() => Promise.resolve(ALL_PROJECTS)),
}));

vi.mock("@features/auth/api/clientAuth", () => ({
  getAllUsers: vi.fn(() => Promise.resolve(JURADO_FIXTURES)),
  isAuthenticated: () => true,
  getUser: () => null,
  getUserRole: () => "Administrador",
  logout: vi.fn(),
}));

// ── Import component after mocks ──────────────────────────────────────────────

import PresentationFormModal from "./PresentationFormModal";

// ── Default props factory ─────────────────────────────────────────────────────

function defaultProps(overrides: Partial<React.ComponentProps<typeof PresentationFormModal>> = {}) {
  return {
    isOpen: true,
    dayId: 7,
    editTarget: null,
    onClose: vi.fn(),
    onSave: vi.fn(() => Promise.resolve()),
    ...overrides,
  };
}

// ── Test suite ────────────────────────────────────────────────────────────────

describe("PresentationFormModal (Sub-K redesign)", () => {

  beforeEach(() => {
    vi.clearAllMocks();
  });

  // 1 — Hidden when closed
  it("renders nothing when isOpen is false", () => {
    render(<PresentationFormModal {...defaultProps({ isOpen: false })} />);
    expect(document.querySelector("[role='dialog']")).toBeNull();
  });

  // 2 — Open
  it("renders a dialog when isOpen is true", async () => {
    render(<PresentationFormModal {...defaultProps()} />);
    await waitFor(() => {
      expect(screen.getByRole("dialog")).toBeInTheDocument();
    });
  });

  // 3 — Band variant is edit
  it("band element has both class modal-band and class edit", async () => {
    render(<PresentationFormModal {...defaultProps()} />);
    await waitFor(() => {
      const band = document.querySelector(".modal-band");
      expect(band).not.toBeNull();
      expect(band).toHaveClass("edit");
    });
  });

  // 4 — Header create mode
  it("shows 'Programar presentación' heading in create mode (editTarget null)", async () => {
    render(<PresentationFormModal {...defaultProps({ editTarget: null })} />);
    await waitFor(() => {
      const dialog = screen.getByRole("dialog");
      expect(dialog.textContent).toMatch(/programar presentaci[oó]n/i);
    });
  });

  // 5 — Header edit mode
  it("shows 'Editar presentación' heading in edit mode (editTarget set)", async () => {
    render(<PresentationFormModal {...defaultProps({ editTarget: EDIT_PRESENTATION })} />);
    await waitFor(() => {
      const dialog = screen.getByRole("dialog");
      expect(dialog.textContent).toMatch(/editar presentaci[oó]n/i);
    });
  });

  // 6 — Three numbered sections
  it("renders three section headings: Proyecto, Tribunal, Horario", async () => {
    render(<PresentationFormModal {...defaultProps()} />);
    await waitFor(() => {
      const dialog = screen.getByRole("dialog");
      expect(dialog.textContent).toContain("Proyecto");
      expect(dialog.textContent).toContain("Tribunal");
      expect(dialog.textContent).toContain("Horario");
    });
  });

  it("section headings carry ordinal markers 01, 02, 03", async () => {
    render(<PresentationFormModal {...defaultProps()} />);
    await waitFor(() => {
      const dialog = screen.getByRole("dialog");
      expect(dialog.textContent).toContain("01");
      expect(dialog.textContent).toContain("02");
      expect(dialog.textContent).toContain("03");
    });
  });

  it("section headers use .section-h with .section-num and .section-title-h children", async () => {
    render(<PresentationFormModal {...defaultProps()} />);
    await waitFor(() => {
      const sectionH = document.querySelector(".section-h");
      expect(sectionH).not.toBeNull();
      expect(sectionH!.querySelector(".section-num")).not.toBeNull();
      expect(sectionH!.querySelector(".section-title-h")).not.toBeNull();
    });
  });

  // 7 — Project Combobox renders with accessible label matching /proyecto|tesis/i
  it("renders a combobox with accessible label matching /proyecto|tesis/i", async () => {
    render(<PresentationFormModal {...defaultProps()} />);
    await waitFor(() => {
      const comboboxes = screen.getAllByRole("combobox");
      const projectCombobox = comboboxes.find(
        (el) => /proyecto|tesis/i.test(el.getAttribute("aria-label") ?? "")
      );
      expect(projectCombobox).toBeInTheDocument();
    });
  });

  // 8 — Project summary shown when editTarget has a project_id pre-set (TEG)
  it("shows .proj-summary with student name and TEG chip when editTarget is a tesis project", async () => {
    render(<PresentationFormModal {...defaultProps({ editTarget: EDIT_PRESENTATION })} />);
    await waitFor(() => {
      const summary = document.querySelector(".proj-summary");
      expect(summary).not.toBeNull();
      expect(summary!.textContent).toContain("Diego Torres");
      // TEG chip: spill element with teg class
      const spillTeg = summary!.querySelector(".spill.teg");
      expect(spillTeg).not.toBeNull();
    });
  });

  it("shows .proj-summary.teg class when editTarget is a tesis project", async () => {
    render(<PresentationFormModal {...defaultProps({ editTarget: EDIT_PRESENTATION })} />);
    await waitFor(() => {
      const summary = document.querySelector(".proj-summary.teg");
      expect(summary).not.toBeNull();
    });
  });

  it("shows .proj-summary.pteg class when selected project is proyecto type", async () => {
    render(<PresentationFormModal {...defaultProps()} />);
    await waitFor(() => {
      expect(screen.getByRole("dialog")).toBeInTheDocument();
    });
    // Select a PTEG project via combobox mock
    const ptegOption = document.querySelector(`[data-testid="combobox-option-1"]`);
    if (ptegOption) {
      fireEvent.click(ptegOption);
      await waitFor(() => {
        expect(document.querySelector(".proj-summary.pteg")).not.toBeNull();
      });
    }
  });

  it("shows .proj-summary-row items inside the summary", async () => {
    render(<PresentationFormModal {...defaultProps({ editTarget: EDIT_PRESENTATION })} />);
    await waitFor(() => {
      const rows = document.querySelectorAll(".proj-summary-row");
      expect(rows.length).toBeGreaterThanOrEqual(1);
    });
  });

  it("shows .proj-summary with tutor name when editTarget has a tutor", async () => {
    render(<PresentationFormModal {...defaultProps({ editTarget: EDIT_PRESENTATION })} />);
    await waitFor(() => {
      const summary = document.querySelector(".proj-summary");
      expect(summary).not.toBeNull();
      expect(summary!.textContent).toContain("Prof. Morales");
    });
  });

  // 9 — Jurado section empty state when no jurados in create mode
  it("shows empty-state text in the jurado section when no jurados are assigned (create mode)", async () => {
    render(<PresentationFormModal {...defaultProps({ editTarget: null })} />);
    await waitFor(() => {
      const dialog = screen.getByRole("dialog");
      expect(dialog.textContent).toMatch(/sin jurados asignados/i);
    });
  });

  it("empty jurado state uses .jur-empty class", async () => {
    render(<PresentationFormModal {...defaultProps({ editTarget: null })} />);
    await waitFor(() => {
      expect(document.querySelector(".jur-empty")).not.toBeNull();
    });
  });

  // 10 — Jurado cap=3: "Añadir jurado" button is disabled when 3 jurados already added
  it("disables the 'Añadir jurado' button when 3 jurados are pre-filled via editTarget", async () => {
    // EDIT_PRESENTATION has jurado: [10, 11, 12] — cap reached
    render(<PresentationFormModal {...defaultProps({ editTarget: EDIT_PRESENTATION })} />);
    await waitFor(() => {
      const addBtn = screen.getByRole("button", { name: /añadir jurado/i });
      const isDisabled =
        addBtn.hasAttribute("disabled") ||
        addBtn.getAttribute("aria-disabled") === "true";
      expect(isDisabled).toBe(true);
    });
  });

  // 11 — Jurado chips use .jur-chips and .jur-chip classes
  it("jurado chips container has class jur-chips and each chip has class jur-chip", async () => {
    render(<PresentationFormModal {...defaultProps({ editTarget: EDIT_PRESENTATION })} />);
    await waitFor(() => {
      expect(document.querySelector(".jur-chips")).not.toBeNull();
      const chips = document.querySelectorAll(".jur-chip");
      expect(chips.length).toBe(3);
    });
  });

  // 12 — Jurado add trigger uses .jur-add class
  it("jurado add area has class jur-add", async () => {
    render(<PresentationFormModal {...defaultProps()} />);
    await waitFor(() => {
      expect(document.querySelector(".jur-add")).not.toBeNull();
    });
  });

  // 13 — Jurado chips are removable
  it("each jurado chip has a remove button with aria-label matching /quitar/i", async () => {
    render(<PresentationFormModal {...defaultProps({ editTarget: EDIT_PRESENTATION })} />);
    await waitFor(() => {
      const removeButtons = screen.getAllByRole("button", { name: /quitar/i });
      expect(removeButtons.length).toBeGreaterThanOrEqual(3);
    });
  });

  it("clicking a jurado chip's remove button removes that chip", async () => {
    render(<PresentationFormModal {...defaultProps({ editTarget: EDIT_PRESENTATION })} />);
    await waitFor(() => {
      expect(document.querySelectorAll(".jur-chip").length).toBe(3);
    });
    const firstRemove = screen.getAllByRole("button", { name: /quitar/i })[0];
    fireEvent.click(firstRemove);
    await waitFor(() => {
      expect(document.querySelectorAll(".jur-chip").length).toBe(2);
    });
  });

  // 14 — Time + Duration row inputs
  it("renders a time input with default value '09:00' in create mode", async () => {
    render(<PresentationFormModal {...defaultProps({ editTarget: null })} />);
    await waitFor(() => {
      const timeInput = document.querySelector<HTMLInputElement>("input[type='time']");
      expect(timeInput).not.toBeNull();
      expect(timeInput!.value).toBe("09:00");
    });
  });

  it("renders a number input for duration with default value 30 in create mode", async () => {
    render(<PresentationFormModal {...defaultProps({ editTarget: null })} />);
    await waitFor(() => {
      const durationInput = document.querySelector<HTMLInputElement>("input[type='number']");
      expect(durationInput).not.toBeNull();
      expect(Number(durationInput!.value)).toBe(30);
    });
  });

  it("pre-fills time and duration from editTarget in edit mode", async () => {
    render(<PresentationFormModal {...defaultProps({ editTarget: EDIT_PRESENTATION })} />);
    await waitFor(() => {
      const timeInput = document.querySelector<HTMLInputElement>("input[type='time']");
      expect(timeInput!.value).toBe("14:30");
      const durationInput = document.querySelector<HTMLInputElement>("input[type='number']");
      expect(Number(durationInput!.value)).toBe(45);
    });
  });

  // 15 — band-title shows modal heading text
  it("band-title element shows the modal heading (Programar or Editar presentación)", async () => {
    render(<PresentationFormModal {...defaultProps({ editTarget: null })} />);
    await waitFor(() => {
      const title = document.querySelector(".band-title");
      expect(title).not.toBeNull();
      expect(title!.textContent).toMatch(/programar presentaci[oó]n/i);
    });
  });

  // 16 — band-close button has aria-label=Cerrar
  it("band-close button has aria-label Cerrar", async () => {
    render(<PresentationFormModal {...defaultProps()} />);
    await waitFor(() => {
      const closeBtn = screen.getByRole("button", { name: /cerrar/i });
      expect(closeBtn).toHaveClass("band-close");
    });
  });

  // 17 — Footer buttons
  it("renders Cancelar and Guardar buttons in the footer", async () => {
    render(<PresentationFormModal {...defaultProps()} />);
    await waitFor(() => {
      expect(screen.getByRole("button", { name: /cancelar/i })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /guardar/i })).toBeInTheDocument();
    });
  });

  it("Guardar button shows 'Guardando…' text while saving", async () => {
    const slowSave = vi.fn(
      () => new Promise<void>((resolve) => setTimeout(resolve, 200))
    );
    render(
      <PresentationFormModal
        {...defaultProps({ editTarget: EDIT_PRESENTATION, onSave: slowSave })}
      />
    );
    await waitFor(() => {
      expect(screen.getByRole("button", { name: /guardar/i })).toBeInTheDocument();
    });
    const submitBtn = screen.getByRole("button", { name: /guardar/i });
    fireEvent.click(submitBtn);
    await waitFor(() => {
      expect(screen.getByText(/guardando/i)).toBeInTheDocument();
    });
  });

  // 18 — Cancel calls onClose
  it("clicking Cancelar fires onClose", async () => {
    const onClose = vi.fn();
    render(<PresentationFormModal {...defaultProps({ onClose })} />);
    await waitFor(() => {
      expect(screen.getByRole("button", { name: /cancelar/i })).toBeInTheDocument();
    });
    fireEvent.click(screen.getByRole("button", { name: /cancelar/i }));
    expect(onClose).toHaveBeenCalledOnce();
  });

  // 19 — Close button (✕) calls onClose
  it("clicking the close button (aria-label=Cerrar) calls onClose", async () => {
    const onClose = vi.fn();
    render(<PresentationFormModal {...defaultProps({ onClose })} />);
    await waitFor(() => {
      expect(screen.getByRole("button", { name: /cerrar/i })).toBeInTheDocument();
    });
    fireEvent.click(screen.getByRole("button", { name: /cerrar/i }));
    expect(onClose).toHaveBeenCalledOnce();
  });

  // 20 — ESC closes
  it("pressing Escape calls onClose when modal is open", async () => {
    const onClose = vi.fn();
    render(<PresentationFormModal {...defaultProps({ isOpen: true, onClose })} />);
    await waitFor(() => {
      expect(screen.getByRole("dialog")).toBeInTheDocument();
    });
    fireEvent.keyDown(document, { key: "Escape", code: "Escape" });
    expect(onClose).toHaveBeenCalledOnce();
  });

  // 21 — Overlay click closes; clicking inside dialog does NOT
  it("clicking the .modal-overlay element calls onClose", async () => {
    const onClose = vi.fn();
    render(<PresentationFormModal {...defaultProps({ onClose })} />);
    await waitFor(() => {
      const overlay = document.querySelector(".modal-overlay");
      expect(overlay).not.toBeNull();
    });
    const overlay = document.querySelector(".modal-overlay")!;
    fireEvent.click(overlay);
    expect(onClose).toHaveBeenCalledOnce();
  });

  it("clicking inside the dialog (role=dialog) does NOT call onClose", async () => {
    const onClose = vi.fn();
    render(<PresentationFormModal {...defaultProps({ onClose })} />);
    await waitFor(() => {
      expect(screen.getByRole("dialog")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByRole("dialog"));
    expect(onClose).not.toHaveBeenCalled();
  });

  // 22 — Save flow create mode
  it("calls onSave(dayId, payload, undefined) in create mode when form is valid", async () => {
    const onSave = vi.fn(() => Promise.resolve());
    const onClose = vi.fn();
    render(
      <PresentationFormModal
        {...defaultProps({ editTarget: null, onSave, onClose })}
      />
    );
    // Wait for data load
    await waitFor(() => {
      expect(screen.getByRole("dialog")).toBeInTheDocument();
    });

    // Select project via the combobox mock option button
    const projectOption = document.querySelector(`[data-testid="combobox-option-1"]`);
    if (projectOption) {
      fireEvent.click(projectOption);
    }

    const submitBtn = screen.getByRole("button", { name: /guardar/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(onSave).toHaveBeenCalled();
      const [calledDayId, calledPayload, calledEditId] = onSave.mock.calls[0];
      expect(calledDayId).toBe(7);
      expect(calledPayload).toMatchObject({
        start_time: expect.any(String),
        jurado: expect.any(Array),
      });
      expect(calledEditId).toBeUndefined();
    });
  });

  // 23 — Save flow edit mode
  it("calls onSave(dayId, payload, editTarget.id) in edit mode", async () => {
    const onSave = vi.fn(() => Promise.resolve());
    const onClose = vi.fn();
    render(
      <PresentationFormModal
        {...defaultProps({ editTarget: EDIT_PRESENTATION, onSave, onClose })}
      />
    );
    await waitFor(() => {
      expect(screen.getByRole("dialog")).toBeInTheDocument();
    });

    const submitBtn = screen.getByRole("button", { name: /guardar/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(onSave).toHaveBeenCalled();
      const [calledDayId, calledPayload, calledEditId] = onSave.mock.calls[0];
      expect(calledDayId).toBe(7);
      expect(calledPayload).toMatchObject({
        project: EDIT_PRESENTATION.project,
        start_time: EDIT_PRESENTATION.start_time,
        jurado: expect.any(Array),
      });
      expect(calledEditId).toBe(EDIT_PRESENTATION.id);
    });
  });

  // 24 — No legacy color classes in rendered HTML
  it("does not use legacy bg-gray-50 class in rendered output", async () => {
    const { container } = render(<PresentationFormModal {...defaultProps()} />);
    await waitFor(() => {
      expect(screen.getByRole("dialog")).toBeInTheDocument();
    });
    expect(container.innerHTML).not.toContain("bg-gray-50");
  });

  it("does not use legacy bg-black/40 class in rendered output", async () => {
    const { container } = render(<PresentationFormModal {...defaultProps()} />);
    await waitFor(() => {
      expect(screen.getByRole("dialog")).toBeInTheDocument();
    });
    expect(container.innerHTML).not.toContain("bg-black/40");
  });

  it("does not use legacy bg-white/60 class in rendered output", async () => {
    const { container } = render(<PresentationFormModal {...defaultProps()} />);
    await waitFor(() => {
      expect(screen.getByRole("dialog")).toBeInTheDocument();
    });
    expect(container.innerHTML).not.toContain("bg-white/60");
  });

  it("does not use legacy backdrop-blur-xl class in rendered output", async () => {
    const { container } = render(<PresentationFormModal {...defaultProps()} />);
    await waitFor(() => {
      expect(screen.getByRole("dialog")).toBeInTheDocument();
    });
    expect(container.innerHTML).not.toContain("backdrop-blur-xl");
  });

  it("does not use legacy bg-[#0f172a] class in rendered output", async () => {
    const { container } = render(<PresentationFormModal {...defaultProps()} />);
    await waitFor(() => {
      expect(screen.getByRole("dialog")).toBeInTheDocument();
    });
    expect(container.innerHTML).not.toContain("bg-[#0f172a]");
  });

  it("does not use legacy text-gray-500 class in rendered output", async () => {
    const { container } = render(<PresentationFormModal {...defaultProps()} />);
    await waitFor(() => {
      expect(screen.getByRole("dialog")).toBeInTheDocument();
    });
    expect(container.innerHTML).not.toContain("text-gray-500");
  });

  it("does not use legacy text-gray-700 class in rendered output", async () => {
    const { container } = render(<PresentationFormModal {...defaultProps()} />);
    await waitFor(() => {
      expect(screen.getByRole("dialog")).toBeInTheDocument();
    });
    expect(container.innerHTML).not.toContain("text-gray-700");
  });

  it("does not use legacy text-gray-900 class in rendered output", async () => {
    const { container } = render(<PresentationFormModal {...defaultProps()} />);
    await waitFor(() => {
      expect(screen.getByRole("dialog")).toBeInTheDocument();
    });
    expect(container.innerHTML).not.toContain("text-gray-900");
  });

  it("does not use legacy border-gray-200 class in rendered output", async () => {
    const { container } = render(<PresentationFormModal {...defaultProps()} />);
    await waitFor(() => {
      expect(screen.getByRole("dialog")).toBeInTheDocument();
    });
    expect(container.innerHTML).not.toContain("border-gray-200");
  });

  // 25 — No legacy modal--form or pres-section* or pres-summary* or jurado-* classes
  it("does not use legacy modal--form class", async () => {
    const { container } = render(<PresentationFormModal {...defaultProps()} />);
    await waitFor(() => {
      expect(screen.getByRole("dialog")).toBeInTheDocument();
    });
    expect(container.innerHTML).not.toContain("modal--form");
  });

  it("does not use legacy pres-section class", async () => {
    const { container } = render(<PresentationFormModal {...defaultProps()} />);
    await waitFor(() => {
      expect(screen.getByRole("dialog")).toBeInTheDocument();
    });
    expect(container.innerHTML).not.toContain("pres-section");
  });

  it("does not use legacy pres-summary class (renamed to proj-summary)", async () => {
    const { container } = render(<PresentationFormModal {...defaultProps({ editTarget: EDIT_PRESENTATION })} />);
    await waitFor(() => {
      expect(screen.getByRole("dialog")).toBeInTheDocument();
    });
    expect(container.innerHTML).not.toContain("pres-summary");
  });

  it("does not use legacy jurado-chips class (renamed to jur-chips)", async () => {
    const { container } = render(<PresentationFormModal {...defaultProps({ editTarget: EDIT_PRESENTATION })} />);
    await waitFor(() => {
      expect(screen.getByRole("dialog")).toBeInTheDocument();
    });
    expect(container.innerHTML).not.toContain("jurado-chips");
  });

  it("does not use legacy jurado-chip class (renamed to jur-chip)", async () => {
    const { container } = render(<PresentationFormModal {...defaultProps({ editTarget: EDIT_PRESENTATION })} />);
    await waitFor(() => {
      expect(screen.getByRole("dialog")).toBeInTheDocument();
    });
    expect(container.innerHTML).not.toContain("jurado-chip");
  });

  it("does not use legacy pres-empty-juradoes class (renamed to jur-empty)", async () => {
    const { container } = render(<PresentationFormModal {...defaultProps({ editTarget: null })} />);
    await waitFor(() => {
      expect(screen.getByRole("dialog")).toBeInTheDocument();
    });
    expect(container.innerHTML).not.toContain("pres-empty-juradoes");
  });

  it("does not use legacy jurado-add class (renamed to jur-add)", async () => {
    const { container } = render(<PresentationFormModal {...defaultProps()} />);
    await waitFor(() => {
      expect(screen.getByRole("dialog")).toBeInTheDocument();
    });
    expect(container.innerHTML).not.toContain("jurado-add");
  });

  // 26 — dayDate prop: when provided, band-sub shows the day label
  it("band-sub shows dayDate label when provided", async () => {
    render(<PresentationFormModal {...defaultProps({ dayDate: "Jueves 12 de marzo" })} />);
    await waitFor(() => {
      const sub = document.querySelector(".band-sub");
      expect(sub).not.toBeNull();
      expect(sub!.textContent).toContain("Jueves 12 de marzo");
    });
  });

  // 27 — Loading state
  it("shows a loading indicator while getAllProjects is pending", async () => {
    const { getAllProjects } = await import("@features/projects/api/projectService");
    (getAllProjects as ReturnType<typeof vi.fn>).mockImplementationOnce(
      () => new Promise(() => {}) // never resolves — simulates pending
    );
    render(<PresentationFormModal {...defaultProps()} />);
    // Should immediately show some loading affordance
    await waitFor(() => {
      const dialog = document.querySelector("[role='dialog']");
      if (!dialog) return;
      const hasLoadingText = /cargando/i.test(dialog.textContent ?? "");
      const hasSkeleton = dialog.querySelector("[class*='skeleton'], [class*='loading'], [data-loading]") !== null;
      const hasSpinner = dialog.querySelector("[role='status']") !== null;
      expect(hasLoadingText || hasSkeleton || hasSpinner).toBe(true);
    });
  });
});
