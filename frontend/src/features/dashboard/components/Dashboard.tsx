"use client";

import React, { useEffect, useMemo, useState, useCallback } from "react";
import DashboardHeader from "@widgets/header/DashboardHeader";
import { PageShell, PageToolbar, PageBody, SectionHeader, StatTile, DataTable } from "@widgets/page-shell";
import type { ColumnDef } from "@widgets/page-shell";
import { Surface } from "@shared/ui/Surface";
import { Project } from "@features/projects/types/project";
import { getAllProjects } from "@features/projects/api/projectService";
import {
  getAvailableSemesters,
  getSemesters,
  getStoredSemester,
  setStoredSemester,
  fetchActiveSemester,
} from "@features/semesters/api/semesters";
import { useRouter } from "next/navigation";
import { getUser } from "@features/auth/api/clientAuth";

const STATUS_DOT: Record<string, string> = {
  checked: "bg-emerald-500",
  pending: "bg-amber-500",
  rejected: "bg-rose-500",
};

const STATUS_LABEL: Record<string, string> = {
  checked: "Aprobado",
  pending: "Pendiente",
  rejected: "Rechazado",
};

interface ProjectRow {
  id: number;
  type: string;
  title: string;
  student: string;
  tutor?: string;
  status?: string;
  date: string;
}

interface FeedEvent {
  id: number;
  text: string;
  time: string;
}

interface DashboardData {
  ptegStats: { total: number; checked: number; pending: number; rejected: number };
  tegStats: { total: number; checked: number; pending: number };
  projectsToReview: ProjectRow[];
  progressFeed: FeedEvent[];
}

function formatDate(dateStr: string): string {
  if (!dateStr) return "—";
  const d = new Date(dateStr);
  if (isNaN(d.getTime())) return dateStr;
  const day = String(d.getDate()).padStart(2, "0");
  const month = String(d.getMonth() + 1).padStart(2, "0");
  const year = String(d.getFullYear()).slice(-2);
  return `${day}.${month}.${year}`;
}

