import type { Project, ProjectState, StateOverride } from "@features/projects/types/project";

export type TimelineEventKind =
  | "creation"
  | "evaluation"
  | "override"
  | "assignment"
  | "state-transition";

export type TimelineVariant = "slate" | "amber" | "blue" | "green" | "red";

export interface TimelineEvent {
  id: string;
  kind: TimelineEventKind;
  label: string;
  variant?: TimelineVariant;
  timestamp: string;
  body: string;
  active?: boolean;
}

export interface ProjectEvaluation {
  id: number;
  kind?: "review" | "defense";
  pass_status: "Pass" | "Fail";
  score: number;
  graded_at: string;
  reviewer_name?: string;
}

export interface ProjectWithEvaluations extends Project {
  evaluations?: ProjectEvaluation[];
}

const TERMINAL: ReadonlySet<ProjectState> = new Set(["approved", "failed_final"]);

function evalLabel(e: ProjectEvaluation): string {
  const k = e.kind === "defense" ? "Defensa" : "Revisión";
  return `${k} → ${e.pass_status}`;
}

function evalVariant(e: ProjectEvaluation): TimelineVariant {
  return e.pass_status === "Pass" ? "green" : "red";
}

export function buildStateTimeline(project: ProjectWithEvaluations): TimelineEvent[] {
  const events: TimelineEvent[] = [];

  const evaluations = project.evaluations ?? [];
  for (const e of evaluations) {
    events.push({
      id: `eval-${e.id}`,
      kind: "evaluation",
      label: evalLabel(e),
      variant: evalVariant(e),
      timestamp: e.graded_at,
      body: `${e.reviewer_name ?? "Jurado"} calificó ${e.score.toFixed(1)}/20.`,
    });
  }

  const overrides: StateOverride[] = project.stateOverrides ?? [];
  for (const o of overrides) {
    events.push({
      id: `override-${o.id}`,
      kind: "override",
      label: `Override · Admin`,
      variant: "amber",
      timestamp: o.createdAt,
      body: `${o.adminName} forzó ${o.fromState} → ${o.toState}. Razón: «${o.reason}»`,
    });
  }

  if (project.submittedDate) {
    events.push({
      id: `creation-${project.id}`,
      kind: "creation",
      label: "Creado",
      variant: "slate",
      timestamp: project.submittedDate,
      body: `Estudiante ${project.student} creó el proyecto.`,
    });
  }

  events.sort((a, b) => (a.timestamp < b.timestamp ? 1 : -1));

  if (events.length > 0 && !TERMINAL.has(project.state)) {
    events[0].active = true;
  }

  return events;
}
