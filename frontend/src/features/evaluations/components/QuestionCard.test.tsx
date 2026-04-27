import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import type { Question } from "@features/evaluations/lib/questions/questions";

// ── shared UI stub ────────────────────────────────────────────────────────────
vi.mock("@shared/ui/ImageTooltip", () => ({
  ImageTooltip: ({
    children,
    imageUrl,
    title,
  }: {
    children: React.ReactNode;
    imageUrl?: string;
    title?: string;
  }) => (
    <span data-testid="image-tooltip" data-image-url={imageUrl} data-title={title}>
      {children}
    </span>
  ),
}));

// ── input stubs ───────────────────────────────────────────────────────────────
vi.mock("./inputs", () => ({
  YesNoInput: ({ onChange, onAdvance }: { onChange: (v: number) => void; onAdvance?: () => void }) => (
    <div data-testid="yesno-input">
      <button type="button" onClick={() => { onChange(2); onAdvance?.(); }}>
        Sí
      </button>
      <button type="button" onClick={() => { onChange(1); onAdvance?.(); }}>
        No
      </button>
    </div>
  ),
  FrequencyInput: ({ onChange, onAdvance }: { onChange: (v: number) => void; onAdvance?: () => void }) => (
    <div data-testid="frequency-input">
      <button type="button" onClick={() => { onChange(3); onAdvance?.(); }}>Sí/Siempre</button>
    </div>
  ),
  TernaryInput: ({ onChange, onAdvance }: { onChange: (v: number) => void; onAdvance?: () => void }) => (
    <div data-testid="ternary-input">
      <button type="button" onClick={() => { onChange(3); onAdvance?.(); }}>Sí</button>
    </div>
  ),
  StarRatingInput: ({ onChange, onAdvance }: { onChange: (v: number) => void; onAdvance?: () => void }) => (
    <div data-testid="star-input">
      <button type="button" aria-label="Puntuación 4" onClick={() => { onChange(4); onAdvance?.(); }}>4</button>
    </div>
  ),
  FreeTextInput: ({ onChange }: { onChange: (v: string) => void }) => (
    <textarea data-testid="free-text-input" onChange={(e) => onChange(e.target.value)} />
  ),
}));

// ── component under test ──────────────────────────────────────────────────────
import QuestionCard from "./QuestionCard";

// ─────────────────────────────────────────────────────────────────────────────

const makeQuestion = (overrides: Partial<Question> = {}): Question => ({
  id: "q01",
  label: "¿El documento tiene portada?",
  section: "Diagramación",
  subsection: "Portada",
  answerType: "yesno",
  documentType: "Proyecto",
  ...overrides,
});

function renderCard(
  props: Partial<{
    question: Question;
    value: number | string;
    onChange: (v: number | string) => void;
    onAdvance: () => void;
    hasError: boolean;
    isFocused: boolean;
    numeral: string;
  }> = {}
) {
  const defaults = {
    question: makeQuestion(),
    value: 0 as number | string,
    onChange: vi.fn(),
    onAdvance: vi.fn(),
    hasError: false,
    isFocused: false,
    numeral: "01",
  };
  return render(<QuestionCard {...defaults} {...props} />);
}

