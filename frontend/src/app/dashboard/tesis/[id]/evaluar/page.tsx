"use client";

import React, { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import DashboardHeader from "@widgets/header/DashboardHeader";
import { FileText, Package, Mic, ArrowLeft, ArrowRight } from "lucide-react";
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
      <main className="flex-1 p-4 sm:p-6 lg:p-8 overflow-y-auto bg-surface-muted">
        <div className="max-w-screen-2xl mx-auto">
          <button
            onClick={() => router.back()}
            className="flex items-center text-text-muted hover:text-text-strong transition-colors mb-6 text-[12.5px] font-bold"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Volver
          </button>

          <section className="dashboard-hero-bg relative overflow-hidden rounded-2xl border border-border-subtle px-7 py-6 mb-8">
            <p className="flex items-center gap-2 text-[10px] font-extrabold uppercase tracking-[0.14em] mb-3 text-[var(--brand-orange)]">
              <span aria-hidden className="inline-block h-[2px] w-6 rounded-full bg-gradient-to-r from-primary to-[var(--brand-orange)]" />
              Evaluar tesis
            </p>
            <h2 className="text-[34px] leading-tight tracking-[-0.03em] font-extrabold text-text-strong">
              Tres fases.{" "}
              <span className="bg-gradient-to-br from-[var(--brand-orange)] to-primary bg-clip-text font-black text-transparent">
                Una a la vez.
              </span>
            </h2>
            <p className="mt-3 max-w-[60ch] text-[13.5px] font-medium leading-relaxed text-text-muted">
              El proceso TEG consta de tres fases secuenciales. Cada fase aprobada desbloquea la siguiente.
            </p>
          </section>

          <div className="grid grid-cols-1 lg:grid-cols-[1fr_auto_1fr_auto_1fr] gap-0 items-stretch">
            {GATES.map((g, i) => {
              const unlocked = state ? g.unlocked(state) : false;
              const active = state ? g.active(state) : false;
              const phaseState =
                active ? "active"
                : state === "failed_final" ? "failed"
                : unlocked ? "passed"
                : "locked";

              return (
                <React.Fragment key={g.key}>
                  <button
                    type="button"
                    disabled={!unlocked}
                    onClick={() => projectId && router.push(g.href(projectId))}
                    data-state={phaseState}
                    className="phase text-left disabled:cursor-not-allowed"
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <div className="text-[10px] uppercase tracking-[0.12em] font-extrabold"
                             style={{
                               color:
                                 phaseState === "active"  ? "var(--primary)" :
                                 phaseState === "passed"  ? "var(--success)" :
                                 phaseState === "failed"  ? "var(--destructive)" :
                                                            "var(--text-muted)",
                             }}>
                          Fase {i + 1}{phaseState === "active" ? " · Activa" : phaseState === "locked" ? " · Bloqueada" : ""}
                        </div>
                        <div className="mt-2 text-[22px] font-extrabold tracking-tight text-text-strong">
                          {g.title.replace(/^Fase \d+:\s*/, "")}
                        </div>
                      </div>
                      <div className="phase-numeral font-display">
                        {String(i + 1).padStart(2, "0")}
                      </div>
                    </div>
                    <p className="text-[13px] text-text-muted font-medium mt-3 leading-relaxed">
                      {g.blurb}
                    </p>
                    <div className="mt-5">
                      {phaseState === "active" && (
                        <div className="flex items-center gap-3">
                          <span className="bg-text-strong text-white rounded-xl px-4 py-2 font-bold text-[13px] inline-flex items-center gap-2">
                            Evaluar ahora
                            <ArrowRight className="w-3 h-3" strokeWidth={2.6} />
                          </span>
                        </div>
                      )}
                      {phaseState === "passed" && (
                        <span className="spill spill-green">Aprobada</span>
                      )}
                      {phaseState === "failed" && (
                        <span className="spill spill-red">Reprobada</span>
                      )}
                      {phaseState === "locked" && (
                        <span className="spill spill-slate">Bloqueada</span>
                      )}
                    </div>
                  </button>
                  {i < GATES.length - 1 && (
                    <div className="hidden lg:flex items-center justify-center">
                      <div className="phase-link w-12" aria-hidden />
                    </div>
                  )}
                </React.Fragment>
              );
            })}
          </div>
        </div>
      </main>
    </>
  );
}
