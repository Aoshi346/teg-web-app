import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

// ── component under test ──────────────────────────────────────────────────────
import StickyActionBar from "./StickyActionBar";

// ─────────────────────────────────────────────────────────────────────────────

function renderBar(
  overrides: Partial<React.ComponentProps<typeof StickyActionBar>> = {}
) {
  const defaults = {
    answeredCount: 5,
    totalRequired: 20,
    isSubmitting: false,
    onSubmit: vi.fn(),
    onCancel: vi.fn(),
    onClearDraft: vi.fn(),
    onJumpToMissing: vi.fn(),
    errorMode: false,
  };
  return render(<StickyActionBar {...defaults} {...overrides} />);
}

// ─────────────────────────────────────────────────────────────────────────────
// No pagination buttons
// ─────────────────────────────────────────────────────────────────────────────
describe("StickyActionBar — no pagination buttons (Sub-N)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("does NOT render an 'Anterior' button", () => {
    renderBar();
    expect(screen.queryByRole("button", { name: /^anterior$/i })).toBeNull();
  });

  it("does NOT render a 'Siguiente' button", () => {
    renderBar();
    expect(screen.queryByRole("button", { name: /^siguiente$/i })).toBeNull();
  });

  it("does NOT render 'page X de Y' or 'sección X de Y' text", () => {
    renderBar();
    expect(screen.queryByText(/sección \d+ de \d+/i)).toBeNull();
    expect(screen.queryByText(/página \d+ de \d+/i)).toBeNull();
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// Always-visible Enviar CTA
// ─────────────────────────────────────────────────────────────────────────────
describe("StickyActionBar — always-visible Enviar CTA (Sub-N)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders 'Enviar evaluación' CTA button in normal mode", () => {
    renderBar({ errorMode: false });
    expect(
      screen.getByRole("button", { name: /enviar evaluaci[oó]n/i })
    ).toBeInTheDocument();
  });

  it("clicking 'Enviar evaluación' calls onSubmit", () => {
    const onSubmit = vi.fn();
    renderBar({ onSubmit, errorMode: false });
    fireEvent.click(screen.getByRole("button", { name: /enviar evaluaci[oó]n/i }));
    expect(onSubmit).toHaveBeenCalledTimes(1);
  });

  it("'Enviar evaluación' button is disabled while isSubmitting=true", () => {
    renderBar({ isSubmitting: true });
    const btn = screen.getByRole("button", { name: /enviando|enviar evaluaci/i });
    expect(btn).toBeDisabled();
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// Brand-gradient progress bar + Fraunces fraction
// ─────────────────────────────────────────────────────────────────────────────
describe("StickyActionBar — progress display (Sub-N)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the action bar root with class 'actions'", () => {
    const { container } = renderBar();
    expect(container.querySelector(".actions")).not.toBeNull();
  });

  it("renders a progress fraction element showing answered/total", () => {
    renderBar({ answeredCount: 5, totalRequired: 20 });
    // Fraction can be in various forms: "5/20" or "5" and "20" separately
    const html = document.body.innerHTML;
    expect(html).toMatch(/5.*20|5\/20/);
  });

  it("fraction element uses .font-display class for Fraunces typography", () => {
    const { container } = renderBar();
    const fraunces = container.querySelector(".actions .font-display");
    expect(fraunces).not.toBeNull();
  });

  it("renders a progress bar element", () => {
    const { container } = renderBar();
    // Accepts any element that serves as the progress bar
    const bar = container.querySelector(
      ".actions-progress, .progress-bar, [class*='progress']"
    );
    expect(bar).not.toBeNull();
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// Error mode — danger CTA swaps to "Saltar a falta"
// ─────────────────────────────────────────────────────────────────────────────
describe("StickyActionBar — error mode (Sub-N)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("when errorMode=true, renders 'Saltar a falta' button instead of 'Enviar'", () => {
    renderBar({ errorMode: true });
    expect(
      screen.getByRole("button", { name: /saltar a falta/i })
    ).toBeInTheDocument();
  });

  it("when errorMode=true, 'Enviar evaluación' button is NOT visible", () => {
    renderBar({ errorMode: true });
    expect(
      screen.queryByRole("button", { name: /^enviar evaluaci[oó]n$/i })
    ).toBeNull();
  });

  it("clicking 'Saltar a falta' calls onJumpToMissing", () => {
    const onJumpToMissing = vi.fn();
    renderBar({ errorMode: true, onJumpToMissing });
    fireEvent.click(screen.getByRole("button", { name: /saltar a falta/i }));
    expect(onJumpToMissing).toHaveBeenCalledTimes(1);
  });

  it("when errorMode=false, 'Saltar a falta' button is NOT rendered", () => {
    renderBar({ errorMode: false });
    expect(
      screen.queryByRole("button", { name: /saltar a falta/i })
    ).toBeNull();
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// No legacy color classes
// ─────────────────────────────────────────────────────────────────────────────
describe("StickyActionBar — no legacy color classes (Sub-N)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const BANNED = [
    "from-blue-500",
    "to-indigo-600",
    "bg-green-600",
    "bg-gradient-to-r",
    "border-gray-200",
  ];

  it("rendered HTML does not contain legacy Tailwind gradient/color classes", () => {
    const { container } = renderBar();
    const html = container.innerHTML;
    for (const cls of BANNED) {
      expect(html, `should not contain '${cls}'`).not.toContain(cls);
    }
  });
});
