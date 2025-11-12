"use client";

import React, { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Star } from "lucide-react";
import PageTransition from "@/components/ui/PageTransition";
import DashboardHeader from "@/components/layout/DashboardHeader";

type Question = {
  id: string;
  label: string;
  helper?: string;
};

const QUESTIONS: Question[] = [
  { id: "q1", label: "Claridad de presentación", helper: "¿El proyecto está bien estructurado y presenta sus objetivos claramente?" },
  { id: "q2", label: "Rigor metodológico", helper: "¿La metodología es adecuada y está correctamente aplicada?" },
  { id: "q3", label: "Pertinencia del contenido", helper: "¿Los resultados y conclusiones son relevantes y fundamentados?" },
  { id: "q4", label: "Originalidad", helper: "¿El trabajo aporta ideas o enfoques novedosos?" },
  { id: "q5", label: "Calidad de la documentación", helper: "¿La documentación, referencias y anexos son suficientes y correctos?" },
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
          <div className="max-w-6xl mx-auto">
            <h2 className="text-2xl font-bold mb-2">Evaluación del Proyecto {projectId ? `#${projectId}` : ''}</h2>
            {projectId && <p className="text-sm text-gray-600 mb-2">Calificando proyecto con id <strong>{projectId}</strong></p>}
            <p className="text-sm text-gray-600 mb-6">Complete la evaluación respondiendo las preguntas y agregue un comentario final si lo desea.</p>

            {!submittedData ? (
              <form onSubmit={handleSubmit} className="bg-white p-6 rounded-xl shadow">
                <div className="flex flex-col gap-6 lg:grid lg:grid-cols-[minmax(0,1fr)_320px] lg:gap-8">
                  <div className="space-y-6">
                    {/* Progress / Page selector */}
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <div className="text-sm text-gray-600">Página {page} de {totalPages}</div>
                        <div className="flex items-center gap-2">
                          {Array.from({ length: totalPages }).map((_, idx) => {
                            const p = idx + 1;
                            return (
                              <button
                                key={p}
                                type="button"
                                onClick={() => setPage(p)}
                                aria-current={p === page}
                                className={`w-8 h-8 rounded-full text-sm inline-flex items-center justify-center ${p === page ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}
                              >
                                {p}
                              </button>
                            );
                          })}
                        </div>
                      </div>
                      <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
                        <div className="h-2 bg-blue-600 rounded-full" style={{ width: `${Math.round((page / totalPages) * 100)}%` }} />
                      </div>
                    </div>

                    {/* Questions for current page */}
                    <div className="grid gap-4 md:grid-cols-2">
                      {QUESTIONS.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE).map((q) => (
                        <div key={q.id} className="border rounded-xl p-4 shadow-sm hover:shadow-md transition-shadow">
                          <div className="flex items-start justify-between gap-3 mb-3">
                            <div>
                              <h3 className="font-semibold text-sm sm:text-base">{q.label}</h3>
                              {q.helper && <p className="text-xs text-gray-500 mt-1 sm:text-sm">{q.helper}</p>}
                            </div>
                            <div className="flex items-center gap-1">
                              {Array.from({ length: 5 }).map((_, i) => {
                                const val = i + 1;
                                return (
                                  <button
                                    key={val}
                                    type="button"
                                    onClick={() => setRating(q.id, val)}
                                    aria-label={`${val} estrellas`}
                                    className={`p-1 rounded ${ratings[q.id] >= val ? 'text-yellow-500' : 'text-gray-300'} hover:text-yellow-400 transition-colors`}
                                  >
                                    <Star className="w-5 h-5" />
                                  </button>
                                );
                              })}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Comentarios</label>
                      <textarea
                        value={comments}
                        onChange={(e) => setComments(e.target.value)}
                        rows={4}
                        className="w-full border border-gray-300 rounded-md p-2 text-sm focus:ring-2 focus:ring-blue-500"
                        placeholder="Observaciones generales sobre el proyecto"
                      />
                    </div>

                    <div className="flex items-center justify-between gap-3">
                      <div className="flex items-center gap-2">
                        <button
                          type="button"
                          onClick={() => setPage((p) => Math.max(1, p - 1))}
                          disabled={page === 1}
                          className="px-3 py-2 rounded bg-gray-100 text-sm hover:bg-gray-200 disabled:opacity-50"
                        >
                          Anterior
                        </button>
                        {page < totalPages ? (
                          <button
                            type="button"
                            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                            className="px-3 py-2 rounded bg-blue-600 text-white text-sm hover:bg-blue-700"
                          >
                            Siguiente
                          </button>
                        ) : (
                          <button
                            type="submit"
                            disabled={isSubmitting}
                            className="inline-flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-60"
                          >
                            {isSubmitting ? 'Enviando...' : 'Enviar evaluación'}
                          </button>
                        )}
                      </div>

                      <div className="flex items-center gap-3">
                        <button
                          type="button"
                          onClick={() => router.back()}
                          className="text-sm text-gray-600 hover:underline"
                        >
                          Cancelar
                        </button>
                      </div>
                    </div>
                  </div>

                  <aside className="hidden lg:flex flex-col gap-4">
                    <div className="rounded-xl border border-dashed border-gray-300 bg-gray-50 p-4 text-center text-sm text-gray-500">
                      <div className="aspect-video mb-3 flex items-center justify-center rounded-lg bg-gradient-to-br from-blue-50 via-white to-blue-100 text-gray-400">
                        Guía visual
                      </div>
                      <p>Espacio reservado para una imagen de referencia o instrucciones para el evaluador.</p>
                    </div>
                    <div className="rounded-xl border border-gray-200 p-4 text-sm text-gray-600 bg-white shadow-sm">
                      <h4 className="font-semibold text-gray-800 mb-2">Sugerencias</h4>
                      <ul className="space-y-1 text-left">
                        <li>• Revise los criterios antes de enviar.</li>
                        <li>• Puede volver a páginas anteriores sin perder sus calificaciones.</li>
                      </ul>
                    </div>
                  </aside>
                </div>
              </form>
            ) : (
              <div className="bg-white p-6 rounded-xl shadow space-y-4">
                <h3 className="text-lg font-semibold">Evaluación enviada</h3>
                <p className="text-sm text-gray-600">La evaluación se ha registrado localmente (demo). Reemplace con su API para guardar en el servidor.</p>
                <pre className="text-xs bg-gray-100 p-3 rounded overflow-auto">{JSON.stringify(submittedData, null, 2)}</pre>
                <div className="flex gap-2">
                  <button onClick={() => router.push('/dashboard/proyectos')} className="bg-blue-600 text-white px-3 py-2 rounded">Volver a Proyectos</button>
                  <button onClick={() => setSubmittedData(null)} className="border px-3 py-2 rounded">Nueva evaluación</button>
                </div>
              </div>
            )}
          </div>
        </main>
      </PageTransition>
    </>
  );
}
