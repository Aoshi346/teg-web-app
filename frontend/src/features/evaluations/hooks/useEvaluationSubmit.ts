import { useCallback } from "react";
import { useRouter } from "next/navigation";
import type { Question } from "@features/evaluations/lib/questions/questions";
import type { Project } from "@features/projects/types/project";
import {
  calculateScore,
  calculateSectionScores,
  getPassStatus,
} from "@features/evaluations/lib/questions/scoring";
import {
  createEvaluation,
  updateProject,
} from "@features/projects/api/projectService";

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

      // Persist the evaluation. For PTEG the backend updates Project.state
      // (and legacy status) automatically — see api/lifecycle.next_state().
      // TEG keeps its two-phase stage1_passed flow: we still PATCH the
      // project below.
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

      // TEG-only: PATCH stage1_passed + status. PTEG state is already
      // updated server-side by the evaluation POST above.
      if (projectData && projectId && documentType === "Tesis") {
        const isStage1 = questions.some((q) => q.id === "q57");
        const status = (
          passStatus === "Pass" ? "checked" : "rejected"
        ) as "checked" | "rejected";
        const reviewDate = new Date().toISOString().split("T")[0];
        try {
          await updateProject(projectData.id, {
            status,
            review_date: reviewDate,
            stage1_passed:
              isStage1 && passStatus === "Pass"
                ? true
                : (projectData.stage1Passed ?? false),
          });
        } catch (err: unknown) {
          const msg =
            err instanceof Error ? err.message : "Error al actualizar el proyecto.";
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
