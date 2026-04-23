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
  SemesterStrip,
  StatTile,
} from "@shared/ui";

import { buildDashboardContent } from "../lib/roleContent";

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

  const content = useMemo(() => {
    if (!semesterPeriod) return null;
    return buildDashboardContent({
      role,
      user: user ? { role: user.role, id: user.id, semester: user.semester } : null,
      semester: semesterPeriod,
      projects,
      assignedProjectsCount: role === "Jurado" ? projects.length : undefined,
    });
  }, [role, user, semesterPeriod, projects]);

  const greeting = (() => {
    const h = new Date().getHours();
    if (h < 12) return "Buenos días";
    if (h < 18) return "Buenas tardes";
    return "Buenas noches";
  })();

  const subtitle = role === "Estudiante"
    ? "Resumen de tu trabajo."
    : "Resumen del período académico.";

  return (
    <>
      <DashboardHeader pageTitle="Dashboard" />
      <main className="flex-1 overflow-hidden bg-surface-muted p-3 sm:p-4 md:p-6 lg:p-8">
        <div className="mx-auto flex h-full max-w-7xl flex-col gap-4">
          <section className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div>
              <h1 className="text-2xl font-extrabold tracking-tight text-text-strong md:text-3xl">
                {greeting}, <span className="text-primary">{userName}</span>
              </h1>
              <p className="text-sm text-text-muted">{subtitle}</p>
            </div>
            {semesterObj && <SemesterStrip semester={semesterObj} />}
          </section>

          {isLoading || !content ? (
            <div className="grid flex-1 min-h-0 grid-cols-1 gap-4 lg:grid-cols-[minmax(0,2fr)_minmax(280px,1fr)]">
              <div className="flex min-h-0 flex-col gap-4">
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                  <div className="h-[140px] animate-pulse rounded-2xl bg-surface-sunken" />
                  <div className="h-[140px] animate-pulse rounded-2xl bg-surface-sunken" />
                </div>
                <div className="flex-1 animate-pulse rounded-xl bg-surface-sunken" />
              </div>
              <div className="animate-pulse rounded-xl bg-surface-sunken" />
            </div>
          ) : (
            <div className="grid flex-1 min-h-0 grid-cols-1 gap-4 lg:grid-cols-[minmax(0,2fr)_minmax(280px,1fr)]">
              <div className="flex min-h-0 flex-col gap-4">
                <div
                  className={
                    content.stats.length === 1
                      ? "grid grid-cols-1 gap-4"
                      : "grid grid-cols-1 gap-4 sm:grid-cols-2"
                  }
                >
                  {content.stats.map((s, i) => (
                    <StatTile
                      key={`${s.label}-${i}`}
                      tone={s.tone}
                      label={s.label}
                      value={s.value}
                      breakdown={s.breakdown}
                      href={s.href}
                    />
                  ))}
                </div>
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
              </div>
              <ActivityFeed items={content.feedItems} />
            </div>
          )}
        </div>
      </main>
    </>
  );
};

export default Dashboard;
