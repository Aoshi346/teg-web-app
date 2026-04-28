"use client";

import React from "react";
import { useRouter, useParams } from "next/navigation";
import DashboardHeader from "@widgets/header/DashboardHeader";
import EvaluationForm from "@features/evaluations/components/EvaluationForm";
import { TEG_DEFENSA_QUESTIONS } from "@features/evaluations/lib/questions/questions";
import { ArrowLeft } from "lucide-react";

export default function EvaluarTesisDefensaPage() {
  const router = useRouter();
  const routeParams = useParams();
  const projectId = Array.isArray(routeParams.id) ? routeParams.id[0] : (routeParams.id ?? "");

  return (
    <>
      <DashboardHeader pageTitle="Evaluar Tesis — Defensa Oral" />

      <main className="flex-1 p-4 sm:p-6 lg:p-8 overflow-y-auto bg-surface-muted">
        <div className="max-w-screen-2xl mx-auto">
          <button
            onClick={() => router.back()}
            className="flex items-center text-text-muted hover:text-text-strong transition-colors mb-6 text-[12.5px] font-bold"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Volver
          </button>
          <EvaluationForm
            projectId={projectId}
            typeParam="tesis"
            questions={TEG_DEFENSA_QUESTIONS}
            kind="defense"
            projectState="pending_defensa"
          />
        </div>
      </main>
    </>
  );
}
