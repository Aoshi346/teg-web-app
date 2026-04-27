"use client";

import * as React from "react";
import Link from "next/link";
import type { Project, ProjectState } from "@features/projects/types/project";
import { StatePill } from "./StatePill";
import { cardAction, type Role } from "../lib/cardAction";
import { seguimientoColumnsFor, type SeguimientoColumnKey } from "../lib/seguimientoColumns";

const HEADER_LABEL: Record<SeguimientoColumnKey, string> = {
  title:           "Trabajo",
  estudiante:      "Estudiante",
  tutorJurado:     "Tutor / Jurado",
  jurado:          "Jurado",
  estado:          "Estado",
  fase:            "Fase",
  ultimaActividad: "Última actividad",
  recibido:        "Recibido",
  action:          "",
};

const PTEG_STATE_STEP: Partial<Record<ProjectState, number>> = {
  pending_review_1: 0,
  pending_review_2: 1,
  pending_defense:  2,
};

const TEG_STATE_STEP: Partial<Record<ProjectState, number>> = {
  pending_articulo: 0,
  pending_entrega:  1,
  pending_defensa:  2,
};

function getLifecycleStep(project: Project): number {
  if (project.state === "approved") return 3;
  if (project.state === "failed_final") return 2;
  if (project.type === "tesis") {
    return TEG_STATE_STEP[project.state] ?? 0;
  }
  return PTEG_STATE_STEP[project.state] ?? 0;
}

function FaseLadder({ project }: { project: Project }) {
  const step = getLifecycleStep(project);
  const total = 3;
  const label =
    project.state === "approved"
      ? "3/3"
      : project.state === "failed_final"
      ? `${Math.min(step + 1, total)}/${total}`
      : `${step + 1}/${total}`;

  return (
    <div className="ladder">
      {Array.from({ length: total }).map((_, i) => {
        let cls = "step";
        if (project.state === "approved") {
          cls += " done";
        } else if (i < step) {
          cls += " done";
        } else if (i === step) {
          cls += " now";
        }
        return <span key={i} className={cls} />;
      })}
      <span className="lbl">{label}</span>
    </div>
  );
}

function reviewerDisplay(reviewerName: string | null | undefined): React.ReactNode {
  if (!reviewerName) {
    return <span className="seg-sin-asignar">Sin asignar</span>;
  }
  return <span>{reviewerName}</span>;
}

function formatDate(dateStr: string): string {
  if (!dateStr) return "—";
  const d = new Date(dateStr);
  return d.toLocaleDateString("es-VE", { day: "2-digit", month: "short", year: "numeric" });
}

function intentToClass(intent: "primary" | "muted" | "danger"): string {
  if (intent === "primary") return "seg-btn seg-btn-primary";
  if (intent === "danger") return "seg-btn seg-btn-ghost";
  return "seg-btn seg-btn-ghost";
}

export interface SeguimientoTableProps {
  items: Project[];
  role: Role;
  viewerId?: number;
  pagination: {
    currentPage: number;
    totalPages: number;
    onPageChange: (page: number) => void;
  };
}

