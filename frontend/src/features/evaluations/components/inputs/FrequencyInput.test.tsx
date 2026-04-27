import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

// ── component under test ──────────────────────────────────────────────────────
import FrequencyInput from "./FrequencyInput";

// ─────────────────────────────────────────────────────────────────────────────

function renderInput(
  overrides: Partial<React.ComponentProps<typeof FrequencyInput>> = {}
) {
  const defaults = {
    value: 0,
    onChange: vi.fn(),
    onAdvance: vi.fn(),
  };
  return render(<FrequencyInput {...defaults} {...overrides} />);
}

// ─────────────────────────────────────────────────────────────────────────────
// CSS namespace
// ─────────────────────────────────────────────────────────────────────────────
describe("FrequencyInput — CSS namespace (Sub-N)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders an element with class inp-seg", () => {
    const { container } = renderInput();
    expect(container.querySelector(".inp-seg")).not.toBeNull();
  });

  it("inp-seg does NOT have v-yesno modifier (only YesNo uses that)", () => {
    const { container } = renderInput();
    expect(container.querySelector(".inp-seg.v-yesno")).toBeNull();
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// Buttons rendering
// ─────────────────────────────────────────────────────────────────────────────
describe("FrequencyInput — button rendering", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders 'Muy Poco/Nunca' option", () => {
    renderInput();
    expect(screen.getByRole("button", { name: /Muy Poco/i })).toBeInTheDocument();
  });

  it("renders 'Sí/Siempre' option", () => {
    renderInput();
    expect(screen.getByRole("button", { name: /Sí\/Siempre/i })).toBeInTheDocument();
  });

  it("renders 'No aplica' option", () => {
    renderInput();
    expect(screen.getByRole("button", { name: /No aplica/i })).toBeInTheDocument();
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// Click behaviour
// ─────────────────────────────────────────────────────────────────────────────
describe("FrequencyInput — click triggers onChange", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("clicking 'Sí/Siempre' calls onChange with value 3", () => {
    const onChange = vi.fn();
    renderInput({ onChange });
    fireEvent.click(screen.getByRole("button", { name: /Sí\/Siempre/i }));
    expect(onChange).toHaveBeenCalledWith(3);
  });

  it("clicking 'Muy Poco/Nunca' calls onChange with value 1", () => {
    const onChange = vi.fn();
    renderInput({ onChange });
    fireEvent.click(screen.getByRole("button", { name: /Muy Poco/i }));
    expect(onChange).toHaveBeenCalledWith(1);
  });

  it("clicking any option calls onAdvance", () => {
    const onAdvance = vi.fn();
    renderInput({ onAdvance });
    fireEvent.click(screen.getByRole("button", { name: /Sí\/Siempre/i }));
    expect(onAdvance).toHaveBeenCalledTimes(1);
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// Active state
// ─────────────────────────────────────────────────────────────────────────────
describe("FrequencyInput — active state (Sub-N)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("selected option button carries 'active' class or brand-blue styling", () => {
    renderInput({ value: 3 });
    const siBtn = screen.getByRole("button", { name: /Sí\/Siempre/i });
    const isActive =
      siBtn.classList.contains("active") ||
      siBtn.className.includes("brand") ||
      siBtn.className.includes("blue") ||
      siBtn.getAttribute("aria-pressed") === "true";
    expect(isActive).toBe(true);
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// No points text
// ─────────────────────────────────────────────────────────────────────────────
describe("FrequencyInput — no points text (Sub-N)", () => {
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

  it("does NOT render 'puntos' text", () => {
    const { container } = renderInput({ value: 3 });
    expect(container.innerHTML.toLowerCase()).not.toContain("puntos");
  });
});
