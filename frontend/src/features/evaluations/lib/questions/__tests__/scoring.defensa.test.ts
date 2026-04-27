import { describe, it, expect } from "vitest";
import { getPointValue } from "../scoring";
import { PTEG_DEFENSA_QUESTIONS } from "../questions";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const fakeTecnicaQuestion: any = {
  id: "pd-tech1",
  label: "Test técnica",
  section: "Criterios de Evaluación Técnica",
  documentType: "Proyecto",
  answerType: "ternary_defense",
  kind: "defense",
};

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const fakeDivulgativaQuestion: any = {
  id: "pd-div1",
  label: "Test divulgativa",
  section: "Criterios de Evaluación Divulgativa",
  documentType: "Proyecto",
  answerType: "ternary_defense",
  kind: "defense",
};

describe("getPointValue — ternary_defense answerType (Técnica section)", () => {
  it("returns 0.2 for value 1 (Deficiente)", () => {
    expect(getPointValue(fakeTecnicaQuestion, 1)).toBeCloseTo(0.2, 5);
  });

  it("returns 0.5 for value 2 (Satisfactorio)", () => {
    expect(getPointValue(fakeTecnicaQuestion, 2)).toBeCloseTo(0.5, 5);
  });

  it("returns 1.0 for value 3 (Excelente)", () => {
    expect(getPointValue(fakeTecnicaQuestion, 3)).toBeCloseTo(1.0, 5);
  });
});

describe("getPointValue — ternary_defense answerType (Divulgativa section)", () => {
  it("returns 0.2 for value 1 (Deficiente)", () => {
    expect(getPointValue(fakeDivulgativaQuestion, 1)).toBeCloseTo(0.2, 5);
  });

  it("returns 0.5 for value 2 (Satisfactorio)", () => {
    expect(getPointValue(fakeDivulgativaQuestion, 2)).toBeCloseTo(0.5, 5);
  });

  it("returns 1.0 for value 3 (Excelente)", () => {
    expect(getPointValue(fakeDivulgativaQuestion, 3)).toBeCloseTo(1.0, 5);
  });
});

describe("getPointValue — ternary_defense scoring is section-independent", () => {
  it("Técnica and Divulgativa return the same score for value 1", () => {
    expect(getPointValue(fakeTecnicaQuestion, 1)).toBe(
      getPointValue(fakeDivulgativaQuestion, 1)
    );
  });

  it("Técnica and Divulgativa return the same score for value 2", () => {
    expect(getPointValue(fakeTecnicaQuestion, 2)).toBe(
      getPointValue(fakeDivulgativaQuestion, 2)
    );
  });

  it("Técnica and Divulgativa return the same score for value 3", () => {
    expect(getPointValue(fakeTecnicaQuestion, 3)).toBe(
      getPointValue(fakeDivulgativaQuestion, 3)
    );
  });
});

describe("getPointValue — ternary_defense sum over all 20 questions", () => {
  it("all 20 questions answered Excelente (3) sum to 20", () => {
    const total = PTEG_DEFENSA_QUESTIONS.reduce(
      (sum, q) => sum + getPointValue(q, 3),
      0
    );
    expect(total).toBeCloseTo(20, 5);
  });

  it("all 20 questions answered Deficiente (1) sum to 4", () => {
    const total = PTEG_DEFENSA_QUESTIONS.reduce(
      (sum, q) => sum + getPointValue(q, 1),
      0
    );
    expect(total).toBeCloseTo(4, 5);
  });
});
