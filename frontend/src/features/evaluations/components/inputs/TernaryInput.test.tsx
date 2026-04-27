import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

// ── component under test ──────────────────────────────────────────────────────
import TernaryInput from "./TernaryInput";

// ─────────────────────────────────────────────────────────────────────────────

function renderInput(
  overrides: Partial<React.ComponentProps<typeof TernaryInput>> = {}
) {
  const defaults = {
    value: 0,
    onChange: vi.fn(),
    variant: "ternary" as const,
    onAdvance: vi.fn(),
  };
  return render(<TernaryInput {...defaults} {...overrides} />);
}

// ─────────────────────────────────────────────────────────────────────────────
// CSS namespace
// ─────────────────────────────────────────────────────────────────────────────
describe("TernaryInput — CSS namespace (Sub-N)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders an element with class inp-seg", () => {
    const { container } = renderInput();
    expect(container.querySelector(".inp-seg")).not.toBeNull();
  });

  it("inp-seg does NOT carry v-yesno modifier", () => {
    const { container } = renderInput();
    expect(container.querySelector(".inp-seg.v-yesno")).toBeNull();
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// Ternary variant options
// ─────────────────────────────────────────────────────────────────────────────
describe("TernaryInput — ternary variant renders 3 options", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders 'No' option", () => {
    renderInput({ variant: "ternary" });
    expect(screen.getByRole("button", { name: /^No$/i })).toBeInTheDocument();
  });

  it("renders 'Medianamente' option", () => {
    renderInput({ variant: "ternary" });
    expect(screen.getByRole("button", { name: /^Medianamente$/i })).toBeInTheDocument();
  });

  it("renders 'Sí' option", () => {
    renderInput({ variant: "ternary" });
    expect(screen.getByRole("button", { name: /^Sí$/i })).toBeInTheDocument();
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// Click behaviour
// ─────────────────────────────────────────────────────────────────────────────
describe("TernaryInput — click triggers onChange", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("clicking 'Sí' calls onChange with value 3", () => {
    const onChange = vi.fn();
    renderInput({ onChange });
    fireEvent.click(screen.getByRole("button", { name: /^Sí$/i }));
    expect(onChange).toHaveBeenCalledWith(3);
  });

  it("clicking 'No' calls onChange with value 1", () => {
    const onChange = vi.fn();
    renderInput({ onChange });
    fireEvent.click(screen.getByRole("button", { name: /^No$/i }));
    expect(onChange).toHaveBeenCalledWith(1);
  });

  it("clicking 'Medianamente' calls onChange with value 2", () => {
    const onChange = vi.fn();
    renderInput({ onChange });
    fireEvent.click(screen.getByRole("button", { name: /^Medianamente$/i }));
    expect(onChange).toHaveBeenCalledWith(2);
  });

  it("clicking any option calls onAdvance", () => {
    const onAdvance = vi.fn();
    renderInput({ onAdvance });
    fireEvent.click(screen.getByRole("button", { name: /^Sí$/i }));
    expect(onAdvance).toHaveBeenCalledTimes(1);
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// No points text
// ─────────────────────────────────────────────────────────────────────────────
describe("TernaryInput — no points text (Sub-N)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("does NOT render 'pt' in the component HTML", () => {
    const { container } = renderInput({ value: 3 });
    expect(container.innerHTML).not.toMatch(/\bpt\b/);
  });

  it("does NOT render '+' followed by digits", () => {
    const { container } = renderInput({ value: 3 });
    expect(container.innerHTML).not.toMatch(/\+\d/);
  });

  it("does NOT render '0.5' text", () => {
    const { container } = renderInput({ value: 3 });
    expect(container.innerHTML).not.toContain("0.5");
  });

  it("does NOT render 'puntos' text", () => {
    const { container } = renderInput({ value: 3 });
    expect(container.innerHTML.toLowerCase()).not.toContain("puntos");
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// ternary_na variant
// ─────────────────────────────────────────────────────────────────────────────
describe("TernaryInput — ternary_na variant", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders 'No se incluyó información' option for ternary_na", () => {
    renderInput({ variant: "ternary_na" });
    expect(screen.getByRole("button", { name: /No se incluyó/i })).toBeInTheDocument();
  });
});
