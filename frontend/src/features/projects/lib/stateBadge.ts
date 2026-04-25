import type { ProjectState } from "@features/projects/types/project";

export type BadgeTone = "amber" | "green" | "red";

const STATE_LABEL: Record<ProjectState, string> = {
  pending_review_1: "Revisión 1",
  pending_review_2: "Revisión 2",
  pending_defense: "Defensa",
  pending_articulo: "Artículo",
  pending_entrega: "Entrega",
  pending_defensa: "Defensa",
  approved: "Aprobado",
  failed_final: "Reprobado",
};

export function stateBadge(state: ProjectState): { tone: BadgeTone; label: string } {
  if (state === "approved") return { tone: "green", label: STATE_LABEL[state] };
  if (state === "failed_final") return { tone: "red", label: STATE_LABEL[state] };
  return { tone: "amber", label: STATE_LABEL[state] };
}
