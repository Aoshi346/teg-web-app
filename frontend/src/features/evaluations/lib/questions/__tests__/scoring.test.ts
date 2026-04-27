import { describe, it, expect } from "vitest";
import {
  getPointValue,
  getPassStatus,
  calculateTegEntregaScore,
  calculateTegEntregaSectionScores,
  getTegEntregaPassStatus,
} from "../scoring";
import type { Question } from "../questions";

// ---------------------------------------------------------------------------
// Shared question fixtures
// ---------------------------------------------------------------------------

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const makeQuintaryQuestion = (id: string, section: string): any => ({
  id,
  label: `Question ${id}`,
  section,
  documentType: "Tesis",
  answerType: "quintary",
  kind: "review",
});

// Section label strings that the scoring engine uses to identify sections
const SECTION_DIAGRAMACION = "Diagramación";
const SECTION_1 = "Sección 1 (Capítulo 1)";
const SECTION_2 = "Sección 2 (Capítulo 2)";
const SECTION_3 = "Sección 3 (Capítulo 3)";
const SECTION_4 = "Sección 4 (Capítulo 4)";
const SECTION_5 = "Sección 5 (Capítulo 5)";
const SECTION_FINAL = "Sección Final";

// Distribution: 4 / 10 / 3 / 12 / 9 / 6 / 3
function buildEntregaQuestions(): Question[] {
  const questions: Question[] = [];

  for (let i = 1; i <= 4; i++) {
    questions.push(makeQuintaryQuestion(`te-d${i}`, SECTION_DIAGRAMACION));
  }
  for (let i = 1; i <= 10; i++) {
    questions.push(makeQuintaryQuestion(`te-s1-${i}`, SECTION_1));
  }
  for (let i = 1; i <= 3; i++) {
    questions.push(makeQuintaryQuestion(`te-s2-${i}`, SECTION_2));
  }
  for (let i = 1; i <= 12; i++) {
    questions.push(makeQuintaryQuestion(`te-s3-${i}`, SECTION_3));
  }
  for (let i = 1; i <= 9; i++) {
    questions.push(makeQuintaryQuestion(`te-s4-${i}`, SECTION_4));
  }
  for (let i = 1; i <= 6; i++) {
    questions.push(makeQuintaryQuestion(`te-s5-${i}`, SECTION_5));
  }
  for (let i = 1; i <= 3; i++) {
    questions.push(makeQuintaryQuestion(`te-f${i}`, SECTION_FINAL));
  }

  return questions;
}

const ENTREGA_QUESTIONS = buildEntregaQuestions();

// Helper: build a ratings map where every question gets the same value
function uniformRatings(
  questions: Question[],
  value: number
): Record<string, number> {
  return Object.fromEntries(questions.map((q) => [q.id, value]));
}

// ---------------------------------------------------------------------------
// 1. getPointValue — quintary answerType
// ---------------------------------------------------------------------------

describe("getPointValue — quintary answerType", () => {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const q: any = makeQuintaryQuestion("te-d1", SECTION_DIAGRAMACION);

  it("returns 0.2 for value 1", () => {
    expect(getPointValue(q, 1)).toBeCloseTo(0.2, 5);
  });

  it("returns 0.4 for value 2", () => {
    expect(getPointValue(q, 2)).toBeCloseTo(0.4, 5);
  });

  it("returns 0.6 for value 3", () => {
    expect(getPointValue(q, 3)).toBeCloseTo(0.6, 5);
  });

  it("returns 0.8 for value 4", () => {
    expect(getPointValue(q, 4)).toBeCloseTo(0.8, 5);
  });

  it("returns 1.0 for value 5", () => {
    expect(getPointValue(q, 5)).toBeCloseTo(1.0, 5);
  });

  it("returns 0 for value 0 (out-of-range)", () => {
    expect(getPointValue(q, 0)).toBe(0);
  });

  it("returns 0 for value 6 (out-of-range)", () => {
    expect(getPointValue(q, 6)).toBe(0);
  });
});

// ---------------------------------------------------------------------------
// 2. calculateTegEntregaScore
// ---------------------------------------------------------------------------

