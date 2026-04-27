import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

import TernaryDefenseInput from "../TernaryDefenseInput";

function renderInput(
  overrides: Partial<React.ComponentProps<typeof TernaryDefenseInput>> = {}
) {
  const defaults = {
    value: 0,
    onChange: vi.fn(),
  };
  return render(<TernaryDefenseInput {...defaults} {...overrides} />);
}

describe("TernaryDefenseInput — three buttons rendered in DOM order", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders a 'Deficiente' button", () => {
    renderInput();
    expect(screen.getByRole("button", { name: /^Deficiente$/i })).toBeInTheDocument();
  });

  it("renders a 'Satisfactorio' button", () => {
    renderInput();
    expect(screen.getByRole("button", { name: /^Satisfactorio$/i })).toBeInTheDocument();
  });

  it("renders an 'Excelente' button", () => {
    renderInput();
    expect(screen.getByRole("button", { name: /^Excelente$/i })).toBeInTheDocument();
  });

  it("buttons appear in Deficiente → Satisfactorio → Excelente DOM order", () => {
    const { container } = renderInput();
    const buttons = Array.from(container.querySelectorAll("button"));
    const labels = buttons.map((b) => b.textContent?.trim());
    const defIdx = labels.indexOf("Deficiente");
    const satIdx = labels.indexOf("Satisfactorio");
    const excIdx = labels.indexOf("Excelente");
    expect(defIdx).toBeLessThan(satIdx);
    expect(satIdx).toBeLessThan(excIdx);
  });
});

describe("TernaryDefenseInput — click calls onChange with correct values", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("clicking 'Deficiente' calls onChange(1)", () => {
    const onChange = vi.fn();
    renderInput({ onChange });
    fireEvent.click(screen.getByRole("button", { name: /^Deficiente$/i }));
    expect(onChange).toHaveBeenCalledWith(1);
  });

  it("clicking 'Satisfactorio' calls onChange(2)", () => {
    const onChange = vi.fn();
    renderInput({ onChange });
    fireEvent.click(screen.getByRole("button", { name: /^Satisfactorio$/i }));
    expect(onChange).toHaveBeenCalledWith(2);
  });

  it("clicking 'Excelente' calls onChange(3)", () => {
    const onChange = vi.fn();
    renderInput({ onChange });
    fireEvent.click(screen.getByRole("button", { name: /^Excelente$/i }));
    expect(onChange).toHaveBeenCalledWith(3);
  });
});

describe("TernaryDefenseInput — active state when value is set", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("value=2 marks 'Satisfactorio' button as aria-pressed='true'", () => {
    renderInput({ value: 2 });
    const btn = screen.getByRole("button", { name: /^Satisfactorio$/i });
    expect(btn).toHaveAttribute("aria-pressed", "true");
  });

  it("value=2 does NOT mark 'Deficiente' as aria-pressed='true'", () => {
    renderInput({ value: 2 });
    const btn = screen.getByRole("button", { name: /^Deficiente$/i });
    expect(btn).not.toHaveAttribute("aria-pressed", "true");
  });

  it("value=2 does NOT mark 'Excelente' as aria-pressed='true'", () => {
    renderInput({ value: 2 });
    const btn = screen.getByRole("button", { name: /^Excelente$/i });
    expect(btn).not.toHaveAttribute("aria-pressed", "true");
  });

  it("value=1 marks 'Deficiente' button as aria-pressed='true'", () => {
    renderInput({ value: 1 });
    const btn = screen.getByRole("button", { name: /^Deficiente$/i });
    expect(btn).toHaveAttribute("aria-pressed", "true");
  });

  it("value=3 marks 'Excelente' button as aria-pressed='true'", () => {
    renderInput({ value: 3 });
    const btn = screen.getByRole("button", { name: /^Excelente$/i });
    expect(btn).toHaveAttribute("aria-pressed", "true");
  });
});

describe("TernaryDefenseInput — CSS namespace", () => {
  it("renders an element with class inp-seg", () => {
    const { container } = renderInput();
    expect(container.querySelector(".inp-seg")).not.toBeNull();
  });
});
