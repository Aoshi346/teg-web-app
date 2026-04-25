import { describe, it, expect } from "vitest";
import { stateBadge } from "./stateBadge";
import type { ProjectState } from "@features/projects/types/project";

describe("stateBadge", () => {
  const cases: Array<[ProjectState, "amber" | "green" | "red", string]> = [
    ["pending_review_1", "amber", "Revisión 1"],
    ["pending_review_2", "amber", "Revisión 2"],
    ["pending_defense", "amber", "Defensa"],
    ["pending_articulo", "amber", "Artículo"],
    ["pending_entrega", "amber", "Entrega"],
    ["pending_defensa", "amber", "Defensa"],
    ["approved", "green", "Aprobado"],
    ["failed_final", "red", "Reprobado"],
  ];

  it.each(cases)("maps %s to %s/%s", (state, expectedTone, expectedLabel) => {
    expect(stateBadge(state)).toEqual({ tone: expectedTone, label: expectedLabel });
  });
});
