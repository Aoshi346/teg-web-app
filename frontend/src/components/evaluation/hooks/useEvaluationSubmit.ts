import { useCallback } from "react";
import { useRouter } from "next/navigation";
import type { Question } from "@/lib/questions/questions";
import type { Project } from "@/types/project";
import {
  calculateScore,
  calculateSectionScores,
  getPassStatus,
} from "@/lib/questions/scoring";
import {
  createEvaluation,
  updateProject,
} from "@/features/projects/projectService";

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
) {
  const router = useRouter();

  const submit = useCallback(
    async (
      ratings: Ratings,
      comments: string,
      onSuccess: (result: SubmitResult) => void,
      onError: (msg: string) => void,
    ) => {
      // Enforce max attempts for proyectos
      if (
        documentType !== "Tesis" &&
        projectData &&
        (projectData.failedAttempts || 0) >= 2
      ) {
        onError("Este proyecto ya agotó los 2 intentos permitidos.");
        return;
      }

      const score = calculateScore(ratings, questions);
      const passStatus = getPassStatus(score);

      const sectionScores =
        documentType !== "Tesis"
          ? calculateSectionScores(ratings, questions)
          : null;

      // Persist evaluation
      if (projectId) {
        const id = parseInt(projectId);
        if (Number.isNaN(id)) {
          onError("Proyecto inválido para evaluación.");
          return;
        }
        await createEvaluation({
          project: id,
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
      }

      // Update project status
      if (projectData && projectId) {
        const status = (
          passStatus === "Pass" ? "checked" : "rejected"
        ) as "checked" | "rejected";
        const reviewDate = new Date().toISOString().split("T")[0];

        if (documentType === "Tesis") {
          const isStage1 = questions.some((q) => q.id === "q57");
          await updateProject(projectData.id, {
            status,
            review_date: reviewDate,
            stage1_passed:
              isStage1 && passStatus === "Pass"
                ? true
                : (projectData.stage1Passed ?? false),
          });
        } else {
          let failedAttempts = projectData.failedAttempts || 0;
          if (passStatus === "Fail") {
            failedAttempts = Math.min(failedAttempts + 1, 2);
          } else {
            failedAttempts = 0;
          }
          await updateProject(projectData.id, {
            status,
            review_date: reviewDate,
            failed_attempts: failedAttempts,
          });
        }
      }

      onSuccess({ score, passStatus, ratings, comments });

      // Redirect after delay
      setTimeout(() => {
        router.push(
          typeParam === "tesis" ? "/dashboard/tesis" : "/dashboard/proyectos",
        );
      }, 2000);
    },
    [projectId, documentType, typeParam, questions, projectData, router],
  );

  return { submit };
}
