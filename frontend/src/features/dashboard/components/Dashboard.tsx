"use client";

import React, { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import DashboardHeader from "@widgets/header/DashboardHeader";
import { getUser } from "@features/auth/api/clientAuth";
import { getAllProjects } from "@features/projects/api/projectService";
import {
  type Semester,
  fetchActiveSemester,
  getSemesters,
  getStoredSemester,
  setStoredSemester,
  getAvailableSemesters,
} from "@features/semesters/api/semesters";
import type { Project } from "@features/projects/types/project";
import {
  ActivityFeed,
  ListPanel,
  ListRow,
  StatTile,
} from "@shared/ui";
import { getSemesterProgress } from "@features/dashboard/lib/semesterWeek";

import { buildDashboardContent } from "../lib/roleContent";
import { DashboardHero } from "./DashboardHero";

const Dashboard: React.FC = () => {
  const router = useRouter();
  const user = useMemo(() => getUser(), []);
  const userName = user?.fullName || user?.email?.split("@")[0] || "Usuario";
  const role = (user?.role ?? "Estudiante") as
    | "Administrador"
    | "Estudiante"
    | "Jurado"
    | "Tutor";

  const [semesterObj, setSemesterObj] = useState<Semester | null>(null);
  const [semesterPeriod, setSemesterPeriod] = useState<string>("");
  const [projects, setProjects] = useState<Project[]>([]);
  const [semesterOptions, setSemesterOptions] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchActiveSemester().then((active) => {
      if (active) {
        setSemesterObj(active);
        setSemesterPeriod(active.period);
      } else {
        setSemesterPeriod(getStoredSemester());
      }
    });
  }, []);

  useEffect(() => {
    if (!semesterPeriod) return;
    let cancelled = false;
    (async () => {
      try {
        const [projectList, semesters] = await Promise.all([getAllProjects(), getSemesters()]);
        if (cancelled) return;
        setProjects(projectList);
        setSemesterOptions(semesters.map((s) => s.period));
        if (!semesterObj) {
          const match = semesters.find((s) => s.period === semesterPeriod) ?? null;
          setSemesterObj(match);
        }
      } catch (err) {
        console.error("Failed to fetch dashboard data", err);
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [semesterPeriod, semesterObj]);

  useEffect(() => {
    const available = getAvailableSemesters(projects, semesterOptions);
    if (available.length > 0 && !available.includes(semesterPeriod)) {
      setSemesterPeriod(available[0]);
      setStoredSemester(available[0]);
    }
  }, [projects, semesterOptions, semesterPeriod]);

  const now = useMemo(() => new Date(), []);

  const semesterDaysRemaining = useMemo(() => {
    if (!semesterObj) return 0;
    const p = getSemesterProgress(semesterObj, now);
    if (p.status === "in-progress") {
      return Math.max(0, (p.totalWeeks - p.week) * 7);
    }
    if (p.status === "not-started") return p.daysUntilStart;
    return 0;
  }, [semesterObj, now]);

  const todaysDeliveries = useMemo(() => {
    if (!semesterPeriod) return 0;
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    return projects.filter((p) => {
      if (p.period !== semesterPeriod || !p.submittedDate) return false;
      const d = new Date(p.submittedDate);
      d.setHours(0, 0, 0, 0);
      return d.getTime() === today.getTime();
    }).length;
  }, [projects, semesterPeriod]);

  const content = useMemo(() => {
    if (!semesterPeriod) return null;
    return buildDashboardContent({
      role,
      user: user ? { role: user.role, id: user.id, semester: user.semester } : null,
      semester: semesterPeriod,
      projects,
      assignedProjectsCount: role === "Jurado" ? projects.length : undefined,
      semesterDaysRemaining,
      totalProjects: projects.filter((p) => p.period === semesterPeriod).length,
      todaysDeliveries,
    });
  }, [role, user, semesterPeriod, projects, semesterDaysRemaining, todaysDeliveries]);

  const eyebrow = (() => {
    const h = now.getHours();
    const greet = h < 12 ? "Buenos días" : h < 18 ? "Buenas tardes" : "Buenas noches";
    const dayMonth = now.toLocaleDateString("es-VE", { day: "numeric", month: "long" });
    return `${greet} · ${dayMonth}`;
  })();

  const greetingByRole: Record<typeof role, string> = {
    Administrador: "Bienvenido",
    Tutor: "Hola",
    Jurado: "Hola",
    Estudiante: "Hola",
  };

  const ledeByRole: Record<typeof role, string> = {
    Administrador: "Resumen del período académico — supervisión global, métricas vivas, atajos contextuales.",
    Tutor: "Tus proyectos como tutor — los que requieren tu atención más arriba, comentarios sin respuesta a un click.",
    Jurado: "Tus proyectos asignados, evaluaciones pendientes y defensas próximas en una sola vista.",
    Estudiante: "Resumen de tu proyecto — estado actual, comentarios pendientes y tiempo restante del período.",
  };

  const tilesGridClass =
    role === "Estudiante"
      ? "grid grid-cols-1 gap-3 sm:grid-cols-3"
      : "grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4";

  return (
    <>
      <DashboardHeader pageTitle="Dashboard" />
      <main className="flex-1 overflow-y-auto bg-surface-muted p-3 sm:p-4 md:p-6 lg:p-8">
        <div className="mx-auto flex max-w-7xl flex-col gap-4">
          {semesterObj ? (
            <DashboardHero
              eyebrow={eyebrow}
              greeting={greetingByRole[role]}
              userName={userName}
              lede={ledeByRole[role]}
              semester={semesterObj}
              now={now}
              semesterStats={content?.semesterStats}
            />
          ) : (
            <div className="h-[140px] animate-pulse rounded-2xl bg-surface-sunken" />
          )}

          {isLoading || !content ? (
            <>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
                {[0, 1, 2, 3].map((i) => (
                  <div key={i} className="h-[180px] animate-pulse rounded-2xl bg-surface-sunken" />
                ))}
              </div>
              <div className="grid grid-cols-1 gap-3 lg:grid-cols-[2fr_1fr]">
                <div className="h-[260px] animate-pulse rounded-2xl bg-surface-sunken" />
                <div className="h-[260px] animate-pulse rounded-2xl bg-surface-sunken" />
              </div>
            </>
          ) : (
            <>
              <div className={tilesGridClass}>
                {content.stats.map((s, i) => (
                  <StatTile
                    key={`${s.label}-${i}`}
                    tone={s.tone}
                    label={s.label}
                    value={s.value}
                    breakdown={s.breakdown}
                    segments={s.segments}
                    chips={s.chips}
                    urgent={s.urgent}
                    href={s.href}
                    spanCols={role === "Estudiante" && i === 0 ? 3 : 1}
                  />
                ))}
              </div>
              <div className="grid grid-cols-1 gap-3 lg:grid-cols-[2fr_1fr]">
                <ListPanel
                  title={content.listTitle}
                  count={content.listItems.length}
                  isEmpty={content.listItems.length === 0}
                  emptyText={content.listEmpty.text}
                  emptyHint={content.listEmpty.hint}
                >
                  {content.listItems.map((row) => (
                    <ListRow
                      key={row.id}
                      title={row.title}
                      subtitle={row.subtitle}
                      type={row.type}
                      status={row.status as "checked" | "pending" | "rejected" | "upcoming" | undefined}
                      hint={row.hint}
                      href={row.href}
                      onHoverHref={row.href ? () => router.prefetch(row.href!) : undefined}
                    />
                  ))}
                </ListPanel>
                <ActivityFeed items={content.feedItems} />
              </div>
            </>
          )}
        </div>
      </main>
    </>
  );
};

export default Dashboard;
