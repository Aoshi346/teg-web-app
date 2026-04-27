import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, within } from "@testing-library/react";
import UnifiedCalendar, {
  type UnifiedCalendarProps,
} from "./UnifiedCalendar";
import type { PresentationDay, Presentation } from "../types/planificacion";

// ── Fixture helpers ───────────────────────────────────────────────────────────

let _presentationId = 1;

function makePresentation(
  date: string,
  overrides: Partial<Presentation> = {},
): Presentation {
  return {
    id: _presentationId++,
    day: 1,
    project: 1,
    project_title: "Test Project",
    project_type: "proyecto",
    student_name: "Ana López",
    student_email: "ana@test.com",
    tutor: null,
    tutor_name: null,
    jurado: [],
    jurado_names: [],
    start_time: "10:00",
    duration_minutes: 30,
    order: 0,
    ...overrides,
  };
}

function makeDay(
  date: string,
  presentations: Partial<Presentation>[] = [],
): PresentationDay {
  return {
    id: _presentationId++,
    date,
    notes: "",
    presentations: presentations.map((p) => makePresentation(date, p)),
  };
}

// Reset fixture IDs and rebuild days per test to avoid ID collisions
function makeFixtures() {
  _presentationId = 1;
  const ptegDay = makeDay("2026-03-03", [{ project_type: "proyecto" }]);
  const tegDay = makeDay("2026-03-10", [{ project_type: "tesis" }]);
  const bothDay = makeDay("2026-03-17", [
    { project_type: "proyecto" },
    { project_type: "tesis" },
  ]);
  const manyDay = makeDay("2026-03-24", [
    { project_type: "proyecto" },
    { project_type: "proyecto" },
    { project_type: "proyecto" },
    { project_type: "tesis" },
    { project_type: "tesis" },
  ]);
  const clickDay = makeDay("2026-03-12", [{ project_type: "proyecto" }]);
  return [ptegDay, tegDay, bothDay, manyDay, clickDay];
}

const TODAY_OVERRIDE = "2026-03-11";
const MONTH_ANCHOR = "2026-03-01";

function renderCalendar(props: Partial<UnifiedCalendarProps> = {}) {
  const defaults: UnifiedCalendarProps = {
    days: makeFixtures(),
    mode: "view",
    monthAnchor: MONTH_ANCHOR,
    onMonthChange: vi.fn(),
    todayOverride: TODAY_OVERRIDE,
  };
  return render(<UnifiedCalendar {...defaults} {...props} />);
}

// ── View-mode tests ───────────────────────────────────────────────────────────

describe("UnifiedCalendar — grid structure", () => {
  beforeEach(() => {
    _presentationId = 1;
  });

  it("renders 7-column weekday header row (Lu Ma Mi Ju Vi Sá Do)", () => {
    renderCalendar();
    const headers = ["Lu", "Ma", "Mi", "Ju", "Vi", "Sá", "Do"];
    for (const h of headers) {
      expect(screen.getByText(h)).toBeInTheDocument();
    }
  });

  it("renders the 31 days of March 2026", () => {
    const { container } = renderCalendar();
    for (let d = 1; d <= 31; d++) {
      const dateStr = `2026-03-${String(d).padStart(2, "0")}`;
      const cell = container.querySelector(`[data-date="${dateStr}"]`);
      expect(cell, `cell for ${dateStr} should be present`).not.toBeNull();
    }
  });

  it("renders dimmed leading days from February 2026", () => {
    const { container } = renderCalendar();
    // March 1 2026 is a Sunday — the Mon-start grid has Mon-Sat of Feb as leading days.
    // Cells with dim class for dates before 2026-03-01.
    const dimCells = container.querySelectorAll(".cal-day.dim");
    expect(dimCells.length).toBeGreaterThan(0);
  });

  it("renders dimmed trailing days from April 2026", () => {
    const { container } = renderCalendar();
    const aprilCell = container.querySelector('[data-date="2026-04-01"]');
    expect(aprilCell).not.toBeNull();
    expect(aprilCell!.classList.contains("dim")).toBe(true);
  });
});

