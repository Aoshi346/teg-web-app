import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

// ── component under test ──────────────────────────────────────────────────────
import YesNoInput from "./YesNoInput";

// ─────────────────────────────────────────────────────────────────────────────

function renderInput(
  overrides: Partial<React.ComponentProps<typeof YesNoInput>> = {}
) {
  const defaults = {
    value: 0,
    onChange: vi.fn(),
    onAdvance: vi.fn(),
  };
  return render(<YesNoInput {...defaults} {...overrides} />);
}

// ─────────────────────────────────────────────────────────────────────────────
// CSS namespace
// ─────────────────────────────────────────────────────────────────────────────
describe("YesNoInput — CSS namespace (Sub-N)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders an element with class inp-seg", () => {
    const { container } = renderInput();
    expect(container.querySelector(".inp-seg")).not.toBeNull();
  });

  it("inp-seg also carries class v-yesno", () => {
    const { container } = renderInput();
    expect(container.querySelector(".inp-seg.v-yesno")).not.toBeNull();
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// Renders Sí and No buttons
// ─────────────────────────────────────────────────────────────────────────────
describe("YesNoInput — button rendering", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders a 'Sí' button", () => {
    renderInput();
    expect(screen.getByRole("button", { name: /^Sí$/i })).toBeInTheDocument();
  });

  it("renders a 'No' button", () => {
    renderInput();
    expect(screen.getByRole("button", { name: /^No$/i })).toBeInTheDocument();
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// Click behaviour
// ─────────────────────────────────────────────────────────────────────────────
describe("YesNoInput — click triggers onChange", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("clicking 'Sí' calls onChange with value 2", () => {
    const onChange = vi.fn();
    renderInput({ onChange });
    fireEvent.click(screen.getByRole("button", { name: /^Sí$/i }));
    expect(onChange).toHaveBeenCalledWith(2);
  });

  it("clicking 'No' calls onChange with value 1", () => {
    const onChange = vi.fn();
    renderInput({ onChange });
    fireEvent.click(screen.getByRole("button", { name: /^No$/i }));
    expect(onChange).toHaveBeenCalledWith(1);
  });

  it("clicking 'Sí' calls onAdvance", () => {
    const onAdvance = vi.fn();
    renderInput({ onAdvance });
    fireEvent.click(screen.getByRole("button", { name: /^Sí$/i }));
    expect(onAdvance).toHaveBeenCalledTimes(1);
  });

  it("clicking 'No' calls onAdvance", () => {
    const onAdvance = vi.fn();
    renderInput({ onAdvance });
    fireEvent.click(screen.getByRole("button", { name: /^No$/i }));
    expect(onAdvance).toHaveBeenCalledTimes(1);
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// Active state visual classes
// ─────────────────────────────────────────────────────────────────────────────
describe("YesNoInput — active state classes (Sub-N)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("active 'Sí' button has success-bg class", () => {
    const { container } = renderInput({ value: 2 });
    const siBtn = screen.getByRole("button", { name: /^Sí$/i });
    // The active Sí should have some success styling (class containing 'success')
    const hasSuccess =
      siBtn.className.includes("success") ||
      siBtn.className.includes("--success") ||
      siBtn.getAttribute("data-active") === "true" ||
      siBtn.classList.contains("active");
    expect(hasSuccess).toBe(true);
  });

  it("active 'No' button has danger-bg class", () => {
    const { container } = renderInput({ value: 1 });
    const noBtn = screen.getByRole("button", { name: /^No$/i });
    const hasDanger =
      noBtn.className.includes("danger") ||
      noBtn.className.includes("--danger") ||
      noBtn.getAttribute("data-active") === "true" ||
      noBtn.classList.contains("active");
    expect(hasDanger).toBe(true);
    void container; // suppress unused var
  });

  it("inactive 'Sí' button does not carry active styling when No is selected", () => {
    renderInput({ value: 1 });
    const siBtn = screen.getByRole("button", { name: /^Sí$/i });
    expect(siBtn.className.includes("success")).toBe(false);
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// No points text
// ─────────────────────────────────────────────────────────────────────────────
describe("YesNoInput — no points text (Sub-N)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("does NOT render 'pt' substring in the component HTML", () => {
    const { container } = renderInput({ value: 2 });
    expect(container.innerHTML).not.toMatch(/\bpt\b/);
  });

  it("does NOT render '+1' text", () => {
    const { container } = renderInput({ value: 2 });
    expect(container.innerHTML).not.toContain("+1");
  });

  it("does NOT render 'puntos' text", () => {
    const { container } = renderInput({ value: 2 });
    expect(container.innerHTML.toLowerCase()).not.toContain("puntos");
  });
});