describe("calculateTegEntregaScore", () => {
  // Section weights and question counts:
  //   diagramacion: 0.25 × 4
  //   seccion1:     0.30 × 10
  //   seccion2:     0.67 × 3
  //   seccion3:     0.25 × 12
  //   seccion4:     0.56 × 9
  //   seccion5:     0.83 × 6
  //   seccion_final: 0.5 × 3
  //
  // Raw max (all 5s, factor 1.0) = Σ(weight × Nq)
  //   = 0.25*4 + 0.30*10 + 0.67*3 + 0.25*12 + 0.56*9 + 0.83*6 + 0.5*3
  //   = 1.0 + 3.0 + 2.01 + 3.0 + 5.04 + 4.98 + 1.5
  //   = 20.53
  const RAW_MAX = 0.25 * 4 + 0.3 * 10 + 0.67 * 3 + 0.25 * 12 + 0.56 * 9 + 0.83 * 6 + 0.5 * 3;

  it("all 5s, factible=false → clamped to 20 (raw ~20.53)", () => {
    const ratings = uniformRatings(ENTREGA_QUESTIONS, 5);
    const score = calculateTegEntregaScore(ratings, ENTREGA_QUESTIONS, {
      isFactible: false,
      includesModelo: false,
    });
    expect(score).toBeCloseTo(20, 5);
  });

  it("all 5s, factible=true & includesModelo=true → clamped to 20 (no penalty)", () => {
    const ratings = uniformRatings(ENTREGA_QUESTIONS, 5);
    const score = calculateTegEntregaScore(ratings, ENTREGA_QUESTIONS, {
      isFactible: true,
      includesModelo: true,
    });
    expect(score).toBeCloseTo(20, 5);
  });

  it("all 5s, factible=true & includesModelo=false → ~18.53 (penalty −2, below clamp)", () => {
    const ratings = uniformRatings(ENTREGA_QUESTIONS, 5);
    const score = calculateTegEntregaScore(ratings, ENTREGA_QUESTIONS, {
      isFactible: true,
      includesModelo: false,
    });
    // 20.53 − 2 = 18.53
    expect(score).toBeCloseTo(18.53, 2);
  });

  it("all 1s, factible=false → 0.2 × RAW_MAX (no penalty)", () => {
    const ratings = uniformRatings(ENTREGA_QUESTIONS, 1);
    const score = calculateTegEntregaScore(ratings, ENTREGA_QUESTIONS, {
      isFactible: false,
      includesModelo: false,
    });
    // Each question earns factor 0.2 per level; level 1 → 0.2 per question point
    const expected = 0.2 * RAW_MAX; // ≈ 4.106
    expect(score).toBeCloseTo(expected, 3);
  });

  it("mixed half-1s half-5s, factible=true & includesModelo=true → computed expected", () => {
    // Build a ratings map: first half of each section uses value 1, second half uses value 5
    const ratings: Record<string, number> = {};

    // Compute expected inline so there is no magic constant
    // Per-question contribution = level × 0.2 × sectionWeight
    // For levels alternating [1,5] half/half within each section:
    //   avg level per section = (1 + 5) / 2 = 3   (or exact per-section calculation below)
    // We compute exactly by processing the question array
    const sectionWeights: Record<string, number> = {
      [SECTION_DIAGRAMACION]: 0.25,
      [SECTION_1]: 0.3,
      [SECTION_2]: 0.67,
      [SECTION_3]: 0.25,
      [SECTION_4]: 0.56,
      [SECTION_5]: 0.83,
      [SECTION_FINAL]: 0.5,
    };

    // Count questions per section to determine split point
    const sectionCounts: Record<string, number> = {};
    for (const q of ENTREGA_QUESTIONS) {
      const sec = q.section ?? "";
      sectionCounts[sec] = (sectionCounts[sec] ?? 0) + 1;
    }
    const sectionIdx: Record<string, number> = {};
    for (const q of ENTREGA_QUESTIONS) {
      const sec = q.section ?? "";
      const idx = sectionIdx[sec] ?? 0;
      const half = Math.floor((sectionCounts[sec] ?? 0) / 2);
      ratings[q.id] = idx < half ? 1 : 5;
      sectionIdx[sec] = idx + 1;
    }

    // Compute expected total
    let expectedRaw = 0;
    const sectionAccum: Record<string, number> = {};
    for (const q of ENTREGA_QUESTIONS) {
      const sec = q.section ?? "";
      const level = ratings[q.id];
      const points = level * 0.2;
      sectionAccum[sec] = (sectionAccum[sec] ?? 0) + points;
    }
    for (const [sec, subtotal] of Object.entries(sectionAccum)) {
      expectedRaw += subtotal * (sectionWeights[sec] ?? 0);
    }
    const penalty = 0; // isFactible=true, includesModelo=true → no penalty
    const expectedScore = Math.min(expectedRaw + penalty, 20);

    const score = calculateTegEntregaScore(ratings, ENTREGA_QUESTIONS, {
      isFactible: true,
      includesModelo: true,
    });

    expect(score).toBeCloseTo(expectedScore, 2);
  });
});

// ---------------------------------------------------------------------------
// 3. getTegEntregaPassStatus
// ---------------------------------------------------------------------------

describe("getTegEntregaPassStatus", () => {
  it("returns 'Fail' for score 13.99", () => {
    expect(getTegEntregaPassStatus(13.99)).toBe("Fail");
  });

  it("returns 'Pass' for score 14", () => {
    expect(getTegEntregaPassStatus(14)).toBe("Pass");
  });

  it("returns 'Pass' for score 14.01", () => {
    expect(getTegEntregaPassStatus(14.01)).toBe("Pass");
  });

  it("returns 'Fail' for score 0", () => {
    expect(getTegEntregaPassStatus(0)).toBe("Fail");
  });

  it("returns 'Pass' for score 20", () => {
    expect(getTegEntregaPassStatus(20)).toBe("Pass");
  });
});

