"use client";

import React, { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import DashboardHeader from "@widgets/header/DashboardHeader";
import EvaluationForm from "@features/evaluations/components/EvaluationForm";
import { PROJECT_QUESTIONS, PTEG_DEFENSA_QUESTIONS } from "@features/evaluations/lib/questions/questions";

const ALL_PROYECTO_QUESTIONS = [...PROJECT_QUESTIONS, ...PTEG_DEFENSA_QUESTIONS];
import { getProject } from "@features/projects/api/projectService";
import type { Project, ProjectState } from "@features/projects/types/project";
import { ArrowLeft } from "lucide-react";

type EvalKind = "review" | "defense";

const REVIEW_STATES: ProjectState[] = ["pending_review_1", "pending_review_2"];
const DEFENSE_STATES: ProjectState[] = ["pending_defense"];
const TERMINAL_STATES: ProjectState[] = ["approved", "failed_final"];

function defaultKindForState(state: ProjectState | undefined): EvalKind {
  if (state && DEFENSE_STATES.includes(state)) return "defense";
  return "review";
}

export default function EvaluarProyectoPage() {
  const router = useRouter();
  const params = useParams();
  const projectId = Array.isArray(params.id) ? params.id[0] : params.id;
  const typeParam = "proyecto";

  const [project, setProject] = useState<Project | null>(null);
  const [kind, setKind] = useState<EvalKind>("review");
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    if (!projectId) return;
    const id = parseInt(projectId);
    if (Number.isNaN(id)) return;
    getProject(id)
      .then((p) => {
        if (p) {
          setProject(p);
          setKind(defaultKindForState(p.state));
        } else {
          setLoadError("Proyecto no encontrado.");
        }
      })
      .catch((err) => {
        const msg =
          err instanceof Error ? err.message : "Error al cargar el proyecto.";
        setLoadError(msg);
      });
  }, [projectId]);

  const isTerminal = project ? TERMINAL_STATES.includes(project.state) : false;
  const canReview = project ? REVIEW_STATES.includes(project.state) : true;
  const canDefense = project ? DEFENSE_STATES.includes(project.state) : false;

  return (
    <>
      <DashboardHeader pageTitle="Evaluar Proyecto" />

      <main className="flex-1 p-4 sm:p-6 lg:p-8 bg-gray-50">
        <div className="max-w-7xl mx-auto">
          <button
            onClick={() => router.back()}
            className="flex items-center text-gray-600 hover:text-gray-900 transition-colors mb-6"
          >
            <ArrowLeft className="w-5 h-5 mr-2" />
            Volver
          </button>

          {loadError ? (
            <div className="rounded-xl border border-red-200 bg-red-50 p-8 text-center shadow-sm">
              <p className="text-lg font-semibold text-red-800">
                No se pudo cargar el proyecto
              </p>
              <p className="mt-2 text-sm text-red-600">{loadError}</p>
            </div>
          ) : isTerminal ? (
            <div className="rounded-xl border border-slate-200 bg-white p-8 text-center shadow-sm">
              <p className="text-lg font-semibold text-slate-800">
                Este proyecto ya finalizó su ciclo.
              </p>
              <p className="mt-2 text-sm text-slate-500">
                Estado actual:{" "}
                <span className="font-medium">
                  {project?.state === "approved" ? "Aprobado" : "Reprobado"}
                </span>
                . No se permiten más evaluaciones.
              </p>
            </div>
          ) : (
            <>
              <div className="mb-6 inline-flex rounded-xl border border-slate-200 bg-white p-1 shadow-sm">
                <button
                  type="button"
                  aria-pressed={kind === "review"}
                  disabled={!canReview}
                  onClick={() => canReview && setKind("review")}
                  className={`rounded-lg px-4 py-2 text-sm font-medium transition ${
                    kind === "review"
                      ? "bg-blue-600 text-white"
                      : "text-slate-600 hover:text-slate-900"
                  } ${!canReview ? "cursor-not-allowed opacity-50" : ""}`}
                  title={canReview ? undefined : "Ya aprobó revisión"}
                >
                  Revisión
                </button>
                <button
                  type="button"
                  aria-pressed={kind === "defense"}
                  disabled={!canDefense}
                  onClick={() => canDefense && setKind("defense")}
                  className={`rounded-lg px-4 py-2 text-sm font-medium transition ${
                    kind === "defense"
                      ? "bg-blue-600 text-white"
                      : "text-slate-600 hover:text-slate-900"
                  } ${!canDefense ? "cursor-not-allowed opacity-50" : ""}`}
                  title={canDefense ? undefined : "Aún no aprobado para defensa"}
                >
                  Defensa oral
                </button>
              </div>

              <EvaluationForm
                projectId={projectId}
                typeParam={typeParam}
                questions={ALL_PROYECTO_QUESTIONS}
                kind={kind}
              />
            </>
          )}
        </div>
      </main>
    </>
  );
}
