import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor, within } from "@testing-library/react";
import EditDayModal from "./EditDayModal";
import type { PresentationDay } from "../types/planificacion";
import {
  formatWeekday,
  formatDayNumeral,
  formatMonthYear,
} from "../lib/formatDate";

// ── Service mock ──────────────────────────────────────────────────────────────

vi.mock("../api/planificacionService", () => ({
  updateDay: vi.fn(() => Promise.resolve({})),
  deleteDay: vi.fn(() => Promise.resolve()),
}));

// ── Fixture ───────────────────────────────────────────────────────────────────

const FIXTURE_DATE = "2026-03-12";

const baseDay: PresentationDay = {
  id: 7,
  date: FIXTURE_DATE,
  notes: "Traer laptop",
  presentations: [
    {
      id: 1, day: 7, project: 101,
      project_title: "P1", project_type: "tesis",
      student_name: "A", student_email: "a@test.com",
      tutor: null, tutor_name: null, jurado: [], jurado_names: [],
      start_time: "10:00", duration_minutes: 30, order: 1,
    },
    {
      id: 2, day: 7, project: 102,
      project_title: "P2", project_type: "proyecto",
      student_name: "B", student_email: "b@test.com",
      tutor: null, tutor_name: null, jurado: [], jurado_names: [],
      start_time: "11:00", duration_minutes: 30, order: 2,
    },
    {
      id: 3, day: 7, project: 103,
      project_title: "P3", project_type: "tesis",
      student_name: "C", student_email: "c@test.com",
      tutor: null, tutor_name: null, jurado: [], jurado_names: [],
      start_time: "12:00", duration_minutes: 30, order: 3,
    },
  ],
};

// Expected human-readable parts from formatDate helpers
const EXPECTED_WEEKDAY = formatWeekday(FIXTURE_DATE);      // "jueves"
const EXPECTED_NUMERAL = formatDayNumeral(FIXTURE_DATE);   // "12"
const EXPECTED_MONTHYEAR = formatMonthYear(FIXTURE_DATE);  // "marzo de 2026"

// Helper: import the service mock for assertion
async function getServiceMock() {
  const mod = await import("../api/planificacionService");
  return {
    updateDay: mod.updateDay as ReturnType<typeof vi.fn>,
    deleteDay: mod.deleteDay as ReturnType<typeof vi.fn>,
  };
}

// ── Render helper ─────────────────────────────────────────────────────────────

