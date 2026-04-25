"use client";

import React, { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import DashboardHeader from "@widgets/header/DashboardHeader";
import { FileText, Package, Mic, Lock, ArrowLeft } from "lucide-react";
import { getProject } from "@features/projects/api/projectService";
import type { ProjectState } from "@features/projects/types/project";

type GateKey = "articulo" | "entrega" | "defensa";

interface Gate {
  key: GateKey;
  title: string;
  blurb: string;
  icon: React.ComponentType<{ className?: string }>;
  href: (id: string) => string;
  unlocked: (s: ProjectState) => boolean;
  active: (s: ProjectState) => boolean;
}

const GATES: Gate[] = [
  {
    key: "articulo",
    title: "Fase 1: Artículo",
    blurb: "Evaluación de aspectos formales, estructura, ortografía y normas de presentación.",
    icon: FileText,
    href: (id) => `/dashboard/tesis/${id}/evaluar/articulo`,
    unlocked: (s) =>
      s === "pending_articulo" ||
      s === "pending_entrega" ||
      s === "pending_defensa" ||
      s === "approved" ||
      s === "failed_final",
    active: (s) => s === "pending_articulo",
  },
  {
    key: "entrega",
    title: "Fase 2: Entrega Ejemplar",
    blurb: "Revisión del ejemplar entregado: planteamiento, marco teórico, metodología.",
    icon: Package,
    href: (id) => `/dashboard/tesis/${id}/evaluar/entrega`,
    unlocked: (s) =>
      s === "pending_entrega" || s === "pending_defensa" || s === "approved" || s === "failed_final",
    active: (s) => s === "pending_entrega",
  },
  {
    key: "defensa",
    title: "Fase 3: Defensa Oral",
    blurb: "Evaluación de la presentación oral y defensa ante el jurado.",
    icon: Mic,
    href: (id) => `/dashboard/tesis/${id}/evaluar/defensa`,
    unlocked: (s) => s === "pending_defensa" || s === "approved" || s === "failed_final",
    active: (s) => s === "pending_defensa",
  },
];

export default function EvaluarTesisPage() {
  const router = useRouter();
  const params = useParams();
  const projectId = Array.isArray(params.id) ? params.id[0] : params.id;
  const [state, setState] = useState<ProjectState | null>(null);

  useEffect(() => {
    let mounted = true;
    (async () => {
      const apiProject = await getProject(Number(projectId));
      if (mounted && apiProject) setState(apiProject.state);
    })();
    return () => {
      mounted = false;
    };
  }, [projectId]);

  return (
    <>
      <DashboardHeader pageTitle="Evaluar Tesis - Selección de fase" />
      <main className="flex-1 p-4 sm:p-6 lg:p-8 bg-gray-50">
        <div className="max-w-7xl mx-auto">
          <button
            onClick={() => router.back()}
            className="flex items-center text-gray-600 hover:text-gray-900 transition-colors mb-6"
          >
            <ArrowLeft className="w-5 h-5 mr-2" />
            Volver
          </button>

          <div className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900">Seleccione la fase a evaluar</h2>
            <p className="text-gray-600 mt-2">
              El proceso TEG consta de tres fases secuenciales: Artículo, Entrega Ejemplar y Defensa Oral.
              Cada fase se desbloquea cuando se aprueba la anterior.
            </p>

            <div className="grid md:grid-cols-3 gap-6 mt-6">
              {GATES.map((g) => {
                const unlocked = state ? g.unlocked(state) : false;
                const active = state ? g.active(state) : false;
                const Icon = g.icon;
                return (
                  <button
                    key={g.key}
                    type="button"
                    disabled={!unlocked}
                    onClick={() => projectId && router.push(g.href(projectId))}
                    className={`text-left bg-white p-6 rounded-xl shadow-sm border transition-all relative overflow-hidden
                      ${
                        unlocked
                          ? "border-gray-200 hover:shadow-md hover:border-blue-300 cursor-pointer"
                          : "border-gray-200 opacity-60 bg-gray-50 cursor-not-allowed"
                      }
                      ${active ? "ring-2 ring-blue-500" : ""}`}
                  >
                    {!unlocked && (
                      <div className="absolute top-4 right-4">
                        <Lock className="w-5 h-5 text-gray-400" />
                      </div>
                    )}
                    <div
                      className={`w-12 h-12 rounded-lg flex items-center justify-center mb-4 ${
                        unlocked ? "bg-blue-100" : "bg-gray-200"
                      }`}
                    >
                      <Icon className={`w-6 h-6 ${unlocked ? "text-blue-600" : "text-gray-400"}`} />
                    </div>
                    <h3 className="text-xl font-bold text-gray-900 mb-2">{g.title}</h3>
                    <p className="text-gray-600 text-sm mb-4">{g.blurb}</p>
                    <div
                      className={`flex items-center text-sm font-medium ${
                        unlocked ? "text-blue-600" : "text-gray-400"
                      }`}
                    >
                      {active ? "Evaluar ahora →" : unlocked ? "Ver fase" : "Bloqueado"}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      </main>
    </>
  );
}
