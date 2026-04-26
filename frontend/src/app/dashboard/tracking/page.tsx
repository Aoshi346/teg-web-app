"use client";

import React, { useEffect, useState, useMemo } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import DashboardHeader from "@widgets/header/DashboardHeader";
import SemesterSelector from "@features/semesters/components/SemesterSelector";
import SeguimientoTable from "@features/projects/components/SeguimientoTable";
import MyProjectCard from "@features/projects/components/MyProjectCard";
import {
  getAvailableSemesters,
  getStoredSemester,
  setStoredSemester,
  getCurrentSemester,
  getSemesters,
} from "@features/semesters/api/semesters";
import { getAllProjects } from "@features/projects/api/projectService";
import type { Project, ProjectState } from "@features/projects/types/project";
import { getUser, getUserRole } from "@features/auth/api/clientAuth";
import type { Role } from "@features/projects/lib/cardAction";
import {
  applyStateFilter,
  readStateFromSearchParams,
} from "@features/projects/lib/applyStateFilter";

const ITEMS_PER_PAGE = 5;

const HERO_COPY: Record<
  Role,
  { eyebrowPrefix: string; title: string; lede: string }
> = {
  Administrador: {
    eyebrowPrefix: "Período",
    title: "Seguimiento de trabajos en curso",
    lede: "Cola operativa de proyectos y tesis con evaluaciones pendientes en el período activo.",
  },
  Jurado: {
    eyebrowPrefix: "Tus asignaciones ·",
    title: "Evaluaciones pendientes",
    lede: "Trabajos en los que estás asignado como jurado, ordenados por fecha de entrega.",
  },
  Tutor: {
    eyebrowPrefix: "Tus asesorados ·",
    title: "Mis tutorías",
    lede: "Avance del semestre de los estudiantes que asesoras. La evaluación la realizan los jurados.",
  },
  Estudiante: {
    eyebrowPrefix: "Mi proyecto ·",
    title: "",
    lede: "",
  },
};

const DEFENSE_STATES: readonly ProjectState[] = ["pending_defense", "pending_defensa"];

const PENDING_REVIEW_STATES: readonly ProjectState[] = [
  "pending_review_1",
  "pending_review_2",
  "pending_articulo",
  "pending_entrega",
];

