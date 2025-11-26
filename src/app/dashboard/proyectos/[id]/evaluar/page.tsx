"use client";

import React from "react";
import { useRouter } from "next/navigation";
import PageTransition from "@/components/ui/PageTransition";
import DashboardHeader from "@/components/layout/DashboardHeader";
import EvaluationForm from "@/components/evaluation/EvaluationForm";
import { PROJECT_QUESTIONS } from "@/lib/questions/questions";
import { ArrowLeft } from "lucide-react";

export default function EvaluarProyectoPage({
  params,
}: {
  params: { id: string };
}) {
  const router = useRouter();
  const projectId = params.id;
  const typeParam = "proyecto";

  return (
    <>
      <DashboardHeader pageTitle={`Evaluar Proyecto`} />

      <PageTransition>
        <main className="flex-1 p-4 sm:p-6 lg:p-8 overflow-y-auto bg-gray-50">
          <div className="max-w-4xl mx-auto mb-6">
            <button
              onClick={() => router.back()}
              className="flex items-center text-gray-600 hover:text-gray-900 transition-colors"
            >
              <ArrowLeft className="w-5 h-5 mr-2" />
              Volver
            </button>
          </div>
          <EvaluationForm
            projectId={projectId}
            typeParam={typeParam}
            questions={PROJECT_QUESTIONS}
          />
        </main>
      </PageTransition>
    </>
  );
}