const Dashboard: React.FC = () => {
  const router = useRouter();
  const user = useMemo(() => getUser(), []);
  const isStudent = user?.role === "Estudiante";
  const userRole = user?.role || "Usuario";

  const [semester, setSemester] = useState("");
  const [apiProjects, setApiProjects] = useState<Project[]>([]);
  const [semesterOptions, setSemesterOptions] = useState<string[]>([]);
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);

  useEffect(() => {
    fetchActiveSemester().then((active) => {
      setSemester(active ? active.period : getStoredSemester());
    });
  }, []);

  useEffect(() => {
    if (!semester) return;
    const load = async () => {
      try {
        const [projects, semesters] = await Promise.all([getAllProjects(), getSemesters()]);
        setApiProjects(projects);
        setSemesterOptions(semesters.map((s) => s.period));

        const allProyectos = projects.filter((p) => p.type === "proyecto");
        const allTesis = projects.filter((p) => p.type === "tesis");

        if (isStudent) {
          const myPteg = allProyectos.find((p) => p.period === semester);
          const myTeg = allTesis.find((p) => p.period === semester);
          const myProject = myTeg || myPteg;

          const ptegStats = {
            total: myPteg ? 1 : 0,
            checked: myPteg?.status === "checked" ? 1 : 0,
            pending: myPteg?.status === "pending" ? 1 : 0,
            rejected: myPteg?.status === "rejected" ? 1 : 0,
          };
          const tegStats = {
            total: myTeg ? 1 : 0,
            checked: myTeg?.status === "checked" ? 1 : 0,
            pending: myTeg?.status === "pending" ? 1 : 0,
          };
          const projectsToReview: ProjectRow[] = myProject
            ? [{
                id: myProject.id,
                type: myTeg ? "TEG" : "PTEG",
                title: myProject.title,
                student: myProject.student,
                tutor: myProject.advisorNames?.[0],
                status: myProject.status,
                date: myProject.submittedDate,
              }]
            : [];

          const feedEvents: FeedEvent[] = [];
          if (myProject?.submittedDate) feedEvents.push({ id: 0, text: "Has enviado tu proyecto.", time: myProject.submittedDate });
          if (myProject?.reviewDate) feedEvents.push({ id: 1, text: "Tu proyecto ha sido revisado.", time: myProject.reviewDate });

          setDashboardData({ ptegStats, tegStats, projectsToReview, progressFeed: feedEvents });
          return;
        }

        const semP = allProyectos.filter((p) => p.period === semester);
        const semT = allTesis.filter((t) => t.period === semester);

        const ptegStats = {
          total: semP.length,
          checked: semP.filter((p) => p.status === "checked").length,
          pending: semP.filter((p) => p.status === "pending").length,
          rejected: semP.filter((p) => p.status === "rejected").length,
        };
        const tegStats = {
          total: semT.length,
          checked: semT.filter((t) => t.status === "checked").length,
          pending: semT.filter((t) => t.status === "pending").length,
        };

        const semPending = [...semP, ...semT].filter((p) => p.status === "pending");
        const projectsToReview: ProjectRow[] = semPending
          .sort((a, b) => new Date(b.submittedDate).getTime() - new Date(a.submittedDate).getTime())
          .slice(0, 10)
          .map((p) => ({
            id: p.id,
            type: "stage1Passed" in p ? "TEG" : "PTEG",
            title: p.title,
            student: p.student,
            tutor: p.advisorNames?.[0],
            status: p.status,
            date: p.submittedDate,
          }));

        const feedRaw: { date: string; text: string }[] = [];
        [...semP, ...semT].forEach((p) => {
          if (p.submittedDate) feedRaw.push({ date: p.submittedDate, text: `Nueva entrega de ${p.student}` });
          if (p.reviewDate) {
            const label = p.status === "checked"
              ? `Proyecto de ${p.student} aprobado`
              : p.status === "rejected"
              ? `Correcciones para ${p.student}`
              : `Comentarios en proyecto de ${p.student}`;
            feedRaw.push({ date: p.reviewDate, text: label });
          }
        });

        const progressFeed: FeedEvent[] = feedRaw
          .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
          .slice(0, 5)
          .map((e, i) => {
            const diffDays = Math.floor((Date.now() - new Date(e.date).getTime()) / 86400000);
            const time = diffDays === 0 ? "Hoy" : diffDays === 1 ? "Ayer" : `${diffDays}d`;
            return { id: i, text: e.text, time };
          });

        setDashboardData({ ptegStats, tegStats, projectsToReview, progressFeed });
      } catch (err) {
        console.error("Failed to fetch projects", err);
      }
    };
    load();
  }, [semester, isStudent]);

  useEffect(() => {
    const available = getAvailableSemesters(apiProjects, semesterOptions);
    if (available.length > 0 && !available.includes(semester)) {
      setSemester(available[0]);
      setStoredSemester(available[0]);
    }
  }, [apiProjects, semesterOptions, semester]);

  const handleProjectClick = useCallback(
    (row: ProjectRow) => {
      router.push(row.type === "TEG" ? `/dashboard/tesis/${row.id}` : `/dashboard/proyectos/${row.id}`);
    },
    [router]
  );

  const statTiles = useMemo(() => {
    if (!dashboardData) return [];
    if (isStudent) {
      const proj = dashboardData.projectsToReview[0];
      const statusAccent = proj?.status === "checked"
        ? "success"
        : proj?.status === "rejected"
        ? "destructive"
        : proj?.status === "pending"
        ? "pending"
        : undefined;
      const statusLabel = !proj
        ? "Sin proyecto"
        : proj.status === "checked"
        ? "Aprobado"
        : proj.status === "rejected"
        ? "Requiere correcciones"
        : "En revisión";
      return [
        { label: "Estado actual", value: statusLabel, accent: statusAccent as "success" | "pending" | "destructive" | undefined },
        { label: "Próxima presentación", value: "—", accent: undefined as undefined },
        { label: "Evaluaciones recibidas", value: dashboardData.tegStats.checked + dashboardData.ptegStats.checked, accent: undefined as undefined },
        {
          label: "Promedio",
          value: "—",
          accent: undefined as undefined,
        },
      ];
    }
    return [
      {
        label: "PTEG activos",
        value: dashboardData.ptegStats.total,
        accent: "pteg" as const,
        subtext: `${dashboardData.ptegStats.pending} en revisión`,
        variant: "hero" as const,
      },
      {
        label: "TEG activos",
        value: dashboardData.tegStats.total,
        accent: "teg" as const,
        subtext: `${dashboardData.tegStats.pending} pendientes`,
      },
      {
        label: "Evaluaciones pendientes",
        value: dashboardData.ptegStats.pending + dashboardData.tegStats.pending,
        accent: undefined as undefined,
        subtext: "proyectos y tesis",
      },
      {
        label: "Aprobados este período",
        value: dashboardData.ptegStats.checked + dashboardData.tegStats.checked,
        accent: "success" as const,
        subtext: "PTEG + TEG",
      },
    ];
  }, [dashboardData, isStudent]);

  const columns: ColumnDef<ProjectRow>[] = [
    {
      key: "type",
      header: "Tipo",
      width: "64px",
      render: (row) => (
        <span
          className={`inline-flex items-center justify-center w-6 h-6 rounded border font-mono text-[10px] font-semibold ${
            row.type === "TEG"
              ? "text-[color:var(--color-accent-teg)] border-[color:var(--color-accent-teg)]/30"
              : "text-[color:var(--color-accent-pteg)] border-[color:var(--color-accent-pteg)]/30"
          }`}
        >
          {row.type === "TEG" ? "T" : "P"}
        </span>
      ),
    },
    {
      key: "title",
      header: "Título",
      render: (row) => (
        <span className="truncate text-slate-800 font-medium">{row.title}</span>
      ),
    },
    {
      key: "student",
      header: "Estudiante",
      width: "192px",
      render: (row) => <span className="truncate">{row.student}</span>,
    },
    {
      key: "tutor",
      header: "Tutor",
      width: "160px",
      render: (row) => <span className="truncate text-slate-500">{row.tutor || "—"}</span>,
    },
    {
      key: "status",
      header: "Estado",
      width: "128px",
      render: (row) => (
        <span className="flex items-center gap-1.5">
          <span
            className={`inline-block w-1.5 h-1.5 rounded-full flex-shrink-0 ${STATUS_DOT[row.status ?? ""] ?? "bg-slate-300"}`}
          />
          <span className="text-slate-600 text-xs">
            {STATUS_LABEL[row.status ?? ""] ?? row.status ?? "—"}
          </span>
        </span>
      ),
    },
    {
      key: "date",
      header: "Entregado",
      width: "96px",
      render: (row) => (
        <span className="font-mono tabular-nums text-xs text-slate-500">
          {formatDate(row.date)}
        </span>
      ),
    },
  ];

  if (!semester) return null;

  return (
    <>
      <DashboardHeader pageTitle="Dashboard" />
      <PageShell>
        <PageToolbar>
          <div className="flex items-baseline gap-3 min-w-0 flex-1">
            <PageToolbar.Title>Dashboard</PageToolbar.Title>
            <PageToolbar.Subtitle>{semester} · {userRole}</PageToolbar.Subtitle>
          </div>
          <PageToolbar.Actions>
            <div className="scale-90 origin-right">
              <span className="font-mono text-xs text-slate-500 border border-slate-200 rounded px-2 py-1">
                {semester}
              </span>
            </div>
          </PageToolbar.Actions>
        </PageToolbar>

        <PageBody>
          {!dashboardData ? (
            <div className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                {Array.from({ length: 4 }).map((_, i) => (
                  <div key={i} className="h-24 rounded-xl bg-slate-100 animate-pulse" />
                ))}
              </div>
              <div className="h-48 rounded-xl bg-slate-100 animate-pulse" />
            </div>
          ) : (
            <>
              <div
                className="section-in grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4"
                style={{ "--section-i": 0 } as React.CSSProperties}
              >
                {statTiles.map((tile, i) => (
                  <StatTile
                    key={i}
                    label={tile.label}
                    value={tile.value}
                    subtext={"subtext" in tile ? tile.subtext : undefined}
                    accent={tile.accent}
                    variant={"variant" in tile ? tile.variant : undefined}
                  />
                ))}
              </div>

              <section
                className="section-in"
                style={{ "--section-i": 1 } as React.CSSProperties}
              >
                <SectionHeader title="PROYECTOS RECIENTES">
                  <SectionHeader.Action href="/dashboard/proyectos">
                    Ver todos →
                  </SectionHeader.Action>
                </SectionHeader>
                <DataTable<ProjectRow>
                  columns={columns}
                  data={dashboardData.projectsToReview}
                  onRowClick={handleProjectClick}
                  rowAccent={(row) => row.type === "TEG" ? "teg" : "pteg"}
                  getRowKey={(row) => row.id}
                  empty="Sin proyectos este período"
                />
              </section>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <section
                  className="section-in"
                  style={{ "--section-i": 2 } as React.CSSProperties}
                >
                  <SectionHeader title="PRÓXIMAS FECHAS" />
                  <Surface className="p-0">
                    <ul className="divide-y divide-slate-100">
                      {dashboardData.progressFeed.length === 0 ? (
                        <li className="h-16 flex items-center px-4 font-mono text-xs text-slate-400">
                          Sin fechas programadas
                        </li>
                      ) : (
                        dashboardData.progressFeed.slice(0, 5).map((event) => (
                          <li key={event.id} className="flex items-start justify-between gap-2 px-4 py-3">
                            <span className="text-sm text-slate-700 truncate">{event.text}</span>
                            <span className="font-mono tabular-nums text-xs text-slate-400 flex-shrink-0">
                              {event.time}
                            </span>
                          </li>
                        ))
                      )}
                    </ul>
                  </Surface>
                </section>

                <section
                  className="section-in"
                  style={{ "--section-i": 3 } as React.CSSProperties}
                >
                  <SectionHeader title="ACTIVIDAD RECIENTE" />
                  <Surface className="p-0">
                    <ul className="divide-y divide-slate-100">
                      {dashboardData.progressFeed.length === 0 ? (
                        <li className="h-16 flex items-center px-4 font-mono text-xs text-slate-400">
                          Sin actividad reciente
                        </li>
                      ) : (
                        dashboardData.progressFeed.slice(0, 5).map((event) => (
                          <li key={event.id} className="flex items-start justify-between gap-2 px-4 py-3">
                            <span className="text-sm text-slate-700 truncate">{event.text}</span>
                            <span className="font-mono tabular-nums text-xs text-slate-400 flex-shrink-0">
                              {event.time}
                            </span>
                          </li>
                        ))
                      )}
                    </ul>
                  </Surface>
                </section>
              </div>
            </>
          )}
        </PageBody>
      </PageShell>
    </>
  );
};

export default Dashboard;
