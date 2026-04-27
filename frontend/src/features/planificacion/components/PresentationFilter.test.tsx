import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import PresentationFilter from "./PresentationFilter";
import { DEFAULT_FILTERS } from "../lib/applyPresentationFilters";
import type { PresentationDay, Presentation } from "../types/planificacion";
import type { PresentationFilters } from "../lib/applyPresentationFilters";

// ── Fixture ────────────────────────────────────────────────────────────────────
// Total: 38 presentations, 22 PTEG, 16 TEG across a realistic set of days.

function makePresentation(id: number, overrides: Partial<Presentation> = {}): Presentation {
  return {
    id,
    day: 1,
    project: id + 100,
    project_title: `Project ${id}`,
    project_type: "proyecto",
    student_name: "Student Name",
    student_email: "student@test.com",
    tutor: 5,
    tutor_name: "Tutor Name",
    jurado: [9, 10],
    jurado_names: ["Jurado A", "Jurado B"],
    start_time: "09:00",
    duration_minutes: 30,
    order: id,
    ...overrides,
  };
}

function buildDays(): PresentationDay[] {
  const days: PresentationDay[] = [];
  let presId = 1;
  // Build 6 days with 38 total presentations (22 PTEG + 16 TEG)
  // Day 1: 8 PTEG
  days.push({
    id: 1, date: "2026-03-08", notes: "",
    presentations: Array.from({ length: 8 }, () =>
      makePresentation(presId++, { project_type: "proyecto" })
    ),
  });
  // Day 2: 6 PTEG + 4 TEG = 10
  days.push({
    id: 2, date: "2026-03-10", notes: "",
    presentations: [
      ...Array.from({ length: 6 }, () => makePresentation(presId++, { project_type: "proyecto" })),
      ...Array.from({ length: 4 }, () => makePresentation(presId++, { project_type: "tesis" })),
    ],
  });
  // Day 3: 5 PTEG + 5 TEG = 10
  days.push({
    id: 3, date: "2026-03-12", notes: "",
    presentations: [
      ...Array.from({ length: 5 }, () => makePresentation(presId++, { project_type: "proyecto" })),
      ...Array.from({ length: 5 }, () => makePresentation(presId++, { project_type: "tesis" })),
    ],
  });
  // Day 4: 3 PTEG + 7 TEG = 10 — presId reaches ~37
  days.push({
    id: 4, date: "2026-03-18", notes: "",
    presentations: [
      ...Array.from({ length: 3 }, () => makePresentation(presId++, { project_type: "proyecto" })),
      ...Array.from({ length: 7 }, () => makePresentation(presId++, { project_type: "tesis" })),
    ],
  });
  return days;
}

const FIXTURE_DAYS = buildDays();
const TOTAL_COUNT = FIXTURE_DAYS.reduce((s, d) => s + d.presentations.length, 0);
const PTEG_COUNT = FIXTURE_DAYS.flatMap((d) => d.presentations).filter((p) => p.project_type === "proyecto").length;
const TEG_COUNT = FIXTURE_DAYS.flatMap((d) => d.presentations).filter((p) => p.project_type === "tesis").length;

const NO_OP: (next: PresentationFilters) => void = () => {};

function renderFilter(overrides: Partial<{
  days: PresentationDay[];
  filters: PresentationFilters;
  onChange: (next: PresentationFilters) => void;
  resultCount: number;
}> = {}) {
  const props = {
    days: FIXTURE_DAYS,
    filters: DEFAULT_FILTERS,
    onChange: NO_OP,
    resultCount: TOTAL_COUNT,
    ...overrides,
  };
  return render(<PresentationFilter {...props} />);
}

// ── Tests ──────────────────────────────────────────────────────────────────────

