"use client";

import * as React from "react";
import { AlertTriangle } from "lucide-react";
import type { Project } from "@features/projects/types/project";
import { StateTimeline } from "@shared/ui/StateTimeline";
import { buildStateTimeline, type ProjectWithEvaluations } from "@features/projects/lib/buildStateTimeline";
import type { DetailEvaluation } from "./EvaluationsTab";
import type { Role } from "@features/projects/lib/cardAction";

export interface HistoryTabProps {
  project: Project;
  evaluations: DetailEvaluation[];
  role: Role;
}

export function HistoryTab({ project, evaluations, role }: HistoryTabProps) {
  const events = React.useMemo(
    () => buildStateTimeline({ ...project, evaluations } as ProjectWithEvaluations),
    [project, evaluations],
  );
  const overrides = role === "Administrador" ? project.stateOverrides ?? [] : [];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-8">
      <div className="space-y-5">
        {overrides.length > 0 && (
          <div className="dsec">
            <div className="dsec-head">
              <h3 className="dsec-title">Overrides administrativos</h3>
              <span className="dsec-count">{overrides.length} {overrides.length === 1 ? "registro" : "registros"}</span>
            </div>
            <div className="space-y-3">
              {overrides.map((o) => (
                <div
                  key={o.id}
                  className="flex gap-3 items-start p-3.5 rounded-lg border"
                  style={{ borderColor: "#fed7aa", background: "#fffbeb" }}
                >
                  <AlertTriangle className="w-[18px] h-[18px] shrink-0 mt-0.5" style={{ color: "var(--pending)" }} />
                  <div className="flex-1">
                    <div className="text-[13px] font-extrabold text-text-strong">
                      {o.adminName} forzó el estado a {o.toState}
                    </div>
                    <div className="text-[11.5px] text-text-muted font-semibold mt-1">
                      {new Date(o.createdAt).toLocaleString("es-VE", {
                        day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit",
                      })}
                    </div>
                    <p className="text-[12.5px] text-text-default font-medium mt-2 leading-relaxed">
                      «{o.reason}»
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="dsec">
          <div className="dsec-head">
            <h3 className="dsec-title">Línea de tiempo · transiciones</h3>
          </div>
          <StateTimeline events={events} />
        </div>
      </div>

      <aside className="space-y-4">
        <div className="dsec">
          <div className="dsec-head">
            <h3 className="dsec-title">Resumen del ciclo</h3>
          </div>
          <dl className="space-y-3 text-[12.5px]">
            <div>
              <dt className="text-[10px] uppercase tracking-wider text-text-muted font-extrabold mb-0.5">Transiciones</dt>
              <dd className="text-text-strong font-extrabold text-[18px]">{events.length}</dd>
            </div>
            {role === "Administrador" && (
              <div>
                <dt className="text-[10px] uppercase tracking-wider text-text-muted font-extrabold mb-0.5">Overrides</dt>
                <dd className="text-text-strong font-extrabold text-[18px]">{overrides.length}</dd>
              </div>
            )}
          </dl>
        </div>
      </aside>
    </div>
  );
}
