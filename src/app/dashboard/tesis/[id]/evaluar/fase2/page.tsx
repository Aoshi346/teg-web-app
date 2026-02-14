"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import PageTransition from "@/components/ui/PageTransition";
import DashboardHeader from "@/components/layout/DashboardHeader";
import EvaluationForm from "@/components/evaluation/EvaluationForm";
import { getProject } from "@/features/projects/projectService";
import { TESIS_STAGE2_QUESTIONS } from "@/lib/questions/questions";
import { AlertCircle, ArrowLeft } from "lucide-react";

export default function EvaluarTesisFase2Page({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const router = useRouter();
  const { id: projectId } = React.use(params);
  const [isAllowed, setIsAllowed] = useState<boolean | null>(null);

  useEffect(() => {
    const checkStatus = async () => {
      const id = Number(projectId);
      const project = await getProject(id);

      // Allow if project exists and stage1Passed is true
      if (project && project.stage1Passed) {
        setIsAllowed(true);
      } else {
        setIsAllowed(false);
      }
    };

    if (projectId) {
      checkStatus();
    } else {
      setIsAllowed(false);
    }
  }, [projectId]);

  if (isAllowed === null) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-50">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!isAllowed) {
    return (
      <>
        <DashboardHeader pageTitle={`Evaluar Tesis - Fase 2`} />
        <PageTransition>
          <main className="flex-1 p-4 sm:p-6 lg:p-8 bg-gray-50 flex items-center justify-center">
            <div className="max-w-md w-full bg-white p-8 rounded-xl shadow-lg text-center border border-gray-200">
              <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <AlertCircle className="w-8 h-8 text-red-600" />
              </div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">
                Acceso Restringido
              </h2>
              <p className="text-gray-600 mb-6">
                No es posible evaluar la Fase 2 (Entrega Final) porque el
                proyecto no ha aprobado la Fase 1 (Artículo).
              </p>
              <div className="flex flex-col gap-3">
                <button
                  onClick={() =>
                    router.push(`/dashboard/tesis/${projectId}/evaluar/fase1`)
                  }
                  className="w-full bg-blue-600 text-white py-2.5 rounded-lg font-semibold hover:bg-blue-700 transition-colors"
                >
                  Ir a Evaluación Fase 1
                </button>
                <button
                  onClick={() => router.back()}
                  className="w-full border border-gray-300 text-gray-700 py-2.5 rounded-lg font-semibold hover:bg-gray-50 transition-colors"
                >
                  Volver
                </button>
              </div>
            </div>
          </main>
        </PageTransition>
      </>
    );
  }

  return (
    <>
      <DashboardHeader pageTitle={`Evaluar Tesis - Fase 2 (Entrega Final)`} />

      <PageTransition>
        <main className="flex-1 p-4 sm:p-6 lg:p-8 bg-gray-50">
          <div className="max-w-7xl mx-auto">
            <button
              onClick={() => router.back()}
              className="flex items-center text-gray-600 hover:text-gray-900 transition-colors mb-6"
            >
              <ArrowLeft className="w-5 h-5 mr-2" />
              Volver
            </button>
            <EvaluationForm
              projectId={projectId}
              typeParam={"tesis"}
              questions={TESIS_STAGE2_QUESTIONS}
            />
          </div>
        </main>
      </PageTransition>
    </>
  );
}
