"use client";

import React, { useState, useEffect, useMemo } from "react";
import { Search, FileText, AlertCircle } from "lucide-react";
import { useRouter, useSearchParams } from "next/navigation";

import {
  applyStateFilter,
  readStateFromSearchParams,
} from "@features/projects/lib/applyStateFilter";
import DashboardHeader from "@widgets/header/DashboardHeader";
import SemesterSelector from "@features/semesters/components/SemesterSelector";
import { Project, ProjectState } from "@features/projects/types/project";
import { getAllProjects } from "@features/projects/api/projectService";
import {
  getAvailableSemesters,
  getSemesters,
  getStoredSemester,
  setStoredSemester,
} from "@features/semesters/api/semesters";
import ProjectCard from "@features/projects/components/ProjectCard";
import { StateFilter, type StateFilterOption } from "@features/projects/components/StateFilter";
import { getUser, getUserRole } from "@features/auth/api/clientAuth";
import type { Role } from "@features/projects/lib/cardAction";

const PTEG_STATES: ProjectState[] = [
  "pending_review_1",
  "pending_review_2",
  "pending_defense",
  "approved",
  "failed_final",
];

const STATE_LABEL: Record<ProjectState, string> = {
  pending_review_1: "Rev 1",
  pending_review_2: "Rev 2",
  pending_defense:  "Defensa",
  pending_articulo: "Artículo",
  pending_entrega:  "Entrega",
  pending_defensa:  "Defensa",
  approved:         "Aprob.",
  failed_final:     "Reprob.",
};

const STATE_DOT_COLOR: Record<ProjectState, string> = {
  pending_review_1: "var(--text-muted)",
  pending_review_2: "var(--pending)",
  pending_defense:  "var(--primary)",
  pending_articulo: "var(--text-muted)",
  pending_entrega:  "var(--pending)",
  pending_defensa:  "var(--primary)",
  approved:         "var(--success)",
  failed_final:     "var(--destructive)",
};

