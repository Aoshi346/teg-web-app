import { useCallback } from "react";
import { useRouter } from "next/navigation";
import type { Question } from "@features/evaluations/lib/questions/questions";
import type { Project } from "@features/projects/types/project";
import {
  calculateScore,
  calculateSectionScores,
  getPassStatus,
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
) {
  const router = useRouter();

  const submit = useCallback(
    async (
      ratings: Ratings,
      comments: string,
      onSuccess: (result: SubmitResult) => void,
      onError: (msg: string) => void,
    ) => {
      const score = calculateScore(ratings, questions);
      const passStatus = getPassStatus(score);

      const sectionScores =
        documentType !== "Tesis"
          ? calculateSectionScores(ratings, questions)
          : null;

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
            section_scores: sectionScores
              ? {
                  total: sectionScores.total,
                  diagramacion: sectionScores.diagramacion,
                  contenido: sectionScores.contenido,
                }
              : undefined,
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
    [projectId, documentType, typeParam, questions, projectData, kind, router],
  );

  return { submit };
}