// ─────────────────────────────────────────────────────────────────────────────
// Root element and namespace
// ─────────────────────────────────────────────────────────────────────────────
describe("QuestionCard — root element (Sub-N)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders an element with class qcard", () => {
    const { container } = renderCard();
    expect(container.querySelector(".qcard")).not.toBeNull();
  });

  it("qcard has an id of qt-{question.id}", () => {
    const { container } = renderCard();
    expect(container.querySelector("#qt-q01")).not.toBeNull();
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// Fraunces numeral
// ─────────────────────────────────────────────────────────────────────────────
describe("QuestionCard — Fraunces numeral (Sub-N)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the numeral prop value '01'", () => {
    renderCard({ numeral: "01" });
    expect(screen.getByText("01")).toBeInTheDocument();
  });

  it("renders numeral '07' when passed as prop", () => {
    renderCard({ numeral: "07" });
    expect(screen.getByText("07")).toBeInTheDocument();
  });

  it("numeral element carries .font-display or .qcard-num class for Fraunces font", () => {
    const { container } = renderCard({ numeral: "01" });
    const numEl = container.querySelector(".font-display, .qcard-num");
    expect(numEl).not.toBeNull();
    expect(numEl!.textContent).toContain("01");
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// Idle state
// ─────────────────────────────────────────────────────────────────────────────
describe("QuestionCard — idle state (value=0)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("idle card does not have done class", () => {
    const { container } = renderCard({ value: 0 });
    expect(container.querySelector(".qcard.done")).toBeNull();
  });

  it("idle card does not have error class", () => {
    const { container } = renderCard({ value: 0, hasError: false });
    expect(container.querySelector(".qcard.error")).toBeNull();
  });

  it("renders status pill 'Pendiente' when unanswered", () => {
    renderCard({ value: 0 });
    expect(screen.getByText(/^Pendiente$/i)).toBeInTheDocument();
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// Done state
// ─────────────────────────────────────────────────────────────────────────────
describe("QuestionCard — done state (value > 0)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("answered card has class qcard done", () => {
    const { container } = renderCard({ value: 2 });
    expect(container.querySelector(".qcard.done")).not.toBeNull();
  });

  it("renders status pill 'Respondida' when answered", () => {
    renderCard({ value: 2 });
    expect(screen.getByText(/^Respondida$/i)).toBeInTheDocument();
  });

  it("done card does not show 'Pendiente' pill", () => {
    renderCard({ value: 2 });
    expect(screen.queryByText(/^Pendiente$/i)).toBeNull();
  });

  it("done card does not show 'Falta' pill", () => {
    renderCard({ value: 2 });
    expect(screen.queryByText(/^Falta$/i)).toBeNull();
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// Error state
// ─────────────────────────────────────────────────────────────────────────────
describe("QuestionCard — error state (hasError=true)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("card with hasError=true has class qcard error", () => {
    const { container } = renderCard({ value: 0, hasError: true });
    expect(container.querySelector(".qcard.error")).not.toBeNull();
  });

  it("renders status pill 'Falta' when hasError=true", () => {
    renderCard({ value: 0, hasError: true });
    expect(screen.getByText(/^Falta$/i)).toBeInTheDocument();
  });

  it("error card does not show 'Pendiente' pill", () => {
    renderCard({ value: 0, hasError: true });
    expect(screen.queryByText(/^Pendiente$/i)).toBeNull();
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// Helper text
// ─────────────────────────────────────────────────────────────────────────────
describe("QuestionCard — helper text", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders helper text when question.helper is set", () => {
    const q = makeQuestion({ helper: "Verifique márgenes de 2.5 cm." });
    renderCard({ question: q });
    expect(screen.getByText("Verifique márgenes de 2.5 cm.")).toBeInTheDocument();
  });

  it("does NOT render helper paragraph when question.helper is absent", () => {
    const q = makeQuestion({ helper: undefined });
    renderCard({ question: q });
    expect(screen.queryByText(/márgenes/i)).toBeNull();
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// Image badge
// ─────────────────────────────────────────────────────────────────────────────
describe("QuestionCard — image badge (.qcard-img-badge)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders .qcard-img-badge when question.relatedImage is set", () => {
    const q = makeQuestion({ relatedImage: "https://example.com/img.png" });
    const { container } = renderCard({ question: q });
    expect(container.querySelector(".qcard-img-badge")).not.toBeNull();
  });

  it("does NOT render .qcard-img-badge when question.relatedImage is absent", () => {
    const q = makeQuestion({ relatedImage: undefined });
    const { container } = renderCard({ question: q });
    expect(container.querySelector(".qcard-img-badge")).toBeNull();
  });

  it("image badge wraps or triggers ImageTooltip component", () => {
    const q = makeQuestion({ relatedImage: "https://example.com/img.png" });
    renderCard({ question: q });
    expect(screen.getByTestId("image-tooltip")).toBeInTheDocument();
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// No points text
// ─────────────────────────────────────────────────────────────────────────────
describe("QuestionCard — no points text", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("does NOT render 'pt' substring in rendered HTML", () => {
    const { container } = renderCard({ value: 2 });
    expect(container.innerHTML).not.toMatch(/\bpt\b/);
  });

  it("does NOT render '+1' text", () => {
    const { container } = renderCard({ value: 2 });
    expect(container.innerHTML).not.toContain("+1");
  });

  it("does NOT render 'puntos' text", () => {
    const { container } = renderCard({ value: 2 });
    expect(container.innerHTML.toLowerCase()).not.toContain("puntos");
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// Question label rendered
// ─────────────────────────────────────────────────────────────────────────────
describe("QuestionCard — question label", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the question label text", () => {
    const q = makeQuestion({ label: "¿La portada incluye el título completo?" });
    renderCard({ question: q });
    expect(screen.getByText("¿La portada incluye el título completo?")).toBeInTheDocument();
  });
});