describe("UnifiedCalendar — modality coloring", () => {
  beforeEach(() => {
    _presentationId = 1;
  });

  it("gives has-pteg class to a day with only PTEG presentations", () => {
    const { container } = renderCalendar({ days: [makeDay("2026-03-03", [{ project_type: "proyecto" }])] });
    const cell = container.querySelector('[data-date="2026-03-03"]');
    expect(cell).not.toBeNull();
    expect(cell!.classList.contains("has-pteg")).toBe(true);
    expect(cell!.classList.contains("has-teg")).toBe(false);
    expect(cell!.classList.contains("has-both")).toBe(false);
  });

  it("gives has-teg class to a day with only TEG presentations", () => {
    const { container } = renderCalendar({ days: [makeDay("2026-03-10", [{ project_type: "tesis" }])] });
    const cell = container.querySelector('[data-date="2026-03-10"]');
    expect(cell).not.toBeNull();
    expect(cell!.classList.contains("has-teg")).toBe(true);
    expect(cell!.classList.contains("has-pteg")).toBe(false);
    expect(cell!.classList.contains("has-both")).toBe(false);
  });

  it("gives has-both class to a day with both PTEG and TEG presentations", () => {
    const { container } = renderCalendar({
      days: [makeDay("2026-03-17", [{ project_type: "proyecto" }, { project_type: "tesis" }])],
    });
    const cell = container.querySelector('[data-date="2026-03-17"]');
    expect(cell).not.toBeNull();
    expect(cell!.classList.contains("has-both")).toBe(true);
    expect(cell!.classList.contains("has-pteg")).toBe(false);
    expect(cell!.classList.contains("has-teg")).toBe(false);
  });

  it("renders cal-count chip with count for a day with 5 presentations", () => {
    const { container } = renderCalendar({
      days: [
        makeDay("2026-03-24", [
          { project_type: "proyecto" },
          { project_type: "proyecto" },
          { project_type: "proyecto" },
          { project_type: "tesis" },
          { project_type: "tesis" },
        ]),
      ],
    });
    const cell = container.querySelector('[data-date="2026-03-24"]');
    expect(cell).not.toBeNull();
    const chip = cell!.querySelector(".cal-count");
    expect(chip).not.toBeNull();
    expect(chip!.textContent).toBe("5");
  });
});

describe("UnifiedCalendar — today highlight", () => {
  beforeEach(() => {
    _presentationId = 1;
  });

  it("marks todayOverride date with today class", () => {
    const { container } = renderCalendar({ todayOverride: "2026-03-11" });
    const todayCell = container.querySelector('[data-date="2026-03-11"]');
    expect(todayCell).not.toBeNull();
    expect(todayCell!.classList.contains("today")).toBe(true);
  });

  it("does not mark other days as today", () => {
    const { container } = renderCalendar({ todayOverride: "2026-03-11" });
    const otherCell = container.querySelector('[data-date="2026-03-03"]');
    expect(otherCell).not.toBeNull();
    expect(otherCell!.classList.contains("today")).toBe(false);
  });
});

describe("UnifiedCalendar — view mode interactions", () => {
  beforeEach(() => {
    _presentationId = 1;
  });

  it("fires onDayClick with ISO date string when a day is clicked in view mode", () => {
    const onDayClick = vi.fn();
    const { container } = renderCalendar({ mode: "view", onDayClick, days: [makeDay("2026-03-12", [{ project_type: "proyecto" }])] });
    const cell = container.querySelector('[data-date="2026-03-12"]');
    expect(cell).not.toBeNull();
    fireEvent.click(cell!);
    expect(onDayClick).toHaveBeenCalledTimes(1);
    expect(onDayClick).toHaveBeenCalledWith("2026-03-12");
  });

  it("does not throw when onDayClick is not provided and a day is clicked", () => {
    const { container } = renderCalendar({ mode: "view", onDayClick: undefined });
    const cell = container.querySelector('[data-date="2026-03-12"]');
    expect(cell).not.toBeNull();
    expect(() => fireEvent.click(cell!)).not.toThrow();
  });
});

describe("UnifiedCalendar — mineDates overlay", () => {
  beforeEach(() => {
    _presentationId = 1;
  });

  it("adds mine class to cells in mineDates set", () => {
    const mineDates = new Set(["2026-03-11", "2026-03-20"]);
    const { container } = renderCalendar({ mineDates });
    for (const d of mineDates) {
      const cell = container.querySelector(`[data-date="${d}"]`);
      expect(cell, `cell ${d} should exist`).not.toBeNull();
      expect(cell!.classList.contains("mine")).toBe(true);
    }
  });

  it("does not add mine class to cells not in mineDates set", () => {
    const mineDates = new Set(["2026-03-11", "2026-03-20"]);
    const { container } = renderCalendar({ mineDates });
    const otherCell = container.querySelector('[data-date="2026-03-03"]');
    expect(otherCell).not.toBeNull();
    expect(otherCell!.classList.contains("mine")).toBe(false);
  });

  it("no mine class on any cell when mineDates is empty", () => {
    const { container } = renderCalendar({ mineDates: new Set() });
    const mineCells = container.querySelectorAll(".cal-day.mine");
    expect(mineCells.length).toBe(0);
  });
});

