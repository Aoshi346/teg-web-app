import { describe, it, expect } from "vitest";
import {
  getPointValue,
  getPassStatus,
  PASSING_SCORE,
  calculateTegEntregaScore,
  calculateTegEntregaSectionScores,
  getTegEntregaPassStatus,
  calculateTegDefensaScore,
  getTegDefensaPassStatus,
  calculateTegDefensaSectionScores,
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
// 4. Global threshold change: PASSING_SCORE raised from 10 to 14
// ---------------------------------------------------------------------------

describe("PASSING_SCORE — global threshold", () => {
  it("PASSING_SCORE constant equals 14", () => {
    expect(PASSING_SCORE).toBe(14);
  });

  it("getPassStatus returns 'Fail' for score 13.99", () => {
    expect(getPassStatus(13.99)).toBe("Fail");
  });

  it("getPassStatus returns 'Pass' for score 14", () => {
    expect(getPassStatus(14)).toBe("Pass");
  });

  it("getPassStatus returns 'Pass' for score 20", () => {
    expect(getPassStatus(20)).toBe("Pass");
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

// ---------------------------------------------------------------------------
// TEG Entrega pass status: its own constant TEG_ENTREGA_PASSING_SCORE = 14
// (regression guard — entrega threshold is independent of global PASSING_SCORE)
// ---------------------------------------------------------------------------

describe("getTegEntregaPassStatus — regression guard (independent threshold 14)", () => {
  it("returns 'Fail' for 13.99", () => {
    expect(getTegEntregaPassStatus(13.99)).toBe("Fail");
  });

  it("returns 'Pass' for 14", () => {
    expect(getTegEntregaPassStatus(14)).toBe("Pass");
  });
});

// ---------------------------------------------------------------------------
// getPointValue — quaternary_defense answerType
// ---------------------------------------------------------------------------

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const makeQuaternaryDefenseQuestion = (id: string, section: string): any => ({
  id,
  label: `Question ${id}`,
  section,
  documentType: "Tesis",
  answerType: "quaternary_defense",
  kind: "defense",
  phase: "defensa",
});

const SECTION_TECNICA = "Criterios de Evaluación Técnica";
const SECTION_DIVULGATIVA = "Criterios de Evaluación Divulgativa";

describe("getPointValue — quaternary_defense, Criterios de Evaluación Técnica", () => {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const q: any = makeQuaternaryDefenseQuestion("td-tech1", SECTION_TECNICA);

  it("returns 0.2 for value 1 (Deficiente)", () => {
    expect(getPointValue(q, 1)).toBeCloseTo(0.2, 5);
  });

  it("returns 0.5 for value 2 (Regular)", () => {
    expect(getPointValue(q, 2)).toBeCloseTo(0.5, 5);
  });

  it("returns 0.8 for value 3 (Satisfactorio)", () => {
    expect(getPointValue(q, 3)).toBeCloseTo(0.8, 5);
  });

  it("returns 1.0 for value 4 (Excelente)", () => {
    expect(getPointValue(q, 4)).toBeCloseTo(1.0, 5);
  });

  it("returns 0 for value 0 (out-of-range)", () => {
    expect(getPointValue(q, 0)).toBe(0);
  });

  it("returns 0 for value 5 (out-of-range)", () => {
    expect(getPointValue(q, 5)).toBe(0);
  });
});

describe("getPointValue — quaternary_defense, Criterios de Evaluación Divulgativa", () => {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const q: any = makeQuaternaryDefenseQuestion("td-div1", SECTION_DIVULGATIVA);

  it("returns 0.4 for value 1 (Deficiente)", () => {
    expect(getPointValue(q, 1)).toBeCloseTo(0.4, 5);
  });

  it("returns 1.0 for value 2 (Regular)", () => {
    expect(getPointValue(q, 2)).toBeCloseTo(1.0, 5);
  });

  it("returns 1.6 for value 3 (Satisfactorio)", () => {
    expect(getPointValue(q, 3)).toBeCloseTo(1.6, 5);
  });

  it("returns 2.0 for value 4 (Excelente)", () => {
    expect(getPointValue(q, 4)).toBeCloseTo(2.0, 5);
  });

  it("returns 0 for value 0 (out-of-range)", () => {
    expect(getPointValue(q, 0)).toBe(0);
  });

  it("returns 0 for value 5 (out-of-range)", () => {
    expect(getPointValue(q, 5)).toBe(0);
  });
});

describe("getPointValue — quaternary_defense, unknown/missing section", () => {
  it("returns 0 for a question with no section", () => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const q: any = makeQuaternaryDefenseQuestion("td-unknown", undefined);
    expect(getPointValue(q, 4)).toBe(0);
  });

  it("returns 0 for a question with an unrecognised section", () => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const q: any = makeQuaternaryDefenseQuestion("td-other", "Sección Fantasma");
    expect(getPointValue(q, 4)).toBe(0);
  });
});

// ---------------------------------------------------------------------------
// Fixture: 15 TEG defensa questions (10 Técnica + 5 Divulgativa)
// ---------------------------------------------------------------------------

function buildDefensaQuestions(): Question[] {
  const questions: Question[] = [];
  for (let i = 1; i <= 10; i++) {
    questions.push(makeQuaternaryDefenseQuestion(`td-tech${i}`, SECTION_TECNICA));
  }
  for (let i = 1; i <= 5; i++) {
    questions.push(makeQuaternaryDefenseQuestion(`td-div${i}`, SECTION_DIVULGATIVA));
  }
  return questions;
}

const DEFENSA_QUESTIONS = buildDefensaQuestions();

// ---------------------------------------------------------------------------
// calculateTegDefensaScore
// ---------------------------------------------------------------------------

describe("calculateTegDefensaScore", () => {
  it("all Excelente (value 4) → 10×1.0 + 5×2.0 = 20", () => {
    const ratings = Object.fromEntries(DEFENSA_QUESTIONS.map((q) => [q.id, 4]));
    const score = calculateTegDefensaScore(ratings, DEFENSA_QUESTIONS);
    expect(score).toBeCloseTo(20, 5);
  });

  it("all Deficiente (value 1) → 10×0.2 + 5×0.4 = 4", () => {
    const ratings = Object.fromEntries(DEFENSA_QUESTIONS.map((q) => [q.id, 1]));
    const score = calculateTegDefensaScore(ratings, DEFENSA_QUESTIONS);
    expect(score).toBeCloseTo(4, 5);
  });

  it("all Regular (value 2) → 10×0.5 + 5×1.0 = 10", () => {
    const ratings = Object.fromEntries(DEFENSA_QUESTIONS.map((q) => [q.id, 2]));
    const score = calculateTegDefensaScore(ratings, DEFENSA_QUESTIONS);
    expect(score).toBeCloseTo(10, 5);
  });

  it("all Satisfactorio (value 3) → 10×0.8 + 5×1.6 = 16", () => {
    const ratings = Object.fromEntries(DEFENSA_QUESTIONS.map((q) => [q.id, 3]));
    const score = calculateTegDefensaScore(ratings, DEFENSA_QUESTIONS);
    expect(score).toBeCloseTo(16, 5);
  });

  it("mixed: first 5 Técnica=4, last 5 Técnica=1, all Divulgativa=3 → expected breakdown", () => {
    // First 5 Técnica (Excelente=4): 5×1.0 = 5.0
    // Last 5 Técnica (Deficiente=1): 5×0.2 = 1.0
    // All 5 Divulgativa (Satisfactorio=3): 5×1.6 = 8.0
    // Total = 5.0 + 1.0 + 8.0 = 14.0
    const ratings: Record<string, number> = {};
    DEFENSA_QUESTIONS.forEach((q, i) => {
      if (q.section === SECTION_TECNICA) {
        ratings[q.id] = i < 5 ? 4 : 1;
      } else {
        ratings[q.id] = 3;
      }
    });
    const expected = 5 * 1.0 + 5 * 0.2 + 5 * 1.6;
    const score = calculateTegDefensaScore(ratings, DEFENSA_QUESTIONS);
    expect(score).toBeCloseTo(expected, 5);
  });
});

// ---------------------------------------------------------------------------
// getTegDefensaPassStatus
// ---------------------------------------------------------------------------

describe("getTegDefensaPassStatus", () => {
  it("returns 'Fail' for score 13.99", () => {
    expect(getTegDefensaPassStatus(13.99)).toBe("Fail");
  });

  it("returns 'Pass' for score 14", () => {
    expect(getTegDefensaPassStatus(14)).toBe("Pass");
  });

  it("returns 'Pass' for score 14.01", () => {
    expect(getTegDefensaPassStatus(14.01)).toBe("Pass");
  });

  it("returns 'Fail' for score 0", () => {
    expect(getTegDefensaPassStatus(0)).toBe("Fail");
  });

  it("returns 'Pass' for score 20", () => {
    expect(getTegDefensaPassStatus(20)).toBe("Pass");
  });
});

// ---------------------------------------------------------------------------
// calculateTegDefensaSectionScores
// ---------------------------------------------------------------------------

describe("calculateTegDefensaSectionScores", () => {
  it("all Excelente → { total: 20, tecnica: 10, divulgativa: 10 }", () => {
    const ratings = Object.fromEntries(DEFENSA_QUESTIONS.map((q) => [q.id, 4]));
    const result = calculateTegDefensaSectionScores(ratings, DEFENSA_QUESTIONS);
    expect(result.total).toBeCloseTo(20, 5);
    expect(result.tecnica).toBeCloseTo(10, 5);
    expect(result.divulgativa).toBeCloseTo(10, 5);
  });

  it("all Deficiente → { total: 4, tecnica: 2, divulgativa: 2 }", () => {
    const ratings = Object.fromEntries(DEFENSA_QUESTIONS.map((q) => [q.id, 1]));
    const result = calculateTegDefensaSectionScores(ratings, DEFENSA_QUESTIONS);
    // tecnica: 10×0.2 = 2; divulgativa: 5×0.4 = 2; total = 4
    expect(result.total).toBeCloseTo(4, 5);
    expect(result.tecnica).toBeCloseTo(2, 5);
    expect(result.divulgativa).toBeCloseTo(2, 5);
  });

  it("all Regular (value 2) → { total: 10, tecnica: 5, divulgativa: 5 }", () => {
    const ratings = Object.fromEntries(DEFENSA_QUESTIONS.map((q) => [q.id, 2]));
    const result = calculateTegDefensaSectionScores(ratings, DEFENSA_QUESTIONS);
    // tecnica: 10×0.5 = 5; divulgativa: 5×1.0 = 5; total = 10
    expect(result.total).toBeCloseTo(10, 5);
    expect(result.tecnica).toBeCloseTo(5, 5);
    expect(result.divulgativa).toBeCloseTo(5, 5);
  });

  it("mixed half-and-half → expected breakdown", () => {
    // First 5 Técnica = 4 (Excelente): 5×1.0 = 5.0
    // Last 5 Técnica  = 1 (Deficiente): 5×0.2 = 1.0
    // All Divulgativa = 3 (Satisfactorio): 5×1.6 = 8.0
    // total = 14, tecnica = 6, divulgativa = 8
    const ratings: Record<string, number> = {};
    DEFENSA_QUESTIONS.forEach((q, i) => {
      if (q.section === SECTION_TECNICA) {
        ratings[q.id] = i < 5 ? 4 : 1;
      } else {
        ratings[q.id] = 3;
      }
    });
    const result = calculateTegDefensaSectionScores(ratings, DEFENSA_QUESTIONS);
    expect(result.tecnica).toBeCloseTo(6, 5);
    expect(result.divulgativa).toBeCloseTo(8, 5);
    expect(result.total).toBeCloseTo(14, 5);
  });

  it("all Regular (score 10) → getTegDefensaPassStatus returns 'Fail' (10 < 14)", () => {
    const ratings = Object.fromEntries(DEFENSA_QUESTIONS.map((q) => [q.id, 2]));
    const score = calculateTegDefensaScore(ratings, DEFENSA_QUESTIONS);
    expect(getTegDefensaPassStatus(score)).toBe("Fail");
  });

  it("all Satisfactorio (score 16) → getTegDefensaPassStatus returns 'Pass' (16 ≥ 14)", () => {
    const ratings = Object.fromEntries(DEFENSA_QUESTIONS.map((q) => [q.id, 3]));
    const score = calculateTegDefensaScore(ratings, DEFENSA_QUESTIONS);
    expect(getTegDefensaPassStatus(score)).toBe("Pass");
  });
});
