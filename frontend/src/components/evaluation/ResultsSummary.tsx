"use client";

import React from "react";
import { useRouter } from "next/navigation";
import { Check, X } from "lucide-react";
import type { Question } from "@/lib/questions/questions";
import {
  YESNO_OPTIONS,
  FREQUENCY_OPTIONS,
  TERNARY_OPTIONS,
  TERNARY_NA_OPTIONS,
  TERNARY_INFO_OPTIONS,
} from "@/lib/questions/questions";
import { MAX_SCORE, PASSING_SCORE } from "@/lib/questions/scoring";

interface ResultsSummaryProps {
  score: number;
  passStatus: "Pass" | "Fail";
  ratings: Record<string, number | string>;
  comments: string;
  questions: Question[];
  typeParam: string;
  onReset: () => void;
}

function getLabel(q: Question, val: number | string | undefined): string {
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

  return (
    <div className="bg-white p-6 sm:p-8 rounded-xl shadow-lg space-y-6">
      <div className="flex items-center gap-3 pb-4 border-b border-gray-200">
        <div
          className={`w-12 h-12 rounded-full flex items-center justify-center ${
            passed ? "bg-green-100" : "bg-red-100"
          }`}
        >
          {passed ? (
            <Check className="w-6 h-6 text-green-600" />
          ) : (
            <X className="w-6 h-6 text-red-600" />
          )}
        </div>
        <div>
          <h3 className="text-xl font-bold text-gray-900">
            Evaluación completada: {passed ? "Aprobado" : "Reprobado"}
          </h3>
          <p className="text-sm text-gray-600 mt-1">
            Puntaje:{" "}
            <strong className={passed ? "text-green-600" : "text-red-600"}>
              {score} / {MAX_SCORE}
            </strong>{" "}
            (Mínimo: {PASSING_SCORE})
          </p>
        </div>
      </div>

      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 space-y-4">
        <h4 className="font-semibold text-gray-700 text-sm">
          Resumen de respuestas
        </h4>
        <div className="bg-white rounded-lg p-3 border border-gray-200 space-y-2 max-h-80 overflow-y-auto">
          {questions.map((q) => (
            <div
              key={q.id}
              className="pb-2 border-b border-gray-100 last:border-0 last:pb-0"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {q.label}
                  </p>
                  <p className="text-[11px] text-gray-400">{q.section}</p>
                </div>
                <span className="text-sm font-semibold text-blue-600 whitespace-nowrap">
                  {getLabel(q, ratings[q.id])}
                </span>
              </div>
            </div>
          ))}
        </div>
        {comments && (
          <div className="bg-white rounded-lg p-3 border border-gray-200">
            <h5 className="text-xs font-semibold text-gray-600 mb-1">
              Comentarios:
            </h5>
            <p className="text-sm text-gray-600 whitespace-pre-wrap">
              {comments}
            </p>
          </div>
        )}
      </div>

      <div className="flex flex-col sm:flex-row gap-3 pt-4">
        <button
          onClick={() =>
            router.push(
              typeParam === "tesis" ? "/dashboard/tesis" : "/dashboard/proyectos",
            )
          }
          className="flex-1 sm:flex-initial bg-blue-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-700 transition-all shadow-sm"
        >
          Volver
        </button>
        <button
          onClick={onReset}
          className="flex-1 sm:flex-initial border-2 border-gray-300 text-gray-700 px-6 py-3 rounded-lg font-medium hover:bg-gray-50 transition-all"
        >
          Nueva evaluación
        </button>
      </div>
    </div>
  );
}
