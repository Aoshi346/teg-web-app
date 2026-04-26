import { describe, it, expect } from "vitest";
import { render } from "@testing-library/react";
import { StatePill } from "./StatePill";
import type { ProjectState } from "@features/projects/types/project";

describe("StatePill", () => {
  const cases: Array<[ProjectState, string, string]> = [
    ["pending_review_1", "Rev 1", "spill-amber"],
    ["pending_review_2", "Rev 2", "spill-amber"],
    ["pending_defense",  "Defensa", "spill-blue"],
    ["pending_articulo", "Artículo", "spill-amber"],
    ["pending_entrega",  "Entrega", "spill-amber"],
    ["pending_defensa",  "Defensa", "spill-blue"],
    ["approved",         "Aprobado", "spill-green"],
    ["failed_final",     "Reprobado", "spill-red"],
  ];

  it.each(cases)("renders %s as label %s with class %s", (state, expectedLabel, expectedClass) => {
    const { container } = render(<StatePill state={state} />);
    const pill = container.firstChild as HTMLElement;
    expect(pill).toHaveTextContent(expectedLabel);
    expect(pill.className).toContain(expectedClass);
  });

  it("forwards an extra className", () => {
    const { container } = render(<StatePill state="approved" className="ml-2" />);
    expect((container.firstChild as HTMLElement).className).toContain("ml-2");
  });

  it("uses 'Aprobada' (feminine) when projectType is tesis and state is approved", () => {
    const { container } = render(<StatePill state="approved" projectType="tesis" />);
    expect(container.firstChild).toHaveTextContent("Aprobada");
  });

  it("uses 'Reprobada' (feminine) when projectType is tesis and state is failed_final", () => {
    const { container } = render(<StatePill state="failed_final" projectType="tesis" />);
    expect(container.firstChild).toHaveTextContent("Reprobada");
  });
});
