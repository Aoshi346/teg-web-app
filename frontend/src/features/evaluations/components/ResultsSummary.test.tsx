import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import type { Question } from "@features/evaluations/lib/questions/questions";

// ── next/navigation mock ──────────────────────────────────────────────────────
vi.mock("next/navigation", async () => {
  const actual = await vi.importActual<typeof import("next/navigation")>("next/navigation");
  return {
    ...actual,
    useRouter: () => ({
      push: vi.fn(),
      replace: vi.fn(),
      back: vi.fn(),
    }),
  };
});

// ── component under test ──────────────────────────────────────────────────────
import ResultsSummary from "./ResultsSummary";

// ─────────────────────────────────────────────────────────────────────────────

const QUESTIONS: Question[] = [
  {
    id: "d1",
    label: "¿Portada correcta?",
    section: "Diagramación",
    subsection: "Portada",
    answerType: "yesno",
    documentType: "Proyecto",
  },
  {
    id: "d2",
    label: "¿Índice completo?",
    section: "Diagramación",
    subsection: "Índice",
    answerType: "yesno",
    documentType: "Proyecto",
  },
  {
    id: "c1",
    label: "¿Objetivo claro?",
    section: "Contenido",
    subsection: "Introducción",
    answerType: "ternary",
    documentType: "Proyecto",
  },
];

const RATINGS: Record<string, number | string> = {
  d1: 2,
  d2: 1,
  c1: 3,
};

function renderSummary(
  overrides: Partial<React.ComponentProps<typeof ResultsSummary>> = {}
) {
  const defaults = {
    score: 15,
    passStatus: "Pass" as const,
    ratings: RATINGS,
    comments: "",
    questions: QUESTIONS,
    typeParam: "proyecto",
    onReset: vi.fn(),
  };
  return render(<ResultsSummary {...defaults} {...overrides} />);
}