describe("UnifiedCalendar — month navigation", () => {
  beforeEach(() => {
    _presentationId = 1;
  });

  it("calls onMonthChange with next month anchor when next arrow is clicked", () => {
    const onMonthChange = vi.fn();
    renderCalendar({ onMonthChange });
    const nextBtn = screen.getByRole("button", { name: /siguiente|next|›|>/i });
    fireEvent.click(nextBtn);
    expect(onMonthChange).toHaveBeenCalledTimes(1);
    const [calledWith] = onMonthChange.mock.calls[0] as [string];
    expect(calledWith).toMatch(/^2026-04/);
  });

  it("calls onMonthChange with previous month anchor when prev arrow is clicked", () => {
    const onMonthChange = vi.fn();
    renderCalendar({ onMonthChange });
    const prevBtn = screen.getByRole("button", { name: /anterior|prev|‹|</i });
    fireEvent.click(prevBtn);
    expect(onMonthChange).toHaveBeenCalledTimes(1);
    const [calledWith] = onMonthChange.mock.calls[0] as [string];
    expect(calledWith).toMatch(/^2026-02/);
  });
});

// ── Create-mode tests ─────────────────────────────────────────────────────────

describe("UnifiedCalendar — mode toggle visibility", () => {
  beforeEach(() => {
    _presentationId = 1;
  });

  it("hides the mode toggle when allowCreate is false", () => {
    renderCalendar({ allowCreate: false, mode: "view" });
    expect(screen.queryByRole("button", { name: /crear días|vista/i })).toBeNull();
  });

  it("shows the mode toggle when allowCreate is true", () => {
    renderCalendar({ allowCreate: true, mode: "view", onModeChange: vi.fn() });
    expect(
      screen.getByRole("button", { name: /crear días/i }),
    ).toBeInTheDocument();
  });

  it("mode toggle container uses mode-pill class", () => {
    const { container } = renderCalendar({ allowCreate: true, mode: "view", onModeChange: vi.fn() });
    expect(container.querySelector(".mode-pill")).not.toBeNull();
  });
});

describe("UnifiedCalendar — mode toggle interaction", () => {
  beforeEach(() => {
    _presentationId = 1;
  });

  it('calls onModeChange("create") when "Crear días" button is clicked', () => {
    const onModeChange = vi.fn();
    renderCalendar({ allowCreate: true, mode: "view", onModeChange });
    fireEvent.click(screen.getByRole("button", { name: /crear días/i }));
    expect(onModeChange).toHaveBeenCalledWith("create");
  });

  it('calls onModeChange("view") when "Vista" button is clicked in create mode', () => {
    const onModeChange = vi.fn();
    renderCalendar({ allowCreate: true, mode: "create", onModeChange });
    fireEvent.click(screen.getByRole("button", { name: /vista/i }));
    expect(onModeChange).toHaveBeenCalledWith("view");
  });
});

describe("UnifiedCalendar — individual selection", () => {
  beforeEach(() => {
    _presentationId = 1;
  });

  it("calls onToggleDate with ISO date when a cell is clicked in individual create mode", () => {
    const onToggleDate = vi.fn();
    const { container } = renderCalendar({
      mode: "create",
      selectionMode: "individual",
      selectedDates: new Set(),
      onToggleDate,
    });
    const cell = container.querySelector('[data-date="2026-03-12"]');
    expect(cell).not.toBeNull();
    fireEvent.click(cell!);
    expect(onToggleDate).toHaveBeenCalledWith("2026-03-12");
  });

  it("adds selected class to cells whose date is in selectedDates", () => {
    const selectedDates = new Set(["2026-03-12", "2026-03-24"]);
    const { container } = renderCalendar({
      mode: "create",
      selectionMode: "individual",
      selectedDates,
      onToggleDate: vi.fn(),
    });
    for (const d of selectedDates) {
      const cell = container.querySelector(`[data-date="${d}"]`);
      expect(cell, `cell ${d} should exist`).not.toBeNull();
      expect(cell!.classList.contains("selected")).toBe(true);
    }
  });

  it("does not add selected class to cells not in selectedDates", () => {
    const selectedDates = new Set(["2026-03-12"]);
    const { container } = renderCalendar({
      mode: "create",
      selectionMode: "individual",
      selectedDates,
      onToggleDate: vi.fn(),
    });
    const otherCell = container.querySelector('[data-date="2026-03-03"]');
    expect(otherCell).not.toBeNull();
    expect(otherCell!.classList.contains("selected")).toBe(false);
  });
});

