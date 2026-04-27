"use client";

import React from "react";
import { useRouter } from "next/navigation";
import type { Question } from "@features/evaluations/lib/questions/questions";
import {
  YESNO_OPTIONS,
  FREQUENCY_OPTIONS,
  TERNARY_OPTIONS,
  TERNARY_NA_OPTIONS,
  TERNARY_INFO_OPTIONS,
} from "@features/evaluations/lib/questions/questions";
import { MAX_SCORE } from "@features/evaluations/lib/questions/scoring";

interface ResultsSummaryProps {
  score: number;
  passStatus: "Pass" | "Fail";
  ratings: Record<string, number | string>;
  comments: string;
  questions: Question[];
  typeParam: string;
  onReset: () => void;
}

function getAnswerLabel(q: Question, val: number | string | undefined): string {
  if (q.answerType === "text") {
    return typeof val === "string" && val.trim() ? val.trim() : "Sin respuesta";
  }
  const n = typeof val === "number" ? val : Number(val) || 0;
  if (n === 0) return "Sin respuesta";

  const maps: Record<string, typeof YESNO_OPTIONS> = {
    yesno: YESNO_OPTIONS,
    frequency: FREQUENCY_OPTIONS,
    ternary: TERNARY_OPTIONS,
    ternary_na: TERNARY_NA_OPTIONS,
    ternary_info: TERNARY_INFO_OPTIONS,
  };
  const opts = maps[q.answerType];
  if (opts) return opts.find((o) => o.value === n)?.label || `${n}`;
  if (q.answerType === "stars") return `${n}/5`;
  return "Sin respuesta";
}

function getAnswerPillClass(q: Question, val: number | string | undefined): string {
  if (q.answerType === "text") {
    return typeof val === "string" && val.trim() ? "success-soft" : "neutral";
  }
  const n = typeof val === "number" ? val : Number(val) || 0;
  if (n === 0) return "neutral";
  if (n >= 2) return "success-soft";
  return "danger-soft";
}

export default function ResultsSummary({
  score,
  passStatus,
  ratings,
  comments,
  questions,
  typeParam,
  onReset,
}: ResultsSummaryProps) {
  const router = useRouter();
  const passed = passStatus === "Pass";

  const pct = MAX_SCORE > 0 ? Math.round((score / MAX_SCORE) * 100) : 0;

  const sections = [...new Set(questions.map((q) => q.section || "General"))];

  return (
    <div className="res-wrap">
      <div className="res-band">
        <div
          className="res-score"
          style={{
            background: `conic-gradient(var(--brand-yellow) 0% ${pct}%, rgba(255,255,255,.18) ${pct}% 100%)`,
          }}
        >
          <span className="res-score-num font-display">{score}</span>
        </div>

        <div className="res-band-info">
          <p className="res-band-eyebrow">Evaluación completada</p>
          <h2 className="res-band-title font-display">
            {typeParam === "tesis" ? "Tesis" : "Proyecto"}
          </h2>
        </div>

        <div className="res-band-status">
          <span className={passed ? "success-soft res-pill" : "danger-soft res-pill"}>
            {passed ? "✓ Aprobado" : "✗ Reprobado"}
          </span>
        </div>
      </div>

      <div className="res-body">
        {sections.map((section, idx) => {
          const sectionQs = questions.filter((q) => (q.section || "General") === section);
          const isDiagramacion = !section.toLowerCase().includes("contenido");
          const sectionClass = isDiagramacion ? "pteg-soft" : "teg-soft";
          const sectionAnswered = sectionQs.filter((q) => {
            const v = ratings[q.id];
            if (q.answerType === "text") return typeof v === "string" && v.trim().length > 0;
            const n = typeof v === "number" ? v : Number(v) || 0;
            return n > 0;
          }).length;

          return (
            <div key={section} className={`res-section ${sectionClass}`}>
              <div className="res-sec-header">
                <span className="res-sec-num font-display">
                  {String(idx + 1).padStart(2, "0")}
                </span>
                <span className="res-sec-label">{section}</span>
                <span className="res-sec-count">{sectionAnswered}/{sectionQs.length}</span>
              </div>

              {sectionQs.map((q) => {
                const answerLabel = getAnswerLabel(q, ratings[q.id]);
                const pillClass = getAnswerPillClass(q, ratings[q.id]);
                return (
                  <div key={q.id} className="res-q">
                    <div className="res-q-info">
                      <span className="res-q-label">{q.label}</span>
                      <span className="res-q-sub">{q.subsection}</span>
                    </div>
                    <span className={`res-q-pill ${pillClass}`}>{answerLabel}</span>
                  </div>
                );
              })}
            </div>
          );
        })}

        {comments && (
          <div className="pending-soft comments-callout">
            <p className="comments-callout-title font-display">Comentarios del evaluador</p>
            <p className="comments-callout-text">{comments}</p>
          </div>
        )}
      </div>

      <div className="res-actions">
        <button
          type="button"
          className="btn cta"
          onClick={() =>
            router.push(
              typeParam === "tesis" ? "/dashboard/tesis" : "/dashboard/proyectos",
            )
          }
        >
          Volver
        </button>
        <button
          type="button"
          className="btn outline"
          onClick={onReset}
        >
          Nueva evaluación
        </button>
        <button
          type="button"
          className="btn ghost"
          aria-disabled="true"
          onClick={(e) => e.preventDefault()}
        >
          Descargar PDF
        </button>
      </div>
    </div>
  );
}