// ─────────────────────────────────────────────────────────────────────────────
// .res-band C4 navy band
// ─────────────────────────────────────────────────────────────────────────────
describe("ResultsSummary — .res-band navy band (Sub-N)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders an element with class res-band", () => {
    const { container } = renderSummary();
    expect(container.querySelector(".res-band")).not.toBeNull();
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// .res-score conic-gradient widget
// ─────────────────────────────────────────────────────────────────────────────
describe("ResultsSummary — .res-score conic widget (Sub-N)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders an element with class res-score inside .res-band", () => {
    const { container } = renderSummary();
    const band = container.querySelector(".res-band");
    expect(band).not.toBeNull();
    expect(band!.querySelector(".res-score")).not.toBeNull();
  });

  it("res-score shows the score numeral '15' with Fraunces font-display class", () => {
    renderSummary({ score: 15 });
    expect(screen.getByText("15")).toBeInTheDocument();
  });

  it("res-score numeral element carries .font-display class", () => {
    const { container } = renderSummary({ score: 15 });
    const scoreEl = container.querySelector(".res-score .font-display, .res-score-num");
    expect(scoreEl).not.toBeNull();
    expect(scoreEl!.textContent).toContain("15");
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// Pass/fail pill
// ─────────────────────────────────────────────────────────────────────────────
describe("ResultsSummary — pass/fail pill (Sub-N)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders 'Aprobado' pill when passStatus=Pass", () => {
    renderSummary({ passStatus: "Pass" });
    expect(screen.getByText(/Aprobado/i)).toBeInTheDocument();
  });

  it("renders 'Reprobado' pill when passStatus=Fail", () => {
    renderSummary({ passStatus: "Fail" });
    expect(screen.getByText(/Reprobado/i)).toBeInTheDocument();
  });

  it("Aprobado pill carries success-soft class", () => {
    const { container } = renderSummary({ passStatus: "Pass" });
    const pill = container.querySelector(".success-soft, [class*='success-soft']");
    expect(pill).not.toBeNull();
  });

  it("Reprobado pill carries danger-soft class", () => {
    const { container } = renderSummary({ passStatus: "Fail" });
    const pill = container.querySelector(".danger-soft, [class*='danger-soft']");
    expect(pill).not.toBeNull();
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// Per-section answer review with category tints
// ─────────────────────────────────────────────────────────────────────────────
describe("ResultsSummary — per-section answer review (Sub-N)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders .res-body element with sectioned review", () => {
    const { container } = renderSummary();
    expect(container.querySelector(".res-body")).not.toBeNull();
  });

  it("renders Diagramación section in res-body", () => {
    renderSummary();
    expect(screen.getByText(/Diagramaci/i)).toBeInTheDocument();
  });

  it("renders Contenido section in res-body", () => {
    renderSummary();
    expect(screen.getByText(/Contenido/i)).toBeInTheDocument();
  });

  it("renders .res-q rows for each question", () => {
    const { container } = renderSummary();
    const rows = container.querySelectorAll(".res-q");
    expect(rows.length).toBe(QUESTIONS.length);
  });

  it("Diagramación section has pteg-soft tint class", () => {
    const { container } = renderSummary();
    const ptegSection = container.querySelector(
      ".pteg-soft, [class*='pteg-soft'], .res-sec.pteg, .res-sec-pteg"
    );
    expect(ptegSection).not.toBeNull();
  });

  it("Contenido section has teg-soft tint class", () => {
    const { container } = renderSummary();
    const tegSection = container.querySelector(
      ".teg-soft, [class*='teg-soft'], .res-sec.teg, .res-sec-teg"
    );
    expect(tegSection).not.toBeNull();
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// No points text shown anywhere
// ─────────────────────────────────────────────────────────────────────────────
describe("ResultsSummary — no points text (Sub-N)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("does NOT render 'pt' text in rendered HTML", () => {
    const { container } = renderSummary();
    expect(container.innerHTML).not.toMatch(/\bpt\b/);
  });

  it("does NOT render '+' operator followed by a number (point sum)", () => {
    const { container } = renderSummary();
    expect(container.innerHTML).not.toMatch(/\+\d/);
  });

  it("does NOT render 'puntos' text", () => {
    const { container } = renderSummary();
    expect(container.innerHTML.toLowerCase()).not.toContain("puntos");
  });

  it("does NOT render 'Puntaje X / Y' text (old scoring display)", () => {
    const { container } = renderSummary();
    expect(container.innerHTML).not.toMatch(/Puntaje\s*\d+\s*\/\s*\d+/);
  });

  it("does NOT render 'Mínimo:' text", () => {
    const { container } = renderSummary();
    expect(container.innerHTML).not.toContain("Mínimo:");
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// Comments callout
// ─────────────────────────────────────────────────────────────────────────────
describe("ResultsSummary — comments callout (Sub-N)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders comments callout in pending-soft when comments are present", () => {
    const { container } = renderSummary({
      comments: "El documento tiene buena estructura general.",
    });
    const callout = container.querySelector(
      ".pending-soft, [class*='pending-soft'], .comments-callout"
    );
    expect(callout).not.toBeNull();
    expect(callout!.textContent).toContain("El documento tiene buena estructura general.");
  });

  it("does NOT render comments callout when comments is empty", () => {
    const { container } = renderSummary({ comments: "" });
    const callout = container.querySelector(
      ".comments-callout, .pending-soft"
    );
    if (callout) {
      // If the element exists it must not contain comment text
      expect(callout.textContent?.trim().length).toBe(0);
    } else {
      expect(callout).toBeNull();
    }
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// 3-action footer
// ─────────────────────────────────────────────────────────────────────────────
describe("ResultsSummary — 3-action footer (Sub-N)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders a .res-actions footer element", () => {
    const { container } = renderSummary();
    expect(container.querySelector(".res-actions")).not.toBeNull();
  });

  it("renders 'Volver' primary action button", () => {
    renderSummary();
    expect(screen.getByRole("button", { name: /volver/i })).toBeInTheDocument();
  });

  it("renders 'Nueva evaluación' outline action button", () => {
    renderSummary();
    expect(screen.getByRole("button", { name: /nueva evaluaci[oó]n/i })).toBeInTheDocument();
  });

  it("renders 'Descargar PDF' ghost action button", () => {
    renderSummary();
    expect(screen.getByRole("button", { name: /descargar pdf/i })).toBeInTheDocument();
  });

  it("clicking 'Nueva evaluación' calls onReset", () => {
    const onReset = vi.fn();
    renderSummary({ onReset });
    fireEvent.click(screen.getByRole("button", { name: /nueva evaluaci[oó]n/i }));
    expect(onReset).toHaveBeenCalledTimes(1);
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// No legacy color classes
// ─────────────────────────────────────────────────────────────────────────────
describe("ResultsSummary — no legacy color classes (Sub-N)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const BANNED = [
    "bg-white p-6",
    "bg-green-100",
    "bg-red-100",
    "text-green-600",
    "text-red-600",
    "bg-gray-50",
  ];

  it("rendered HTML does not contain legacy color classes", () => {
    const { container } = renderSummary();
    const html = container.innerHTML;
    for (const cls of BANNED) {
      expect(html, `should not contain '${cls}'`).not.toContain(cls);
    }
  });
});
