"use client";

import React, { useMemo } from "react";
import type { PresentationDay, Presentation } from "../types/planificacion";
import { filterPresentationsForRole } from "../lib/filterForRole";
import { formatDayNumeral, formatWeekday } from "../lib/formatDate";

export interface PlanStudentViewProps {
  days: PresentationDay[];
  loading: boolean;
  viewerEmail: string;
}

/**
 * Retorna el nombre del mes en español (capitalizado) para una fecha YYYY-MM-DD.
 */
function formatSpanishMonth(dateStr: string): string {
  const [y, m, d] = dateStr.split("-").map(Number);
  const date = new Date(y, m - 1, d);
  const month = date.toLocaleDateString("es-VE", { month: "long" });
  return month.charAt(0).toUpperCase() + month.slice(1);
}

interface MyDefCardProps {
  day: PresentationDay;
  presentation: Presentation;
}

function MyDefCard({ day, presentation }: MyDefCardProps) {
  const isTesis = presentation.project_type === "tesis";
  const modalityLabel = isTesis ? "TEG" : "PTEG";
  const modalitySlug = isTesis ? "teg" : "pteg";
  const projectPathBase = isTesis ? "tesis" : "proyectos";

  const firstJurado = presentation.jurado_names[0] ?? "—";
  const remainingJurados = presentation.jurado_names.slice(1);

  return (
    <div className="mydef">
      <div className="mydef-top">
        <div className="mydef-num">
          <span className="m">{formatSpanishMonth(day.date)}</span>
          <span className="d font-display">{formatDayNumeral(day.date)}</span>
          <span className="dow">{formatWeekday(day.date)}</span>
          <span className="yr">{day.date.split("-")[0]}</span>
        </div>
        <div className="mydef-info">
          <p className="mydef-eyebrow">
            {isTesis
              ? "Trabajo Especial de Grado · TEG"
              : "Proyecto de TEG · PTEG"}
          </p>
          <h2>{presentation.project_title}</h2>
          <p>Tu defensa está programada en el período activo.</p>
        </div>
      </div>

      <div className="mydef-meta">
        <div className="field">
          <span className="l">Hora</span>
          <span className="v">{presentation.start_time}</span>
          <span className="vs">Duración {presentation.duration_minutes} min</span>
        </div>
        <div className="field">
          <span className="l">Tutor</span>
          <span className="v">{presentation.tutor_name ?? "—"}</span>
        </div>
        <div className="field">
          <span className="l">
            Jurado ({presentation.jurado.length})
          </span>
          <span className="v">{firstJurado}</span>
          {remainingJurados.length > 0 && (
            <span className="vs">{remainingJurados.join(" · ")}</span>
          )}
        </div>
        <div className="field">
          <span className="l">Modalidad</span>
          <span className="v">
            <span className={`spill ${modalitySlug}`}>{modalityLabel}</span>
          </span>
        </div>
      </div>

      <div className="next-step">
        <div className="what">
          <b>Llega 15 min antes con tu material</b>
          <span>Confirma sala con tu coordinador 24 horas antes.</span>
        </div>
        <div className="flex gap-2">
          <button className="btn ghost">Añadir al calendario</button>
          <a
            className="btn primary"
            href={`/dashboard/${projectPathBase}/${presentation.project}`}
          >
            Ver mi proyecto →
          </a>
        </div>
      </div>
    </div>
  );
}

export default function PlanStudentView({
  days,
  loading,
  viewerEmail,
}: PlanStudentViewProps) {
  const filteredDays = useMemo(
    () =>
      filterPresentationsForRole(days, "Estudiante", { viewerEmail }),
    [days, viewerEmail]
  );

  const myDay = filteredDays[0] ?? null;
  const myPresentation: Presentation | null =
    myDay?.presentations[0] ?? null;
  const hasDefense = myDay !== null && myPresentation !== null;

  const h1Text = hasDefense
    ? "Tu defensa está programada"
    : "Sin defensa programada";
  const lede = hasDefense
    ? "Revisa la fecha, el tribunal y el aula. Llega 15 minutos antes con tu material listo."
    : "Tu coordinador asignará tu fecha y aula cuando completes la fase de revisión. Recibirás un correo cuando esté lista.";

  const pillSummary = hasDefense && myDay && myPresentation
    ? `${myDay.date} · ${myPresentation.start_time} · ${myPresentation.project_type === "tesis" ? "TEG" : "PTEG"}`
    : null;

  return (
    <div>
      {/* ── Hero ── */}
      <section className="dashboard-hero-bg relative overflow-hidden rounded-2xl border border-border-subtle px-7 py-6 mb-6">
        <div className="relative z-10 flex flex-col gap-1.5">
          <p className="hero-eyebrow flex items-center gap-2 text-[10px] font-extrabold uppercase tracking-[0.14em] text-primary">
            <span
              aria-hidden
              className="inline-block h-[2px] w-6 rounded-full bg-gradient-to-r from-primary to-[var(--brand-orange)]"
            />
            Mi defensa
          </p>
          <h1 className="text-3xl font-extrabold leading-tight tracking-[-0.03em] text-text-strong md:text-[34px]">
            {h1Text}
          </h1>
          <p className="max-w-[480px] text-sm font-medium leading-relaxed text-text-muted mt-1">
            {lede}
          </p>
          {pillSummary && (
            <p className="seg-pill-summary">{pillSummary}</p>
          )}
        </div>
      </section>

      {/* ── Body ── */}
      {loading ? (
        <div className="flex justify-center py-12">
          <div className="w-8 h-8 rounded-full border-4 border-border-subtle border-t-primary animate-spin" />
        </div>
      ) : hasDefense && myDay && myPresentation ? (
        <MyDefCard day={myDay} presentation={myPresentation} />
      ) : (
        <div className="empty-card bg-surface border border-border-subtle rounded-2xl p-8 flex flex-col items-center gap-4">
          <div className="ic text-4xl font-display text-text-muted">!</div>
          <h3 className="text-lg font-extrabold text-text-strong">
            Sin defensa programada todavía
          </h3>
          <p className="text-sm text-text-muted text-center max-w-xs">
            Tu coordinador asignará tu fecha y aula cuando completes la fase de revisión.
          </p>
        </div>
      )}
    </div>
  );
}
