/**
 * Tests for useEvaluationSubmit — Phase C (TEG Entrega wiring).
 *
 * CONTRACT DEPENDENCY (frontend-worker must satisfy):
 *   The hook signature must accept an optional 7th argument `projectState`:
 *     useEvaluationSubmit(projectId, documentType, typeParam, questions, projectData, kind, projectState?)
 *   When (documentType==='Tesis' && kind==='review' && projectState==='pending_entrega'):
 *     - Use calculateTegEntregaScore / getTegEntregaPassStatus / calculateTegEntregaSectionScores
 *     - Pass factibilidad derived from te-s6-1 (value 2=Sí/1=No) and te-s6-2 (2=Sí/1=No)
 *     - createEvaluation receives section_scores with 8 entrega keys
 *   All other combinations keep the existing path (calculateScore / getPassStatus / diagramacion+contenido).
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook } from "@testing-library/react";
import { useEvaluationSubmit } from "../useEvaluationSubmit";
import { TEG_ENTREGA_QUESTIONS } from "@features/evaluations/lib/questions/questions";
import {
  calculateTegEntregaScore,
  getTegEntregaPassStatus,
  calculateTegEntregaSectionScores,
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