export default function TrackingPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const activeStateFilter = readStateFromSearchParams(searchParams ?? null);

  const role = useMemo<Role>(() => (getUserRole() as Role) ?? "Administrador", []);
  const viewerUser = useMemo(() => getUser(), []);
  const viewerId = useMemo<number | undefined>(() => {
    return typeof viewerUser?.id === "number" ? viewerUser.id : undefined;
  }, [viewerUser]);

  const isStudent = role === "Estudiante";

  const [projects, setProjects] = useState<Project[]>([]);
  const [semester, setSemester] = useState<string>("");
  const [availableSemesters, setAvailableSemesters] = useState<string[]>([]);
  const [isDataLoaded, setIsDataLoaded] = useState(false);

  const [searchQuery, setSearchQuery] = useState("");
  const [modalidadFilter, setModalidadFilter] = useState<"all" | "proyecto" | "tesis">("all");
  const [tutorFilter, setTutorFilter] = useState("");
  const [currentPage, setCurrentPage] = useState(1);

  useEffect(() => {
    let mounted = true;
    (async () => {
      const [apiProjects, semestersFromApi] = await Promise.all([
        getAllProjects(),
        getSemesters(),
      ]);
      if (!mounted) return;
      setProjects(apiProjects);

      const semesters = getAvailableSemesters(
        apiProjects,
        semestersFromApi.map((s) => s.period),
      );
      const stored = getStoredSemester();
      const fallback = getCurrentSemester();
      const chosen = semesters.length
        ? semesters.includes(stored)
          ? stored
          : semesters[0]
        : stored || fallback;

      setAvailableSemesters(semesters.length ? semesters : [chosen]);
      setSemester(semesters.includes(stored) ? stored : semesters[0] || chosen);
      setIsDataLoaded(true);
    })();
    return () => { mounted = false; };
  }, []);

  const semesterProjects = useMemo(
    () =>
      projects
        .filter((p) => !semester || p.period === semester)
        .sort(
          (a, b) =>
            new Date(b.submittedDate).getTime() -
            new Date(a.submittedDate).getTime(),
        ),
    [projects, semester],
  );

  const ownProject = useMemo<Project | undefined>(() => {
    if (!isStudent) return undefined;
    return semesterProjects[0];
  }, [isStudent, semesterProjects]);

  const filteredItems = useMemo(() => {
    if (isStudent) return semesterProjects;

    let items = semesterProjects.filter(
      (p) => p.state !== "approved" && p.state !== "failed_final",
    );

    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      items = items.filter(
        (p) =>
          p.title.toLowerCase().includes(q) ||
          p.student.toLowerCase().includes(q) ||
          (p.advisorNames ?? []).some((n) => n.toLowerCase().includes(q)),
      );
    }

    if (modalidadFilter !== "all") {
      items = items.filter((p) => p.type === modalidadFilter);
    }

    if (tutorFilter) {
      const tf = tutorFilter.toLowerCase();
      items = items.filter((p) =>
        (p.advisorNames ?? []).some((n) => n.toLowerCase().includes(tf)),
      );
    }

    items = applyStateFilter(items, activeStateFilter);

    return items;
  }, [semesterProjects, searchQuery, modalidadFilter, tutorFilter, activeStateFilter, isStudent]);

  useEffect(() => {
    setCurrentPage(1);
  }, [searchQuery, modalidadFilter, tutorFilter, activeStateFilter, semester]);

  const totalPages = Math.max(1, Math.ceil(filteredItems.length / ITEMS_PER_PAGE));
  const paginatedItems = useMemo(() => {
    const start = (currentPage - 1) * ITEMS_PER_PAGE;
    return filteredItems.slice(start, start + ITEMS_PER_PAGE);
  }, [filteredItems, currentPage]);

  const total = semesterProjects.filter(
    (p) => p.state !== "approved" && p.state !== "failed_final",
  ).length;

  const pendingMine = useMemo(() => {
    if (role === "Jurado") {
      return semesterProjects.filter(
        (p) =>
          (viewerId == null || p.reviewer === viewerId) &&
          p.state !== "approved" &&
          p.state !== "failed_final",
      ).length;
    }
    return semesterProjects.filter((p) =>
      (PENDING_REVIEW_STATES as readonly string[]).includes(p.state),
    ).length;
  }, [semesterProjects, role, viewerId]);

  const defensesThisWeek = useMemo(
    () =>
      semesterProjects.filter((p) =>
        (DEFENSE_STATES as readonly string[]).includes(p.state),
      ).length,
    [semesterProjects],
  );

  const heroCopy = HERO_COPY[role];
  const heroTitle = isStudent
    ? "Estado de mi trabajo"
    : heroCopy.title;
  const heroEyebrow = `${heroCopy.eyebrowPrefix} ${semester}`.trim();

  const handleFaseChange = (val: string) => {
    if (val) {
      router.replace(`/dashboard/tracking?state=${val}`);
    } else {
      router.replace("/dashboard/tracking");
    }
  };

  return (
    <>
      <DashboardHeader pageTitle={isStudent ? "Estado de mi trabajo" : "Seguimiento"} />

      <main className="flex-1 p-4 sm:p-6 lg:p-8 overflow-y-auto bg-surface-muted">
        <div className="max-w-screen-2xl mx-auto">

          <section className="dashboard-hero-bg relative overflow-hidden rounded-2xl border border-border-subtle px-7 py-6 mb-6">
            <div className="relative z-10 flex flex-col gap-5 md:flex-row md:items-start md:justify-between">
              <div className="flex flex-col gap-1.5">
                <p className="flex items-center gap-2 text-[10px] font-extrabold uppercase tracking-[0.14em] text-primary">
                  <span
                    aria-hidden
                    className="inline-block h-[2px] w-6 rounded-full bg-gradient-to-r from-primary to-[var(--brand-orange)]"
                  />
                  {heroEyebrow}
                </p>
                <h1 className="text-3xl font-extrabold leading-tight tracking-[-0.03em] text-text-strong md:text-[34px]">
                  {heroTitle}
                </h1>
                {!isStudent && (
                  <p className="max-w-[480px] text-sm font-medium leading-relaxed text-text-muted mt-1">
                    {heroCopy.lede}
                  </p>
                )}
                {!isStudent && isDataLoaded && (
                  <p className="seg-pill-summary">
                    <span className="num">{total}</span> en curso &middot;{" "}
                    <span className="num">{pendingMine}</span> esperando tu acción &middot;{" "}
                    <span className="num">{defensesThisWeek}</span> defensas esta semana
                  </p>
                )}
                {isStudent && ownProject && (
                  <p className="seg-pill-summary">
                    {ownProject.type === "tesis" ? "TEG" : "PTEG"} &middot;{" "}
                    {ownProject.advisorNames?.[0] ?? "Sin tutor"} &middot;{" "}
                    {ownProject.reviewerName ?? "Sin jurado"}
                  </p>
                )}
              </div>

              <div className="flex items-start gap-3">
                <SemesterSelector
                  selectedSemester={semester}
                  availableSemesters={availableSemesters}
                  onSemesterChange={(sem) => {
                    setStoredSemester(sem);
                    setSemester(sem);
                  }}
                />
              </div>
            </div>
          </section>

          {isStudent ? (
            <div>
              {ownProject ? (
                <MyProjectCard project={ownProject} />
              ) : (
                <div className="seg-table-card">
                  <div className="seg-empty">
                    <p>No tienes ningún proyecto registrado en este período.</p>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <>
              <div className="flex flex-col xl:flex-row items-stretch xl:items-center gap-3 mb-4">
                <div className="relative flex-1">
                  <input
                    type="text"
                    placeholder="Buscar..."
                    aria-label="Buscar"
                    value={searchQuery}
                    onChange={(e) => {
                      setSearchQuery(e.target.value);
                    }}
                    className="w-full pl-4 pr-4 h-11 bg-surface border border-border-subtle rounded-xl text-[13px] font-medium text-text-strong placeholder:text-text-muted focus:outline-none focus:border-primary transition-colors"
                  />
                </div>

                <div className="flex items-center gap-2 flex-wrap">
                  <label className="text-[11px] font-semibold uppercase tracking-[0.1em] text-text-muted">
                    Fase
                    <select
                      aria-label="Fase"
                      value={activeStateFilter ?? ""}
                      onChange={(e) => handleFaseChange(e.target.value)}
                      className="ml-2 h-9 px-3 bg-surface border border-border-subtle rounded-lg text-[12px] font-medium text-text-strong focus:outline-none focus:border-primary"
                    >
                      <option value="">Todas</option>
                      <option value="pending_review_1">Rev 1</option>
                      <option value="pending_review_2">Rev 2</option>
                      <option value="pending_defense">Defensa</option>
                    </select>
                  </label>

                  <label className="text-[11px] font-semibold uppercase tracking-[0.1em] text-text-muted">
                    Modalidad
                    <select
                      aria-label="Modalidad"
                      value={modalidadFilter}
                      onChange={(e) =>
                        setModalidadFilter(
                          e.target.value as "all" | "proyecto" | "tesis",
                        )
                      }
                      className="ml-2 h-9 px-3 bg-surface border border-border-subtle rounded-lg text-[12px] font-medium text-text-strong focus:outline-none focus:border-primary"
                    >
                      <option value="all">Todas</option>
                      <option value="proyecto">PTEG</option>
                      <option value="tesis">TEG</option>
                    </select>
                  </label>

                  {role === "Administrador" && (
                    <label className="text-[11px] font-semibold uppercase tracking-[0.1em] text-text-muted">
                      Tutor
                      <select
                        aria-label="Tutor"
                        value={tutorFilter}
                        onChange={(e) => setTutorFilter(e.target.value)}
                        className="ml-2 h-9 px-3 bg-surface border border-border-subtle rounded-lg text-[12px] font-medium text-text-strong focus:outline-none focus:border-primary"
                      >
                        <option value="">Todos</option>
                        {Array.from(
                          new Set(
                            semesterProjects.flatMap((p) => p.advisorNames ?? [])
                          )
                        ).sort().map((name) => (
                          <option key={name} value={name}>{name}</option>
                        ))}
                      </select>
                    </label>
                  )}
                </div>
              </div>

              {!isDataLoaded ? (
                <div className="flex justify-center items-center py-20">
                  <div className="w-8 h-8 rounded-full border-4 border-border-subtle border-t-primary animate-spin" />
                </div>
              ) : (
                <SeguimientoTable
                  items={paginatedItems}
                  role={role}
                  viewerId={viewerId}
                  pagination={{
                    currentPage,
                    totalPages,
                    onPageChange: setCurrentPage,
                  }}
                />
              )}
            </>
          )}
        </div>
      </main>
    </>
  );
}
