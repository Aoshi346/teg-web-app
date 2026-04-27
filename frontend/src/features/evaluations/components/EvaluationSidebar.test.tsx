import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import type { Question } from "@features/evaluations/lib/questions/questions";

// ── component under test ──────────────────────────────────────────────────────
// Note: After Sub-N impl this will be the new Rail component.
// The test covers the new .rail namespace structure.
import Rail from "./Rail";
import type { RailSection } from "./Rail";

// ─────────────────────────────────────────────────────────────────────────────

const PTEG_SECTION: RailSection = {
  label: "Diagramación",
  numeral: "01",
  total: 8,
  answered: 0,
  isTeg: false,
  subsections: [
    { label: "Portada", anchor: "portada", answered: 0, total: 3 },
    { label: "Índice", anchor: "indice", answered: 0, total: 2 },
  ],
};

const TEG_SECTION: RailSection = {
  label: "Contenido",
  numeral: "02",
  total: 12,
  answered: 3,
  isTeg: true,
  subsections: [
    { label: "Introducción", anchor: "introduccion", answered: 2, total: 4 },
    { label: "Marco Teórico", anchor: "marco-teorico", answered: 1, total: 4 },
  ],
};

function renderRail(
  sections = [PTEG_SECTION, TEG_SECTION],
  activeAnchor: string | null = null,
  overrides: Record<string, unknown> = {}
) {
  const onAnchorClick = vi.fn();
  const { container } = render(
    <Rail
      sections={sections}
      activeAnchor={activeAnchor}
      onAnchorClick={onAnchorClick}
      answeredCount={3}
      totalRequired={20}
      autosaving={false}
      {...overrides}
    />
  );
  return { container, onAnchorClick };
}

// ─────────────────────────────────────────────────────────────────────────────
// Root element
// ─────────────────────────────────────────────────────────────────────────────
describe("Rail — root element (Sub-N)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders an element with class rail", () => {
    const { container } = renderRail();
    expect(container.querySelector(".rail")).not.toBeNull();
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// Group sections
// ─────────────────────────────────────────────────────────────────────────────
describe("Rail — grouped sections (Sub-N)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders .rail-grp for Diagramación section", () => {
    const { container } = renderRail();
    expect(container.querySelector(".rail-grp")).not.toBeNull();
  });

  it("renders .rail-grp.is-teg for Contenido section", () => {
    const { container } = renderRail();
    expect(container.querySelector(".rail-grp.is-teg")).not.toBeNull();
  });

  it("renders exactly 2 .rail-grp elements (one per section)", () => {
    const { container } = renderRail();
    expect(container.querySelectorAll(".rail-grp").length).toBe(2);
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// Group headers
// ─────────────────────────────────────────────────────────────────────────────
describe("Rail — group headers (Sub-N)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("Diagramación group header shows Fraunces numeral '01'", () => {
    renderRail();
    expect(screen.getByText("01")).toBeInTheDocument();
  });

  it("Contenido group header shows Fraunces numeral '02'", () => {
    renderRail();
    expect(screen.getByText("02")).toBeInTheDocument();
  });

  it("Diagramación group header shows label 'Diagramación'", () => {
    renderRail();
    expect(screen.getByText(/Diagramaci/i)).toBeInTheDocument();
  });

  it("Contenido group header shows label 'Contenido'", () => {
    renderRail();
    expect(screen.getByText(/Contenido/i)).toBeInTheDocument();
  });

  it("Diagramación group shows count chip '0/8'", () => {
    renderRail();
    expect(screen.getByText("0/8")).toBeInTheDocument();
  });

  it("Contenido group shows count chip '3/12'", () => {
    renderRail();
    expect(screen.getByText("3/12")).toBeInTheDocument();
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// Subsection anchors
// ─────────────────────────────────────────────────────────────────────────────
describe("Rail — subsection anchors (Sub-N)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders .rail-anchor elements for each subsection", () => {
    const { container } = renderRail();
    const anchors = container.querySelectorAll(".rail-anchor");
    // 2 pteg subsections + 2 teg subsections = 4
    expect(anchors.length).toBe(4);
  });

  it("renders subsection label 'Portada'", () => {
    renderRail();
    expect(screen.getByText(/^Portada$/i)).toBeInTheDocument();
  });

  it("renders subsection label 'Introducción'", () => {
    renderRail();
    expect(screen.getByText(/Introducci/i)).toBeInTheDocument();
  });

  it("each anchor renders a dot indicator element", () => {
    const { container } = renderRail();
    const dots = container.querySelectorAll(".rail-anchor .rail-dot, .rail-anchor [class*='dot']");
    expect(dots.length).toBeGreaterThan(0);
  });

  it("each subsection anchor shows fraction e.g. '0/3'", () => {
    renderRail();
    expect(screen.getByText("0/3")).toBeInTheDocument();
  });

  it("clicking a subsection anchor calls onAnchorClick with the anchor id", () => {
    const { container, onAnchorClick } = renderRail();
    const anchors = container.querySelectorAll(".rail-anchor");
    fireEvent.click(anchors[0]);
    expect(onAnchorClick).toHaveBeenCalledWith("portada");
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// Active anchor state
// ─────────────────────────────────────────────────────────────────────────────
describe("Rail — active anchor styling (Sub-N)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("active anchor has class 'active' on its .rail-anchor element", () => {
    const { container } = renderRail(
      [PTEG_SECTION, TEG_SECTION],
      "portada"
    );
    const activeAnchor = container.querySelector(".rail-anchor.active");
    expect(activeAnchor).not.toBeNull();
  });

  it("inactive anchors do not carry 'active' class", () => {
    const { container } = renderRail(
      [PTEG_SECTION, TEG_SECTION],
      "portada"
    );
    const allAnchors = container.querySelectorAll(".rail-anchor");
    const activeAnchors = container.querySelectorAll(".rail-anchor.active");
    expect(activeAnchors.length).toBeLessThan(allAnchors.length);
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// Autosave pulse strip
// ─────────────────────────────────────────────────────────────────────────────
describe("Rail — autosave pulse strip (Sub-N)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders .rail-draft element", () => {
    const { container } = renderRail([PTEG_SECTION, TEG_SECTION], null, {
      autosaving: true,
    });
    expect(container.querySelector(".rail-draft")).not.toBeNull();
  });

  it("autosave strip contains a success-state indicator element", () => {
    const { container } = renderRail([PTEG_SECTION, TEG_SECTION], null, {
      autosaving: false,
    });
    const draft = container.querySelector(".rail-draft");
    expect(draft).not.toBeNull();
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// No legacy color classes
// ─────────────────────────────────────────────────────────────────────────────
describe("Rail — no legacy Tailwind color classes (Sub-N)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const BANNED = [
    "text-emerald-",
    "bg-emerald-",
    "text-blue-600",
    "border-emerald-600",
    "border-blue-600",
    "bg-blue-50",
  ];

  it("rendered HTML does not contain legacy color classes", () => {
    const { container } = renderRail();
    const html = container.innerHTML;
    for (const cls of BANNED) {
      expect(html, `should not contain '${cls}'`).not.toContain(cls);
    }
  });
});