describe("UnifiedCalendar — rango selection", () => {
  beforeEach(() => {
    _presentationId = 1;
  });

  it("calls onRangeSelect exactly once after the second click with (start, end)", () => {
    const onRangeSelect = vi.fn();
    const { container } = renderCalendar({
      mode: "create",
      selectionMode: "rango",
      selectedDates: new Set(),
      onRangeSelect,
    });

    const startCell = container.querySelector('[data-date="2026-03-05"]');
    const endCell = container.querySelector('[data-date="2026-03-08"]');
    expect(startCell).not.toBeNull();
    expect(endCell).not.toBeNull();

    // First click — starts the range, callback not yet invoked
    fireEvent.click(startCell!);
    expect(onRangeSelect).not.toHaveBeenCalled();

    // Second click — completes the range
    fireEvent.click(endCell!);
    expect(onRangeSelect).toHaveBeenCalledTimes(1);
    expect(onRangeSelect).toHaveBeenCalledWith("2026-03-05", "2026-03-08");
  });

  it("regression: clicking 2026-03-01 then 2026-03-09 fires onRangeSelect('2026-03-01','2026-03-09') exactly once", () => {
    const onRangeSelect = vi.fn();
    const { container } = renderCalendar({
      mode: "create",
      selectionMode: "rango",
      selectedDates: new Set(),
      onRangeSelect,
    });

    const cell1 = container.querySelector('[data-date="2026-03-01"]');
    const cell9 = container.querySelector('[data-date="2026-03-09"]');
    expect(cell1).not.toBeNull();
    expect(cell9).not.toBeNull();

    fireEvent.click(cell1!);
    expect(onRangeSelect).not.toHaveBeenCalled();

    fireEvent.click(cell9!);
    expect(onRangeSelect).toHaveBeenCalledTimes(1);
    expect(onRangeSelect).toHaveBeenCalledWith("2026-03-01", "2026-03-09");
  });

  it("gives the rangeStart cell the start class after first click", () => {
    const { container } = renderCalendar({
      mode: "create",
      selectionMode: "rango",
      selectedDates: new Set(),
      onRangeSelect: vi.fn(),
    });

    const startCell = container.querySelector('[data-date="2026-03-05"]');
    expect(startCell).not.toBeNull();
    fireEvent.click(startCell!);

    // After first click the cell should carry the start class
    expect(startCell!.classList.contains("start")).toBe(true);
  });
});

describe("UnifiedCalendar — Crear button (CTA)", () => {
  beforeEach(() => {
    _presentationId = 1;
  });

  it("shows disabled 'Crear días' CTA when selectedDates is empty", () => {
    renderCalendar({
      mode: "create",
      selectionMode: "individual",
      selectedDates: new Set(),
      onCreate: vi.fn(),
    });
    const btn = screen.getByRole("button", { name: /crear días/i });
    expect(btn).toBeDisabled();
  });

  it("shows enabled 'Crear' CTA with badge count when selectedDates is non-empty", () => {
    renderCalendar({
      mode: "create",
      selectionMode: "individual",
      selectedDates: new Set(["2026-03-12", "2026-03-15"]),
      onCreate: vi.fn(),
    });
    // CTA text is "Crear" + badge "2"
    const btn = screen.getByRole("button", { name: /crear/i });
    expect(btn).not.toBeDisabled();
    // Badge element
    const badge = btn.querySelector(".c4-cta-num");
    expect(badge).not.toBeNull();
    expect(badge!.textContent).toBe("2");
  });

  it("shows badge count of 1 when a single date is selected", () => {
    renderCalendar({
      mode: "create",
      selectionMode: "individual",
      selectedDates: new Set(["2026-03-12"]),
      onCreate: vi.fn(),
    });
    const btn = screen.getByRole("button", { name: /crear/i });
    expect(btn).not.toBeDisabled();
    const badge = btn.querySelector(".c4-cta-num");
    expect(badge).not.toBeNull();
    expect(badge!.textContent).toBe("1");
  });

  it("calls onCreate with array of selected dates when CTA is clicked", () => {
    const onCreate = vi.fn();
    const selectedDates = new Set(["2026-03-12", "2026-03-15"]);
    renderCalendar({
      mode: "create",
      selectionMode: "individual",
      selectedDates,
      onCreate,
    });
    fireEvent.click(screen.getByRole("button", { name: /crear/i }));
    expect(onCreate).toHaveBeenCalledTimes(1);
    const [receivedDates] = onCreate.mock.calls[0] as [string[]];
    expect(receivedDates.sort()).toEqual(Array.from(selectedDates).sort());
  });
});

