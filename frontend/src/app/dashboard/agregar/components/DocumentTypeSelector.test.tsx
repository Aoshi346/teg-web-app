import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import DocumentTypeSelector from "./DocumentTypeSelector";

// Selector strategy notes:
// - Active state: assert that the card element has both class "agg-tcard" and class "active".
//   The implementer should render <div className="agg-tcard pteg active"> or similar.
//   We query via container.querySelector(".agg-tcard.active") and confirm which card it is.
// - Locked state: assert class "locked" on the card element AND aria-disabled="true" on the
//   clickable element (button or div with role="button"). If the implementer uses a <button>
//   with disabled attribute, the aria-disabled check may use .disabled property instead —
//   but explicit aria-disabled="true" is preferred for non-button elements. We assert both
//   class and aria-disabled to give the implementer flexibility on the element type.
// - Check icon: we assert the ".agg-tcard-check" element exists ONLY on the active card (i.e.,
//   the implementer renders it conditionally, not via display:none). getAllByText("✓") must
//   return exactly 1 element. This is the simplest approach that also makes the CSS simpler.
// - Pills: assert exact uppercase text "PTEG" and "TEG" (case-sensitive, matching mockup).
//   Current impl uses "Proyecto (PTEG)" and "Trabajo Especial (TEG)" — these will fail.
// - Numerals: assert "9°" and "10°" with the degree symbol (current uses "9no Semestre" / "10mo Semestre").

type DocType = "proyecto" | "tesis";

function renderSelector(props: {
  value: DocType;
  onChange: ReturnType<typeof vi.fn>;
  allowedTypes: readonly DocType[];
  disabled?: boolean;
}) {
  return render(<DocumentTypeSelector {...props} />);
}

