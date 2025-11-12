"use client";

import React, { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Star } from "lucide-react";
import PageTransition from "@/components/ui/PageTransition";
import DashboardHeader from "@/components/layout/DashboardHeader";

type AnswerType = 'yesno' | 'frequency' | 'stars';

type Question = {
  id: string;
  label: string;
  helper?: string;
  section?: string;
  answerType: AnswerType;
};

const QUESTIONS: Question[] = [
  // Section 1: Presentación y Estructura - Yes/No
  { id: "q1", label: "Claridad de presentación", helper: "¿El proyecto está bien estructurado y presenta sus objetivos claramente?", section: "Presentación y Estructura", answerType: 'yesno' },
  { id: "q2", label: "Organización del contenido", helper: "¿La información está organizada de manera lógica y coherente?", section: "Presentación y Estructura", answerType: 'yesno' },
  { id: "q3", label: "Calidad de la redacción", helper: "¿El lenguaje es claro, preciso y académico?", section: "Presentación y Estructura", answerType: 'yesno' },
  { id: "q4", label: "Formato y presentación visual", helper: "¿El formato es profesional y facilita la lectura?", section: "Presentación y Estructura", answerType: 'yesno' },
  { id: "q5", label: "Consistencia en el estilo", helper: "¿Se mantiene un estilo consistente a lo largo del documento?", section: "Presentación y Estructura", answerType: 'yesno' },
  { id: "q6", label: "Claridad de objetivos", helper: "¿Los objetivos están claramente definidos y son específicos?", section: "Presentación y Estructura", answerType: 'yesno' },
  { id: "q7", label: "Estructura de capítulos", helper: "¿Los capítulos están bien delimitados y conectados?", section: "Presentación y Estructura", answerType: 'yesno' },
  { id: "q8", label: "Resumen ejecutivo", helper: "¿El resumen presenta adecuadamente el contenido del proyecto?", section: "Presentación y Estructura", answerType: 'yesno' },

  // Section 2: Metodología - Frequency
  { id: "q9", label: "Rigor metodológico", helper: "¿La metodología es adecuada y está correctamente aplicada?", section: "Metodología", answerType: 'frequency' },
  { id: "q10", label: "Diseño de investigación", helper: "¿El diseño metodológico es apropiado para los objetivos?", section: "Metodología", answerType: 'frequency' },
  { id: "q11", label: "Técnicas de recolección de datos", helper: "¿Las técnicas utilizadas son válidas y confiables?", section: "Metodología", answerType: 'frequency' },
  { id: "q12", label: "Análisis de datos", helper: "¿Los métodos de análisis son correctos y apropiados?", section: "Metodología", answerType: 'frequency' },
  { id: "q13", label: "Herramientas y software", helper: "¿Se utilizan herramientas adecuadas para el análisis?", section: "Metodología", answerType: 'frequency' },
  { id: "q14", label: "Consideraciones éticas", helper: "¿Se han considerado aspectos éticos en la investigación?", section: "Metodología", answerType: 'frequency' },
  { id: "q15", label: "Limitaciones metodológicas", helper: "¿Se identifican y discuten las limitaciones del método?", section: "Metodología", answerType: 'frequency' },
  { id: "q16", label: "Replicabilidad", helper: "¿El método permite replicar el estudio?", section: "Metodología", answerType: 'frequency' },

  // Section 3: Contenido y Resultados - Stars (5-point scale)
  { id: "q17", label: "Pertinencia del contenido", helper: "¿Los resultados y conclusiones son relevantes y fundamentados?", section: "Contenido y Resultados", answerType: 'stars' },
  { id: "q18", label: "Profundidad del análisis", helper: "¿El análisis es profundo y va más allá de lo superficial?", section: "Contenido y Resultados", answerType: 'stars' },
  { id: "q19", label: "Interpretación de resultados", helper: "¿Los resultados se interpretan correctamente?", section: "Contenido y Resultados", answerType: 'stars' },
  { id: "q20", label: "Conclusiones fundamentadas", helper: "¿Las conclusiones están bien fundamentadas en los datos?", section: "Contenido y Resultados", answerType: 'stars' },
  { id: "q21", label: "Contribución al conocimiento", helper: "¿El trabajo aporta al avance del conocimiento en el área?", section: "Contenido y Resultados", answerType: 'stars' },
  { id: "q22", label: "Aplicabilidad práctica", helper: "¿Los resultados tienen aplicación práctica?", section: "Contenido y Resultados", answerType: 'stars' },
  { id: "q23", label: "Comparación con literatura", helper: "¿Se compara adecuadamente con trabajos previos?", section: "Contenido y Resultados", answerType: 'stars' },
  { id: "q24", label: "Validez de los hallazgos", helper: "¿Los hallazgos son válidos y confiables?", section: "Contenido y Resultados", answerType: 'stars' },

  // Section 4: Originalidad e Innovación - Stars (5-point scale)
  { id: "q25", label: "Originalidad", helper: "¿El trabajo aporta ideas o enfoques novedosos?", section: "Originalidad e Innovación", answerType: 'stars' },
  { id: "q26", label: "Creatividad en la solución", helper: "¿Se demuestra creatividad en la resolución de problemas?", section: "Originalidad e Innovación", answerType: 'stars' },
  { id: "q27", label: "Enfoque innovador", helper: "¿El enfoque utilizado es innovador?", section: "Originalidad e Innovación", answerType: 'stars' },
  { id: "q28", label: "Contribución única", helper: "¿Qué aporta este trabajo que no exista en la literatura?", section: "Originalidad e Innovación", answerType: 'stars' },
  { id: "q29", label: "Impacto potencial", helper: "¿Cuál es el potencial impacto del trabajo?", section: "Originalidad e Innovación", answerType: 'stars' },
  { id: "q30", label: "Avance tecnológico", helper: "¿Incorpora avances tecnológicos relevantes?", section: "Originalidad e Innovación", answerType: 'stars' },
  { id: "q31", label: "Sostenibilidad de la solución", helper: "¿La solución propuesta es sostenible a largo plazo?", section: "Originalidad e Innovación", answerType: 'stars' },
  { id: "q32", label: "Escalabilidad", helper: "¿La solución puede escalarse o generalizarse?", section: "Originalidad e Innovación", answerType: 'stars' },

  // Section 5: Documentación y Calidad - Yes/No
  { id: "q33", label: "Calidad de la documentación", helper: "¿La documentación, referencias y anexos son suficientes y correctos?", section: "Documentación y Calidad", answerType: 'yesno' },
  { id: "q34", label: "Referencias bibliográficas", helper: "¿Las referencias son actuales, relevantes y correctamente citadas?", section: "Documentación y Calidad", answerType: 'yesno' },
  { id: "q35", label: "Anexos y apéndices", helper: "¿Los anexos complementan adecuadamente el contenido?", section: "Documentación y Calidad", answerType: 'yesno' },
  { id: "q36", label: "Corrección ortográfica", helper: "¿El documento está libre de errores ortográficos?", section: "Documentación y Calidad", answerType: 'yesno' },
  { id: "q37", label: "Precisión técnica", helper: "¿Los términos técnicos se usan correctamente?", section: "Documentación y Calidad", answerType: 'yesno' },
  { id: "q38", label: "Calidad de gráficos", helper: "¿Los gráficos, tablas y figuras son claros y profesionales?", section: "Documentación y Calidad", answerType: 'yesno' },
  { id: "q39", label: "Índice y navegación", helper: "¿El índice facilita la navegación por el documento?", section: "Documentación y Calidad", answerType: 'yesno' },
  { id: "q40", label: "Cumplimiento de normas", helper: "¿Se cumplen las normas de presentación requeridas?", section: "Documentación y Calidad", answerType: 'yesno' },
];