describe("UnifiedCalendar — range hover preview", () => {
  beforeEach(() => {
    _presentationId = 1;
  });

  it("adds prev class to cells between rangeStart and hovered date after first click", () => {
    const { container } = renderCalendar({
      mode: "create",
      selectionMode: "rango",
      selectedDates: new Set(),
      onRangeSelect: vi.fn(),
    });

    // First click — sets rangeStart to 2026-03-01
    const startCell = container.querySelector('[data-date="2026-03-01"]');
    expect(startCell).not.toBeNull();
    fireEvent.click(startCell!);

    // Hover over 2026-03-05 — cells 03-02 through 03-05 should get prev; 03-01 gets start
    const hoverCell = container.querySelector('[data-date="2026-03-05"]');
    expect(hoverCell).not.toBeNull();
    fireEvent.mouseEnter(hoverCell!);

    // rangeStart cell has start class
    expect(startCell!.classList.contains("start")).toBe(true);

    // cells 03-02 through 03-05 should be prev or hover
    for (let d = 2; d <= 5; d++) {
      const dateStr = `2026-03-${String(d).padStart(2, "0")}`;
      const cell = container.querySelector(`[data-date="${dateStr}"]`);
      expect(cell, `cell ${dateStr} should exist`).not.toBeNull();
      const hasPrevOrHover =
        cell!.classList.contains("prev") || cell!.classList.contains("hover");
      expect(hasPrevOrHover, `cell ${dateStr} should be prev or hover`).toBe(true);
    }
  });

  it("clears prev class on mouseLeave from hovered cell", () => {
    const { container } = renderCalendar({
      mode: "create",
      selectionMode: "rango",
      selectedDates: new Set(),
      onRangeSelect: vi.fn(),
    });

    const startCell = container.querySelector('[data-date="2026-03-01"]');
    fireEvent.click(startCell!);

    const hoverCell = container.querySelector('[data-date="2026-03-05"]');
    fireEvent.mouseEnter(hoverCell!);

    // Confirm prev is active on an intermediate cell
    const cell3 = container.querySelector('[data-date="2026-03-03"]');
    expect(cell3!.classList.contains("prev")).toBe(true);

    // Mouse leaves — prev clears
    fireEvent.mouseLeave(hoverCell!);
    expect(cell3!.classList.contains("prev")).toBe(false);
  });

  it("does not add prev class before the first click (no rangeStart)", () => {
    const { container } = renderCalendar({
      mode: "create",
      selectionMode: "rango",
      selectedDates: new Set(),
      onRangeSelect: vi.fn(),
    });

    const cell = container.querySelector('[data-date="2026-03-05"]');
    fireEvent.mouseEnter(cell!);

    const otherCell = container.querySelector('[data-date="2026-03-03"]');
    expect(otherCell!.classList.contains("prev")).toBe(false);
  });
});

describe("UnifiedCalendar — Limpiar button", () => {
  beforeEach(() => {
    _presentationId = 1;
  });

  it("renders Limpiar button when selectedDates is non-empty in create mode", () => {
    renderCalendar({
      mode: "create",
      selectionMode: "individual",
      selectedDates: new Set(["2026-03-12"]),
      onClear: vi.fn(),
    });
    expect(screen.getByRole("button", { name: /limpiar/i })).toBeInTheDocument();
  });

  it("does not render Limpiar button when selectedDates is empty and no rangeStart", () => {
    renderCalendar({
      mode: "create",
      selectionMode: "individual",
      selectedDates: new Set(),
      onClear: vi.fn(),
    });
    expect(screen.queryByRole("button", { name: /limpiar/i })).toBeNull();
  });

  it("calls onClear when Limpiar button is clicked", () => {
    const onClear = vi.fn();
    renderCalendar({
      mode: "create",
      selectionMode: "individual",
      selectedDates: new Set(["2026-03-12"]),
      onClear,
    });
    fireEvent.click(screen.getByRole("button", { name: /limpiar/i }));
    expect(onClear).toHaveBeenCalledTimes(1);
  });
});

describe("UnifiedCalendar — rango re-click clears previous selection", () => {
  beforeEach(() => {
    _presentationId = 1;
  });

  it("fires onClear and starts a new range when clicking in rango mode with existing selectedDates and no rangeStart", () => {
    const onClear = vi.fn();
    const onRangeSelect = vi.fn();
    const { container } = renderCalendar({
      mode: "create",
      selectionMode: "rango",
      // Simulate a previously committed range
      selectedDates: new Set(["2026-03-01", "2026-03-02", "2026-03-03"]),
      onRangeSelect,
      onClear,
    });

    // Third click while selectedDates.size > 0 and rangeStart === null
    // Should call onClear and set rangeStart to the clicked date
    const thirdCell = container.querySelector('[data-date="2026-03-10"]');
    fireEvent.click(thirdCell!);

    expect(onClear).toHaveBeenCalledTimes(1);
    // onRangeSelect should NOT be called yet (it's now the start of a new range)
    expect(onRangeSelect).not.toHaveBeenCalled();

    // A subsequent click should commit the new range
    const fourthCell = container.querySelector('[data-date="2026-03-12"]');
    fireEvent.click(fourthCell!);
    expect(onRangeSelect).toHaveBeenCalledTimes(1);
    expect(onRangeSelect).toHaveBeenCalledWith("2026-03-10", "2026-03-12");
  });
});

