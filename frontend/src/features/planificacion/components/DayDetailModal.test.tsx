import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, within } from "@testing-library/react";
import DayDetailModal, { type DayDetailModalProps } from "./DayDetailModal";
import type { PresentationDay, Presentation } from "../types/planificacion";
import {
  formatWeekday,
  formatMonthYear,
  formatDayNumeral,
} from "../lib/formatDate";

// ── Fixture ───────────────────────────────────────────────────────────────────

const FIXTURE_DATE = "2026-03-12";

const p1: Presentation = {
  id: 1,
  day: 1,
  project: 101,
  project_title: "Análisis predictivo de datos climáticos en Venezuela",
  project_type: "tesis",
  student_name: "Diego Torres",
  student_email: "diego@test.com",
  tutor: 5,
  tutor_name: "P. Linares",
  jurado: [9, 10, 11],
  jurado_names: ["R. Linares", "A. Pérez", "M. Núñez"],
  start_time: "14:00",
  duration_minutes: 60,
  order: 1,
};

const p2: Presentation = {
  id: 2,
  day: 1,
  project: 102,
  project_title: "Sistema de tutorías académicas en línea",
  project_type: "proyecto",
  student_name: "N. Gutiérrez",
  student_email: "n.gutierrez@test.com",
  tutor: null,
  tutor_name: "M. Cruz",
  jurado: [12],
  jurado_names: ["M. Cruz"],
  start_time: "15:30",
  duration_minutes: 30,
  order: 2,
};

const p3: Presentation = {
  id: 3,
  day: 1,
  project: 103,
  project_title: "Reconocimiento de voz en idiomas indígenas venezolanos",
  project_type: "tesis",
  student_name: "F. Roa",
  student_email: "f.roa@test.com",
  tutor: null,
  tutor_name: "J. Hernández",
  jurado: [9, 13, 14],
  jurado_names: ["R. Linares", "C. Pérez", "L. Díaz"],
  start_time: "17:00",
  duration_minutes: 45,
  order: 3,
};

const baseDay: PresentationDay = {
  id: 1,
  date: FIXTURE_DATE,
  notes: "Llegar 15 min antes",
  presentations: [p1, p2, p3],
};

// ── Helpers for expected locale strings (avoids hardcoding) ───────────────────

const EXPECTED_NUMERAL = formatDayNumeral(FIXTURE_DATE);  // "12"
const EXPECTED_WEEKDAY = formatWeekday(FIXTURE_DATE);     // "jueves"
const EXPECTED_MONTH   = formatMonthYear(FIXTURE_DATE);   // "marzo de 2026"

// ── Render helper ─────────────────────────────────────────────────────────────

