"use client";

import * as React from "react";
import { ScoreGauge } from "@shared/ui/ScoreGauge";
import { StatePill } from "@features/projects/components/StatePill";

export interface DetailEvaluation {
  id: number;
  kind?: "review" | "defense";
  pass_status: "Pass" | "Fail";
  score: number;
  graded_at: string;
  reviewer_name?: string;
  comments?: { general?: string } | string;
  section_scores?: { diagramacion?: number; contenido?: number; total?: number };
}

function avatarInitials(name: string): string {
  const parts = name.trim().split(/\s+/);
  return ((parts[0]?.[0] ?? "") + (parts[1]?.[0] ?? "")).toUpperCase().slice(0, 2) || "?";
}

function meanScore(evals: DetailEvaluation[]): number {
  if (evals.length === 0) return 0;
  const sum = evals.reduce((s, e) => s + e.score, 0);
  return sum / evals.length;
}

function meanSection(evals: DetailEvaluation[], key: "diagramacion" | "contenido"): number {
  const values = evals.map((e) => e.section_scores?.[key]).filter((v): v is number => v != null);
  if (values.length === 0) return 0;
  return values.reduce((a, b) => a + b, 0) / values.length;
}

function getCommentsBody(c: DetailEvaluation["comments"]): string {
  if (!c) return "";
  if (typeof c === "string") return c;
  return c.general ?? "";
}

export interface EvaluationsTabProps {
  evaluations: DetailEvaluation[];
}

export function EvaluationsTab({ evaluations }: EvaluationsTabProps) {
  const sorted = [...evaluations].sort((a, b) => (a.graded_at < b.graded_at ? 1 : -1));
  const avg = meanScore(sorted);
  const diag = meanSection(sorted, "diagramacion");
  const cont = meanSection(sorted, "contenido");

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-8">
      <div className="space-y-5">
        {sorted.length === 0 ? (
          <div className="dsec text-center py-10">
            <p className="text-[13.5px] text-text-muted font-medium">Sin evaluaciones todavía.</p>
          </div>
        ) : (
          <>
            <div className="dsec">
              <div className="dsec-head">
                <h3 className="dsec-title">Promedio acumulado</h3>
                <span className="dsec-count">{sorted.length} {sorted.length === 1 ? "evaluación" : "evaluaciones"}</span>
              </div>
              <div className="flex items-center gap-8 flex-wrap">
                <div className="flex items-center gap-4">
                  <ScoreGauge score={avg} tone="success" size="lg" />
                  <div>
                    <div className="text-[10px] uppercase tracking-wider text-text-muted font-extrabold">Promedio</div>
                    <div className="text-[28px] font-black tracking-tight text-text-strong leading-none mt-1">
                      {avg.toFixed(1)} / 20
                    </div>
                  </div>
                </div>
                <div className="h-16 w-px bg-border-subtle hidden md:block" />
                <div className="flex-1 min-w-[200px] space-y-3">
                  <ScoreBar label="Diagramación" value={diag} max={5} />
                  <ScoreBar label="Contenido" value={cont} max={15} />
                </div>
              </div>
            </div>

            <div className="dsec">
              <div className="dsec-head">
                <h3 className="dsec-title">Línea de evaluaciones</h3>
              </div>
              <div className="space-y-3">
                {sorted.map((e) => (
                  <EvalCard key={e.id} evaluation={e} />
                ))}
              </div>
            </div>
          </>
        )}
      </div>

      <aside className="space-y-4">
        <div className="dsec">
          <div className="dsec-head">
            <h3 className="dsec-title">Distribución</h3>
          </div>
          <p className="text-[11.5px] text-text-muted font-medium leading-relaxed">
            Las evaluaciones se calculan como promedio simple de todas las revisiones.
            La nota mínima aprobatoria es <strong className="text-text-strong">10/20</strong>.
          </p>
        </div>
      </aside>
    </div>
  );
}

function ScoreBar({ label, value, max }: { label: string; value: number; max: number }) {
  const pct = max === 0 ? 0 : Math.max(0, Math.min(100, (value / max) * 100));
  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <span className="text-[11.5px] font-bold text-text-strong">{label}</span>
        <span className="text-[11.5px] font-extrabold text-text-strong">
          {value.toFixed(1)} <span className="text-text-muted font-medium">/ {max}</span>
        </span>
      </div>
      <div className="h-1.5 rounded-full bg-border-subtle relative overflow-hidden">
        <span
          className="absolute inset-y-0 left-0 rounded-full"
          style={{ width: `${pct}%`, background: "linear-gradient(90deg, var(--primary), #6ba3ff)" }}
        />
      </div>
    </div>
  );
}

function EvalCard({ evaluation: e }: { evaluation: DetailEvaluation }) {
  const body = getCommentsBody(e.comments);
  return (
    <div className="rounded-xl border border-border-subtle p-4">
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-3 flex-1 min-w-0">
          <div className="av" aria-hidden>{avatarInitials(e.reviewer_name ?? "?")}</div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-[13.5px] font-extrabold text-text-strong">{e.reviewer_name ?? "Jurado"}</span>
              <StatePill state={e.pass_status === "Pass" ? "approved" : "failed_final"} />
              <span className="text-[10px] uppercase tracking-wider font-extrabold text-text-muted">
                {e.kind === "defense" ? "Defensa" : "Revisión"}
              </span>
            </div>
            <div className="text-[12px] text-text-muted font-semibold mt-1">
              {new Date(e.graded_at).toLocaleString("es-VE", {
                day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit",
              })}
            </div>
            {body && (
              <p className="text-[13px] text-text-default font-medium mt-3 leading-relaxed">
                «{body}»
              </p>
            )}
          </div>
        </div>
        <div className="text-right shrink-0">
          <div className="text-[28px] font-black text-success leading-none tracking-tight">
            {e.score.toFixed(1)}
          </div>
          <div className="text-[10px] uppercase tracking-wider font-extrabold text-text-muted mt-1">/ 20</div>
        </div>
      </div>
    </div>
  );
}