describe("UnifiedCalendar — selection-mode radiogroup", () => {
  beforeEach(() => {
    _presentationId = 1;
  });

  it("renders both Rango and Individual buttons inside an ARIA radiogroup in the sub-toolbar", () => {
    renderCalendar({
      mode: "create",
      selectionMode: "individual",
      selectedDates: new Set(),
      onSelectionModeChange: vi.fn(),
    });
    const group = screen.getByRole("radiogroup", { name: /modo de selección/i });
    const rangoBtn = within(group).getByRole("radio", { name: /rango/i });
    const indBtn = within(group).getByRole("radio", { name: /individual/i });
    expect(rangoBtn).toBeInTheDocument();
    expect(indBtn).toBeInTheDocument();
  });

  it("active button has active class when selectionMode is individual", () => {
    const { container } = renderCalendar({
      mode: "create",
      selectionMode: "individual",
      selectedDates: new Set(),
      onSelectionModeChange: vi.fn(),
    });
    const group = container.querySelector('[role="radiogroup"][aria-label="Modo de selección"]');
    expect(group).not.toBeNull();
    const indBtn = within(group as HTMLElement).getByRole("radio", {
      name: /individual/i,
    });
    expect(indBtn.classList.contains("active")).toBe(true);
  });

  it("active button has active class when selectionMode is rango", () => {
    const { container } = renderCalendar({
      mode: "create",
      selectionMode: "rango",
      selectedDates: new Set(),
      onSelectionModeChange: vi.fn(),
    });
    const group = container.querySelector('[role="radiogroup"][aria-label="Modo de selección"]');
    expect(group).not.toBeNull();
    const rangoBtn = within(group as HTMLElement).getByRole("radio", {
      name: /rango/i,
    });
    expect(rangoBtn.classList.contains("active")).toBe(true);
  });

  it("calls onSelectionModeChange with rango when Rango button is clicked in individual mode", () => {
    const onSelectionModeChange = vi.fn();
    renderCalendar({
      mode: "create",
      selectionMode: "individual",
      selectedDates: new Set(),
      onSelectionModeChange,
    });
    const group = screen.getByRole("radiogroup", { name: /modo de selección/i });
    fireEvent.click(within(group).getByRole("radio", { name: /rango/i }));
    expect(onSelectionModeChange).toHaveBeenCalledWith("rango");
  });

  it("calls onSelectionModeChange with individual when Individual button is clicked in rango mode", () => {
    const onSelectionModeChange = vi.fn();
    renderCalendar({
      mode: "create",
      selectionMode: "rango",
      selectedDates: new Set(),
      onSelectionModeChange,
    });
    const group = screen.getByRole("radiogroup", { name: /modo de selección/i });
    fireEvent.click(within(group).getByRole("radio", { name: /individual/i }));
    expect(onSelectionModeChange).toHaveBeenCalledWith("individual");
  });

  it("sub-toolbar is not rendered when mode is view", () => {
    const { container } = renderCalendar({ mode: "view" });
    expect(container.querySelector(".subtoolbar")).toBeNull();
  });
});

// ── New C4 tests ──────────────────────────────────────────────────────────────

describe("UnifiedCalendar — legend bar (view mode only)", () => {
  beforeEach(() => {
    _presentationId = 1;
  });

  it("renders the legend bar in view mode", () => {
    const { container } = renderCalendar({ mode: "view" });
    expect(container.querySelector(".legend-bar")).not.toBeNull();
  });

  it("does not render the legend bar in create mode", () => {
    const { container } = renderCalendar({ mode: "create", selectedDates: new Set() });
    expect(container.querySelector(".legend-bar")).toBeNull();
  });

  it("renders PTEG, TEG, and Ambos legend items always", () => {
    renderCalendar({ mode: "view" });
    expect(screen.getByText("PTEG")).toBeInTheDocument();
    expect(screen.getByText("TEG")).toBeInTheDocument();
    expect(screen.getByText("Ambos")).toBeInTheDocument();
  });

  it("does not render 'Tu defensa' legend item when mineDates is empty", () => {
    renderCalendar({ mode: "view", mineDates: new Set() });
    expect(screen.queryByText("Tu defensa")).toBeNull();
  });

  it("does not render 'Tu defensa' legend item when mineDates is undefined", () => {
    renderCalendar({ mode: "view", mineDates: undefined });
    expect(screen.queryByText("Tu defensa")).toBeNull();
  });

  it("renders 'Tu defensa' legend item when mineDates has at least one date", () => {
    renderCalendar({ mode: "view", mineDates: new Set(["2026-03-11"]) });
    expect(screen.getByText("Tu defensa")).toBeInTheDocument();
  });
});

