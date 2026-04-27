"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowRight } from "lucide-react";

import { cn } from "@shared/lib/utils";
import type { Project, ProjectState, ProjectType } from "@features/projects/types/project";
import { StatePill } from "@features/projects/components/StatePill";
import { ScoreGauge } from "@shared/ui/ScoreGauge";
import { cardAction, type Role } from "@features/projects/lib/cardAction";

const STATE_TO_EDGE: Record<ProjectState, string> = {
  pending_review_1: "pcard-slate",
  pending_review_2: "pcard-amber",
  pending_defense:  "pcard-blue",
  pending_articulo: "pcard-slate",
  pending_entrega:  "pcard-amber",
  pending_defensa:  "pcard-blue",
  approved:         "pcard-green",
  failed_final:     "pcard-red",
};

const TEG_PHASE_INDEX: Partial<Record<ProjectState, 0 | 1 | 2>> = {
  pending_articulo: 0,
  pending_entrega:  1,
  pending_defensa:  2,
};

const INTENT_TO_PACT: Record<"primary" | "muted" | "danger", string> = {
  primary: "pact-primary",
  muted:   "pact-muted",
  danger:  "pact-danger",
};

function fctxFor(project: Project): { label: string; tone: "muted" | "pending" | "primary" | "success" | "danger" } | null {
  if (project.state === "approved") {
    return { label: "Defendido", tone: "success" };
  }
  if (project.state === "failed_final") {
    return { label: "Sin más intentos", tone: "danger" };
  }
  if (project.state === "pending_review_2") {
    return { label: "Último intento", tone: "pending" };
  }
  if (project.state === "pending_defense" || project.state === "pending_defensa") {
    return { label: "En defensa", tone: "primary" };
  }
  if (project.type === "tesis") {
    const idx = TEG_PHASE_INDEX[project.state];
    if (idx != null) return { label: `Fase ${idx + 1} de 3`, tone: "muted" };
  }
  if (project.submittedDate) {
    const d = new Date(project.submittedDate);
    return { label: d.toLocaleDateString("es-VE", { day: "2-digit", month: "short" }), tone: "muted" };
  }
  return null;
}

function avatarInitials(name: string): string {
  const parts = name.trim().split(/\s+/);
  return ((parts[0]?.[0] ?? "") + (parts[1]?.[0] ?? "")).toUpperCase().slice(0, 2) || "?";
}

export interface ProjectCardProps {
  project: Project;
  role?: Role;
  viewerId?: number;
  primaryLabel?: string;
  primaryHref?: string;
  /** Legacy prop. Retained for backwards compatibility; no longer rendered. */
  canEdit?: boolean;
  /** Legacy prop. Retained for backwards compatibility; project type comes from `project.type`. */
  type?: ProjectType;
  className?: string;
}

export default function ProjectCard({
  project,
  role,
  viewerId,
  primaryLabel,
  primaryHref,
  className,
}: ProjectCardProps) {
  const router = useRouter();
  const action = role
    ? cardAction(role, project, viewerId)
    : {
        label: primaryLabel ?? "Ver detalles",
        intent: "muted" as const,
        href: primaryHref ?? `/dashboard/proyectos/${project.id}`,
      };

  const phaseIdx = project.type === "tesis" ? TEG_PHASE_INDEX[project.state] : undefined;
  const ctx = fctxFor(project);
  const tutor = project.advisorNames?.[0] ?? null;

  const detailHref =
    project.type === "tesis"
      ? `/dashboard/tesis/${project.id}`
      : `/dashboard/proyectos/${project.id}`;
  const actionIsDetail = action.href === detailHref;

  return (
    <Link
      href={detailHref}
      aria-label={`Ver detalles: ${project.title}`}
      className="block focus:outline-none focus-visible:ring-2 focus-visible:ring-primary rounded-[16px]"
    >
      <article
        className={cn("pcard", STATE_TO_EDGE[project.state], className)}
        data-state={project.state}
        data-project-id={project.id}
      >
        <div className="flex items-start justify-between gap-2">
          <StatePill state={project.state} projectType={project.type} />
          {project.state === "approved" && project.score != null && (
            <ScoreGauge score={project.score} tone="success" />
          )}
        </div>

        <h3
          className="mt-3 text-[15px] font-extrabold leading-snug tracking-[-0.012em] text-text-strong title-clamp-2"
          title={project.title}
        >
          {project.title}
        </h3>

        {project.type === "tesis" && phaseIdx != null && (
          <div className="tegbar mt-3" aria-hidden>
            {[0, 1, 2].map((i) => (
              <span
                key={i}
                className={cn(i < phaseIdx ? "is-passed" : i === phaseIdx ? "is-active" : "")}
              />
            ))}
          </div>
        )}

        <div className="mt-3 flex items-center gap-2.5 text-[12px]">
          <div className="av" aria-hidden>{avatarInitials(project.student)}</div>
          <div className="flex-1 min-w-0">
            <span className="font-bold text-text-strong">{project.student}</span>
            {tutor && (
              <>
                <span className="text-text-faint mx-1">·</span>
                <span className="text-text-muted font-semibold">{tutor}</span>
              </>
            )}
          </div>
        </div>

        <div className="pcard-foot">
          {ctx ? (
            <span className={cn("fctx", `fctx-${ctx.tone}`)}>{ctx.label}</span>
          ) : (
            <span />
          )}
          {actionIsDetail ? (
            <span className={cn("pact", INTENT_TO_PACT[action.intent])}>
              {action.label}
              <ArrowRight className="w-3 h-3" strokeWidth={2.6} />
            </span>
          ) : (
            <button
              type="button"
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                router.push(action.href);
              }}
              aria-label={`${action.label}: ${project.title}`}
              className={cn("pact", INTENT_TO_PACT[action.intent], "focus:outline-none focus-visible:ring-2 focus-visible:ring-primary rounded-md")}
            >
              {action.label}
              <ArrowRight className="w-3 h-3" strokeWidth={2.6} />
            </button>
          )}
        </div>
      </article>
    </Link>
  );
}
