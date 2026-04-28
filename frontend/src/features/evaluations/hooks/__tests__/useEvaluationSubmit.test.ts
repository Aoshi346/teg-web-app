/**
 * Tests for useEvaluationSubmit — Phase C (TEG Entrega wiring) + Phase C TEG Defensa.
 *
 * CONTRACT DEPENDENCY (frontend-worker must satisfy):
 *   The hook signature must accept an optional 7th argument `projectState`:
 *     useEvaluationSubmit(projectId, documentType, typeParam, questions, projectData, kind, projectState?)
 *   When (documentType==='Tesis' && kind==='review' && projectState==='pending_entrega'):
 *     - Use calculateTegEntregaScore / getTegEntregaPassStatus / calculateTegEntregaSectionScores
 *     - Pass factibilidad derived from te-s6-1 (value 2=Sí/1=No) and te-s6-2 (2=Sí/1=No)
 *     - createEvaluation receives section_scores with 8 entrega keys
 *   When (documentType==='Tesis' && kind==='defense' && projectState==='pending_defensa'):
 *     - Use calculateTegDefensaScore / getTegDefensaPassStatus / calculateTegDefensaSectionScores
 *     - createEvaluation receives section_scores with 3 keys: total, tecnica, divulgativa
 *     - kind: 'defense' in the payload
 *   All other combinations keep the existing path (calculateScore / getPassStatus / diagramacion+contenido).
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook } from "@testing-library/react";
import { useEvaluationSubmit } from "../useEvaluationSubmit";
import {
  TEG_ENTREGA_QUESTIONS,
  TEG_DEFENSA_QUESTIONS,
} from "@features/evaluations/lib/questions/questions";
import {
  calculateTegEntregaScore,
  getTegEntregaPassStatus,
  calculateTegEntregaSectionScores,
  calculateTegDefensaScore,
  getTegDefensaPassStatus,
} from "@features/evaluations/lib/questions/scoring";
import type { Project } from "@features/projects/types/project";

// ── mocks ────────────────────────────────────────────────────────────────────

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

const mockCreateEvaluation = vi.fn().mockResolvedValue({ id: 1 });
vi.mock("@features/projects/api/projectService", () => ({
  createEvaluation: (...args: unknown[]) => mockCreateEvaluation(...args),
}));

// ── helpers ──────────────────────────────────────────────────────────────────

function makeProject(state: Project["state"]): Project {
  return {
    id: 42,
    title: "Test Tesis",
    student: "Test Student",
    submittedDate: "2026-01-01",
    state,
    period: "2026-01",
    type: "tesis",
  };
}

/**
 * Construye ratings donde todas las preguntas quintary = 5,
 * te-s6-1 y te-s6-2 con los valores pasados como parámetro.
 */
function buildRatings(s61: number, s62: number): Record<string, number> {
  const ratings: Record<string, number> = {};
  for (const q of TEG_ENTREGA_QUESTIONS) {
    if (q.id === "te-s6-1") {
      ratings[q.id] = s61;
    } else if (q.id === "te-s6-2") {
      ratings[q.id] = s62;
    } else {
      ratings[q.id] = 5;
    }
  }
  return ratings;
}

// ── tests ────────────────────────────────────────────────────────────────────

