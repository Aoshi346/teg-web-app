/**
 * Tests for FactibilidadToggle — Phase C (new component spec).
 *
 * The component does NOT exist yet. These tests are expected to FAIL (RED)
 * with a module resolution error until frontend-worker creates
 * frontend/src/features/evaluations/components/FactibilidadToggle.tsx
 * with the following props interface:
 *
 *   interface FactibilidadToggleProps {
 *     isFactible: boolean | null;       // null = unanswered
 *     includesModelo: boolean | null;
 *     onChange: (next: { isFactible: boolean | null; includesModelo: boolean | null }) => void;
 *     disabled?: boolean;
 *   }
 */

import React, { useState } from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

// ── component under test ───────────────────────────────────────────────────────
// This import will fail (RED) until the component is created.
import FactibilidadToggle from "../FactibilidadToggle";

// ── helper: controlled wrapper ─────────────────────────────────────────────────
interface WrapperProps {
  initialFactible?: boolean | null;
  initialModelo?: boolean | null;
  disabled?: boolean;
  onChangeSpy?: ReturnType<typeof vi.fn>;
}

function Wrapper({
  initialFactible = null,
  initialModelo = null,
  disabled = false,
  onChangeSpy,
}: WrapperProps) {
  const [state, setState] = useState({
    isFactible: initialFactible,
    includesModelo: initialModelo,
  });

  function handleChange(next: {
    isFactible: boolean | null;
    includesModelo: boolean | null;
  }) {
    setState(next);
    onChangeSpy?.(next);
  }

  return (
    <FactibilidadToggle
      isFactible={state.isFactible}
      includesModelo={state.includesModelo}
      onChange={handleChange}
      disabled={disabled}
    />
  );
}

// ── tests ──────────────────────────────────────────────────────────────────────

