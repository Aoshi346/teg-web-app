import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

// ── component under test ──────────────────────────────────────────────────────
import FreeTextInput from "./FreeTextInput";

// ─────────────────────────────────────────────────────────────────────────────

function renderInput(
  overrides: Partial<React.ComponentProps<typeof FreeTextInput>> = {}
) {
  const defaults = {
    value: "",
    onChange: vi.fn(),
  };
  return render(<FreeTextInput {...defaults} {...overrides} />);
}

// ─────────────────────────────────────────────────────────────────────────────
// CSS namespace
// ─────────────────────────────────────────────────────────────────────────────
describe("FreeTextInput — CSS namespace (Sub-N)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders an element with class inp-text", () => {
    const { container } = renderInput();
    expect(container.querySelector(".inp-text")).not.toBeNull();
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// Textarea rendering
// ─────────────────────────────────────────────────────────────────────────────
describe("FreeTextInput — textarea rendering", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders a textarea element", () => {
    renderInput();
    expect(screen.getByRole("textbox")).toBeInTheDocument();
  });

  it("textarea renders with initial value", () => {
    renderInput({ value: "Observación inicial" });
    const ta = screen.getByRole("textbox") as HTMLTextAreaElement;
    expect(ta.value).toBe("Observación inicial");
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// Change behaviour
// ─────────────────────────────────────────────────────────────────────────────
describe("FreeTextInput — change triggers onChange", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("typing in textarea calls onChange with the new string value", () => {
    const onChange = vi.fn();
    renderInput({ onChange });
    const ta = screen.getByRole("textbox");
    fireEvent.change(ta, { target: { value: "Nuevo texto" } });
    expect(onChange).toHaveBeenCalledWith("Nuevo texto");
  });

  it("onChange is called with empty string when field is cleared", () => {
    const onChange = vi.fn();
    renderInput({ value: "texto", onChange });
    const ta = screen.getByRole("textbox");
    fireEvent.change(ta, { target: { value: "" } });
    expect(onChange).toHaveBeenCalledWith("");
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// No points text
// ─────────────────────────────────────────────────────────────────────────────
describe("FreeTextInput — no points text (Sub-N)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("does NOT render 'puntaje numérico' or 'no afecta' scoring copy", () => {
    const { container } = renderInput();
    expect(container.innerHTML.toLowerCase()).not.toContain("puntaje");
  });

  it("does NOT render 'pt' standalone text", () => {
    const { container } = renderInput({ value: "texto" });
    expect(container.innerHTML).not.toMatch(/\bpt\b/);
  });

  it("does NOT render 'puntos' text", () => {
    const { container } = renderInput({ value: "texto" });
    expect(container.innerHTML.toLowerCase()).not.toContain("puntos");
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// No legacy color classes
// ─────────────────────────────────────────────────────────────────────────────
describe("FreeTextInput — no legacy color classes (Sub-N)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const BANNED = [
    "focus:ring-blue-500",
    "focus:border-blue-500",
    "border-gray-200",
    "placeholder:text-gray-400",
  ];

  it("rendered HTML does not contain legacy Tailwind classes", () => {
    const { container } = renderInput();
    const html = container.innerHTML;
    for (const cls of BANNED) {
      expect(html, `should not contain '${cls}'`).not.toContain(cls);
    }
  });
});
