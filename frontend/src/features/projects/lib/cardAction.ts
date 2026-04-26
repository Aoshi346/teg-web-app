import type { Project, ProjectState } from "@features/projects/types/project";

export type Role = "Administrador" | "Estudiante" | "Tutor" | "Jurado";
export type Intent = "primary" | "muted" | "danger";

export interface CardAction {
  label: string;
  intent: Intent;
  href: string;
}

const TEG_PHASE_PATH: Partial<Record<ProjectState, string>> = {
  pending_articulo: "articulo",
  pending_entrega:  "entrega",
  pending_defensa:  "defensa",
};

const TEG_PHASE_VERB: Partial<Record<ProjectState, string>> = {
  pending_articulo: "Revisar artículo",
  pending_entrega:  "Revisar entrega",
  pending_defensa:  "Evaluar defensa",
};

function detailHref(p: Project): string {
  const base = p.type === "tesis" ? "tesis" : "proyectos";
  return `/dashboard/${base}/${p.id}`;
}

function evaluarHref(p: Project): string {
  if (p.type === "tesis") {
    const phase = TEG_PHASE_PATH[p.state];
    return phase ? `/dashboard/tesis/${p.id}/evaluar/${phase}` : `/dashboard/tesis/${p.id}/evaluar`;
  }
  return `/dashboard/proyectos/${p.id}/evaluar`;
}

export function cardAction(role: Role, project: Project, viewerId?: number): CardAction {
  // Terminal states: same label for everyone.
  if (project.state === "approved") {
    return { label: "Ver evaluación", intent: "muted", href: detailHref(project) };
  }
  if (project.state === "failed_final") {
    return { label: "Ver motivo", intent: "danger", href: detailHref(project) };
  }

  // Active states. Action depends on role + project type.
  const isAdmin = role === "Administrador";
  const isAssignedJurado =
    role === "Jurado" && (viewerId == null || project.reviewer === viewerId);

  const canAct = isAdmin || isAssignedJurado;

  if (!canAct) {
    return { label: "Ver detalles", intent: "muted", href: detailHref(project) };
  }

  // Primary actor (Admin or assigned Jurado).
  if (project.type === "tesis") {
    const verb = TEG_PHASE_VERB[project.state] ?? "Evaluar";
    return { label: verb, intent: "primary", href: evaluarHref(project) };
  }
  // PTEG.
  if (project.state === "pending_defense") {
    return { label: "Evaluar defensa", intent: "primary", href: evaluarHref(project) };
  }
  return { label: "Revisar", intent: "primary", href: evaluarHref(project) };
}