function renderModal(props: Partial<React.ComponentProps<typeof EditDayModal>> = {}) {
  const defaults = {
    day: baseDay,
    onClose: vi.fn(),
    onSaved: vi.fn(),
  };
  return render(<EditDayModal {...defaults} {...props} />);
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe("EditDayModal", () => {

  beforeEach(() => {
    vi.clearAllMocks();
  });

  // 1 — Hidden when day === null
  it("renders nothing when day is null", () => {
    render(<EditDayModal day={null} onClose={vi.fn()} onSaved={vi.fn()} />);
    expect(document.querySelector("[role='dialog']")).toBeNull();
  });

  // 2 — Open when day is set
  it("renders a dialog when day is provided", () => {
    renderModal();
    expect(screen.getByRole("dialog")).toBeInTheDocument();
  });

  // 3 — Band variant
  it("band element has both class modal-band and class edit", () => {
    renderModal();
    const band = document.querySelector(".modal-band");
    expect(band).not.toBeNull();
    expect(band).toHaveClass("edit");
  });

  // 4 — Eyebrow text
  it("band-eyebrow contains /editar día/i", () => {
    renderModal();
    const eyebrow = document.querySelector(".band-eyebrow");
    expect(eyebrow).not.toBeNull();
    expect(eyebrow!.textContent).toMatch(/editar día/i);
  });

  // 5 — Title shows day in human form (weekday + numeral + month)
  it("band-title shows the day's date in human form", () => {
    renderModal();
    const title = document.querySelector(".band-title");
    expect(title).not.toBeNull();
    // e.g. "jueves 12 de marzo" — all parts must be present
    expect(title!.textContent?.toLowerCase()).toContain(EXPECTED_WEEKDAY.toLowerCase());
    expect(title!.textContent).toContain(EXPECTED_NUMERAL);
    expect(title!.textContent?.toLowerCase()).toMatch(/marzo/i);
  });

  // 6 — Sub shows presentation count
  it("band-sub shows count of presentations (3 presentaciones programadas)", () => {
    renderModal();
    const sub = document.querySelector(".band-sub");
    expect(sub).not.toBeNull();
    expect(sub!.textContent).toMatch(/3 presentaciones/i);
  });

  // 7 — Section 01 Fecha: date input pre-filled
  it("section 01 Fecha has a date input pre-filled with the day's date", () => {
    renderModal();
    const dateInput = document.querySelector<HTMLInputElement>("input[type='date']");
    expect(dateInput).not.toBeNull();
    expect(dateInput!.value).toBe(FIXTURE_DATE);
  });

  // 8 — Section 02 Notas: textarea pre-filled with day.notes
  it("section 02 Notas has a textarea pre-filled with day.notes", () => {
    renderModal();
    const textarea = document.querySelector<HTMLTextAreaElement>("textarea");
    expect(textarea).not.toBeNull();
    expect(textarea!.value).toBe("Traer laptop");
  });

  // 9 — Footer left: danger button
  it("footer left has a .btn.danger button matching /eliminar día/i", () => {
    renderModal();
    const dangerBtn = document.querySelector(".btn.danger");
    expect(dangerBtn).not.toBeNull();
    expect(dangerBtn!.textContent).toMatch(/eliminar día/i);
  });

  // 10 — Footer right: Cancelar ghost + Guardar primary
  it("footer right has Cancelar and Guardar buttons", () => {
    renderModal();
    expect(screen.getByRole("button", { name: /cancelar/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /guardar/i })).toBeInTheDocument();
  });

  // 11 — Save: edit notes → click Guardar → updateDay + onSaved called
  it("clicking Guardar calls updateDay with day id + new values, then onSaved", async () => {
    const onSaved = vi.fn();
    renderModal({ onSaved });
    const { updateDay } = await getServiceMock();

    const textarea = document.querySelector<HTMLTextAreaElement>("textarea")!;
    fireEvent.change(textarea, { target: { value: "Notas actualizadas" } });

    const guardar = screen.getByRole("button", { name: /guardar/i });
    fireEvent.click(guardar);

    await waitFor(() => {
      expect(updateDay).toHaveBeenCalledWith(
        baseDay.id,
        expect.objectContaining({ notes: "Notas actualizadas" }),
      );
      expect(onSaved).toHaveBeenCalledOnce();
    });
  });

  // 12 — Delete: click Eliminar → confirm true → deleteDay + onSaved called
  it("clicking Eliminar día with confirm=true calls deleteDay and onSaved", async () => {
    const onSaved = vi.fn();
    vi.spyOn(window, "confirm").mockReturnValue(true);
    renderModal({ onSaved });
    const { deleteDay } = await getServiceMock();

    const deleteBtn = document.querySelector(".btn.danger") as HTMLButtonElement;
    fireEvent.click(deleteBtn);

    await waitFor(() => {
      expect(deleteDay).toHaveBeenCalledWith(baseDay.id);
      expect(onSaved).toHaveBeenCalledOnce();
    });
  });

  // 13 — Cancel button calls onClose
  it("clicking Cancelar fires onClose", () => {
    const onClose = vi.fn();
    renderModal({ onClose });
    fireEvent.click(screen.getByRole("button", { name: /cancelar/i }));
    expect(onClose).toHaveBeenCalledOnce();
  });

  // 14 — ✕ button calls onClose
  it("clicking the band-close button fires onClose", () => {
    const onClose = vi.fn();
    renderModal({ onClose });
    const closeBtn = screen.getByRole("button", { name: /cerrar/i });
    expect(closeBtn).toHaveClass("band-close");
    fireEvent.click(closeBtn);
    expect(onClose).toHaveBeenCalledOnce();
  });

  // 15 — ESC calls onClose
  it("pressing Escape calls onClose when modal is open", () => {
    const onClose = vi.fn();
    renderModal({ onClose });
    fireEvent.keyDown(document, { key: "Escape", code: "Escape" });
    expect(onClose).toHaveBeenCalledOnce();
  });

  // 16 — Overlay click calls onClose; inside dialog does NOT
  it("clicking the modal-overlay calls onClose", () => {
    const onClose = vi.fn();
    renderModal({ onClose });
    const overlay = document.querySelector(".modal-overlay")!;
    expect(overlay).not.toBeNull();
    fireEvent.click(overlay);
    expect(onClose).toHaveBeenCalledOnce();
  });

  it("clicking inside the dialog does NOT call onClose", () => {
    const onClose = vi.fn();
    renderModal({ onClose });
    fireEvent.click(screen.getByRole("dialog"));
    expect(onClose).not.toHaveBeenCalled();
  });

  // 17 — Saving disables buttons and shows Guardando…
  it("shows 'Guardando…' text and disables Guardar while saving", async () => {
    const slowSaved = vi.fn(() => new Promise<void>((resolve) => setTimeout(resolve, 200)));
    renderModal({ onSaved: slowSaved });

    // Trigger save
    const guardar = screen.getByRole("button", { name: /guardar/i });
    fireEvent.click(guardar);

    await waitFor(() => {
      expect(screen.getByText(/guardando/i)).toBeInTheDocument();
    });
  });

  // 18 — No legacy classes
  it("does not use legacy bg-gray-* or text-gray-* or bg-white/60 classes", () => {
    const { container } = renderModal();
    expect(container.innerHTML).not.toMatch(/bg-gray-/);
    expect(container.innerHTML).not.toMatch(/text-gray-/);
    expect(container.innerHTML).not.toContain("bg-white/60");
  });
});