describe("FactibilidadToggle", () => {
  it("renders a yes/no pair for section 6.1 (factible)", () => {
    render(<Wrapper />);

    // Expect two buttons/radios for 6.1: "Sí" and "No"
    // Look for the labels adjacent to the 6.1 question about "factible"
    expect(screen.getByText(/factible/i)).toBeTruthy();

    // Both Sí and No options must be present (at least one pair)
    const siButtons = screen.getAllByRole("button", { name: /^sí$/i });
    const noButtons = screen.getAllByRole("button", { name: /^no$/i });
    expect(siButtons.length).toBeGreaterThanOrEqual(1);
    expect(noButtons.length).toBeGreaterThanOrEqual(1);
  });

  it("renders a yes/no pair for section 6.2 (modelo operativo)", () => {
    render(<Wrapper />);
    expect(screen.getByText(/modelo operativo/i)).toBeTruthy();
  });

  it("6.2 yes/no buttons are disabled when isFactible is null", () => {
    render(<Wrapper initialFactible={null} />);

    // Find the 6.2 section buttons — they should be disabled
    const modeloLabel = screen.getByText(/modelo operativo/i);
    // The closest section container should have disabled buttons
    // We look for a button that is a sibling of the modelo label
    const container = modeloLabel.closest("[data-section='s6-2']") ??
      modeloLabel.parentElement;

    // Query buttons within that container
    const buttons = (container ?? document).querySelectorAll
      ? Array.from(
          (container as HTMLElement).querySelectorAll("button"),
        )
      : [];

    // All buttons in the 6.2 section must be disabled
    if (buttons.length > 0) {
      buttons.forEach((btn) => {
        expect((btn as HTMLButtonElement).disabled).toBe(true);
      });
    } else {
      // Fallback: aria-disabled pattern
      const siBtn6_2 = screen.getByRole("button", {
        name: /^sí$/i,
        // Note: there may be two "Sí" buttons; we pick the second one (6.2)
      });
      // The second Sí button belongs to 6.2 and should have aria-disabled or be disabled
      const allSi = screen.getAllByRole("button", { name: /^sí$/i });
      expect(
        allSi[allSi.length - 1].getAttribute("aria-disabled") === "true" ||
          (allSi[allSi.length - 1] as HTMLButtonElement).disabled,
      ).toBe(true);
    }
  });

  it("6.2 buttons are disabled when isFactible is false", () => {
    render(<Wrapper initialFactible={false} />);

    const allSi = screen.getAllByRole("button", { name: /^sí$/i });
    const allNo = screen.getAllByRole("button", { name: /^no$/i });

    // 6.2 = last pair; they should be disabled
    const lastSi = allSi[allSi.length - 1] as HTMLButtonElement;
    const lastNo = allNo[allNo.length - 1] as HTMLButtonElement;
    const lastSiDisabled =
      lastSi.disabled || lastSi.getAttribute("aria-disabled") === "true";
    const lastNoDisabled =
      lastNo.disabled || lastNo.getAttribute("aria-disabled") === "true";

    expect(lastSiDisabled).toBe(true);
    expect(lastNoDisabled).toBe(true);
  });

  it("6.2 buttons are enabled when isFactible is true", () => {
    render(<Wrapper initialFactible={true} />);

    const allSi = screen.getAllByRole("button", { name: /^sí$/i });
    const lastSi = allSi[allSi.length - 1] as HTMLButtonElement;
    const lastSiDisabled =
      lastSi.disabled || lastSi.getAttribute("aria-disabled") === "true";

    expect(lastSiDisabled).toBe(false);
  });

  it("selecting 6.1=No calls onChange with isFactible=false and clears includesModelo to null", () => {
    const spy = vi.fn();
    // Start with 6.1=Sí (true) and 6.2=Sí (true), then click No on 6.1
    render(<Wrapper initialFactible={true} initialModelo={true} onChangeSpy={spy} />);

    const allNo = screen.getAllByRole("button", { name: /^no$/i });
    // First "No" button = 6.1
    fireEvent.click(allNo[0]);

    expect(spy).toHaveBeenCalledOnce();
    const callArg = spy.mock.calls[0][0];
    expect(callArg.isFactible).toBe(false);
    expect(callArg.includesModelo).toBeNull();
  });

  it("selecting 6.1=Sí calls onChange with isFactible=true and preserves includesModelo", () => {
    const spy = vi.fn();
    render(<Wrapper initialFactible={null} initialModelo={null} onChangeSpy={spy} />);

    const allSi = screen.getAllByRole("button", { name: /^sí$/i });
    // First "Sí" = 6.1
    fireEvent.click(allSi[0]);

    expect(spy).toHaveBeenCalledOnce();
    const callArg = spy.mock.calls[0][0];
    expect(callArg.isFactible).toBe(true);
    // includesModelo unchanged from null
    expect(callArg.includesModelo).toBeNull();
  });

  it("onChange is called with merged state on each click", () => {
    const spy = vi.fn();
    render(<Wrapper onChangeSpy={spy} />);

    const allSi = screen.getAllByRole("button", { name: /^sí$/i });
    fireEvent.click(allSi[0]); // 6.1 = Sí

    expect(spy).toHaveBeenCalledTimes(1);
    expect(spy.mock.calls[0][0]).toMatchObject({ isFactible: true });
  });

  it("penalty hint banner appears only when isFactible=true and includesModelo=false", () => {
    const { rerender } = render(
      <FactibilidadToggle
        isFactible={true}
        includesModelo={false}
        onChange={vi.fn()}
      />,
    );

    // Penalty hint should be visible (penalty = -2)
    expect(screen.getByText(/-2/)).toBeTruthy();

    // Rerender with includesModelo=true — banner should disappear
    rerender(
      <FactibilidadToggle
        isFactible={true}
        includesModelo={true}
        onChange={vi.fn()}
      />,
    );
    expect(screen.queryByText(/-2/)).toBeNull();
  });

  it("penalty hint does NOT appear when isFactible=false", () => {
    render(
      <FactibilidadToggle
        isFactible={false}
        includesModelo={null}
        onChange={vi.fn()}
      />,
    );
    expect(screen.queryByText(/-2/)).toBeNull();
  });

  it("penalty hint does NOT appear when isFactible=null", () => {
    render(
      <FactibilidadToggle
        isFactible={null}
        includesModelo={null}
        onChange={vi.fn()}
      />,
    );
    expect(screen.queryByText(/-2/)).toBeNull();
  });
});