describe("PresentationFilter", () => {
  // 1 — Structural zones
  it("renders 4 zones: Buscar, Modalidad, Período, Resultados", () => {
    renderFilter();
    expect(document.querySelector(".pf-zone-search")).not.toBeNull();
    expect(document.querySelector(".pf-zone-modality")).not.toBeNull();
    expect(document.querySelector(".pf-zone-period")).not.toBeNull();
    expect(document.querySelector(".pf-zone-result")).not.toBeNull();
  });

  // 2 — Search input role and aria-label
  it("renders search input with role=searchbox and aria-label=Buscar", () => {
    renderFilter();
    const input = screen.getByRole("searchbox", { name: /buscar/i });
    expect(input).toBeInTheDocument();
  });

  // 3 — Search placeholder
  it("renders search input with placeholder matching /proyecto.*estudiante.*tutor/i", () => {
    renderFilter();
    const input = screen.getByRole("searchbox", { name: /buscar/i });
    expect(input.getAttribute("placeholder")).toMatch(/proyecto.*estudiante.*tutor/i);
  });

  // 4 — Typing in search fires onChange with updated search field
  it("fires onChange with updated search field when user types in the search input", () => {
    const onChange = vi.fn();
    renderFilter({ onChange });
    const input = screen.getByRole("searchbox", { name: /buscar/i });
    fireEvent.change(input, { target: { value: "redes" } });
    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({ search: "redes" })
    );
  });

  // 5 — Clear button hidden when search is empty
  it("does not render the search clear button when search is empty", () => {
    renderFilter({ filters: { ...DEFAULT_FILTERS, search: "" } });
    const clearBtn = document.querySelector(".pf-search-clear");
    // Either null or hidden (aria-hidden or display:none — but we check DOM presence)
    if (clearBtn) {
      expect(clearBtn.getAttribute("aria-hidden")).toBe("true");
    } else {
      expect(clearBtn).toBeNull();
    }
  });

  // 6 — Clear button visible when search has value and clears on click
  it("shows clear button when search has value; clicking it fires onChange with empty search", () => {
    const onChange = vi.fn();
    renderFilter({
      filters: { ...DEFAULT_FILTERS, search: "sistema" },
      onChange,
    });
    const clearBtn = document.querySelector(".pf-search-clear") as HTMLElement | null;
    expect(clearBtn).not.toBeNull();
    fireEvent.click(clearBtn!);
    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({ search: "" })
    );
  });

  // 7 — 3 modality chips render with Todas / PTEG / TEG and counts
  it("renders 3 modality chips with text Todas, PTEG, TEG and respective counts", () => {
    renderFilter();
    const chips = document.querySelectorAll(".pf-mod-chip");
    expect(chips).toHaveLength(3);
    const texts = Array.from(chips).map((c) => c.textContent ?? "");
    expect(texts.some((t) => /todas/i.test(t))).toBe(true);
    expect(texts.some((t) => /pteg/i.test(t))).toBe(true);
    expect(texts.some((t) => /teg/i.test(t) && !/pteg/i.test(t))).toBe(true);
  });

  // 8 — Modality chips show counts from the days prop
  it("modality chips show correct counts for the fixture days", () => {
    renderFilter();
    const chips = Array.from(document.querySelectorAll(".pf-mod-chip"));
    const ptegChip = chips.find((c) => /pteg/i.test(c.textContent ?? ""));
    const tegChip = chips.find((c) => /teg/i.test(c.textContent ?? "") && !/pteg/i.test(c.textContent ?? ""));
    expect(ptegChip?.textContent).toContain(String(PTEG_COUNT));
    expect(tegChip?.textContent).toContain(String(TEG_COUNT));
  });

  // 9 — Clicking PTEG chip fires onChange with modality=proyecto
  it("clicking PTEG chip fires onChange with modality=proyecto", () => {
    const onChange = vi.fn();
    renderFilter({ onChange });
    const chips = Array.from(document.querySelectorAll(".pf-mod-chip"));
    const ptegChip = chips.find((c) => /pteg/i.test(c.textContent ?? "")) as HTMLElement;
    fireEvent.click(ptegChip);
    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({ modality: "proyecto" })
    );
  });

  // 10 — Clicking TEG chip fires onChange with modality=tesis
  it("clicking TEG chip fires onChange with modality=tesis", () => {
    const onChange = vi.fn();
    renderFilter({ onChange });
    const chips = Array.from(document.querySelectorAll(".pf-mod-chip"));
    const tegChip = chips.find(
      (c) => /teg/i.test(c.textContent ?? "") && !/pteg/i.test(c.textContent ?? "")
    ) as HTMLElement;
    fireEvent.click(tegChip);
    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({ modality: "tesis" })
    );
  });

  // 11 — Todas chip has active class when modality=all
  it("Todas chip has active class when filters.modality is all", () => {
    renderFilter({ filters: { ...DEFAULT_FILTERS, modality: "all" } });
    const chips = Array.from(document.querySelectorAll(".pf-mod-chip"));
    const todasChip = chips.find((c) => /todas/i.test(c.textContent ?? ""));
    expect(todasChip?.classList.contains("active")).toBe(true);
  });

  // 12 — PTEG chip has class pteg and active when modality=proyecto
  it("PTEG chip has class pteg and active when filters.modality is proyecto", () => {
    renderFilter({ filters: { ...DEFAULT_FILTERS, modality: "proyecto" } });
    const chips = Array.from(document.querySelectorAll(".pf-mod-chip"));
    const ptegChip = chips.find((c) => /pteg/i.test(c.textContent ?? ""));
    expect(ptegChip?.classList.contains("pteg")).toBe(true);
    expect(ptegChip?.classList.contains("active")).toBe(true);
  });

  // 13 — TEG chip has class teg and active when modality=tesis
  it("TEG chip has class teg and active when filters.modality is tesis", () => {
    renderFilter({ filters: { ...DEFAULT_FILTERS, modality: "tesis" } });
    const chips = Array.from(document.querySelectorAll(".pf-mod-chip"));
    const tegChip = chips.find(
      (c) => /teg/i.test(c.textContent ?? "") && !/pteg/i.test(c.textContent ?? "")
    );
    expect(tegChip?.classList.contains("teg")).toBe(true);
    expect(tegChip?.classList.contains("active")).toBe(true);
  });

  // 14 — Period trigger shows current period label
  it("period trigger shows current period label", () => {
    renderFilter({ filters: { ...DEFAULT_FILTERS, period: "all" } });
    const trigger = document.querySelector(".pf-period-trigger");
    expect(trigger).not.toBeNull();
    // It should show some label for the "all" state (e.g. "Todos" or "Todo el período")
    expect(trigger!.textContent).toBeTruthy();
  });

  // 15 — Clicking period trigger opens popover with period options
  it("clicking period trigger opens a popover with Hoy, Próxima semana, Próximo mes, Este período, Personalizado options", () => {
    renderFilter();
    const trigger = document.querySelector(".pf-period-trigger") as HTMLElement;
    fireEvent.click(trigger);
    const popover = document.querySelector(".pf-period-popover");
    expect(popover).not.toBeNull();
    const options = document.querySelectorAll(".pf-period-option");
    const labels = Array.from(options).map((o) => o.textContent ?? "");
    expect(labels.some((l) => /hoy/i.test(l))).toBe(true);
    expect(labels.some((l) => /próxima semana/i.test(l))).toBe(true);
    expect(labels.some((l) => /próximo mes/i.test(l))).toBe(true);
    expect(labels.some((l) => /este per[íi]odo/i.test(l))).toBe(true);
    expect(labels.some((l) => /personalizado/i.test(l))).toBe(true);
  });

  // 16 — Period options (except Personalizado) show a count
  it("period options except Personalizado show a numeric count", () => {
    renderFilter();
    const trigger = document.querySelector(".pf-period-trigger") as HTMLElement;
    fireEvent.click(trigger);
    const options = Array.from(document.querySelectorAll(".pf-period-option")).filter(
      (o) => !/personalizado/i.test(o.textContent ?? "")
    );
    expect(options.length).toBeGreaterThan(0);
    options.forEach((option) => {
      expect(option.textContent).toMatch(/\d+/);
    });
  });

  // 17 — Selecting a period fires onChange and closes the popover
  it("selecting a period option fires onChange with the new period and closes the popover", () => {
    const onChange = vi.fn();
    renderFilter({ onChange });
    const trigger = document.querySelector(".pf-period-trigger") as HTMLElement;
    fireEvent.click(trigger);
    const hoyOption = Array.from(document.querySelectorAll(".pf-period-option")).find(
      (o) => /hoy/i.test(o.textContent ?? "")
    ) as HTMLElement;
    fireEvent.click(hoyOption);
    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({ period: "today" })
    );
    expect(document.querySelector(".pf-period-popover")).toBeNull();
  });

  // 18 — Personalizado option is disabled
  it("Personalizado option is disabled (aria-disabled or disabled attribute)", () => {
    renderFilter();
    const trigger = document.querySelector(".pf-period-trigger") as HTMLElement;
    fireEvent.click(trigger);
    const customOption = Array.from(document.querySelectorAll(".pf-period-option")).find(
      (o) => /personalizado/i.test(o.textContent ?? "")
    );
    expect(customOption).not.toBeNull();
    const isDisabled =
      customOption!.getAttribute("aria-disabled") === "true" ||
      (customOption as HTMLButtonElement).disabled === true ||
      customOption!.classList.contains("disabled");
    expect(isDisabled).toBe(true);
  });

  // 19 — Result zone: inactive shows {N} presentaciones
  it("result zone shows resultCount and presentaciones when no filters active", () => {
    renderFilter({ filters: DEFAULT_FILTERS, resultCount: TOTAL_COUNT });
    const resultNum = document.querySelector(".pf-result-num");
    expect(resultNum).not.toBeNull();
    expect(resultNum!.textContent).toContain(String(TOTAL_COUNT));
    const zone = document.querySelector(".pf-zone-result");
    expect(zone!.textContent).toMatch(/presentaciones/i);
    expect(zone!.textContent).not.toMatch(/filtrados/i);
  });

  // 20 — Result zone: active filters shows {filtered} de {total} + filtrados
  it("result zone shows {resultCount} de {total} and filtrados when filters are active", () => {
    const filteredCount = 5;
    renderFilter({
      filters: { ...DEFAULT_FILTERS, modality: "proyecto" },
      resultCount: filteredCount,
    });
    const zone = document.querySelector(".pf-zone-result");
    expect(zone!.textContent).toContain(String(filteredCount));
    expect(zone!.textContent).toContain(String(TOTAL_COUNT));
    expect(zone!.textContent).toMatch(/filtrados/i);
  });

  // 21 — Active-filters strip not rendered when no active filters
  it("does not render active-filters strip when DEFAULT_FILTERS are used", () => {
    renderFilter({ filters: DEFAULT_FILTERS });
    expect(document.querySelector(".pf-active-filters")).toBeNull();
  });

  // 22 — Active-filters strip renders one chip per active filter
  it("renders one chip for each active filter in pf-active-filters", () => {
    const activeFilters: PresentationFilters = { search: "redes", modality: "proyecto", period: "today" };
    renderFilter({ filters: activeFilters });
    const strip = document.querySelector(".pf-active-filters");
    expect(strip).not.toBeNull();
    const chips = strip!.querySelectorAll(".pf-af-chip");
    expect(chips.length).toBe(3);
  });

  // 23 — Each chip has a close × button that resets that single filter
  it("clicking a chip close button resets only that filter via onChange", () => {
    const onChange = vi.fn();
    const activeFilters: PresentationFilters = { search: "redes", modality: "all", period: "all" };
    renderFilter({ filters: activeFilters, onChange });
    const strip = document.querySelector(".pf-active-filters");
    const chip = strip!.querySelector(".pf-af-chip");
    const closeBtn = chip!.querySelector("button");
    fireEvent.click(closeBtn!);
    // Should reset only search while keeping other defaults
    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({ search: "" })
    );
  });

  // 24 — Limpiar todo button resets all filters via onChange(DEFAULT_FILTERS)
  it("clicking Limpiar todo fires onChange(DEFAULT_FILTERS)", () => {
    const onChange = vi.fn();
    const activeFilters: PresentationFilters = { search: "x", modality: "tesis", period: "week" };
    renderFilter({ filters: activeFilters, onChange });
    const clearAll = document.querySelector(".pf-clear-all") as HTMLElement;
    expect(clearAll).not.toBeNull();
    fireEvent.click(clearAll);
    expect(onChange).toHaveBeenCalledWith(DEFAULT_FILTERS);
  });
});
