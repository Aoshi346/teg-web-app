"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { Star } from "lucide-react";
import {
  FREQUENCY_OPTIONS,
  YESNO_OPTIONS,
  Question,
} from "@/lib/questions/questions";
import {
  calculateScore,
  getPassStatus,
  MAX_SCORE,
  PASSING_SCORE,
} from "@/lib/questions/scoring";

interface EvaluationFormProps {
  projectId?: string | null;
  typeParam?: string; // 'proyecto' | 'tesis'
  questions: Question[]; // required question set to evaluate
}

type SubmittedData = {
  ratings: Record<string, number>;
  comments: string;
  gradedAt: string;
  score: number;
  passStatus: "Pass" | "Fail";
} | null;

export default function EvaluationForm({
  projectId,
  typeParam = "proyecto",
  questions,
}: EvaluationFormProps) {
  const router = useRouter();
  const documentType =
    (typeParam || "proyecto").toLowerCase() === "tesis" ? "Tesis" : "Proyecto";
  const sourceQuestions = questions;
  const filteredQuestions = sourceQuestions.filter(
    (q) =>
      !q.documentType ||
      q.documentType === "Both" ||
      q.documentType === documentType
  );

  const [ratings, setRatings] = useState<Record<string, number>>(() => {
    const r: Record<string, number> = {};
    for (const q of filteredQuestions) r[q.id] = 0;
    return r;
  });

  const PAGE_SIZE = 8;
  const totalPages = Math.max(
    1,
    Math.ceil(filteredQuestions.length / PAGE_SIZE)
  );
  const [page, setPage] = useState<number>(1);
  const [comments, setComments] = useState<string>("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submittedData, setSubmittedData] = useState<SubmittedData>(null);

  const setRating = (qid: string, value: number) => {
    setRatings((prev) => ({ ...prev, [qid]: value }));
  };

  const getAnswerLabel = (question: Question, value: number): string => {
    if (value === 0) return "Sin respuesta";
    switch (question.answerType) {
      case "yesno":
        const yesNoOption = YESNO_OPTIONS.find((opt) => opt.value === value);
        return yesNoOption?.label || "Sin respuesta";
      case "frequency":
        const freqOption = FREQUENCY_OPTIONS.find((opt) => opt.value === value);
        return freqOption?.label || "Sin respuesta";
      case "stars":
        return `${value} de 5 estrellas`;
      default:
        return "Sin respuesta";
    }
  };

  const renderAnswerInput = (question: Question) => {
    const currentRating = ratings[question.id] || 0;

    switch (question.answerType) {
      case "yesno":
        return (
          <div className="flex items-center justify-center gap-2 pt-2">
            {YESNO_OPTIONS.map((option) => (
              <button
                key={option.value}
                type="button"
                onClick={() => setRating(question.id, option.value)}
                className={`flex-1 px-4 py-3 rounded-lg text-sm font-semibold border-2 transition-all ${
                  currentRating === option.value
                    ? `${option.color} shadow-md scale-105`
                    : "bg-white text-gray-600 border-gray-200 hover:border-gray-300 hover:shadow-sm"
                }`}
              >
                {option.label}
              </button>
            ))}
          </div>
        );

      case "frequency":
        return (
          <div className="space-y-2 pt-2">
            {FREQUENCY_OPTIONS.map((option) => (
              <button
                key={option.value}
                type="button"
                onClick={() => setRating(question.id, option.value)}
                className={`w-full px-4 py-2.5 rounded-lg text-sm font-medium border-2 transition-all text-left ${
                  currentRating === option.value
                    ? `${option.color} shadow-md`
                    : "bg-white text-gray-600 border-gray-200 hover:border-gray-300 hover:shadow-sm"
                }`}
              >
                {option.label}
              </button>
            ))}
          </div>
        );

      case "stars":
        return (
          <>
            <div className="flex items-center justify-center gap-1 pt-2 border-t border-gray-100">
              {Array.from({ length: 5 }).map((_, i) => {
                const val = i + 1;
                const isSelected = currentRating >= val;
                return (
                  <button
                    key={val}
                    type="button"
                    onClick={() => setRating(question.id, val)}
                    aria-label={`${val} estrellas`}
                    className={`p-2 rounded-lg transition-all ${
                      isSelected
                        ? "text-yellow-500 scale-110"
                        : "text-gray-300 hover:text-yellow-400 hover:scale-105"
                    }`}
                  >
                    <Star
                      className={`w-6 h-6 sm:w-7 sm:h-7 ${
                        isSelected ? "fill-current" : ""
                      }`}
                    />
                  </button>
                );
              })}
            </div>
            {currentRating > 0 && (
              <div className="text-center mt-2">
                <span className="inline-block px-3 py-1 bg-blue-50 text-blue-700 text-xs font-semibold rounded-full">
                  {currentRating} de 5 estrellas
                </span>
              </div>
            )}
          </>
        );

      default:
        return null;
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    const missingIndex = filteredQuestions.findIndex(
      (q) => !ratings[q.id] || ratings[q.id] <= 0
    );
    if (missingIndex !== -1) {
      const missingPage = Math.floor(missingIndex / PAGE_SIZE) + 1;
      setPage(missingPage);
      alert(
        "Por favor califique todas las preguntas antes de enviar. Se le redirigirá a la pregunta incompleta."
      );
      setIsSubmitting(false);
      return;
    }

    const score = calculateScore(ratings, filteredQuestions);
    const passStatus = getPassStatus(score);

    const payload: SubmittedData = {
      ratings,
      comments,
      gradedAt: new Date().toISOString(),
      score,
      passStatus,
    };

    // Demo: If this is Tesis Stage 1 (inferred by question ID q57), update session storage
    if (
      documentType === "Tesis" &&
      projectId &&
      filteredQuestions.some((q) => q.id === "q57")
    ) {
      if (passStatus === "Pass") {
        sessionStorage.setItem(`project_${projectId}_stage1_passed`, "true");
      }
    }

    await new Promise((res) => setTimeout(res, 600));
    setSubmittedData(payload);
    setIsSubmitting(false);
  };

  const allSections = [
    ...new Set(filteredQuestions.map((q) => q.section).filter(Boolean)),
  ] as string[];
  const pageQuestions = filteredQuestions.slice(
    (page - 1) * PAGE_SIZE,
    page * PAGE_SIZE
  );
  const sectionsInPage = [...new Set(pageQuestions.map((q) => q.section))];
  const currentSection =
    sectionsInPage.length > 0 ? sectionsInPage[0] : undefined;
  const subsectionsOfCurrent = currentSection
    ? [
        ...new Set(
          filteredQuestions
            .filter((q) => q.section === currentSection)
            .map((q) => q.subsection)
        ),
      ]
    : [];

  const getPageForSection = (section?: string) => {
    if (!section) return 1;
    const idx = filteredQuestions.findIndex((q) => q.section === section);
    return Math.max(1, Math.floor(idx / PAGE_SIZE) + 1);
  };

  const getPageForSubsection = (sub?: string) => {
    if (!sub) return 1;
    const idx = filteredQuestions.findIndex((q) => q.subsection === sub);
    return Math.max(1, Math.floor(idx / PAGE_SIZE) + 1);
  };

  return (
    <>
      <div className="mb-6">
        <h2 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-2">
          Evaluación del {documentType} {projectId ? `#${projectId}` : ""}
        </h2>
        {projectId && (
          <p className="text-sm text-gray-600 mb-2">
            Calificando {documentType.toLowerCase()} con id{" "}
            <strong className="text-blue-600">{projectId}</strong>
          </p>
        )}
        <p className="text-sm sm:text-base text-gray-600">
          Complete la evaluación respondiendo las{" "}
          <strong>{filteredQuestions.length} preguntas</strong> organizadas en{" "}
          <strong>
            {[...new Set(filteredQuestions.map((q) => q.section))].length}{" "}
            secciones
          </strong>
          . Las preguntas utilizan diferentes escalas: Sí/No, frecuencia, y
          estrellas (1-5).
        </p>
      </div>

      {!submittedData ? (
        <form
          onSubmit={handleSubmit}
          className="bg-white p-4 sm:p-6 lg:p-8 rounded-xl shadow-lg"
        >
          {/* ... form content ... */}
          <div className="flex flex-col gap-6 lg:grid lg:grid-cols-[minmax(0,1fr)_300px] xl:grid-cols-[minmax(0,1fr)_340px] lg:gap-8">
            <div className="space-y-6 min-w-0">
              <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl border border-blue-100 p-4 shadow-sm">
                <div className="mb-4">
                  <label className="text-xs font-semibold text-gray-700 uppercase tracking-wide mb-2 block">
                    Secciones
                  </label>
                  <div className="flex gap-2 overflow-x-auto pb-1">
                    {allSections.map((s) => {
                      const pageForSection = getPageForSection(s as string);
                      const count = filteredQuestions.filter(
                        (q) => q.section === s
                      ).length;
                      const isActive = currentSection === s;
                      return (
                        <button
                          key={s}
                          type="button"
                          onClick={() => setPage(pageForSection)}
                          className={`flex-shrink-0 px-4 py-2.5 rounded-lg font-medium text-sm transition-all ${
                            isActive
                              ? "bg-blue-600 text-white shadow-md"
                              : "bg-white text-gray-700 hover:bg-blue-50 border border-gray-200"
                          }`}
                        >
                          <div className="flex items-center gap-2">
                            <span>{s}</span>
                            <span
                              className={`text-xs px-2 py-0.5 rounded-full ${
                                isActive
                                  ? "bg-blue-500 text-white"
                                  : "bg-gray-100 text-gray-600"
                              }`}
                            >
                              {count}
                            </span>
                          </div>
                        </button>
                      );
                    })}
                  </div>
                </div>

                {subsectionsOfCurrent.length > 0 && (
                  <div>
                    <label className="text-xs font-semibold text-gray-700 uppercase tracking-wide mb-2 block">
                      Subsecciones de {currentSection}
                    </label>
                    <div className="flex flex-wrap gap-2">
                      {subsectionsOfCurrent.map((sub) => {
                        const subPage = getPageForSubsection(String(sub));
                        const isCurrentSubPage = subPage === page;
                        return (
                          <button
                            key={String(sub)}
                            type="button"
                            onClick={() => setPage(subPage)}
                            className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                              isCurrentSubPage
                                ? "bg-blue-600 text-white"
                                : "bg-white text-gray-700 hover:bg-blue-50 border border-gray-200"
                            }`}
                          >
                            {sub}
                          </button>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>

              <div className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-3">
                  <div className="text-sm font-medium text-gray-700">
                    <span className="text-blue-600 font-bold">
                      Página {page}
                    </span>{" "}
                    de {totalPages}
                  </div>
                  <div className="text-xs text-gray-500">
                    Preguntas {(page - 1) * PAGE_SIZE + 1}-
                    {Math.min(page * PAGE_SIZE, filteredQuestions.length)} de{" "}
                    {filteredQuestions.length}
                  </div>
                </div>

                <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden mb-4">
                  <div
                    className="h-2 bg-gradient-to-r from-blue-500 to-indigo-600 rounded-full transition-all duration-300"
                    style={{
                      width: `${Math.round((page / totalPages) * 100)}%`,
                    }}
                  />
                </div>

                <div className="flex items-center justify-center gap-1.5 flex-wrap">
                  {Array.from({ length: totalPages }).map((_, idx) => {
                    const p = idx + 1;
                    return (
                      <button
                        key={p}
                        type="button"
                        onClick={() => setPage(p)}
                        className={`min-w-[2.5rem] h-10 px-3 rounded-lg font-semibold text-sm transition-all ${
                          p === page
                            ? "bg-blue-600 text-white shadow-md scale-105"
                            : "bg-gray-50 text-gray-700 hover:bg-gray-100 border border-gray-200"
                        }`}
                      >
                        {p}
                      </button>
                    );
                  })}
                </div>
              </div>

              <div className="space-y-6">
                {(() => {
                  const pageQuestions = filteredQuestions.slice(
                    (page - 1) * PAGE_SIZE,
                    page * PAGE_SIZE
                  );
                  const sectionsInPage = [
                    ...new Set(pageQuestions.map((q) => q.section)),
                  ];

                  return sectionsInPage.map((section) => {
                    const sectionQuestions = pageQuestions.filter(
                      (q) => q.section === section
                    );
                    return (
                      <div key={section} className="space-y-4">
                        <div className="bg-gradient-to-r from-blue-50 to-transparent border-l-4 border-blue-600 pl-4 pr-4 py-3 rounded-r-lg">
                          <h3 className="text-lg sm:text-xl font-bold text-gray-900">
                            {section}
                          </h3>
                          <p className="text-sm text-gray-600 mt-1">
                            {sectionQuestions.length} pregunta
                            {sectionQuestions.length !== 1 ? "s" : ""} en esta
                            sección
                          </p>
                        </div>
                        <div className="grid gap-4 sm:grid-cols-1 lg:grid-cols-2">
                          {sectionQuestions.map((q) => (
                            <div
                              key={q.id}
                              className="border border-gray-200 rounded-xl p-4 bg-white shadow-sm hover:shadow-md transition-all"
                            >
                              <div className="space-y-3">
                                <div>
                                  <h4 className="font-semibold text-sm sm:text-base text-gray-900">
                                    {q.label}
                                  </h4>
                                  {q.helper && (
                                    <p className="text-xs text-gray-600 mt-1.5 leading-relaxed">
                                      {q.helper}
                                    </p>
                                  )}
                                </div>
                                {renderAnswerInput(q)}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    );
                  });
                })()}
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Comentarios adicionales (opcional)
                </label>
                <textarea
                  value={comments}
                  onChange={(e) => setComments(e.target.value)}
                  rows={4}
                  className="w-full border border-gray-300 rounded-lg p-3 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all resize-none"
                  placeholder={`Agregue observaciones generales sobre el ${documentType.toLowerCase()}...`}
                />
              </div>

              <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 pt-4 border-t border-gray-200">
                <div className="flex items-center gap-3 flex-1">
                  <button
                    type="button"
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page === 1}
                    className="flex items-center justify-center gap-2 px-5 py-3 rounded-lg bg-white border-2 border-gray-300 text-sm font-semibold text-gray-700 hover:bg-gray-50 hover:border-gray-400 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
                  >
                    <svg
                      className="w-4 h-4"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M15 19l-7-7 7-7"
                      />
                    </svg>
                    Anterior
                  </button>
                  {page < totalPages ? (
                    <button
                      type="button"
                      onClick={() =>
                        setPage((p) => Math.min(totalPages, p + 1))
                      }
                      className="flex items-center justify-center gap-2 px-5 py-3 rounded-lg bg-blue-600 text-white text-sm font-semibold hover:bg-blue-700 transition-all shadow-sm hover:shadow-md"
                    >
                      Siguiente
                      <svg
                        className="w-4 h-4"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M9 5l7 7-7 7"
                        />
                      </svg>
                    </button>
                  ) : (
                    <button
                      type="submit"
                      disabled={isSubmitting}
                      className="flex items-center justify-center gap-2 bg-green-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-green-700 disabled:opacity-60 disabled:cursor-not-allowed transition-all shadow-md hover:shadow-lg"
                    >
                      {isSubmitting ? (
                        <>
                          <svg
                            className="animate-spin h-5 w-5"
                            viewBox="0 0 24 24"
                          >
                            <circle
                              className="opacity-25"
                              cx="12"
                              cy="12"
                              r="10"
                              stroke="currentColor"
                              strokeWidth="4"
                              fill="none"
                            />
                            <path
                              className="opacity-75"
                              fill="currentColor"
                              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                            />
                          </svg>
                          Enviando...
                        </>
                      ) : (
                        <>
                          <svg
                            className="w-5 h-5"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M5 13l4 4L19 7"
                            />
                          </svg>
                          Enviar evaluación
                        </>
                      )}
                    </button>
                  )}
                </div>

                <button
                  type="button"
                  onClick={() => router.back()}
                  className="text-sm text-gray-600 hover:text-gray-900 font-medium transition-colors px-3 py-2"
                >
                  Cancelar
                </button>
              </div>
            </div>

            <aside className="hidden lg:flex flex-col gap-4 sticky top-4 self-start">
              <div className="rounded-xl border-2 border-dashed border-gray-300 bg-gradient-to-br from-gray-50 to-blue-50 p-6 text-center">
                <div className="aspect-video mb-3 flex items-center justify-center rounded-lg bg-gradient-to-br from-blue-100 via-white to-blue-50 text-gray-400 shadow-inner">
                  <div className="text-center">
                    <svg
                      className="w-12 h-12 mx-auto mb-2 opacity-50"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
                      />
                    </svg>
                    <p className="text-sm font-medium text-gray-500">
                      Guía visual
                    </p>
                  </div>
                </div>
                <p className="text-sm text-gray-600">
                  Espacio reservado para una imagen de referencia o
                  instrucciones para el evaluador.
                </p>
              </div>
              <div className="rounded-xl border border-gray-200 p-4 bg-white shadow-sm">
                <h4 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
                  <svg
                    className="w-5 h-5 text-blue-600"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </svg>
                  Sugerencias
                </h4>
                <ul className="space-y-2 text-sm text-gray-700">
                  <li className="flex items-start gap-2">
                    <span className="text-blue-600 mt-0.5">•</span>
                    <span>Revise todos los criterios antes de enviar.</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-blue-600 mt-0.5">•</span>
                    <span>
                      Puede navegar entre páginas sin perder sus respuestas.
                    </span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-blue-600 mt-0.5">•</span>
                    <span>
                      Use &ldquo;No aplica&rdquo; cuando la pregunta no sea
                      relevante.
                    </span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-blue-600 mt-0.5">•</span>
                    <span>
                      Las 5 estrellas se reservan para trabajos excepcionales.
                    </span>
                  </li>
                </ul>
              </div>
            </aside>
          </div>
        </form>
      ) : (
        <div className="bg-white p-6 sm:p-8 rounded-xl shadow-lg space-y-6">
          <div className="flex items-center gap-3 pb-4 border-b border-gray-200">
            <div
              className={`w-12 h-12 rounded-full flex items-center justify-center ${
                submittedData.passStatus === "Pass"
                  ? "bg-green-100"
                  : "bg-red-100"
              }`}
            >
              {submittedData.passStatus === "Pass" ? (
                <svg
                  className="w-6 h-6 text-green-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M5 13l4 4L19 7"
                  />
                </svg>
              ) : (
                <svg
                  className="w-6 h-6 text-red-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              )}
            </div>
            <div>
              <h3 className="text-xl font-bold text-gray-900">
                Evaluación completada:{" "}
                {submittedData.passStatus === "Pass" ? "Aprobado" : "Reprobado"}
              </h3>
              <p className="text-sm text-gray-600 mt-1">
                Puntaje obtenido:{" "}
                <strong
                  className={
                    submittedData.passStatus === "Pass"
                      ? "text-green-600"
                      : "text-red-600"
                  }
                >
                  {submittedData.score} / {MAX_SCORE}
                </strong>{" "}
                (Mínimo requerido: {PASSING_SCORE})
              </p>
            </div>
          </div>

          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 space-y-4">
            <h4 className="font-semibold text-gray-700 mb-3 flex items-center gap-2">
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01"
                />
              </svg>
              Resumen de respuestas
            </h4>
            <div className="bg-white rounded-lg p-4 border border-gray-200 space-y-3 max-h-96 overflow-y-auto">
              {filteredQuestions.map((q) => (
                <div
                  key={q.id}
                  className="pb-3 border-b border-gray-100 last:border-0 last:pb-0"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900">
                        {q.label}
                      </p>
                      <p className="text-xs text-gray-500 mt-0.5">
                        {q.section}
                      </p>
                    </div>
                    <span className="text-sm font-semibold text-blue-600 whitespace-nowrap">
                      {getAnswerLabel(q, ratings[q.id] || 0)}
                    </span>
                  </div>
                </div>
              ))}
            </div>
            {comments && (
              <div className="bg-white rounded-lg p-4 border border-gray-200">
                <h5 className="text-sm font-semibold text-gray-700 mb-2">
                  Comentarios adicionales:
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
                  typeParam === "tesis"
                    ? "/dashboard/tesis/evaluar"
                    : "/dashboard/proyectos"
                )
              }
              className="flex-1 sm:flex-initial bg-blue-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-700 transition-all shadow-sm hover:shadow-md"
            >
              ← Volver
            </button>
            <button
              onClick={() => setSubmittedData(null)}
              className="flex-1 sm:flex-initial border-2 border-gray-300 text-gray-700 px-6 py-3 rounded-lg font-medium hover:bg-gray-50 transition-all"
            >
              Nueva evaluación
            </button>
          </div>
        </div>
      )}
    </>
  );
}
