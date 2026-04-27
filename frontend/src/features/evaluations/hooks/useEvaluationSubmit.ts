import { useCallback } from "react";
import { useRouter } from "next/navigation";
import type { Question } from "@features/evaluations/lib/questions/questions";
import type { Project, ProjectState } from "@features/projects/types/project";
import {
  calculateScore,
  calculateSectionScores,
  getPassStatus,
  calculateTegEntregaScore,
  calculateTegEntregaSectionScores,
  getTegEntregaPassStatus,
} from "@features/evaluations/lib/questions/scoring";
import { createEvaluation } from "@features/projects/api/projectService";

type Ratings = Record<string, number | string>;

interface SubmitResult {
  score: number;
  passStatus: "Pass" | "Fail";
  ratings: Ratings;
  comments: string;
}

export function useEvaluationSubmit(
  projectId: string | null | undefined,
  documentType: string,
  typeParam: string,
  questions: Question[],
  projectData: Project | null,
  kind: "review" | "defense" = "review",
  projectState?: ProjectState,
) {
  const router = useRouter();

  const submit = useCallback(
    async (
      ratings: Ratings,
      comments: string,
      onSuccess: (result: SubmitResult) => void,
      onError: (msg: string) => void,
    ) => {
      const isTegEntrega =
        documentType === "Tesis" &&
        kind === "review" &&
        projectState === "pending_entrega";

      let score: number;
      let passStatus: "Pass" | "Fail";
      let sectionScores: Record<string, number> | null;

      if (isTegEntrega) {
        // Derivar factibilidad desde los ratings de te-s6-1 y te-s6-2
        // yesno encoding: 2 = Sí, 1 = No, 0/ausente = null
        const s61 = typeof ratings["te-s6-1"] === "number" ? ratings["te-s6-1"] : Number(ratings["te-s6-1"]) || 0;
        const s62 = typeof ratings["te-s6-2"] === "number" ? ratings["te-s6-2"] : Number(ratings["te-s6-2"]) || 0;

        const isFactible = s61 === 2 ? true : s61 === 1 ? false : false;
        const includesModelo = s62 === 2 ? true : s62 === 1 ? false : false;

        const factibilidad = { isFactible, includesModelo };

        score = calculateTegEntregaScore(ratings, questions, factibilidad);
        passStatus = getTegEntregaPassStatus(score);
        const entregaSections = calculateTegEntregaSectionScores(ratings, questions, factibilidad);
        sectionScores = {
          total: entregaSections.total,
          diagramacion: entregaSections.diagramacion,
          seccion1: entregaSections.seccion1,
          seccion2: entregaSections.seccion2,
          seccion3: entregaSections.seccion3,
          seccion4: entregaSections.seccion4,
          seccion5: entregaSections.seccion5,
          seccion_final: entregaSections.seccion_final,
          seccion6_penalty: entregaSections.seccion6_penalty,
        };
      } else {
        score = calculateScore(ratings, questions);
        passStatus = getPassStatus(score);

        const rawSectionScores =
          documentType !== "Tesis"
            ? calculateSectionScores(ratings, questions)
            : null;

        sectionScores = rawSectionScores
          ? {
              total: rawSectionScores.total,
              diagramacion: rawSectionScores.diagramacion,
              contenido: rawSectionScores.contenido,
            }
          : null;
      }

      // Persist the evaluation. The backend advances Project.state for both
      // PTEG and TEG via api/lifecycle.next_state() — no follow-up PATCH needed.
      if (projectId) {
        const id = parseInt(projectId);
        if (Number.isNaN(id)) {
          onError("Proyecto inválido para evaluación.");
          return;
        }
        try {
          await createEvaluation({
            project: id,
            kind,
            ratings: ratings || {},
            comments: { general: comments || "" },
            score,
            pass_status: passStatus,
            section_scores: sectionScores ?? undefined,
          });
        } catch (err: unknown) {
          const msg =
            err instanceof Error ? err.message : "Error al guardar la evaluación.";
          onError(msg);
          return;
        }
      }

      onSuccess({ score, passStatus, ratings, comments });

      setTimeout(() => {
        router.push(
          typeParam === "tesis" ? "/dashboard/tesis" : "/dashboard/proyectos",
        );
      }, 2000);
    },
    [projectId, documentType, typeParam, questions, projectData, kind, projectState, router],
  );

  return { submit };
}