// ---------------------------------------------------------------------------
// 4. Regression: existing getPassStatus is untouched (threshold 10)
// ---------------------------------------------------------------------------

describe("getPassStatus — regression (existing threshold 10 unchanged)", () => {
  it("returns 'Pass' for score 10", () => {
    expect(getPassStatus(10)).toBe("Pass");
  });

  it("returns 'Fail' for score 9.99", () => {
    expect(getPassStatus(9.99)).toBe("Fail");
  });
});

// ---------------------------------------------------------------------------
// 5. calculateTegEntregaSectionScores
// ---------------------------------------------------------------------------

describe("calculateTegEntregaSectionScores", () => {
  it("returns an object with 8 keys", () => {
    const ratings = uniformRatings(ENTREGA_QUESTIONS, 5);
    const result = calculateTegEntregaSectionScores(ratings, ENTREGA_QUESTIONS, {
      isFactible: false,
      includesModelo: false,
    });
    const keys = Object.keys(result);
    expect(keys).toContain("total");
    expect(keys).toContain("diagramacion");
    expect(keys).toContain("seccion1");
    expect(keys).toContain("seccion2");
    expect(keys).toContain("seccion3");
    expect(keys).toContain("seccion4");
    expect(keys).toContain("seccion5");
    expect(keys).toContain("seccion_final");
    expect(keys).toContain("seccion6_penalty");
  });

  it("all 5s, factible=true, includesModelo=false → seccion6_penalty === -2", () => {
    const ratings = uniformRatings(ENTREGA_QUESTIONS, 5);
    const result = calculateTegEntregaSectionScores(ratings, ENTREGA_QUESTIONS, {
      isFactible: true,
      includesModelo: false,
    });
    expect(result.seccion6_penalty).toBe(-2);
  });

  it("all 5s, factible=true, includesModelo=false → total ≈ 18.53", () => {
    const ratings = uniformRatings(ENTREGA_QUESTIONS, 5);
    const result = calculateTegEntregaSectionScores(ratings, ENTREGA_QUESTIONS, {
      isFactible: true,
      includesModelo: false,
    });
    expect(result.total).toBeCloseTo(18.53, 2);
  });

  it("all 5s, factible=true, includesModelo=false → diagramacion ≈ 1.0", () => {
    // 4 questions × 1.0 (level 5 × 0.2) × weight 0.25 = 4 × 1.0 × 0.25 = 1.0
    const ratings = uniformRatings(ENTREGA_QUESTIONS, 5);
    const result = calculateTegEntregaSectionScores(ratings, ENTREGA_QUESTIONS, {
      isFactible: true,
      includesModelo: false,
    });
    expect(result.diagramacion).toBeCloseTo(1.0, 5);
  });

  it("all 5s, factible=true, includesModelo=false → seccion1 ≈ 3.0", () => {
    // 10 questions × 1.0 × weight 0.30 = 3.0
    const ratings = uniformRatings(ENTREGA_QUESTIONS, 5);
    const result = calculateTegEntregaSectionScores(ratings, ENTREGA_QUESTIONS, {
      isFactible: true,
      includesModelo: false,
    });
    expect(result.seccion1).toBeCloseTo(3.0, 5);
  });

  it("all 5s, factible=true, includesModelo=false → seccion_final ≈ 1.5", () => {
    // 3 questions × 1.0 × weight 0.5 = 1.5
    const ratings = uniformRatings(ENTREGA_QUESTIONS, 5);
    const result = calculateTegEntregaSectionScores(ratings, ENTREGA_QUESTIONS, {
      isFactible: true,
      includesModelo: false,
    });
    expect(result.seccion_final).toBeCloseTo(1.5, 5);
  });

  it("all 5s, factible=false → seccion6_penalty === 0", () => {
    const ratings = uniformRatings(ENTREGA_QUESTIONS, 5);
    const result = calculateTegEntregaSectionScores(ratings, ENTREGA_QUESTIONS, {
      isFactible: false,
      includesModelo: false,
    });
    expect(result.seccion6_penalty).toBe(0);
  });

  it("total matches calculateTegEntregaScore output", () => {
    const ratings = uniformRatings(ENTREGA_QUESTIONS, 3);
    const scoreFromSimple = calculateTegEntregaScore(ratings, ENTREGA_QUESTIONS, {
      isFactible: true,
      includesModelo: false,
    });
    const result = calculateTegEntregaSectionScores(ratings, ENTREGA_QUESTIONS, {
      isFactible: true,
      includesModelo: false,
    });
    expect(result.total).toBeCloseTo(scoreFromSimple, 5);
  });
});