export default function SeguimientoTable({
  items,
  role,
  viewerId,
  pagination,
}: SeguimientoTableProps) {
  const columns = seguimientoColumnsFor(role).filter((c) => c !== "action");
  const { currentPage, totalPages, onPageChange } = pagination;

  if (items.length === 0) {
    return (
      <div className="seg-table-card">
        <div className="seg-empty">
          <div className="seg-empty-ic">✓</div>
          <p>Todo al día</p>
        </div>
      </div>
    );
  }

  const showColumn = (key: SeguimientoColumnKey) =>
    (columns as readonly SeguimientoColumnKey[]).includes(key);

  return (
    <div className="seg-table-card">
      <div className="seg-cards">
        {items.map((project) => {
          const action = cardAction(role, project, viewerId);
          const isTesis = project.type === "tesis";
          return (
            <article key={project.id} className="seg-card">
              <header className="seg-card-head">
                <span className={`tdot ${isTesis ? "teg" : "pteg"}`} aria-hidden />
                <span className="seg-card-title" title={project.title}>{project.title}</span>
                <span className={`spill ${isTesis ? "teg" : "pteg"}`}>
                  {isTesis ? "TEG" : "PTEG"}
                </span>
              </header>

              <dl className="seg-card-meta">
                {showColumn("estudiante") && (
                  <div className="seg-card-row">
                    <dt>Estudiante</dt>
                    <dd>{project.student}</dd>
                  </div>
                )}
                {showColumn("tutorJurado") && (
                  <>
                    <div className="seg-card-row">
                      <dt>Tutor</dt>
                      <dd>{project.advisorNames?.[0] ?? "—"}</dd>
                    </div>
                    {role !== "Jurado" && (
                      <div className="seg-card-row">
                        <dt>Jurado</dt>
                        <dd>
                          {project.reviewerName ?? (
                            <span className="seg-sin-asignar">Sin asignar</span>
                          )}
                        </dd>
                      </div>
                    )}
                  </>
                )}
                {showColumn("jurado") && (
                  <div className="seg-card-row">
                    <dt>Jurado</dt>
                    <dd>{reviewerDisplay(project.reviewerName)}</dd>
                  </div>
                )}
                {(showColumn("ultimaActividad") || showColumn("recibido")) && (
                  <div className="seg-card-row">
                    <dt>{showColumn("recibido") ? "Recibido" : "Actividad"}</dt>
                    <dd>{formatDate(project.submittedDate)}</dd>
                  </div>
                )}
              </dl>

              <footer className="seg-card-foot">
                <div className="seg-card-state">
                  {showColumn("estado") && (
                    <StatePill state={project.state} projectType={project.type} />
                  )}
                  {showColumn("fase") && <FaseLadder project={project} />}
                </div>
                <Link href={action.href} className={intentToClass(action.intent)}>
                  {action.label}
                </Link>
              </footer>
            </article>
          );
        })}
      </div>

      <div className="seg-table-scroll">
      <table className="seg-table">
        <colgroup>
          {columns.map((col) => (
            <col key={col} className={`seg-col-${col}`} />
          ))}
          <col className="seg-col-action" />
        </colgroup>
        <thead>
          <tr>
            {columns.map((col) => (
              <th key={col} className="seg-th" scope="col">
                {HEADER_LABEL[col]}
              </th>
            ))}
            <th className="seg-th" scope="col" />
          </tr>
        </thead>
        <tbody>
          {items.map((project) => {
            const action = cardAction(role, project, viewerId);
            return (
              <tr key={project.id}>
                {columns.map((col) => (
                  <td key={col} className="seg-td">
                    {col === "title" && (
                      <div className="seg-title-cell">
                        <span
                          className={`tdot ${project.type === "tesis" ? "teg" : "pteg"}`}
                          aria-hidden
                        />
                        <span className="seg-title-name" title={project.title}>{project.title}</span>
                      </div>
                    )}
                    {col === "estudiante" && (
                      <span className="seg-person">{project.student}</span>
                    )}
                    {col === "tutorJurado" && (
                      role === "Jurado" ? (
                        <span className="seg-nm">{project.advisorNames?.[0] ?? "—"}</span>
                      ) : (
                        <div className="seg-person-c">
                          <span className="seg-nm">{project.advisorNames?.[0] ?? "—"}</span>
                          <span className="seg-role">
                            {project.reviewerName
                              ? `Jur. ${project.reviewerName}`
                              : <span className="seg-sin-asignar">Sin asignar</span>}
                          </span>
                        </div>
                      )
                    )}
                    {col === "jurado" && (
                      <span className="seg-person">
                        {reviewerDisplay(project.reviewerName)}
                      </span>
                    )}
                    {col === "estado" && (
                      <StatePill state={project.state} projectType={project.type} />
                    )}
                    {col === "fase" && <FaseLadder project={project} />}
                    {col === "ultimaActividad" && (
                      <span className="seg-date">
                        {formatDate(project.submittedDate)}
                      </span>
                    )}
                    {col === "recibido" && (
                      <span className="seg-date">
                        {formatDate(project.submittedDate)}
                      </span>
                    )}
                  </td>
                ))}
                <td className="seg-td seg-td-action">
                  <Link
                    href={action.href}
                    className={intentToClass(action.intent)}
                  >
                    {action.label}
                  </Link>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
      </div>

      {totalPages > 1 && (
        <div className="seg-pager">
          <button
            type="button"
            className="seg-pn"
            disabled={currentPage <= 1}
            onClick={() => onPageChange(currentPage - 1)}
            aria-label="Anterior"
          >
            Anterior
          </button>
          <div className="seg-pager-pages">
            {Array.from({ length: totalPages }).map((_, i) => (
              <button
                key={i}
                type="button"
                className={`seg-pn ${i + 1 === currentPage ? "cur" : ""}`}
                onClick={() => onPageChange(i + 1)}
                aria-label={`Página ${i + 1}`}
                aria-current={i + 1 === currentPage ? "page" : undefined}
              >
                {i + 1}
              </button>
            ))}
          </div>
          <button
            type="button"
            className="seg-pn"
            disabled={currentPage >= totalPages}
            onClick={() => onPageChange(currentPage + 1)}
            aria-label="Siguiente"
          >
            Siguiente
          </button>
        </div>
      )}
    </div>
  );
}
