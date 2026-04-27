import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import type { Question } from "@features/evaluations/lib/questions/questions";

// ── hook mocks ────────────────────────────────────────────────────────────────
vi.mock("../hooks/useEvaluationDraft", () => ({
  useEvaluationDraft: () => ({
    buildDefaults: () => ({}),
    saveDraft: vi.fn(),
    clearDraft: vi.fn(),
    loadDraft: () => ({}),
  }),
}));

vi.mock("../hooks/useScrollSpy", () => ({
  useScrollSpy: () => ({ activeId: null, scrollTo: vi.fn() }),
}));

vi.mock("../hooks/useEvaluationSubmit", () => ({
  useEvaluationSubmit: () => ({
    submit: vi.fn(),
  }),
}));

vi.mock("@shared/hooks/useValidation", () => ({
  useValidation: () => ({
    showBanner: vi.fn(),
    bannerProps: { visible: false },
  }),
}));

// ── service mock ──────────────────────────────────────────────────────────────
vi.mock("@features/projects/api/projectService", () => ({
  getProject: vi.fn().mockResolvedValue(null),
}));

// ── shared UI stubs ───────────────────────────────────────────────────────────
vi.mock("@shared/ui/Banner", () => ({
  default: () => <div data-testid="banner" />,
}));

vi.mock("@shared/ui/ImageTooltip", () => ({
  ImageTooltip: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

// ── sub-component stubs ───────────────────────────────────────────────────────
vi.mock("./EvaluationSidebar", () => ({
  default: () => <div data-testid="evaluation-sidebar" />,
}));

vi.mock("./Rail", () => ({
  default: () => <aside className="rail" data-testid="rail" />,
}));

vi.mock("./ResultsSummary", () => ({
  default: () => <div data-testid="results-summary" />,
}));

// ── component under test ──────────────────────────────────────────────────────
import EvaluationForm from "./EvaluationForm";

// ─────────────────────────────────────────────────────────────────────────────

const DIAGRAMACION_QUESTIONS: Question[] = [
  {
    id: "d1",
    label: "Pregunta Diagramación 1",
    section: "Diagramación",
    subsection: "Portada",
    answerType: "yesno",
    documentType: "Proyecto",
  },
  {
    id: "d2",
    label: "Pregunta Diagramación 2",
    section: "Diagramación",
    subsection: "Portada",
    answerType: "yesno",
    documentType: "Proyecto",
  },
  {
    id: "d3",
    label: "Pregunta Diagramación 3 con imagen",
    section: "Diagramación",
    subsection: "Índice",
    answerType: "yesno",
    documentType: "Proyecto",
    relatedImage: "https://example.com/img.png",
  },
];

const CONTENIDO_QUESTIONS: Question[] = [
  {
    id: "c1",
    label: "Pregunta Contenido 1",
    section: "Contenido",
    subsection: "Intro",
    answerType: "ternary",
    documentType: "Proyecto",
  },
  {
    id: "c2",
    label: "Pregunta Contenido 2",
    section: "Contenido",
    subsection: "Intro",
    answerType: "ternary",
    documentType: "Proyecto",
  },
];

const ALL_QUESTIONS = [...DIAGRAMACION_QUESTIONS, ...CONTENIDO_QUESTIONS];

const TEXT_QUESTION: Question = {
  id: "t1",
  label: "Observaciones generales",
  section: "Diagramación",
  subsection: "General",
  answerType: "text",
  documentType: "Proyecto",
};

function renderForm(questions = ALL_QUESTIONS, typeParam = "proyecto") {
  return render(
    <EvaluationForm
      projectId="42"
      typeParam={typeParam}
      questions={questions}
    />
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Hero section
// ─────────────────────────────────────────────────────────────────────────────
describe("EvaluationForm — hero section (Sub-N)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders an element with class ev-hero", () => {
    const { container } = renderForm();
    expect(container.querySelector(".ev-hero")).not.toBeNull();
  });

  it("renders an eyebrow pill containing 'Evaluación'", () => {
    renderForm();
    expect(screen.getByText(/Evaluación/)).toBeInTheDocument();
  });

  it("hero contains a Fraunces title (font-display class) element", () => {
    const { container } = renderForm();
    const hero = container.querySelector(".ev-hero");
    expect(hero).not.toBeNull();
    const fraunces = hero!.querySelector(".font-display");
    expect(fraunces).not.toBeNull();
  });

  it("renders 3-stat strip with Diagramación count chip", () => {
    renderForm();
    expect(screen.getByText(/Diagramaci/i, { selector: ".ev-hero-stat-l" })).toBeInTheDocument();
  });

  it("renders 3-stat strip with Contenido count chip", () => {
    renderForm();
    expect(screen.getByText(/Contenido/i, { selector: ".ev-hero-stat-l" })).toBeInTheDocument();
  });

  it("renders 3-stat strip with Respondidas count", () => {
    renderForm();
    expect(screen.getByText(/Respondidas/i)).toBeInTheDocument();
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// Single scroll — no pagination controls
// ─────────────────────────────────────────────────────────────────────────────
describe("EvaluationForm — single-scroll layout (no pagination)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("does NOT render an 'Anterior' button", () => {
    renderForm();
    expect(screen.queryByRole("button", { name: /^anterior$/i })).toBeNull();
  });

  it("does NOT render a 'Siguiente' button", () => {
    renderForm();
    expect(screen.queryByRole("button", { name: /^siguiente$/i })).toBeNull();
  });

  it("does NOT render 'página X de Y' or 'sección X de Y' text", () => {
    renderForm();
    expect(screen.queryByText(/sección \d+ de \d+/i)).toBeNull();
    expect(screen.queryByText(/página \d+ de \d+/i)).toBeNull();
  });

  it("does NOT render mobile section pills navigator (numbered page buttons)", () => {
    const { container } = renderForm();
    // Old pattern: numbered buttons [1] [2] for mobile navigation
    const pageButtons = container.querySelectorAll("button[class*='w-8'][class*='h-8']");
    expect(pageButtons.length).toBe(0);
  });

  it("all questions from both sections are visible in the DOM simultaneously", () => {
    renderForm();
    for (const q of ALL_QUESTIONS) {
      expect(screen.getByText(q.label)).toBeInTheDocument();
    }
  });

  it("comments textarea always renders (not gated by page === totalPages)", () => {
    renderForm();
    expect(screen.getByPlaceholderText(/Observaciones generales|observaciones/i)).toBeInTheDocument();
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// Ribbon headers
// ─────────────────────────────────────────────────────────────────────────────
describe("EvaluationForm — category ribbon headers (Sub-N)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders a .ribbon element for Diagramación section", () => {
    const { container } = renderForm();
    const ribbons = container.querySelectorAll(".ribbon");
    expect(ribbons.length).toBeGreaterThanOrEqual(1);
  });

  it("renders a .ribbon.is-teg element for Contenido section", () => {
    const { container } = renderForm();
    expect(container.querySelector(".ribbon.is-teg")).not.toBeNull();
  });

  it("Diagramación ribbon does NOT carry is-teg class", () => {
    const { container } = renderForm();
    const ribbons = Array.from(container.querySelectorAll(".ribbon"));
    const diagramacionRibbon = ribbons.find(
      (r) => r.textContent?.includes("Diagramaci") && !r.classList.contains("is-teg")
    );
    expect(diagramacionRibbon).not.toBeUndefined();
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// Question cards — Fraunces numerals
// ─────────────────────────────────────────────────────────────────────────────
describe("EvaluationForm — question card numerals (Sub-N)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders .qcard elements for each question", () => {
    const { container } = renderForm();
    const cards = container.querySelectorAll(".qcard");
    expect(cards.length).toBe(ALL_QUESTIONS.length);
  });

  it("first question card displays numeral '01'", () => {
    renderForm();
    expect(screen.getByText("01")).toBeInTheDocument();
  });

  it("second question card displays numeral '02'", () => {
    renderForm();
    expect(screen.getByText("02")).toBeInTheDocument();
  });

  it("question card numerals use .font-display Fraunces class", () => {
    const { container } = renderForm();
    const numerals = container.querySelectorAll(".qcard .font-display, .qcard-num");
    expect(numerals.length).toBeGreaterThan(0);
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// Status pills — no points text
// ─────────────────────────────────────────────────────────────────────────────
describe("EvaluationForm — status pills (no points)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("unanswered questions show 'Pendiente' status pill", () => {
    renderForm();
    const pills = screen.getAllByText(/^Pendiente$/i);
    expect(pills.length).toBeGreaterThan(0);
  });

  it("does NOT render any 'pt' substring in the DOM", () => {
    const { container } = renderForm();
    expect(container.innerHTML).not.toMatch(/\bpt\b/);
  });

  it("does NOT render '+1' substring in the DOM", () => {
    const { container } = renderForm();
    expect(container.innerHTML).not.toContain("+1");
  });

  it("does NOT render '0.5' substring in the DOM", () => {
    const { container } = renderForm();
    expect(container.innerHTML).not.toContain("0.5");
  });

  it("does NOT render 'puntos' substring in the DOM", () => {
    const { container } = renderForm();
    expect(container.innerHTML.toLowerCase()).not.toContain("puntos");
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// Sticky action bar — always-visible Enviar CTA
// ─────────────────────────────────────────────────────────────────────────────
describe("EvaluationForm — sticky action bar always-visible submit (Sub-N)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("always renders 'Enviar evaluación' button regardless of question count", () => {
    renderForm();
    expect(
      screen.getByRole("button", { name: /enviar evaluaci[oó]n/i })
    ).toBeInTheDocument();
  });

  it("action bar element has class 'actions'", () => {
    const { container } = renderForm();
    expect(container.querySelector(".actions")).not.toBeNull();
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// Validation — .err-banner with jump CTA
// ─────────────────────────────────────────────────────────────────────────────
describe("EvaluationForm — validation error banner (Sub-N)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("does NOT render .err-banner before submit is attempted", () => {
    const { container } = renderForm();
    expect(container.querySelector(".err-banner")).toBeNull();
  });

  it("clicking 'Enviar evaluación' with missing answers shows .err-banner", async () => {
    const { container } = renderForm();
    const submitBtn = screen.getByRole("button", { name: /enviar evaluaci[oó]n/i });
    fireEvent.click(submitBtn);
    await waitFor(() => {
      expect(container.querySelector(".err-banner")).not.toBeNull();
    });
  });

  it(".err-banner contains a 'Saltar a falta' jump button", async () => {
    renderForm();
    const submitBtn = screen.getByRole("button", { name: /enviar evaluaci[oó]n/i });
    fireEvent.click(submitBtn);
    await waitFor(() => {
      expect(screen.getByRole("button", { name: /saltar a falta/i })).toBeInTheDocument();
    });
  });

  it("clicking 'Saltar a falta' does not throw (scrollToQuestion is called)", async () => {
    renderForm();
    const submitBtn = screen.getByRole("button", { name: /enviar evaluaci[oó]n/i });
    fireEvent.click(submitBtn);
    await waitFor(() => {
      expect(screen.getByRole("button", { name: /saltar a falta/i })).toBeInTheDocument();
    });
    expect(() =>
      fireEvent.click(screen.getByRole("button", { name: /saltar a falta/i }))
    ).not.toThrow();
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// kind=defense — defensa oral 20-question set
// ─────────────────────────────────────────────────────────────────────────────
describe("EvaluationForm — kind=defense", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // Import the real questions array that will contain both review and defensa
  // entries after implementation. Before implementation, PTEG_DEFENSA_QUESTIONS
  // does not exist, so the import below will fail — that is the expected RED failure.
  it("renders exactly 20 questions when kind='defense' and typeParam='proyecto'", async () => {
    const { PTEG_DEFENSA_QUESTIONS } = await import(
      "@features/evaluations/lib/questions/questions"
    );
    const { default: EvaluationFormFresh } = await import("./EvaluationForm");
    const { container } = render(
      <EvaluationFormFresh
        projectId="99"
        typeParam="proyecto"
        kind="defense"
        questions={PTEG_DEFENSA_QUESTIONS}
      />
    );
    const cards = container.querySelectorAll(".qcard");
    expect(cards.length).toBe(20);
  });

  it("section headings include 'Criterios de Evaluación Técnica' when kind='defense'", async () => {
    const { PTEG_DEFENSA_QUESTIONS } = await import(
      "@features/evaluations/lib/questions/questions"
    );
    const { default: EvaluationFormFresh } = await import("./EvaluationForm");
    render(
      <EvaluationFormFresh
        projectId="99"
        typeParam="proyecto"
        kind="defense"
        questions={PTEG_DEFENSA_QUESTIONS}
      />
    );
    expect(screen.getByText(/Criterios de Evaluación Técnica/)).toBeInTheDocument();
  });

  it("section headings include 'Criterios de Evaluación Divulgativa' when kind='defense'", async () => {
    const { PTEG_DEFENSA_QUESTIONS } = await import(
      "@features/evaluations/lib/questions/questions"
    );
    const { default: EvaluationFormFresh } = await import("./EvaluationForm");
    render(
      <EvaluationFormFresh
        projectId="99"
        typeParam="proyecto"
        kind="defense"
        questions={PTEG_DEFENSA_QUESTIONS}
      />
    );
    expect(screen.getByText(/Criterios de Evaluación Divulgativa/)).toBeInTheDocument();
  });

  it("does NOT render review-only section 'Diagramación' when kind='defense'", async () => {
    const { PTEG_DEFENSA_QUESTIONS } = await import(
      "@features/evaluations/lib/questions/questions"
    );
    const { default: EvaluationFormFresh } = await import("./EvaluationForm");
    render(
      <EvaluationFormFresh
        projectId="99"
        typeParam="proyecto"
        kind="defense"
        questions={PTEG_DEFENSA_QUESTIONS}
      />
    );
    // Ribbon text for review-only sections must not appear
    const ribbons = document.querySelectorAll(".ribbon");
    const ribbonTexts = Array.from(ribbons).map((r) => r.textContent || "");
    expect(ribbonTexts.some((t) => t.includes("Diagramación"))).toBe(false);
  });

  it("does NOT render review-only section 'Contenido' when kind='defense'", async () => {
    const { PTEG_DEFENSA_QUESTIONS } = await import(
      "@features/evaluations/lib/questions/questions"
    );
    const { default: EvaluationFormFresh } = await import("./EvaluationForm");
    render(
      <EvaluationFormFresh
        projectId="99"
        typeParam="proyecto"
        kind="defense"
        questions={PTEG_DEFENSA_QUESTIONS}
      />
    );
    const ribbons = document.querySelectorAll(".ribbon");
    const ribbonTexts = Array.from(ribbons).map((r) => r.textContent || "");
    expect(ribbonTexts.some((t) => /^Contenido$/.test(t.trim()))).toBe(false);
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// No legacy Tailwind color classes
// ─────────────────────────────────────────────────────────────────────────────
describe("EvaluationForm — no legacy Tailwind color classes (Sub-N)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const BANNED = [
    "text-blue-600",
    "bg-emerald-50",
    "from-blue-500",
    "to-indigo-600",
    "bg-green-100",
    "bg-red-100",
    "bg-blue-50/60",
    "border-emerald-600",
    "border-blue-600",
  ];

  it("rendered HTML does not contain legacy color classes", () => {
    const { container } = renderForm();
    const html = container.innerHTML;
    for (const cls of BANNED) {
      expect(html, `should not contain '${cls}'`).not.toContain(cls);
    }
  });
});
