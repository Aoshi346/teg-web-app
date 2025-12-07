"use client";

import React from "react";
import { useRouter } from "next/navigation";
import PageTransition from "@/components/ui/PageTransition";
import DashboardHeader from "@/components/layout/DashboardHeader";
import EvaluationForm from "@/components/evaluation/EvaluationForm";
import { TESIS_STAGE1_QUESTIONS } from "@/lib/questions/questions";
import { ArrowLeft } from "lucide-react";

export default function EvaluarTesisFase1Page({
  params,
}: {
  params: { id: string };
}) {
  const router = useRouter();
  const projectId = params.id;

  return (
    <>
      <DashboardHeader pageTitle={`Evaluar Tesis - Fase 1 (Diagramación)`} />

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
            <EvaluationForm
              projectId={projectId}
              typeParam={"tesis"}
              questions={TESIS_STAGE1_QUESTIONS}
            />
          </div>
        </main>
      </PageTransition>
    </>
  );
}
