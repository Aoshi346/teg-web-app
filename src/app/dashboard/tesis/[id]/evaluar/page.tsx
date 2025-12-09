"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import PageTransition from "@/components/ui/PageTransition";
import DashboardHeader from "@/components/layout/DashboardHeader";
import { FileText, CheckCircle, Lock, ArrowLeft } from "lucide-react";

export default function EvaluarTesisPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const router = useRouter();
  const { id: projectId } = React.use(params);
  const [stage1Passed, setStage1Passed] = useState(false);

  useEffect(() => {
    // Mock check
    const passed =
      sessionStorage.getItem(`project_${projectId}_stage1_passed`) === "true";
    setStage1Passed(passed);
  }, [projectId]);

  // Helper to toggle pass status for demo purposes
  const toggleStage1Pass = () => {
    const newState = !stage1Passed;
    setStage1Passed(newState);
    if (projectId) {
      sessionStorage.setItem(
        `project_${projectId}_stage1_passed`,
        String(newState)
      );
    }
  };

  return (
    <>
      <DashboardHeader pageTitle={`Evaluar Tesis - Selección de Fase`} />

      <PageTransition>
        <main className="flex-1 p-4 sm:p-6 lg:p-8 overflow-y-auto bg-gray-50">
          <div className="max-w-7xl mx-auto">
            <button
              onClick={() => router.back()}
              className="flex items-center text-gray-600 hover:text-gray-900 transition-colors mb-6"
            >
              <ArrowLeft className="w-5 h-5 mr-2" />
              Volver
            </button>

            <div className="mb-8">
              <h2 className="text-2xl font-bold text-gray-900">
                Seleccione la fase a evaluar
              </h2>
              <p className="text-gray-600 mt-2">
                El proceso de evaluación de Tesis consta de dos fases
                secuenciales. La Fase 2 solo estará disponible una vez aprobada
                la Fase 1.
              </p>

              {/* Demo Control */}
              <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg inline-block">
                <p className="text-xs font-bold text-yellow-800 uppercase mb-2">
                  Control de Demo
                </p>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={stage1Passed}
                    onChange={toggleStage1Pass}
                    className="rounded text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-sm text-yellow-900">
                    Simular Fase 1 Aprobada
                  </span>
                </label>
              </div>

              <div className="grid md:grid-cols-2 gap-6 mt-6">
                {/* Fase 1 Card */}
                <div
                  onClick={() =>
                    router.push(`/dashboard/tesis/${projectId}/evaluar/fase1`)
                  }
                  className="bg-white p-6 rounded-xl shadow-sm border border-gray-200 hover:shadow-md hover:border-blue-300 transition-all cursor-pointer group"
                >
                  <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4 group-hover:bg-blue-600 transition-colors">
                    <FileText className="w-6 h-6 text-blue-600 group-hover:text-white transition-colors" />
                  </div>
                  <h3 className="text-xl font-bold text-gray-900 mb-2">
                    Fase 1: Diagramación
                  </h3>
                  <p className="text-gray-600 text-sm mb-4">
                    Evaluación de aspectos formales, estructura, ortografía y
                    cumplimiento de normas de presentación.
                  </p>
                  <div className="flex items-center text-sm font-medium text-blue-600">
                    Evaluar ahora &rarr;
                  </div>
                </div>

                {/* Fase 2 Card */}
                <div
                  onClick={() => {
                    // We allow clicking to show the "Disallowed" page if not passed,
                    // or the form if passed.
                    router.push(`/dashboard/tesis/${projectId}/evaluar/fase2`);
                  }}
                  className={`bg-white p-6 rounded-xl shadow-sm border transition-all cursor-pointer group relative overflow-hidden ${
                    stage1Passed
                      ? "border-gray-200 hover:shadow-md hover:border-green-300"
                      : "border-gray-200 opacity-75 bg-gray-50"
                  }`}
                >
                  {!stage1Passed && (
                    <div className="absolute top-4 right-4">
                      <Lock className="w-5 h-5 text-gray-400" />
                    </div>
                  )}
                  <div
                    className={`w-12 h-12 rounded-lg flex items-center justify-center mb-4 transition-colors ${
                      stage1Passed
                        ? "bg-green-100 group-hover:bg-green-600"
                        : "bg-gray-200"
                    }`}
                  >
                    <CheckCircle
                      className={`w-6 h-6 transition-colors ${
                        stage1Passed
                          ? "text-green-600 group-hover:text-white"
                          : "text-gray-400"
                      }`}
                    />
                  </div>
                  <h3 className="text-xl font-bold text-gray-900 mb-2">
                    Fase 2: Contenido
                  </h3>
                  <p className="text-gray-600 text-sm mb-4">
                    Evaluación del planteamiento, objetivos, marco teórico,
                    metodología y resultados.
                  </p>
                  <div
                    className={`flex items-center text-sm font-medium ${
                      stage1Passed ? "text-green-600" : "text-gray-400"
                    }`}
                  >
                    {stage1Passed
                      ? "Evaluar ahora →"
                      : "Bloqueado (Requiere Fase 1)"}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </main>
      </PageTransition>
    </>
  );
}