describe("DocumentTypeSelector — Sub-H redesign", () => {
  let onChange: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    onChange = vi.fn();
  });

  // Test 1: Fraunces numerals
  it("renders the Fraunces numeral 9° on the PTEG card", () => {
    renderSelector({ value: "proyecto", onChange, allowedTypes: ["proyecto", "tesis"] });
    expect(screen.getByText("9°")).toBeTruthy();
  });

  it("renders the Fraunces numeral 10° on the TEG card", () => {
    renderSelector({ value: "proyecto", onChange, allowedTypes: ["proyecto", "tesis"] });
    expect(screen.getByText("10°")).toBeTruthy();
  });

  // Test 2: Active card class
  it("PTEG card has .agg-tcard.active when value is 'proyecto'", () => {
    const { container } = renderSelector({
      value: "proyecto",
      onChange,
      allowedTypes: ["proyecto", "tesis"],
    });
    const activeCard = container.querySelector(".agg-tcard.active");
    expect(activeCard).not.toBeNull();
    expect(activeCard!.classList.contains("pteg")).toBe(true);
  });

  it("TEG card has .agg-tcard.active when value is 'tesis'", () => {
    const { container } = renderSelector({
      value: "tesis",
      onChange,
      allowedTypes: ["proyecto", "tesis"],
    });
    const activeCard = container.querySelector(".agg-tcard.active");
    expect(activeCard).not.toBeNull();
    expect(activeCard!.classList.contains("teg")).toBe(true);
  });

  // Test 3: Locked state
  it("TEG card has .locked class and aria-disabled when allowedTypes=['proyecto']", () => {
    const { container } = renderSelector({
      value: "proyecto",
      onChange,
      allowedTypes: ["proyecto"],
    });
    const tegCard = container.querySelector(".agg-tcard.teg");
    expect(tegCard).not.toBeNull();
    expect(tegCard!.classList.contains("locked")).toBe(true);
    // aria-disabled on the card element itself (or the button inside)
    const ariaDisabled =
      tegCard!.getAttribute("aria-disabled") === "true" ||
      tegCard!.querySelector("[aria-disabled='true']") !== null;
    expect(ariaDisabled).toBe(true);
  });

  it("PTEG card has .locked class and aria-disabled when allowedTypes=['tesis']", () => {
    const { container } = renderSelector({
      value: "tesis",
      onChange,
      allowedTypes: ["tesis"],
    });
    const ptegCard = container.querySelector(".agg-tcard.pteg");
    expect(ptegCard).not.toBeNull();
    expect(ptegCard!.classList.contains("locked")).toBe(true);
    const ariaDisabled =
      ptegCard!.getAttribute("aria-disabled") === "true" ||
      ptegCard!.querySelector("[aria-disabled='true']") !== null;
    expect(ariaDisabled).toBe(true);
  });

  // Test 4: Locked card click is no-op
  it("clicking the locked TEG card does not call onChange", () => {
    const { container } = renderSelector({
      value: "proyecto",
      onChange,
      allowedTypes: ["proyecto"],
    });
    const tegCard = container.querySelector(".agg-tcard.teg") as HTMLElement;
    expect(tegCard).not.toBeNull();
    fireEvent.click(tegCard);
    expect(onChange).not.toHaveBeenCalled();
  });

  // Test 5: Allowed inactive click triggers onChange
  it("clicking the inactive but allowed TEG card calls onChange with 'tesis'", () => {
    const { container } = renderSelector({
      value: "proyecto",
      onChange,
      allowedTypes: ["proyecto", "tesis"],
    });
    const tegCard = container.querySelector(".agg-tcard.teg") as HTMLElement;
    expect(tegCard).not.toBeNull();
    fireEvent.click(tegCard);
    expect(onChange).toHaveBeenCalledTimes(1);
    expect(onChange).toHaveBeenCalledWith("tesis");
  });

  // Test 6: disabled prop
  it("clicking either card does not call onChange when disabled=true", () => {
    const { container } = renderSelector({
      value: "proyecto",
      onChange,
      allowedTypes: ["proyecto", "tesis"],
      disabled: true,
    });
    const ptegCard = container.querySelector(".agg-tcard.pteg") as HTMLElement;
    const tegCard = container.querySelector(".agg-tcard.teg") as HTMLElement;
    fireEvent.click(ptegCard);
    fireEvent.click(tegCard);
    expect(onChange).not.toHaveBeenCalled();
  });

  it("shows 'Documento asignado' label when disabled=true", () => {
    renderSelector({
      value: "proyecto",
      onChange,
      allowedTypes: ["proyecto", "tesis"],
      disabled: true,
    });
    expect(screen.getByText("Documento asignado")).toBeTruthy();
  });

  it("shows 'Tipo de documento' label when not disabled", () => {
    renderSelector({
      value: "proyecto",
      onChange,
      allowedTypes: ["proyecto", "tesis"],
    });
    // The label text from the mockup (case-insensitive flexible match)
    const label = screen.getByText(/tipo de documento/i);
    expect(label).toBeTruthy();
  });

  // Test 7: Pills present
  it("shows PTEG pill badge on the PTEG card", () => {
    const { container } = renderSelector({
      value: "proyecto",
      onChange,
      allowedTypes: ["proyecto", "tesis"],
    });
    // The pill must be "PTEG" exactly (uppercase, matching mockup <span class="agg-tcard-pill">PTEG</span>)
    const ptegCard = container.querySelector(".agg-tcard.pteg");
    expect(ptegCard).not.toBeNull();
    const pill = ptegCard!.querySelector(".agg-tcard-pill");
    expect(pill).not.toBeNull();
    expect(pill!.textContent).toBe("PTEG");
  });

  it("shows TEG pill badge on the TEG card", () => {
    const { container } = renderSelector({
      value: "proyecto",
      onChange,
      allowedTypes: ["proyecto", "tesis"],
    });
    const tegCard = container.querySelector(".agg-tcard.teg");
    expect(tegCard).not.toBeNull();
    const pill = tegCard!.querySelector(".agg-tcard-pill");
    expect(pill).not.toBeNull();
    expect(pill!.textContent).toBe("TEG");
  });

  // Test 8: Active card shows the check icon; inactive cards do not
  it("only the active card contains the .agg-tcard-check element with ✓ text", () => {
    renderSelector({
      value: "proyecto",
      onChange,
      allowedTypes: ["proyecto", "tesis"],
    });
    // Implementer renders .agg-tcard-check only on the active card (conditional render, not display:none)
    const checks = screen.getAllByText("✓");
    expect(checks).toHaveLength(1);
  });

  it("when value changes to 'tesis', the TEG card becomes the only one with the ✓ check", () => {
    renderSelector({
      value: "tesis",
      onChange,
      allowedTypes: ["proyecto", "tesis"],
    });
    const checks = screen.getAllByText("✓");
    expect(checks).toHaveLength(1);
    // The single check should be inside the teg card
    const { container } = render(
      <DocumentTypeSelector value="tesis" onChange={onChange} allowedTypes={["proyecto", "tesis"]} />
    );
    const tegCard = container.querySelector(".agg-tcard.teg");
    expect(tegCard).not.toBeNull();
    expect(tegCard!.querySelector(".agg-tcard-check")).not.toBeNull();
    const ptegCard = container.querySelector(".agg-tcard.pteg");
    expect(ptegCard).not.toBeNull();
    expect(ptegCard!.querySelector(".agg-tcard-check")).toBeNull();
  });
});
