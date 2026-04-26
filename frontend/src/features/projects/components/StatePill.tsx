import * as React from "react";
import type { ProjectState, ProjectType } from "@features/projects/types/project";
import { cn } from "@shared/lib/utils";

type Variant = "slate" | "amber" | "blue" | "green" | "red";

const STATE_TO_VARIANT: Record<ProjectState, Variant> = {
  pending_review_1: "slate",
  pending_review_2: "amber",
  pending_defense:  "blue",
  pending_articulo: "slate",
  pending_entrega:  "amber",
  pending_defensa:  "blue",
  approved:         "green",
  failed_final:     "red",
};

const STATE_TO_LABEL: Record<ProjectState, string> = {
  pending_review_1: "Rev 1",
  pending_review_2: "Rev 2",
  pending_defense:  "Defensa",
  pending_articulo: "Artículo",
  pending_entrega:  "Entrega",
  pending_defensa:  "Defensa",
  approved:         "Aprobado",
  failed_final:     "Reprobado",
};

const FEMININE_OVERRIDES: Partial<Record<ProjectState, string>> = {
  approved:     "Aprobada",
  failed_final: "Reprobada",
};

const VARIANT_CLASS: Record<Variant, string> = {
  slate: "spill-slate",
  amber: "spill-amber",
  blue:  "spill-blue",
  green: "spill-green",
  red:   "spill-red",
};

export interface StatePillProps {
  state: ProjectState;
  /** When `tesis`, uses feminine forms ("Aprobada", "Reprobada"). */
  projectType?: ProjectType;
  className?: string;
}

export function StatePill({ state, projectType, className }: StatePillProps) {
  const variant = STATE_TO_VARIANT[state];
  const label =
    projectType === "tesis" && FEMININE_OVERRIDES[state]
      ? (FEMININE_OVERRIDES[state] as string)
      : STATE_TO_LABEL[state];

  return (
    <span className={cn("spill", VARIANT_CLASS[variant], className)} data-state={state}>
      {label}
    </span>
  );
}
