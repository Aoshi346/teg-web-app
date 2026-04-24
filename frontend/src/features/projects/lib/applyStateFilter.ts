import type { Project, ProjectState } from "@features/projects/types/project";

const VALID_STATES: readonly ProjectState[] = [
  "pending_review_1",
  "pending_review_2",
  "pending_defense",
  "approved",
  "failed_final",
];

export function readStateFromSearchParams(
  params: URLSearchParams | null,
): ProjectState | null {
  if (!params) return null;
  const raw = params.get("state");
  if (!raw) return null;
  return (VALID_STATES as readonly string[]).includes(raw)
    ? (raw as ProjectState)
    : null;
}

export function applyStateFilter(
  projects: Project[],
  state: ProjectState | null,
): Project[] {
  if (!state) return projects;
  return projects.filter((p) => p.type === "proyecto" && p.state === state);
}