describe("UnifiedCalendar — cal-count chip", () => {
  beforeEach(() => {
    _presentationId = 1;
  });

  it("renders .cal-count chip inside a cell that has presentations", () => {
    const { container } = renderCalendar({
      days: [makeDay("2026-03-05", [{ project_type: "proyecto" }, { project_type: "tesis" }, { project_type: "proyecto" }])],
    });
    const cell = container.querySelector('[data-date="2026-03-05"]');
    expect(cell).not.toBeNull();
    const chip = cell!.querySelector(".cal-count");
    expect(chip).not.toBeNull();
    expect(chip!.textContent).toBe("3");
  });

  it("does not render .cal-count chip in a cell with no presentations", () => {
    const { container } = renderCalendar({ days: [] });
    const cell = container.querySelector('[data-date="2026-03-05"]');
    expect(cell).not.toBeNull();
    expect(cell!.querySelector(".cal-count")).toBeNull();
  });
});

describe("UnifiedCalendar — footer state machine", () => {
  beforeEach(() => {
    _presentationId = 1;
  });

  it("footer has c4-foot empty class when nothing is selected and no rangeStart", () => {
    const { container } = renderCalendar({
      mode: "create",
      selectionMode: "individual",
      selectedDates: new Set(),
      onCreate: vi.fn(),
    });
    const foot = container.querySelector(".c4-foot");
    expect(foot).not.toBeNull();
    expect(foot!.classList.contains("empty")).toBe(true);
  });

  it("footer has c4-foot committed class when selectedDates is non-empty and no rangeStart", () => {
    const { container } = renderCalendar({
      mode: "create",
      selectionMode: "individual",
      selectedDates: new Set(["2026-03-12", "2026-03-15"]),
      onCreate: vi.fn(),
    });
    const foot = container.querySelector(".c4-foot");
    expect(foot).not.toBeNull();
    expect(foot!.classList.contains("committed")).toBe(true);
    expect(foot!.classList.contains("empty")).toBe(false);
  });

  it("footer has no empty or committed class during range preview (default tinted state)", () => {
    const { container } = renderCalendar({
      mode: "create",
      selectionMode: "rango",
      selectedDates: new Set(),
      onRangeSelect: vi.fn(),
    });

    // Click to set rangeStart
    const startCell = container.querySelector('[data-date="2026-03-01"]');
    fireEvent.click(startCell!);
    // Hover to trigger preview
    const hoverCell = container.querySelector('[data-date="2026-03-05"]');
    fireEvent.mouseEnter(hoverCell!);

    const foot = container.querySelector(".c4-foot");
    expect(foot).not.toBeNull();
    expect(foot!.classList.contains("empty")).toBe(false);
    expect(foot!.classList.contains("committed")).toBe(false);
  });

  it("footer has no empty or committed class when anchored (rangeStart set, no hover)", () => {
    const { container } = renderCalendar({
      mode: "create",
      selectionMode: "rango",
      selectedDates: new Set(),
      onRangeSelect: vi.fn(),
    });

    // Click to set rangeStart only — no hover
    const startCell = container.querySelector('[data-date="2026-03-01"]');
    fireEvent.click(startCell!);

    const foot = container.querySelector(".c4-foot");
    expect(foot).not.toBeNull();
    expect(foot!.classList.contains("empty")).toBe(false);
    expect(foot!.classList.contains("committed")).toBe(false);
  });

  it("footer does not render when mode is view", () => {
    const { container } = renderCalendar({ mode: "view" });
    expect(container.querySelector(".c4-foot")).toBeNull();
  });
});