describe("useEvaluationSubmit — TEG Entrega phase", () => {
  const projectId = "42";
  const documentType = "Tesis";
  const typeParam = "tesis";
  const kind = "review" as const;
  const projectState = "pending_entrega" as const;

  beforeEach(() => {
    mockCreateEvaluation.mockClear();
  });

  it("calls createEvaluation with score matching calculateTegEntregaScore (all 5s, no penalty)", async () => {
    const ratings = buildRatings(1, 1); // 6.1=No → no penalty
    const factibilidad = { isFactible: false, includesModelo: false };
    const expectedScore = calculateTegEntregaScore(ratings, TEG_ENTREGA_QUESTIONS, factibilidad);
    const expectedPassStatus = getTegEntregaPassStatus(expectedScore);

    const { result } = renderHook(() =>
      useEvaluationSubmit(
        projectId,
        documentType,
        typeParam,
        TEG_ENTREGA_QUESTIONS,
        makeProject(projectState),
        kind,
        projectState,
      ),
    );

    await result.current.submit(ratings, "test comment", vi.fn(), vi.fn());

    expect(mockCreateEvaluation).toHaveBeenCalledOnce();
    const payload = mockCreateEvaluation.mock.calls[0][0];
    expect(payload.score).toBeCloseTo(expectedScore, 4);
    expect(payload.pass_status).toBe(expectedPassStatus);
    expect(payload.kind).toBe("review");
  });

  it("sends section_scores with all 8 entrega keys", async () => {
    const ratings = buildRatings(1, 1);

    const { result } = renderHook(() =>
      useEvaluationSubmit(
        projectId,
        documentType,
        typeParam,
        TEG_ENTREGA_QUESTIONS,
        makeProject(projectState),
        kind,
        projectState,
      ),
    );

    await result.current.submit(ratings, "", vi.fn(), vi.fn());

    const payload = mockCreateEvaluation.mock.calls[0][0];
    const ss = payload.section_scores;
    expect(ss).toBeDefined();
    expect(ss).toHaveProperty("diagramacion");
    expect(ss).toHaveProperty("seccion1");
    expect(ss).toHaveProperty("seccion2");
    expect(ss).toHaveProperty("seccion3");
    expect(ss).toHaveProperty("seccion4");
    expect(ss).toHaveProperty("seccion5");
    expect(ss).toHaveProperty("seccion_final");
    expect(ss).toHaveProperty("seccion6_penalty");
    expect(ss).toHaveProperty("total");
  });

  it("sends seccion6_penalty === -2 when te-s6-1=Sí (2) and te-s6-2=No (1)", async () => {
    // All quintary=5, 6.1=Sí (2), 6.2=No (1) → penalty -2
    const ratings = buildRatings(2, 1);
    const factibilidad = { isFactible: true, includesModelo: false };
    const expectedSectionScores = calculateTegEntregaSectionScores(
      ratings,
      TEG_ENTREGA_QUESTIONS,
      factibilidad,
    );

    const { result } = renderHook(() =>
      useEvaluationSubmit(
        projectId,
        documentType,
        typeParam,
        TEG_ENTREGA_QUESTIONS,
        makeProject(projectState),
        kind,
        projectState,
      ),
    );

    await result.current.submit(ratings, "", vi.fn(), vi.fn());

    const payload = mockCreateEvaluation.mock.calls[0][0];
    expect(payload.section_scores.seccion6_penalty).toBe(-2);
    expect(payload.section_scores.total).toBeCloseTo(expectedSectionScores.total, 4);
  });

  it("getTegEntregaPassStatus: score >= 14 is Pass, < 14 is Fail", () => {
    expect(getTegEntregaPassStatus(14)).toBe("Pass");
    expect(getTegEntregaPassStatus(13.9999)).toBe("Fail");
    expect(getTegEntregaPassStatus(20)).toBe("Pass");
    expect(getTegEntregaPassStatus(0)).toBe("Fail");
  });
});

describe("useEvaluationSubmit — articulo phase regression (non-entrega)", () => {
  const projectId = "99";
  const documentType = "Tesis";
  const typeParam = "tesis";
  const kind = "review" as const;
  const projectState = "pending_articulo" as const;

  beforeEach(() => {
    mockCreateEvaluation.mockClear();
  });

  it("does NOT include entrega section_scores keys when state is pending_articulo", async () => {
    // Use a minimal tesis question pool (not TEG_ENTREGA_QUESTIONS)
    const minimalQuestion = {
      id: "q1",
      label: "¿Algo?",
      section: "Contenido",
      documentType: "Tesis" as const,
      kind: "review" as const,
      answerType: "yesno" as const,
    };
    const ratings = { q1: 2 };

    const { result } = renderHook(() =>
      useEvaluationSubmit(
        projectId,
        documentType,
        typeParam,
        [minimalQuestion],
        {
          id: 99,
          title: "Test",
          student: "S",
          submittedDate: "2026-01-01",
          state: projectState,
          period: "2026-01",
          type: "tesis",
        },
        kind,
        projectState,
      ),
    );

    await result.current.submit(ratings, "", vi.fn(), vi.fn());

    const payload = mockCreateEvaluation.mock.calls[0][0];
    // For articulo, the existing code sends null or diagramacion+contenido keys,
    // but must NOT send the 8 entrega-specific keys.
    const ss = payload.section_scores;
    if (ss != null) {
      expect(ss).not.toHaveProperty("seccion1");
      expect(ss).not.toHaveProperty("seccion2");
      expect(ss).not.toHaveProperty("seccion3");
      expect(ss).not.toHaveProperty("seccion4");
      expect(ss).not.toHaveProperty("seccion5");
      expect(ss).not.toHaveProperty("seccion_final");
      expect(ss).not.toHaveProperty("seccion6_penalty");
    }
  });
});

// ── TEG Defensa describe block ─────────────────────────────────────────────────

/**
 * Construye ratings donde todas las preguntas de TEG_DEFENSA tienen el valor pasado.
 */
function buildDefensaRatings(value: number): Record<string, number> {
  const ratings: Record<string, number> = {};
  for (const q of TEG_DEFENSA_QUESTIONS) {
    ratings[q.id] = value;
  }
  return ratings;
}

