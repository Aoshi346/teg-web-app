"use client";

import * as React from "react";
import Link from "next/link";
import { Calendar, ChevronRight, Download, Edit3 } from "lucide-react";

import type { Project, ProjectState, ProjectType } from "@features/projects/types/project";
import { StatePill } from "@features/projects/components/StatePill";
import type { Role } from "@features/projects/lib/cardAction";

const PTEG_LADDER: ProjectState[] = ["pending_review_1", "pending_review_2", "pending_defense", "approved"];
const TEG_LADDER: ProjectState[] = ["pending_articulo", "pending_entrega", "pending_defensa", "approved"];

function ladderFor(type?: ProjectType): ProjectState[] {
  return type === "tesis" ? TEG_LADDER : PTEG_LADDER;
}

const SHORT_LABEL: Record<ProjectState, string> = {
  pending_review_1: "Rev 1",
  pending_review_2: "Rev 2",
  pending_defense:  "Defensa",
  pending_articulo: "Artículo",
  pending_entrega:  "Entrega",
  pending_defensa:  "Defensa",
  approved:         "Aprobado",
  failed_final:     "Reprobado",
};

const STATE_TITLE: Record<ProjectState, string> = {
  pending_review_1: "Pendiente 1ra revisión",
  pending_review_2: "Pendiente 2da revisión",
  pending_defense:  "Pendiente defensa",
  pending_articulo: "Pendiente Artículo",
  pending_entrega:  "Pendiente Entrega",
  pending_defensa:  "Pendiente Defensa",
  approved:         "Aprobado",
  failed_final:     "Reprobado",
};

function indexInLadder(ladder: ProjectState[], state: ProjectState): number {
  if (state === "failed_final") return -1;
  return ladder.indexOf(state);
}

function avatarInitials(name: string): string {
  const parts = name.trim().split(/\s+/);
  return ((parts[0]?.[0] ?? "") + (parts[1]?.[0] ?? "")).toUpperCase().slice(0, 2) || "?";
}

export interface DetailHeroProps {
  project: Project;
  role?: Role;
  viewerId?: number;
  onOverrideClick?: () => void;
  onEditClick?: () => void;
  defenseAt?: string;
  defenseLocation?: string;
  evaluarHref?: string;
  onAssignJuradoClick?: () => void;
  onReassignStudentClick?: () => void;
}