describe("UnifiedCalendar — footer hint texts", () => {
  beforeEach(() => {
    _presentationId = 1;
  });

  it("shows hint 'Selecciona el día final' when anchored (rangeStart set, no hover)", () => {
    const { container } = renderCalendar({
      mode: "create",
      selectionMode: "rango",
      selectedDates: new Set(),
      onRangeSelect: vi.fn(),
    });

    const startCell = container.querySelector('[data-date="2026-03-01"]');
    fireEvent.click(startCell!);

    expect(screen.getByText("Selecciona el día final")).toBeInTheDocument();
    const sub = container.querySelector(".c4-text .sub");
    expect(sub).not.toBeNull();
    expect(sub!.classList.contains("hint")).toBe(true);
  });

  it("shows hint 'Clic para confirmar el rango' when hovering during rango preview", () => {
    const { container } = renderCalendar({
      mode: "create",
      selectionMode: "rango",
      selectedDates: new Set(),
      onRangeSelect: vi.fn(),
    });

    const startCell = container.querySelector('[data-date="2026-03-01"]');
    fireEvent.click(startCell!);
    const hoverCell = container.querySelector('[data-date="2026-03-05"]');
    fireEvent.mouseEnter(hoverCell!);

    expect(screen.getByText("Clic para confirmar el rango")).toBeInTheDocument();
    const sub = container.querySelector(".c4-text .sub");
    expect(sub).not.toBeNull();
    expect(sub!.classList.contains("hint")).toBe(true);
  });

  it("shows sub-text 'Selecciona un día para empezar' in empty state", () => {
    renderCalendar({
      mode: "create",
      selectionMode: "individual",
      selectedDates: new Set(),
    });
    expect(screen.getByText("Selecciona un día para empezar")).toBeInTheDocument();
    const { container } = renderCalendar({
      mode: "create",
      selectionMode: "individual",
      selectedDates: new Set(),
    });
    const sub = container.querySelector(".c4-text .sub");
    expect(sub).not.toBeNull();
    expect(sub!.classList.contains("hint")).toBe(false);
  });
});

describe("UnifiedCalendar — Limpiar visibility (C4)", () => {
  beforeEach(() => {
    _presentationId = 1;
  });

  it("Limpiar button is hidden when footer is in empty state", () => {
    renderCalendar({
      mode: "create",
      selectionMode: "individual",
      selectedDates: new Set(),
      onClear: vi.fn(),
    });
    expect(screen.queryByRole("button", { name: /limpiar/i })).toBeNull();
  });

  it("Limpiar button is visible when footer is in committed state", () => {
    renderCalendar({
      mode: "create",
      selectionMode: "individual",
      selectedDates: new Set(["2026-03-12"]),
      onClear: vi.fn(),
    });
    expect(screen.getByRole("button", { name: /limpiar/i })).toBeInTheDocument();
  });

  it("Limpiar button is visible during preview state", () => {
    const { container } = renderCalendar({
      mode: "create",
      selectionMode: "rango",
      selectedDates: new Set(),
      onRangeSelect: vi.fn(),
      onClear: vi.fn(),
    });

    const startCell = container.querySelector('[data-date="2026-03-01"]');
    fireEvent.click(startCell!);
    const hoverCell = container.querySelector('[data-date="2026-03-05"]');
    fireEvent.mouseEnter(hoverCell!);

    expect(screen.getByRole("button", { name: /limpiar/i })).toBeInTheDocument();
  });
});

describe("UnifiedCalendar — CTA disabled / enabled (C4)", () => {
  beforeEach(() => {
    _presentationId = 1;
  });

  it("CTA is disabled in empty state", () => {
    renderCalendar({
      mode: "create",
      selectionMode: "individual",
      selectedDates: new Set(),
      onCreate: vi.fn(),
    });
    const btn = screen.getByRole("button", { name: /crear días/i });
    expect(btn).toBeDisabled();
  });

  it("CTA is disabled during preview state", () => {
    const { container } = renderCalendar({
      mode: "create",
      selectionMode: "rango",
      selectedDates: new Set(),
      onRangeSelect: vi.fn(),
      onCreate: vi.fn(),
    });

    const startCell = container.querySelector('[data-date="2026-03-01"]');
    fireEvent.click(startCell!);
    const hoverCell = container.querySelector('[data-date="2026-03-05"]');
    fireEvent.mouseEnter(hoverCell!);

    const btn = screen.getByRole("button", { name: /crear días/i });
    expect(btn).toBeDisabled();
  });

  it("CTA is disabled in anchored state", () => {
    const { container } = renderCalendar({
      mode: "create",
      selectionMode: "rango",
      selectedDates: new Set(),
      onRangeSelect: vi.fn(),
      onCreate: vi.fn(),
    });

    const startCell = container.querySelector('[data-date="2026-03-01"]');
    fireEvent.click(startCell!);

    const btn = screen.getByRole("button", { name: /crear días/i });
    expect(btn).toBeDisabled();
  });

  it("CTA is enabled when selectedDates.size > 0 and rangeStart is null (committed)", () => {
    renderCalendar({
      mode: "create",
      selectionMode: "individual",
      selectedDates: new Set(["2026-03-12"]),
      onCreate: vi.fn(),
    });
    const btn = screen.getByRole("button", { name: /crear/i });
    expect(btn).not.toBeDisabled();
  });
});