describe("useEvaluationSubmit — TEG Defensa branch", () => {
  const projectId = "7";
  const documentType = "Tesis";
  const typeParam = "tesis";
  const kind = "defense" as const;
  const projectState = "pending_defensa" as const;

  beforeEach(() => {
    mockCreateEvaluation.mockClear();
  });

  it("calls createEvaluation with score matching calculateTegDefensaScore (all Excelente = 4)", async () => {
    const ratings = buildDefensaRatings(4);
    const expectedScore = calculateTegDefensaScore(ratings, TEG_DEFENSA_QUESTIONS);
    const expectedPassStatus = getTegDefensaPassStatus(expectedScore);

    const { result } = renderHook(() =>
      useEvaluationSubmit(
        projectId,
        documentType,
        typeParam,
        TEG_DEFENSA_QUESTIONS,
        makeProject(projectState),
        kind,
        projectState,
      ),
    );

    await result.current.submit(ratings, "defensa comment", vi.fn(), vi.fn());

    expect(mockCreateEvaluation).toHaveBeenCalledOnce();
    const payload = mockCreateEvaluation.mock.calls[0][0];
    expect(payload.score).toBeCloseTo(expectedScore, 4);
    expect(payload.pass_status).toBe(expectedPassStatus);
  });

  it("sends total === 20, tecnica === 10, divulgativa === 10 when all ratings = 4 (Excelente)", async () => {
    // 10 técnica × 1.0 = 10, 5 divulgativa × 2.0 = 10 → total = 20
    const ratings = buildDefensaRatings(4);

    const { result } = renderHook(() =>
      useEvaluationSubmit(
        projectId,
        documentType,
        typeParam,
        TEG_DEFENSA_QUESTIONS,
        makeProject(projectState),
        kind,
        projectState,
      ),
    );

    await result.current.submit(ratings, "", vi.fn(), vi.fn());

    const payload = mockCreateEvaluation.mock.calls[0][0];
    const ss = payload.section_scores;
    expect(ss).toBeDefined();
    expect(ss.total).toBeCloseTo(20, 4);
    expect(ss.tecnica).toBeCloseTo(10, 4);
    expect(ss.divulgativa).toBeCloseTo(10, 4);
    expect(payload.pass_status).toBe("Pass");
  });

  it("sends pass_status === 'Pass' when score >= 14", async () => {
    // All Excelente → score 20 → Pass
    const ratings = buildDefensaRatings(4);

    const { result } = renderHook(() =>
      useEvaluationSubmit(
        projectId,
        documentType,
        typeParam,
        TEG_DEFENSA_QUESTIONS,
        makeProject(projectState),
        kind,
        projectState,
      ),
    );

    await result.current.submit(ratings, "", vi.fn(), vi.fn());

    const payload = mockCreateEvaluation.mock.calls[0][0];
    expect(payload.pass_status).toBe("Pass");
  });

  it("sends pass_status === 'Fail' when score < 14 (all Deficiente = 1 → score 4)", async () => {
    // 10 × 0.2 + 5 × 0.4 = 2 + 2 = 4 → Fail
    const ratings = buildDefensaRatings(1);
    const expectedScore = calculateTegDefensaScore(ratings, TEG_DEFENSA_QUESTIONS);

    const { result } = renderHook(() =>
      useEvaluationSubmit(
        projectId,
        documentType,
        typeParam,
        TEG_DEFENSA_QUESTIONS,
        makeProject(projectState),
        kind,
        projectState,
      ),
    );

    await result.current.submit(ratings, "", vi.fn(), vi.fn());

    const payload = mockCreateEvaluation.mock.calls[0][0];
    expect(payload.score).toBeCloseTo(expectedScore, 4);
    expect(payload.pass_status).toBe("Fail");
  });

  it("sends kind: 'defense' in the payload", async () => {
    const ratings = buildDefensaRatings(4);

    const { result } = renderHook(() =>
      useEvaluationSubmit(
        projectId,
        documentType,
        typeParam,
        TEG_DEFENSA_QUESTIONS,
        makeProject(projectState),
        kind,
        projectState,
      ),
    );

    await result.current.submit(ratings, "", vi.fn(), vi.fn());

    const payload = mockCreateEvaluation.mock.calls[0][0];
    expect(payload.kind).toBe("defense");
  });

  it("sends section_scores with exactly the 3 keys: total, tecnica, divulgativa", async () => {
    const ratings = buildDefensaRatings(3); // Mixed: satisfactorio

    const { result } = renderHook(() =>
      useEvaluationSubmit(
        projectId,
        documentType,
        typeParam,
        TEG_DEFENSA_QUESTIONS,
        makeProject(projectState),
        kind,
        projectState,
      ),
    );

    await result.current.submit(ratings, "", vi.fn(), vi.fn());

    const payload = mockCreateEvaluation.mock.calls[0][0];
    const ss = payload.section_scores;
    expect(ss).toBeDefined();
    expect(ss).toHaveProperty("total");
    expect(ss).toHaveProperty("tecnica");
    expect(ss).toHaveProperty("divulgativa");
    // Must NOT have entrega keys
    expect(ss).not.toHaveProperty("seccion1");
    expect(ss).not.toHaveProperty("seccion6_penalty");
    expect(ss).not.toHaveProperty("diagramacion");
  });
});