const FREQUENCY_OPTIONS = [
  { value: 1, label: 'Muy Poco/Nunca', color: 'bg-red-100 text-red-700 border-red-300' },
  { value: 2, label: 'A veces', color: 'bg-yellow-100 text-yellow-700 border-yellow-300' },
  { value: 3, label: 'Sí/Siempre', color: 'bg-green-100 text-green-700 border-green-300' },
  { value: 4, label: 'No aplica', color: 'bg-gray-100 text-gray-700 border-gray-300' },
];

const YESNO_OPTIONS = [
  { value: 1, label: 'No', color: 'bg-red-100 text-red-700 border-red-300' },
  { value: 2, label: 'Sí', color: 'bg-green-100 text-green-700 border-green-300' },
];

interface EvaluarProps {
  handleSidebarCollapse?: () => void;
  handleMobileSidebarToggle?: () => void;
  isSidebarCollapsed?: boolean;
  isMobileSidebarOpen?: boolean;
}

type SubmittedData = {
  ratings: Record<string, number>;
  comments: string;
  gradedAt: string;
} | null;

export default function EvaluarProyectoPage({
  // layout passthrough (optional)
  handleSidebarCollapse,
  handleMobileSidebarToggle,
  isSidebarCollapsed,
  isMobileSidebarOpen,
}: EvaluarProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const projectId = searchParams?.get("projectId");
  const [ratings, setRatings] = useState<Record<string, number>>(() => {
    const r: Record<string, number> = {};
    for (const q of QUESTIONS) r[q.id] = 0;
    return r;
  });
  // Pagination for long forms: show more questions per page on wide screens
  const PAGE_SIZE = 8;
  const totalPages = Math.max(1, Math.ceil(QUESTIONS.length / PAGE_SIZE));
  const [page, setPage] = useState<number>(1);
  const [comments, setComments] = useState<string>("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submittedData, setSubmittedData] = useState<SubmittedData>(null);

  const setRating = (qid: string, value: number) => {
    setRatings((prev) => ({ ...prev, [qid]: value }));
  };

  const getAnswerLabel = (question: Question, value: number): string => {
    if (value === 0) return 'Sin respuesta';
    
    switch (question.answerType) {
      case 'yesno':
        const yesNoOption = YESNO_OPTIONS.find(opt => opt.value === value);
        return yesNoOption?.label || 'Sin respuesta';
      case 'frequency':
        const freqOption = FREQUENCY_OPTIONS.find(opt => opt.value === value);
        return freqOption?.label || 'Sin respuesta';
      case 'stars':
        return `${value} de 5 estrellas`;
      default:
        return 'Sin respuesta';
    }
  };

  const renderAnswerInput = (question: Question) => {
    const currentRating = ratings[question.id] || 0;

    switch (question.answerType) {
      case 'yesno':
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
                    : 'bg-white text-gray-600 border-gray-200 hover:border-gray-300 hover:shadow-sm'
                }`}
              >
                {option.label}
              </button>
            ))}
          </div>
        );

      case 'frequency':
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
                    : 'bg-white text-gray-600 border-gray-200 hover:border-gray-300 hover:shadow-sm'
                }`}
              >
                {option.label}
              </button>
            ))}
          </div>
        );

      case 'stars':
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
                        ? 'text-yellow-500 scale-110' 
                        : 'text-gray-300 hover:text-yellow-400 hover:scale-105'
                    }`}
                  >
                    <Star className={`w-6 h-6 sm:w-7 sm:h-7 ${isSelected ? 'fill-current' : ''}`} />
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
    // Simple validation: ensure all ratings provided
    const missingIndex = QUESTIONS.findIndex((q) => !ratings[q.id] || ratings[q.id] <= 0);
    if (missingIndex !== -1) {
      // Move to the page that contains the first missing answer so the user can complete it
      const missingPage = Math.floor(missingIndex / PAGE_SIZE) + 1;
      setPage(missingPage);
      alert("Por favor califique todas las preguntas antes de enviar. Se le redirigirá a la pregunta incompleta.");
      setIsSubmitting(false);
      return;
    }

    // For now, store locally and show summary. Replace with API call as needed.
    const payload = {
      ratings,
      comments,
      gradedAt: new Date().toISOString(),
    };

    // Simulate network delay
    await new Promise((res) => setTimeout(res, 600));
    setSubmittedData(payload);
    setIsSubmitting(false);
  };

  return (
    <>
      <DashboardHeader
        pageTitle="Evaluar Proyecto"
        isSidebarCollapsed={isSidebarCollapsed}
        isMobileSidebarOpen={isMobileSidebarOpen}
        onMobileSidebarToggle={handleMobileSidebarToggle}
        onSidebarCollapse={handleSidebarCollapse}
      />

      <PageTransition>
        <main className="flex-1 p-4 sm:p-6 lg:p-8 overflow-y-auto bg-gray-50">
          <div className="max-w-7xl mx-auto">
            <div className="mb-6">
              <h2 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-2">
                Evaluación del Proyecto {projectId ? `#${projectId}` : ''}
              </h2>
              {projectId && (
                <p className="text-sm text-gray-600 mb-2">
                  Calificando proyecto con id <strong className="text-blue-600">{projectId}</strong>
                </p>
              )}
              <p className="text-sm sm:text-base text-gray-600">
                Complete la evaluación respondiendo las <strong>{QUESTIONS.length} preguntas</strong> organizadas en{' '}
                <strong>{[...new Set(QUESTIONS.map(q => q.section))].length} secciones</strong>.
                Use el sistema de calificación de 1-5 estrellas.
              </p>
            </div>

            {!submittedData ? (
              <form onSubmit={handleSubmit} className="bg-white p-4 sm:p-6 lg:p-8 rounded-xl shadow-lg">
                <div className="flex flex-col gap-6 lg:grid lg:grid-cols-[minmax(0,1fr)_300px] xl:grid-cols-[minmax(0,1fr)_340px] lg:gap-8">
                  <div className="space-y-6 min-w-0">
                    {/* Progress / Page selector */}
                    <div className="space-y-3">
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-2">
                        <div className="text-sm text-gray-600 font-medium">
                          Página {page} de {totalPages}
                          <span className="hidden sm:inline">
                            {(() => {
                              const pageQuestions = QUESTIONS.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);
                              const sectionsInPage = [...new Set(pageQuestions.map(q => q.section))];
                              return sectionsInPage.length > 0 ? ` - ${sectionsInPage.join(', ')}` : '';
                            })()}
                          </span>
                        </div>
                        <div className="flex items-center gap-1.5 sm:gap-2 flex-wrap">
                          {Array.from({ length: totalPages }).map((_, idx) => {
                            const p = idx + 1;
                            const pageQuestions = QUESTIONS.slice((p - 1) * PAGE_SIZE, p * PAGE_SIZE);
                            const sectionsInPage = [...new Set(pageQuestions.map(q => q.section))];
                            const sectionAbbrev = sectionsInPage.length > 0 ? sectionsInPage[0]?.split(' ')[0] : '';
                            return (
                              <button
                                key={p}
                                type="button"
                                onClick={() => setPage(p)}
                                aria-current={p === page}
                                title={`Página ${p}: ${sectionsInPage.join(', ')}`}
                                className={`min-w-[2rem] h-8 px-2 rounded-lg text-xs sm:text-sm font-medium inline-flex items-center justify-center transition-all ${
                                  p === page 
                                    ? 'bg-blue-600 text-white shadow-md' 
                                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200 hover:shadow-sm'
                                }`}
                              >
                                {sectionAbbrev || p}
                              </button>
                            );
                          })}
                        </div>
                      </div>
                      <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
                        <div 
                          className="h-2 bg-blue-600 rounded-full transition-all duration-300" 
                          style={{ width: `${Math.round((page / totalPages) * 100)}%` }} 
                        />
                      </div>
                      <div className="text-xs text-gray-500">
                        Preguntas {((page - 1) * PAGE_SIZE) + 1}-{Math.min(page * PAGE_SIZE, QUESTIONS.length)} de {QUESTIONS.length}
                      </div>
                    </div>

                    {/* Questions for current page */}
                    <div className="space-y-6">
                      {(() => {
                        const pageQuestions = QUESTIONS.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);
                        const sectionsInPage = [...new Set(pageQuestions.map(q => q.section))];

                        return sectionsInPage.map(section => {
                          const sectionQuestions = pageQuestions.filter(q => q.section === section);
                          return (
                            <div key={section} className="space-y-4">
                              <div className="bg-gradient-to-r from-blue-50 to-transparent border-l-4 border-blue-600 pl-4 pr-4 py-3 rounded-r-lg">
                                <h3 className="text-lg sm:text-xl font-bold text-gray-900">{section}</h3>
                                <p className="text-sm text-gray-600 mt-1">
                                  {sectionQuestions.length} pregunta{sectionQuestions.length !== 1 ? 's' : ''} en esta sección
                                </p>
                              </div>
                              <div className="grid gap-4 sm:grid-cols-1 lg:grid-cols-2">
                                {sectionQuestions.map((q) => (
                                  <div key={q.id} className="border border-gray-200 rounded-xl p-4 bg-white shadow-sm hover:shadow-md transition-all">
                                    <div className="space-y-3">
                                      <div>
                                        <h4 className="font-semibold text-sm sm:text-base text-gray-900">{q.label}</h4>
                                        {q.helper && <p className="text-xs text-gray-600 mt-1.5 leading-relaxed">{q.helper}</p>}
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
                      <label className="block text-sm font-semibold text-gray-700 mb-2">Comentarios adicionales (opcional)</label>
                      <textarea
                        value={comments}
                        onChange={(e) => setComments(e.target.value)}
                        rows={4}
                        className="w-full border border-gray-300 rounded-lg p-3 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all resize-none"
                        placeholder="Agregue observaciones generales sobre el proyecto..."
                      />
                    </div>

                    <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 pt-4 border-t border-gray-200">
                      <div className="flex items-center gap-2">
                        <button
                          type="button"
                          onClick={() => setPage((p) => Math.max(1, p - 1))}
                          disabled={page === 1}
                          className="flex-1 sm:flex-initial px-4 py-2.5 rounded-lg bg-gray-100 text-sm font-medium text-gray-700 hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                        >
                          ← Anterior
                        </button>
                        {page < totalPages ? (
                          <button
                            type="button"
                            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                            className="flex-1 sm:flex-initial px-4 py-2.5 rounded-lg bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 transition-all shadow-sm"
                          >
                            Siguiente →
                          </button>
                        ) : (
                          <button
                            type="submit"
                            disabled={isSubmitting}
                            className="flex-1 sm:flex-initial inline-flex items-center justify-center gap-2 bg-green-600 text-white px-6 py-2.5 rounded-lg font-medium hover:bg-green-700 disabled:opacity-60 disabled:cursor-not-allowed transition-all shadow-md hover:shadow-lg"
                          >
                            {isSubmitting ? (
                              <>
                                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"/>
                                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
                                </svg>
                                Enviando...
                              </>
                            ) : (
                              '✓ Enviar evaluación'
                            )}
                          </button>
                        )}
                      </div>

                      <button
                        type="button"
                        onClick={() => router.back()}
                        className="text-sm text-gray-600 hover:text-gray-800 hover:underline font-medium transition-colors"
                      >
                        Cancelar
                      </button>
                    </div>
                  </div>

                  <aside className="hidden lg:flex flex-col gap-4 sticky top-4 self-start">
                    <div className="rounded-xl border-2 border-dashed border-gray-300 bg-gradient-to-br from-gray-50 to-blue-50 p-6 text-center">
                      <div className="aspect-video mb-3 flex items-center justify-center rounded-lg bg-gradient-to-br from-blue-100 via-white to-blue-50 text-gray-400 shadow-inner">
                        <div className="text-center">
                          <svg className="w-12 h-12 mx-auto mb-2 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                          </svg>
                          <p className="text-sm font-medium text-gray-500">Guía visual</p>
                        </div>
                      </div>
                      <p className="text-sm text-gray-600">Espacio reservado para una imagen de referencia o instrucciones para el evaluador.</p>
                    </div>
                    <div className="rounded-xl border border-gray-200 p-4 bg-white shadow-sm">
                      <h4 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
                        <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
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
                          <span>Puede navegar entre páginas sin perder sus respuestas.</span>
                        </li>
                        <li className="flex items-start gap-2">
                          <span className="text-blue-600 mt-0.5">•</span>
                          <span>Use &ldquo;No aplica&rdquo; cuando la pregunta no sea relevante.</span>
                        </li>
                        <li className="flex items-start gap-2">
                          <span className="text-blue-600 mt-0.5">•</span>
                          <span>Las 5 estrellas se reservan para trabajos excepcionales.</span>
                        </li>
                      </ul>
                    </div>
                  </aside>
                </div>
              </form>
            ) : (
              <div className="bg-white p-6 sm:p-8 rounded-xl shadow-lg space-y-6">
                <div className="flex items-center gap-3 pb-4 border-b border-gray-200">
                  <div className="w-12 h-12 rounded-full bg-green-100 flex items-center justify-center">
                    <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-gray-900">Evaluación enviada exitosamente</h3>
                    <p className="text-sm text-gray-600 mt-1">
                      La evaluación se ha registrado localmente (demo). Reemplace con su API para guardar en el servidor.
                    </p>
                  </div>
                </div>
                
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 space-y-4">
                  <h4 className="font-semibold text-gray-700 mb-3 flex items-center gap-2">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
                    </svg>
                    Resumen de respuestas
                  </h4>
                  <div className="bg-white rounded-lg p-4 border border-gray-200 space-y-3 max-h-96 overflow-y-auto">
                    {QUESTIONS.map((q) => (
                      <div key={q.id} className="pb-3 border-b border-gray-100 last:border-0 last:pb-0">
                        <div className="flex items-start justify-between gap-3">
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-gray-900">{q.label}</p>
                            <p className="text-xs text-gray-500 mt-0.5">{q.section}</p>
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
                      <h5 className="text-sm font-semibold text-gray-700 mb-2">Comentarios adicionales:</h5>
                      <p className="text-sm text-gray-600 whitespace-pre-wrap">{comments}</p>
                    </div>
                  )}
                </div>
                
                <div className="flex flex-col sm:flex-row gap-3 pt-4">
                  <button 
                    onClick={() => router.push('/dashboard/proyectos')} 
                    className="flex-1 sm:flex-initial bg-blue-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-700 transition-all shadow-sm hover:shadow-md"
                  >
                    ← Volver a Proyectos
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
          </div>
        </main>
      </PageTransition>
    </>
  );
}