function renderModal(props: Partial<DayDetailModalProps> = {}) {
  const defaultProps: DayDetailModalProps = {
    day: baseDay,
    isAdmin: false,
    onClose: vi.fn(),
    onEditDay: vi.fn(),
    onAddPresentation: vi.fn(),
  };
  return render(<DayDetailModal {...defaultProps} {...props} />);
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe("DayDetailModal", () => {
  describe("closed state", () => {
    it("renders nothing when day is null", () => {
      const { container } = render(
        <DayDetailModal day={null} isAdmin={false} onClose={vi.fn()} />,
      );
      expect(container.firstChild).toBeNull();
    });
  });

  describe("open state", () => {
    it("renders a dialog when day is provided", () => {
      renderModal();
      expect(screen.getByRole("dialog")).toBeInTheDocument();
    });

    it("modal title shows presentation count", () => {
      renderModal();
      expect(screen.getByRole("dialog")).toHaveTextContent("3 presentaciones");
    });
  });

  describe("band shell", () => {
    it("band element has both class modal-band and class read", () => {
      renderModal();
      const band = document.querySelector(".modal-band");
      expect(band).not.toBeNull();
      expect(band).toHaveClass("read");
    });
  });

  describe("Fraunces day numeral block", () => {
    it("shows the day numeral inside .band-numblk", () => {
      renderModal();
      const numblk = document.querySelector(".band-numblk");
      expect(numblk).not.toBeNull();
      expect(numblk).toHaveTextContent(EXPECTED_NUMERAL);
    });

    it("shows the Spanish month label", () => {
      renderModal();
      const dialog = screen.getByRole("dialog");
      // EXPECTED_MONTH is "marzo de 2026"; test for the month portion
      expect(dialog.textContent).toMatch(/marzo/i);
    });

    it("shows the Spanish weekday label", () => {
      renderModal();
      const dialog = screen.getByRole("dialog");
      expect(dialog.textContent?.toLowerCase()).toContain(
        EXPECTED_WEEKDAY.toLowerCase(),
      );
    });
  });

  describe("eyebrow", () => {
    it("element with class band-eyebrow contains /día de presentación/i", () => {
      renderModal();
      const eyebrow = document.querySelector(".band-eyebrow");
      expect(eyebrow).not.toBeNull();
      expect(eyebrow!.textContent).toMatch(/día de presentación/i);
    });
  });

  describe("band title", () => {
    it("element with class band-title shows '3 presentaciones' for 3 presentations", () => {
      renderModal();
      const title = document.querySelector(".band-title");
      expect(title).not.toBeNull();
      expect(title).toHaveTextContent("3 presentaciones");
    });
  });

  describe("subtitle shape", () => {
    it("shows modality counts in the band-sub line", () => {
      renderModal();
      const sub = document.querySelector(".band-sub");
      expect(sub).not.toBeNull();
      expect(sub).toHaveTextContent("2 TEG");
      expect(sub).toHaveTextContent("1 PTEG");
    });

    it("shows the time range 14:00 to 17:45 in the band-sub line", () => {
      // p3 starts 17:00 + 45 min = 17:45
      renderModal();
      const sub = document.querySelector(".band-sub");
      expect(sub?.textContent).toMatch(/14:00.*17:45/);
    });
  });

  describe("stats strip", () => {
    it("shows Inicio, Cierre, and Duración total labels and values", () => {
      renderModal();
      const dialog = screen.getByRole("dialog");
      // Labels
      expect(within(dialog).getByText(/inicio/i)).toBeInTheDocument();
      expect(within(dialog).getByText(/cierre/i)).toBeInTheDocument();
      expect(within(dialog).getByText(/duración total/i)).toBeInTheDocument();
      // Values — 14:00 start, 17:45 end, 3h 45m total (60+30+45=135 min)
      expect(dialog.textContent).toContain("14:00");
      expect(dialog.textContent).toContain("17:45");
      expect(dialog.textContent).toContain("3h 45m");
    });

    it("stats container has class read-stats and each stat has class read-stat", () => {
      renderModal();
      const statsContainer = document.querySelector(".read-stats");
      expect(statsContainer).not.toBeNull();
      const stats = statsContainer!.querySelectorAll(".read-stat");
      expect(stats.length).toBeGreaterThanOrEqual(3);
    });
  });

  describe("agenda", () => {
    it("lists exactly 3 presentation rows in time order", () => {
      renderModal();
      const rows = document.querySelectorAll(".prow");
      expect(rows).toHaveLength(3);
      // Time order: 14:00 → 15:30 → 17:00
      expect(rows[0].textContent).toContain("14:00");
      expect(rows[1].textContent).toContain("15:30");
      expect(rows[2].textContent).toContain("17:00");
    });

    it("each row has a modality dot with correct type class", () => {
      renderModal();
      const rows = document.querySelectorAll(".prow");
      // p1=tesis → .tdot.teg
      expect(rows[0].querySelector(".tdot.teg")).not.toBeNull();
      // p2=proyecto → .tdot.pteg
      expect(rows[1].querySelector(".tdot.pteg")).not.toBeNull();
      // p3=tesis → .tdot.teg
      expect(rows[2].querySelector(".tdot.teg")).not.toBeNull();
    });

    it("each row has a modality chip (spill) with correct text", () => {
      renderModal();
      const rows = document.querySelectorAll(".prow");
      expect(rows[0].textContent).toContain("TEG");
      expect(rows[1].textContent).toContain("PTEG");
      expect(rows[2].textContent).toContain("TEG");
    });

    it("each row shows the student name", () => {
      renderModal();
      const rows = document.querySelectorAll(".prow");
      expect(rows[0].textContent).toContain("Diego Torres");
      expect(rows[1].textContent).toContain("N. Gutiérrez");
      expect(rows[2].textContent).toContain("F. Roa");
    });

    it("each row shows the tutor name", () => {
      renderModal();
      const rows = document.querySelectorAll(".prow");
      expect(rows[0].textContent).toContain("P. Linares");
      expect(rows[1].textContent).toContain("M. Cruz");
      expect(rows[2].textContent).toContain("J. Hernández");
    });

    it("each row shows joined jurado names", () => {
      renderModal();
      const rows = document.querySelectorAll(".prow");
      // p1 jurado_names: ["R. Linares","A. Pérez","M. Núñez"]
      expect(rows[0].textContent).toContain("R. Linares");
      expect(rows[0].textContent).toContain("A. Pérez");
      expect(rows[0].textContent).toContain("M. Núñez");
      // p2 jurado_names: ["M. Cruz"]
      expect(rows[1].textContent).toContain("M. Cruz");
      // p3 jurado_names: ["R. Linares","C. Pérez","L. Díaz"]
      expect(rows[2].textContent).toContain("R. Linares");
    });
  });

  describe("section headings", () => {
    it("section headers use .section-h with .section-num and .section-title-h children", () => {
      renderModal();
      const sectionH = document.querySelector(".section-h");
      expect(sectionH).not.toBeNull();
      expect(sectionH!.querySelector(".section-num")).not.toBeNull();
      expect(sectionH!.querySelector(".section-title-h")).not.toBeNull();
    });
  });

  describe("notes block", () => {
    it("shows notes content and does not carry class 'empty' when notes is set", () => {
      renderModal();
      const notesBlock = document.querySelector(".notes");
      expect(notesBlock).not.toBeNull();
      expect(notesBlock).toHaveTextContent("Llegar 15 min antes");
      expect(notesBlock).not.toHaveClass("empty");
    });

    it("carries class 'empty' and shows fallback when notes is empty string", () => {
      renderModal({ day: { ...baseDay, notes: "" } });
      const notesBlock = document.querySelector(".notes");
      expect(notesBlock).not.toBeNull();
      expect(notesBlock).toHaveClass("empty");
      expect(notesBlock?.textContent).toMatch(/sin notas/i);
    });
  });

  describe("admin footer actions", () => {
    it("shows Editar día and Añadir presentación buttons when isAdmin=true", () => {
      renderModal({ isAdmin: true });
      expect(
        screen.getByRole("button", { name: /editar día/i }),
      ).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: /añadir presentación/i }),
      ).toBeInTheDocument();
    });

    it("footer left slot has class foot-meta and right slot has class foot-actions when isAdmin=true", () => {
      renderModal({ isAdmin: true });
      expect(document.querySelector(".foot-meta")).not.toBeNull();
      const footActions = document.querySelector(".foot-actions");
      expect(footActions).not.toBeNull();
      expect(within(footActions as HTMLElement).getByRole("button", { name: /editar día/i })).toBeInTheDocument();
      expect(within(footActions as HTMLElement).getByRole("button", { name: /añadir presentación/i })).toBeInTheDocument();
    });

    it("clicking Editar día calls onEditDay with the day object", () => {
      const onEditDay = vi.fn();
      renderModal({ isAdmin: true, onEditDay });
      fireEvent.click(screen.getByRole("button", { name: /editar día/i }));
      expect(onEditDay).toHaveBeenCalledOnce();
      expect(onEditDay).toHaveBeenCalledWith(baseDay);
    });

    it("clicking Añadir presentación calls onAddPresentation with the day object", () => {
      const onAddPresentation = vi.fn();
      renderModal({ isAdmin: true, onAddPresentation });
      fireEvent.click(
        screen.getByRole("button", { name: /añadir presentación/i }),
      );
      expect(onAddPresentation).toHaveBeenCalledOnce();
      expect(onAddPresentation).toHaveBeenCalledWith(baseDay);
    });
  });

  describe("non-admin footer", () => {
    it("hides Editar día and Añadir presentación buttons when isAdmin=false", () => {
      renderModal({ isAdmin: false });
      expect(
        screen.queryByRole("button", { name: /editar día/i }),
      ).toBeNull();
      expect(
        screen.queryByRole("button", { name: /añadir presentación/i }),
      ).toBeNull();
    });

    it("still shows the close button when isAdmin=false", () => {
      renderModal({ isAdmin: false });
      expect(
        screen.getByRole("button", { name: /cerrar/i }),
      ).toBeInTheDocument();
    });
  });

  describe("close interactions", () => {
    it("clicking the close button calls onClose", () => {
      const onClose = vi.fn();
      renderModal({ onClose });
      fireEvent.click(screen.getByRole("button", { name: /cerrar/i }));
      expect(onClose).toHaveBeenCalledOnce();
    });

    it("close button has class band-close", () => {
      renderModal();
      const closeBtn = screen.getByRole("button", { name: /cerrar/i });
      expect(closeBtn).toHaveClass("band-close");
    });

    it("clicking the overlay calls onClose", () => {
      const onClose = vi.fn();
      renderModal({ onClose });
      const overlay = document.querySelector(".modal-overlay");
      expect(overlay).not.toBeNull();
      fireEvent.click(overlay!);
      expect(onClose).toHaveBeenCalledOnce();
    });

    it("clicking inside the modal body does NOT call onClose", () => {
      const onClose = vi.fn();
      renderModal({ onClose });
      const dialog = screen.getByRole("dialog");
      fireEvent.click(dialog);
      expect(onClose).not.toHaveBeenCalled();
    });

    it("pressing Escape calls onClose when modal is open", () => {
      const onClose = vi.fn();
      renderModal({ onClose });
      fireEvent.keyDown(document, { key: "Escape", code: "Escape" });
      expect(onClose).toHaveBeenCalledOnce();
    });

    it("pressing Escape does NOT call onClose when day is null", () => {
      const onClose = vi.fn();
      render(<DayDetailModal day={null} isAdmin={false} onClose={onClose} />);
      fireEvent.keyDown(document, { key: "Escape", code: "Escape" });
      expect(onClose).not.toHaveBeenCalled();
    });
  });

  describe("empty agenda variant", () => {
    const emptyDay: PresentationDay = { ...baseDay, presentations: [] };

    it("shows 'Sin presentaciones' as modal title", () => {
      renderModal({ day: emptyDay });
      expect(screen.getByRole("dialog")).toHaveTextContent(
        "Sin presentaciones",
      );
    });

    it("renders no .prow rows", () => {
      renderModal({ day: emptyDay });
      expect(document.querySelectorAll(".prow")).toHaveLength(0);
    });

    it("still renders the notes block", () => {
      renderModal({ day: emptyDay });
      expect(document.querySelector(".notes")).not.toBeNull();
    });
  });
});