// ── Regression: TEG entrega branch still works ────────────────────────────────

describe("useEvaluationSubmit — TEG Entrega regression after defensa branch added", () => {
  const projectId = "42";
  const documentType = "Tesis";
  const typeParam = "tesis";
  const kind = "review" as const;
  const projectState = "pending_entrega" as const;

  beforeEach(() => {
    mockCreateEvaluation.mockClear();
  });

  it("still uses calculateTegEntregaScore and sends 9-key section_scores for pending_entrega", async () => {
    // Minimal ratings: all quintary = 5, both s6 = 1 (No)
    const ratings: Record<string, number> = {};
    for (const q of TEG_ENTREGA_QUESTIONS) {
      ratings[q.id] = q.id === "te-s6-1" || q.id === "te-s6-2" ? 1 : 5;
    }
    const factibilidad = { isFactible: false, includesModelo: false };
    const expectedScore = calculateTegEntregaScore(ratings, TEG_ENTREGA_QUESTIONS, factibilidad);
    const expectedPass = getTegEntregaPassStatus(expectedScore);

    const { result } = renderHook(() =>
      useEvaluationSubmit(
        projectId,
        documentType,
        typeParam,
        TEG_ENTREGA_QUESTIONS,
        makeProject(projectState),
        kind,
        projectState,
      ),
    );

    await result.current.submit(ratings, "", vi.fn(), vi.fn());

    const payload = mockCreateEvaluation.mock.calls[0][0];
    expect(payload.score).toBeCloseTo(expectedScore, 4);
    expect(payload.pass_status).toBe(expectedPass);
    const ss = payload.section_scores;
    expect(ss).toHaveProperty("seccion1");
    expect(ss).toHaveProperty("seccion6_penalty");
    expect(ss).toHaveProperty("total");
    // Must NOT have defensa keys
    expect(ss).not.toHaveProperty("tecnica");
    expect(ss).not.toHaveProperty("divulgativa");
  });
});

// ── Regression: PTEG defensa still uses default scorer ───────────────────────

describe("useEvaluationSubmit — PTEG defensa regression (must NOT use TEG defensa scorer)", () => {
  const projectId = "55";
  const documentType = "Proyecto";  // PTEG, not Tesis
  const typeParam = "proyecto";
  const kind = "defense" as const;
  const projectState = "pending_defense" as const;

  beforeEach(() => {
    mockCreateEvaluation.mockClear();
  });

  it("uses calculateScore (default scorer) for Proyecto + defense, not calculateTegDefensaScore", async () => {
    const minimalQuestion = {
      id: "pd1",
      label: "¿Domina el tema?",
      section: "Criterios de Evaluación Técnica",
      documentType: "Proyecto" as const,
      kind: "defense" as const,
      answerType: "ternary_defense" as const,
    };
    const ratings = { pd1: 3 };

    const { result } = renderHook(() =>
      useEvaluationSubmit(
        projectId,
        documentType,
        typeParam,
        [minimalQuestion],
        {
          id: 55,
          title: "Mi Proyecto",
          student: "Estudiante",
          submittedDate: "2026-01-01",
          state: projectState,
          period: "2026-01",
          type: "proyecto",
        },
        kind,
        projectState,
      ),
    );

    await result.current.submit(ratings, "", vi.fn(), vi.fn());

    const payload = mockCreateEvaluation.mock.calls[0][0];
    // PTEG defensa does NOT produce a 3-key {total, tecnica, divulgativa} section_scores
    // produced by the TEG defensa scorer. It may be null or have the PTEG keys.
    const ss = payload.section_scores;
    if (ss != null) {
      // If section scores are present they should NOT be the TEG defensa shape
      // (i.e. not both tecnica and divulgativa together with total as the only keys)
      const isTegDefensaShape =
        "tecnica" in ss && "divulgativa" in ss && Object.keys(ss).length === 3;
      expect(isTegDefensaShape).toBe(false);
    }
    // score must NOT be 20 (all Excelente TEG shape) — it uses the default scorer
    // which for a single ternary_defense question with value 3 gives a small number
    expect(payload.score).toBeLessThan(20);
  });
});