export default function ProyectosPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const activeStateFilter = readStateFromSearchParams(searchParams ?? null);
  const userRole = useMemo<Role | null>(() => getUserRole() as Role | null, []);
  const viewerId = useMemo<number | undefined>(() => {
    const u = getUser();
    return typeof u?.id === "number" ? u.id : undefined;
  }, []);
  const isStudent = userRole === "Estudiante";

  const [searchQuery, setSearchQuery] = useState("");

  const [allProjects, setAllProjects] = useState<Project[]>([]);
  const [semesterOptions, setSemesterOptions] = useState<string[]>([]);
  const [isDataLoaded, setIsDataLoaded] = useState(false);

  useEffect(() => {
    let mounted = true;
    (async () => {
      const [apiProjects, semestersFromApi] = await Promise.all([
        getAllProjects(),
        getSemesters(),
      ]);
      const onlyProyectos = apiProjects.filter((p) => p.type === "proyecto");
      if (mounted) {
        setAllProjects(onlyProyectos);
        setSemesterOptions(semestersFromApi.map((s) => s.period));
        setIsDataLoaded(true);
      }
    })();
    return () => { mounted = false; };
  }, []);

  const availableSemesters = useMemo(
    () => getAvailableSemesters(allProjects, semesterOptions),
    [allProjects, semesterOptions],
  );

  const [selectedSemester, setSelectedSemester] = useState(() => {
    const stored = getStoredSemester();
    return availableSemesters.includes(stored)
      ? stored
      : availableSemesters[0] || stored;
  });

  useEffect(() => {
    if (availableSemesters.length === 0) return;
    if (!availableSemesters.includes(selectedSemester)) {
      const next = availableSemesters[0];
      setSelectedSemester(next);
      setStoredSemester(next);
    }
  }, [availableSemesters, selectedSemester]);

  const handleSemesterChange = (semester: string) => {
    setSelectedSemester(semester);
    setStoredSemester(semester);
  };

  const semesterProjects = useMemo<Project[]>(
    () => allProjects.filter((p) => p.period === selectedSemester),
    [selectedSemester, allProjects],
  );

  const counts = useMemo(() => {
    const c: Record<ProjectState, number> = {
      pending_review_1: 0, pending_review_2: 0, pending_defense: 0,
      pending_articulo: 0, pending_entrega: 0, pending_defensa: 0,
      approved: 0, failed_final: 0,
    };
    for (const p of semesterProjects) c[p.state]++;
    return c;
  }, [semesterProjects]);

  const filteredProjects = useMemo(() => {
    const afterSearch = semesterProjects.filter((project) => {
      const q = searchQuery.toLowerCase();
      return (
        project.title.toLowerCase().includes(q) ||
        project.student.toLowerCase().includes(q) ||
        (project.advisorNames || []).some((n) => n.toLowerCase().includes(q))
      );
    });
    return applyStateFilter(afterSearch, activeStateFilter);
  }, [semesterProjects, searchQuery, activeStateFilter]);

  const total = semesterProjects.length;
  const tuAccion = counts.pending_review_1 + counts.pending_review_2;
  const defensas = counts.pending_defense;

  const ptegOptions = useMemo<StateFilterOption[]>(
    () =>
      PTEG_STATES.map((s) => ({
        state: s,
        label: STATE_LABEL[s],
        count: counts[s],
        dotColor: STATE_DOT_COLOR[s],
      })),
    [counts],
  );

  const setStateFilter = (next: ProjectState | null) => {
    if (next == null) {
      router.push("/dashboard/proyectos");
    } else {
      router.push(`/dashboard/proyectos?state=${next}`);
    }
  };

  return (
    <>
      <DashboardHeader pageTitle="Proyectos" />

      <main className="flex-1 p-4 sm:p-6 lg:p-8 overflow-y-auto bg-surface-muted">
        <div className="max-w-screen-2xl mx-auto">
          {/* HERO */}
          <section className="dashboard-hero-bg relative overflow-hidden rounded-2xl border border-border-subtle px-7 py-6 mb-6">
            <div className="relative z-10 flex flex-col gap-6 md:flex-row md:items-start md:justify-between">
              <div className="flex flex-col gap-1.5">
                <p className="flex items-center gap-2 text-[10px] font-extrabold uppercase tracking-[0.14em] text-primary">
                  <span aria-hidden className="inline-block h-[2px] w-6 rounded-full bg-gradient-to-r from-primary to-[var(--brand-orange)]" />
                  PTEG · Período {selectedSemester}
                </p>
                <h1 className="text-3xl font-extrabold leading-tight tracking-[-0.03em] text-text-strong md:text-[34px]">
                  Proyectos{" "}
                  <span className="bg-gradient-to-br from-primary to-[var(--brand-orange)] bg-clip-text font-black text-transparent">
                    Trabajos Especiales de Grado
                  </span>
                </h1>
                <p className="max-w-[480px] text-sm font-medium leading-relaxed text-text-muted mt-1">
                  Registro y seguimiento de los proyectos del período. {total} en evaluación, distribuidos entre las fases de revisión y defensa.
                </p>
              </div>

              <div className="flex items-start gap-3 flex-wrap">
                <SemesterSelector
                  selectedSemester={selectedSemester}
                  availableSemesters={availableSemesters}
                  onSemesterChange={handleSemesterChange}
                />
                {isStudent && (
                  <button
                    onClick={() => router.push("/dashboard/agregar")}
                    className="rounded-xl px-5 py-2.5 text-sm font-bold bg-text-strong text-white shadow-md hover:bg-[#0a1424] transition-colors flex items-center gap-2"
                  >
                    <FileText className="w-4 h-4" />
                    Subir Proyecto
                  </button>
                )}
              </div>
            </div>
          </section>

          {/* STAT TILES */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <div className="stile stile-hero lg:col-span-2 sm:col-span-2">
              <span className="stile-hero-glow" aria-hidden />
              <p className="relative z-10 flex items-center gap-2 text-[10px] font-extrabold uppercase tracking-[0.12em] text-[var(--brand-yellow)] before:block before:h-[1.5px] before:w-3.5 before:rounded-full before:bg-[var(--brand-yellow)]">
                Total PTEG · período
              </p>
              <p className="relative z-10 text-[60px] leading-none tracking-[-0.045em] font-black text-white">{total}</p>
              <p className="relative z-10 text-[13px] text-white/70 font-medium leading-snug">
                <span className="text-white font-bold">{tuAccion}</span> esperando revisión &middot;{" "}
                <span className="text-white font-bold">{defensas}</span> en defensa
              </p>
            </div>

            <div className="stile">
              <p className="flex items-center gap-2 text-[10px] font-extrabold uppercase tracking-[0.12em] text-pending">
                <span className="h-1.5 w-1.5 rounded-full ring-[3px] bg-pending ring-pending/22" aria-hidden />
                Tu acción
                {tuAccion > 0 && <span className="ml-1 inline-block w-2 h-2 rounded-full bg-pending pulse-soft" />}
              </p>
              <p className="text-[46px] leading-none tracking-[-0.035em] font-black text-text-strong">{tuAccion}</p>
              <p className="text-[13px] text-text-muted font-medium leading-snug">por evaluar</p>
            </div>

            <div className="stile">
              <p className="flex items-center gap-2 text-[10px] font-extrabold uppercase tracking-[0.12em] text-[var(--brand-orange)]">
                <span className="h-1.5 w-1.5 rounded-full ring-[3px] bg-[var(--brand-orange)] ring-[var(--brand-orange)]/22" aria-hidden />
                Defensas próx.
              </p>
              <p className="text-[46px] leading-none tracking-[-0.035em] font-black text-text-strong">{defensas}</p>
              <p className="text-[13px] text-text-muted font-medium">esta semana</p>
            </div>
          </div>

          {/* SEARCH + FILTER ROW */}
          <div className="flex flex-col xl:flex-row items-stretch xl:items-center gap-3 mb-6">
            <div className="relative flex-1">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-text-muted w-4 h-4" />
              <input
                type="text"
                placeholder="Buscar por título, estudiante o tutor…"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-11 pr-4 h-11 bg-surface border border-border-subtle rounded-xl text-[13px] font-medium text-text-strong placeholder:text-text-muted focus:outline-none focus:border-primary transition-colors"
              />
            </div>

            <StateFilter
              value={activeStateFilter}
              onChange={setStateFilter}
              options={ptegOptions}
              totalCount={total}
              allLabel="Todos los estados"
            />
          </div>

          {/* GRID */}
          {!isDataLoaded ? (
            <div className="flex justify-center items-center py-20">
              <div className="w-8 h-8 rounded-full border-4 border-border-subtle border-t-primary animate-spin" />
            </div>
          ) : filteredProjects.length === 0 ? (
            <div className="bg-surface border border-dashed border-border-default rounded-2xl py-16 text-center">
              <AlertCircle className="w-10 h-10 text-text-muted mx-auto mb-4" />
              <h3 className="text-lg font-extrabold text-text-strong mb-1">No se encontraron proyectos</h3>
              <p className="text-sm text-text-muted">Ajusta tu búsqueda o filtros.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {filteredProjects.map((project) => (
                <ProjectCard
                  key={project.id}
                  project={project}
                  role={userRole ?? undefined}
                  viewerId={viewerId}
                />
              ))}
            </div>
          )}
        </div>
      </main>
    </>
  );
}

