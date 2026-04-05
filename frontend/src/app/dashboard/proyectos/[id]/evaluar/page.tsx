"use client";

import React from "react";
import { useRouter, useParams } from "next/navigation";
import DashboardHeader from "@/components/layout/DashboardHeader";
import EvaluationForm from "@/components/evaluation/EvaluationForm";
import { PROJECT_QUESTIONS } from "@/lib/questions/questions";
import { ArrowLeft } from "lucide-react";

export default function EvaluarProyectoPage() {
  const router = useRouter();
  const params = useParams();
  const projectId = Array.isArray(params.id) ? params.id[0] : params.id;
  const typeParam = "proyecto";

  return (
    <>
      <DashboardHeader pageTitle={`Evaluar Proyecto`} />

        
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
              typeParam={typeParam}
              questions={PROJECT_QUESTIONS}
            />
          </div>
        </main>
        
    </>
  );
}
