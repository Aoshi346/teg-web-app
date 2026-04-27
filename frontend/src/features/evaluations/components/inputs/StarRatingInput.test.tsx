import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

// ── component under test ──────────────────────────────────────────────────────
import StarRatingInput from "./StarRatingInput";

// ─────────────────────────────────────────────────────────────────────────────

function renderInput(
  overrides: Partial<React.ComponentProps<typeof StarRatingInput>> = {}
) {
  const defaults = {
    value: 0,
    onChange: vi.fn(),
    onAdvance: vi.fn(),
  };
  return render(<StarRatingInput {...defaults} {...overrides} />);
}

// ─────────────────────────────────────────────────────────────────────────────
// CSS namespace
// ─────────────────────────────────────────────────────────────────────────────
describe("StarRatingInput — CSS namespace (Sub-N)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders an element with class inp-stars", () => {
    const { container } = renderInput();
    expect(container.querySelector(".inp-stars")).not.toBeNull();
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// Buttons
// ─────────────────────────────────────────────────────────────────────────────
describe("StarRatingInput — button rendering", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders 5 rating buttons", () => {
    renderInput();
    const buttons = screen.getAllByRole("button");
    expect(buttons.length).toBe(5);
  });

  it("renders a button with aria-label 'Puntuación 1'", () => {
    renderInput();
    expect(screen.getByRole("button", { name: /Puntuaci[oó]n 1/i })).toBeInTheDocument();
  });

  it("renders a button with aria-label 'Puntuación 5'", () => {
    renderInput();
    expect(screen.getByRole("button", { name: /Puntuaci[oó]n 5/i })).toBeInTheDocument();
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// Click behaviour
// ─────────────────────────────────────────────────────────────────────────────
describe("StarRatingInput — click triggers onChange", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("clicking star 4 calls onChange with value 4", () => {
    const onChange = vi.fn();
    renderInput({ onChange });
    fireEvent.click(screen.getByRole("button", { name: /Puntuaci[oó]n 4/i }));
    expect(onChange).toHaveBeenCalledWith(4);
  });

  it("clicking star 1 calls onChange with value 1", () => {
    const onChange = vi.fn();
    renderInput({ onChange });
    fireEvent.click(screen.getByRole("button", { name: /Puntuaci[oó]n 1/i }));
    expect(onChange).toHaveBeenCalledWith(1);
  });

  it("clicking any star calls onAdvance", () => {
    const onAdvance = vi.fn();
    renderInput({ onAdvance });
    fireEvent.click(screen.getByRole("button", { name: /Puntuaci[oó]n 3/i }));
    expect(onAdvance).toHaveBeenCalledTimes(1);
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// Active state — brand-yellow
// ─────────────────────────────────────────────────────────────────────────────
describe("StarRatingInput — active state brand-yellow (Sub-N)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("active star button carries brand-yellow class or 'active' marker", () => {
    renderInput({ value: 4 });
    const btn4 = screen.getByRole("button", { name: /Puntuaci[oó]n 4/i });
    const isActive =
      btn4.classList.contains("active") ||
      btn4.className.includes("yellow") ||
      btn4.className.includes("brand") ||
      btn4.getAttribute("aria-pressed") === "true";
    expect(isActive).toBe(true);
  });

  it("non-selected star button does not carry active styling", () => {
    renderInput({ value: 4 });
    const btn1 = screen.getByRole("button", { name: /Puntuaci[oó]n 1/i });
    const isActive =
      btn1.classList.contains("active") ||
      btn1.getAttribute("aria-pressed") === "true";
    expect(isActive).toBe(false);
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// No points text
// ─────────────────────────────────────────────────────────────────────────────
describe("StarRatingInput — no points text (Sub-N)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("does NOT render 'Puntuación: X/5' text (old display)", () => {
    const { container } = renderInput({ value: 4 });
    expect(container.innerHTML).not.toMatch(/Puntuaci[oó]n:\s*\d+\/5/);
  });

  it("does NOT render 'puntos' text", () => {
    const { container } = renderInput({ value: 4 });
    expect(container.innerHTML.toLowerCase()).not.toContain("puntos");
  });

  it("does NOT render 'pt' standalone text", () => {
    const { container } = renderInput({ value: 4 });
    expect(container.innerHTML).not.toMatch(/\bpt\b/);
  });
});