export function DetailHero({
  project,
  role,
  onOverrideClick,
  onEditClick,
  defenseAt,
  defenseLocation,
  evaluarHref,
  onAssignJuradoClick,
  onReassignStudentClick,
}: DetailHeroProps) {
  const ladder = ladderFor(project.type);
  const currentIdx = indexInLadder(ladder, project.state);

  const detailListBase = project.type === "tesis" ? "tesis" : "proyectos";
  const isAdmin = role === "Administrador";
  const isJurado = role === "Jurado";
  const idCode = (project.type === "tesis" ? "TG" : "PT") + "-" + project.period.replace("-", "") + "-" + String(project.id).padStart(3, "0");

  return (
    <>
      <nav
        aria-label="Breadcrumb"
        className="text-[11.5px] text-text-muted font-bold flex items-center gap-2 mb-6"
      >
        <Link href={`/dashboard/${detailListBase}`} className="hover:text-text-strong uppercase tracking-wider transition-colors">
          {project.type === "tesis" ? "Tesis" : "Proyectos"}
        </Link>
        <span>/</span>
        <span className="text-text-strong uppercase tracking-wider truncate max-w-[40ch]">{project.title}</span>
      </nav>

      <section className="dashboard-hero-bg relative overflow-hidden rounded-2xl border border-border-subtle px-8 py-7 mb-6">
        <div className="relative z-10 grid grid-cols-12 gap-10 items-start">
          <div className="col-span-12 lg:col-span-8">
            <div className="flex items-center gap-1.5 text-[10px] font-extrabold uppercase tracking-[0.12em] mb-5 flex-wrap">
              {ladder.map((s, i) => {
                const isPast = currentIdx >= 0 && i < currentIdx;
                const isCurrent = currentIdx >= 0 && i === currentIdx;
                const isFuture = !isPast && !isCurrent;
                return (
                  <React.Fragment key={s}>
                    {isPast && <span className="text-success">{SHORT_LABEL[s]} ✓</span>}
                    {isCurrent && <StatePill state={s} projectType={project.type} />}
                    {isFuture && <span className="text-text-muted opacity-50">{SHORT_LABEL[s]}</span>}
                    {i < ladder.length - 1 && (
                      <ChevronRight className="w-3 h-3 text-text-muted" strokeWidth={2.4} aria-hidden />
                    )}
                  </React.Fragment>
                );
              })}
              {project.state === "failed_final" && (
                <>
                  <ChevronRight className="w-3 h-3 text-text-muted" strokeWidth={2.4} aria-hidden />
                  <StatePill state="failed_final" projectType={project.type} />
                </>
              )}
            </div>

            <p className="flex items-center gap-2 text-[10px] font-extrabold uppercase tracking-[0.14em] text-primary mb-3">
              <span aria-hidden className="inline-block h-[2px] w-6 rounded-full bg-gradient-to-r from-primary to-[var(--brand-orange)]" />
              {project.type === "tesis" ? "Tesis" : "Proyecto"} · {idCode}
            </p>
            <h1 className="text-[44px] leading-[1.05] font-extrabold tracking-[-0.035em] text-text-strong max-w-[24ch]">
              {project.title}
            </h1>

            <div className="mt-7 grid grid-cols-3 gap-6">
              <div>
                <div className="text-[10px] uppercase tracking-[0.12em] text-text-muted font-extrabold">Estudiante</div>
                <div className="mt-2 flex items-center gap-2.5">
                  <div className="av" aria-hidden>{avatarInitials(project.student)}</div>
                  <span className="text-[13px] font-extrabold text-text-strong">{project.student}</span>
                </div>
              </div>
              <div>
                <div className="text-[10px] uppercase tracking-[0.12em] text-text-muted font-extrabold">Tutor</div>
                <div className="mt-2 text-[13px] font-extrabold text-text-strong">
                  {project.advisorNames?.[0] ?? "—"}
                </div>
              </div>
              <div>
                <div className="text-[10px] uppercase tracking-[0.12em] text-text-muted font-extrabold">Jurado</div>
                <div className="mt-2 text-[13px] font-extrabold text-text-strong">
                  {project.reviewerName ?? "—"}
                </div>
              </div>
            </div>
          </div>

          <aside className="col-span-12 lg:col-span-4">
            <div className="rounded-2xl border border-border-subtle bg-surface px-4 py-3 shadow-[0_1px_2px_rgba(12,21,48,0.04)] relative overflow-hidden">
              <span aria-hidden className="absolute inset-x-0 top-0 h-[3px] bg-gradient-to-r from-primary to-[var(--brand-orange)]" />
              <div className="mt-1 flex items-center gap-2">
                <span
                  aria-hidden
                  className="h-2 w-2 rounded-full bg-primary ring-[3px] ring-primary/22"
                />
                <span className="text-[19px] font-extrabold tracking-tight text-text-strong">
                  {STATE_TITLE[project.state]}
                </span>
              </div>

              {defenseAt && (
                <div className="mt-4 mb-4 flex items-center gap-3">
                  <div className="bg-surface-muted border border-border-subtle rounded-xl px-3 py-2 text-center min-w-[52px]">
                    <div className="text-[9px] uppercase tracking-wider text-primary font-extrabold">
                      {new Date(defenseAt).toLocaleDateString("es-VE", { month: "short" })}
                    </div>
                    <div className="text-[22px] leading-none font-extrabold mt-0.5 text-text-strong">
                      {new Date(defenseAt).getDate()}
                    </div>
                  </div>
                  <div>
                    <div className="text-[12.5px] font-extrabold text-text-strong">
                      {new Date(defenseAt).toLocaleTimeString("es-VE", { hour: "2-digit", minute: "2-digit" })}
                      {defenseLocation && ` · ${defenseLocation}`}
                    </div>
                  </div>
                </div>
              )}

              <div className="mt-3 space-y-2">
                {(isAdmin || isJurado) && evaluarHref && (
                  <Link
                    href={evaluarHref}
                    className="w-full justify-center bg-text-strong text-white rounded-xl py-2.5 px-3 text-[12.5px] font-bold flex items-center gap-2 hover:bg-[#0a1424] transition-colors"
                  >
                    <Calendar className="w-3.5 h-3.5" />
                    {project.state === "pending_defense" || project.state === "pending_defensa"
                      ? "Evaluar defensa"
                      : "Evaluar"}
                  </Link>
                )}
                <button className="w-full justify-center bg-surface border border-border-subtle text-text-strong rounded-xl py-2 px-3 text-[12px] font-bold flex items-center gap-2 hover:bg-surface-muted transition-colors">
                  <Download className="w-3.5 h-3.5" />
                  Archivos · {project.files?.length ?? 0}
                </button>
                {onEditClick && (
                  <button
                    onClick={onEditClick}
                    className="w-full text-text-muted hover:text-text-strong text-[11.5px] font-bold uppercase tracking-wider py-1.5 transition-colors flex items-center gap-1 justify-center"
                  >
                    <Edit3 className="w-3 h-3" />
                    Editar
                  </button>
                )}
                {isAdmin && onAssignJuradoClick && (
                  <button
                    onClick={onAssignJuradoClick}
                    className="w-full text-text-muted hover:text-text-strong text-[11.5px] font-bold uppercase tracking-wider py-1.5 transition-colors flex items-center gap-1 justify-center"
                  >
                    Asignar jurado
                  </button>
                )}
                {isAdmin && onReassignStudentClick && project.type !== "tesis" && (
                  <button
                    onClick={onReassignStudentClick}
                    className="w-full text-text-muted hover:text-text-strong text-[11.5px] font-bold uppercase tracking-wider py-1.5 transition-colors flex items-center gap-1 justify-center"
                  >
                    Reasignar estudiante
                  </button>
                )}
                {isAdmin && onOverrideClick && (
                  <button
                    onClick={onOverrideClick}
                    className="w-full text-text-muted hover:text-text-strong text-[11.5px] font-bold uppercase tracking-wider py-1.5 transition-colors flex items-center gap-1 justify-center"
                  >
                    <Edit3 className="w-3 h-3" />
                    Forzar estado
                  </button>
                )}
              </div>
            </div>
          </aside>
        </div>
      </section>
    </>
  );
}
