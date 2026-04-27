"use client";

import React from "react";
import { useRouter } from "next/navigation";
import DashboardHeader from "@widgets/header/DashboardHeader";
import EvaluationForm from "@features/evaluations/components/EvaluationForm";
import { TEG_ENTREGA_QUESTIONS } from "@features/evaluations/lib/questions/questions";
import { ArrowLeft } from "lucide-react";

export default function EvaluarTesisEntregaPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const router = useRouter();
  const { id: projectId } = React.use(params);

  return (
    <>
      <DashboardHeader pageTitle="Evaluar Tesis — Entrega del tomo" />

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
            questions={TEG_ENTREGA_QUESTIONS}
            kind="review"
            projectState="pending_entrega"
          />
        </div>
      </main>
    </>
  );
}
