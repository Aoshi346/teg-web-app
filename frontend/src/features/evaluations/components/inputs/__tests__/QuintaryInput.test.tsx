import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

import QuintaryInput from "../QuintaryInput";

const LABELS = ["Deficiente", "Medio-bajo", "Intermedio", "Medio-alto", "Excelente"];
const VALUES = [1, 2, 3, 4, 5] as const;

function renderInput(
  overrides: Partial<React.ComponentProps<typeof QuintaryInput>> = {}
) {
  const defaults = {
    value: 0,
    onChange: vi.fn(),
  };
  return render(<QuintaryInput {...defaults} {...overrides} />);
}

describe("QuintaryInput — five buttons rendered in DOM order", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it.each(LABELS)("renders a '%s' button", (label) => {
    renderInput();
    expect(screen.getByRole("button", { name: new RegExp(`^${label}$`, "i") })).toBeInTheDocument();
  });

  it("buttons appear in Deficiente → Medio-bajo → Intermedio → Medio-alto → Excelente DOM order", () => {
    const { container } = renderInput();
    const buttons = Array.from(container.querySelectorAll("button"));
    const positions = LABELS.map((label) =>
      buttons.findIndex((b) => b.textContent?.trim() === label)
    );
    for (let i = 0; i < positions.length - 1; i++) {
      expect(positions[i]).toBeLessThan(positions[i + 1]);
    }
  });

  it("all buttons have type='button'", () => {
    const { container } = renderInput();
    const buttons = Array.from(container.querySelectorAll("button"));
    expect(buttons).toHaveLength(5);
    buttons.forEach((btn) => {
      expect(btn).toHaveAttribute("type", "button");
    });
  });
});

describe("QuintaryInput — click calls onChange with correct value", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it.each(LABELS.map((label, i) => [label, VALUES[i]] as [string, number]))(
    "clicking '%s' calls onChange(%i)",
    (label, value) => {
      const onChange = vi.fn();
      renderInput({ onChange });
      fireEvent.click(screen.getByRole("button", { name: new RegExp(`^${label}$`, "i") }));
      expect(onChange).toHaveBeenCalledWith(value);
    }
  );
});

describe("QuintaryInput — aria-pressed reflects active value", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("when value=3, the 'Intermedio' button has aria-pressed='true'", () => {
    renderInput({ value: 3 });
    const btn = screen.getByRole("button", { name: /^Intermedio$/i });
    expect(btn).toHaveAttribute("aria-pressed", "true");
  });

  it("when value=3, non-active buttons have aria-pressed='false'", () => {
    renderInput({ value: 3 });
    const inactiveLabels = LABELS.filter((l) => l !== "Intermedio");
    inactiveLabels.forEach((label) => {
      const btn = screen.getByRole("button", { name: new RegExp(`^${label}$`, "i") });
      expect(btn).toHaveAttribute("aria-pressed", "false");
    });
  });

  it.each(LABELS.map((label, i) => [label, VALUES[i]] as [string, number]))(
    "value=%i marks '%s' as aria-pressed='true'",
    (label, value) => {
      renderInput({ value });
      const btn = screen.getByRole("button", { name: new RegExp(`^${label}$`, "i") });
      expect(btn).toHaveAttribute("aria-pressed", "true");
    }
  );
});

describe("QuintaryInput — active class on selected button", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it.each(LABELS.map((label, i) => [label, VALUES[i]] as [string, number]))(
    "value=%i gives 'active' class to '%s' button",
    (label, value) => {
      renderInput({ value });
      const btn = screen.getByRole("button", { name: new RegExp(`^${label}$`, "i") });
      expect(btn.className).toMatch(/active/);
    }
  );

  it("unselected buttons do not have 'active' class when value=2", () => {
    renderInput({ value: 2 });
    const inactiveLabels = LABELS.filter((l) => l !== "Medio-bajo");
    inactiveLabels.forEach((label) => {
      const btn = screen.getByRole("button", { name: new RegExp(`^${label}$`, "i") });
      expect(btn.className).not.toMatch(/\bactive\b/);
    });
  });
});

describe("QuintaryInput — disabled prop", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("when disabled, all buttons are disabled", () => {
    const { container } = renderInput({ disabled: true });
    const buttons = Array.from(container.querySelectorAll("button"));
    buttons.forEach((btn) => {
      expect(btn).toBeDisabled();
    });
  });

  it("without disabled prop, buttons are not disabled", () => {
    const { container } = renderInput({ disabled: false });
    const buttons = Array.from(container.querySelectorAll("button"));
    buttons.forEach((btn) => {
      expect(btn).not.toBeDisabled();
    });
  });
});

describe("QuintaryInput — onAdvance callback", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("clicking a button calls onAdvance once if provided", () => {
    const onAdvance = vi.fn();
    const onChange = vi.fn();
    renderInput({ onChange, onAdvance });
    fireEvent.click(screen.getByRole("button", { name: /^Intermedio$/i }));
    expect(onAdvance).toHaveBeenCalledTimes(1);
  });

  it("does not throw when onAdvance is not provided", () => {
    const onChange = vi.fn();
    renderInput({ onChange });
    expect(() =>
      fireEvent.click(screen.getByRole("button", { name: /^Excelente$/i }))
    ).not.toThrow();
  });
});

describe("QuintaryInput — onFocus callback", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("focusing a button calls onFocus", () => {
    const onFocus = vi.fn();
    renderInput({ onFocus });
    fireEvent.focus(screen.getByRole("button", { name: /^Deficiente$/i }));
    expect(onFocus).toHaveBeenCalledTimes(1);
  });
});

describe("QuintaryInput — CSS namespace", () => {
  it("renders the root element with class 'inp-seg'", () => {
    const { container } = renderInput();
    expect(container.querySelector(".inp-seg")).not.toBeNull();
  });

  it("renders the root element with class 'v-quintary'", () => {
    const { container } = renderInput();
    expect(container.querySelector(".v-quintary")).not.toBeNull();
  });
});
