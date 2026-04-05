"use client";

import React, { useEffect, useRef, useMemo, memo, useState, useCallback } from "react";
import {
  CheckCircle,
  FileText,
  BookOpen,
  XCircle,
  Clock,
  Check,
  MessageSquare,
  Calendar,
  ArrowRight,
  Sparkles,
  TrendingUp,
} from "lucide-react";
import DashboardHeader from "@/components/layout/DashboardHeader";
import { Project } from "@/types/project";
import { getAllProjects } from "@/features/projects/projectService";
import {
  getAvailableSemesters,
  getSemesters,
  getStoredSemester,
  setStoredSemester,
  fetchActiveSemester,
} from "@/lib/semesters";
import { useRouter } from "next/navigation";
import { getUser } from "@/features/auth/clientAuth";

// ─── StatCard ───

interface StatCardProps {
  title: string;
  mainValue: string;
  mainLabel: string;
  secondaryStats: {
    label: string;
    value: number;
    color: string;
    icon: React.ReactNode;
  }[];
  icon: React.ReactNode;
  accentFrom: string;
  accentTo: string;
  bgClass: string;
}

const StatCard: React.FC<StatCardProps> = memo(
  ({ title, mainValue, mainLabel, secondaryStats, icon, accentFrom, accentTo, bgClass }) => {
    return (
      <div className={`stat-card relative rounded-2xl overflow-hidden group cursor-default transition-all duration-300 hover:-translate-y-1 hover:shadow-2xl ${bgClass}`}>
        {/* Animated gradient border top */}
        <div
          className="absolute inset-x-0 top-0 h-1"
          style={{ background: `linear-gradient(90deg, ${accentFrom}, ${accentTo})` }}
        />

        {/* Hover shimmer */}
        <div className="absolute inset-0 -translate-x-full group-hover:translate-x-full transition-transform duration-[1.2s] ease-out bg-gradient-to-r from-transparent via-white/[0.07] to-transparent pointer-events-none" />

        {/* Decorative corner glow */}
        <div
          className="absolute -top-12 -right-12 w-32 h-32 rounded-full opacity-20 group-hover:opacity-30 transition-opacity duration-500"
          style={{ background: `radial-gradient(circle, ${accentFrom}, transparent 70%)` }}
        />

        <div className="relative z-10 p-5 sm:p-6">
          {/* Header row */}
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="w-11 h-11 sm:w-12 sm:h-12 rounded-xl flex items-center justify-center bg-white/10 border border-white/10 backdrop-blur-sm shadow-inner">
                {icon}
              </div>
              <div>
                <h3 className="text-sm sm:text-base font-bold text-white/90 tracking-tight">{title}</h3>
                <p className="text-xs text-white/50 font-medium mt-0.5">{mainLabel}</p>
              </div>
            </div>
            <div
              className="px-2.5 py-1 rounded-lg text-[10px] font-bold uppercase tracking-widest border"
              style={{
                color: accentFrom,
                borderColor: `${accentFrom}40`,
                backgroundColor: `${accentFrom}15`,
              }}
            >
              Activo
            </div>
          </div>

          {/* Main value — large */}
          <div className="mb-5">
            <p
              className="text-4xl sm:text-5xl md:text-6xl font-extrabold text-white tracking-tighter leading-none"
              style={{ textShadow: `0 0 40px ${accentFrom}30` }}
            >
              {mainValue}
            </p>
          </div>

          {/* Secondary stats row */}
          {secondaryStats.length > 0 && (
            <div className="flex items-center gap-4 pt-4 border-t border-white/10">
              {secondaryStats.map((stat) => (
                <div key={stat.label} className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-lg flex items-center justify-center bg-white/10 border border-white/5">
                    <span style={{ color: stat.color }}>{stat.icon}</span>
                  </div>
                  <div>
                    <p className="text-lg font-bold text-white leading-none">{stat.value}</p>
                    <p className="text-[11px] text-white/50 font-medium">{stat.label}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  }
);
StatCard.displayName = "StatCard";

// ─── ProjectRow ───

const ProjectRow = memo(({ project, isStudent, onClick, onHover }: {
  project: { id: number; student: string; title: string; date: string; type: string; status?: string };
  isStudent: boolean;
  onClick: () => void;
  onHover?: () => void;
}) => {
  const statusColors: Record<string, string> = {
    checked: "bg-emerald-50 text-emerald-700 border-emerald-200",
    pending: "bg-amber-50 text-amber-700 border-amber-200",
    rejected: "bg-red-50 text-red-700 border-red-200",
  };
  const statusLabels: Record<string, string> = {
    checked: "Aprobado",
    pending: "Pendiente",
    rejected: "Rechazado",
  };

  return (
    <div
      className="project-row flex flex-col sm:flex-row sm:items-center gap-3 sm:gap-4 p-4 sm:p-5 rounded-2xl bg-white border border-slate-100 hover:border-usm-blue/20 hover:shadow-lg hover:shadow-blue-900/5 hover:-translate-y-0.5 transition-all duration-200 group"
      onMouseEnter={onHover}
    >
      {/* Type badge */}
      <div className={`flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center text-sm font-bold border ${
        project.type === "TEG"
          ? "bg-gradient-to-br from-purple-50 to-violet-50 text-purple-600 border-purple-100"
          : "bg-gradient-to-br from-blue-50 to-sky-50 text-usm-blue border-blue-100"
      }`}>
        {project.type === "TEG" ? <BookOpen className="w-4 h-4" /> : <FileText className="w-4 h-4" />}
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <p className="text-sm sm:text-base font-bold text-slate-800 line-clamp-1 group-hover:text-usm-blue transition-colors">{project.title}</p>
        <div className="flex flex-wrap items-center gap-2 text-xs text-slate-500 mt-1.5">
          <span className="font-medium text-slate-600">{project.student}</span>
          <span className="text-slate-300">&middot;</span>
          <span className="font-medium">{project.date}</span>
        </div>
      </div>

      {/* Status + action */}
      <div className="flex items-center gap-2 mt-1 sm:mt-0">
        {project.status && (
          <span className={`px-2.5 py-1 rounded-lg text-[11px] font-bold border ${statusColors[project.status] || ""}`}>
            {statusLabels[project.status] || project.status}
          </span>
        )}
        <button
          onClick={onClick}
          className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-sm font-semibold text-slate-600 bg-slate-50 border border-slate-200 hover:text-usm-blue hover:border-usm-blue/30 hover:bg-blue-50 active:scale-95 transition-all duration-200 touch-manipulation"
        >
          {isStudent ? "Ver" : "Revisar"}
          <ArrowRight className="w-3.5 h-3.5 transition-transform duration-200 group-hover:translate-x-0.5" />
        </button>
      </div>
    </div>
  );
});
ProjectRow.displayName = "ProjectRow";

// ─── Dashboard ───

const Dashboard: React.FC = () => {
  const router = useRouter();
  const user = useMemo(() => getUser(), []);
  const isStudent = user?.role === "Estudiante";
  const userName = user?.fullName || user?.email?.split("@")[0] || "Usuario";

  const [semester, setSemester] = useState("");
  const [apiProjects, setApiProjects] = useState<Project[]>([]);
  const [semesterOptions, setSemesterOptions] = useState<string[]>([]);
  const [dashboardData, setDashboardData] = useState<{
    ptegStats: { total: number; checked: number; pending: number; rejected: number };
    tegStats: { total: number; checked: number; pending: number };
    projectsToReview: { id: number; student: string; title: string; date: string; type: string; status?: string }[];
    progressFeed: { id: number; icon: React.ReactNode; text: string; time: string }[];
  } | null>(null);

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
          const ptegStats = { total: myPteg ? 1 : 0, checked: myPteg?.status === "checked" ? 1 : 0, pending: myPteg?.status === "pending" ? 1 : 0, rejected: myPteg?.status === "rejected" ? 1 : 0 };
          const tegStats = { total: myTeg ? 1 : 0, checked: myTeg?.status === "checked" ? 1 : 0, pending: myTeg?.status === "pending" ? 1 : 0 };
          const projectsToReview = myProject ? [{ id: myProject.id, student: myProject.student, title: myProject.title, date: myProject.submittedDate, type: myTeg ? "TEG" : "PTEG", status: myProject.status }] : [];
          const feedEvents: { date: string; type: "submitted" | "reviewed"; project: Project }[] = [];
          if (myProject?.submittedDate) feedEvents.push({ date: myProject.submittedDate, type: "submitted", project: myProject });
          if (myProject?.reviewDate) feedEvents.push({ date: myProject.reviewDate, type: "reviewed", project: myProject });
          setDashboardData({ ptegStats, tegStats, projectsToReview, progressFeed: feedEvents.map((e, i) => ({ id: i, icon: <FileText className="w-5 h-5 text-blue-600" />, text: e.type === "submitted" ? "Has enviado tu proyecto." : "Tu proyecto ha sido revisado.", time: e.date })) });
          return;
        }

        const semP = allProyectos.filter((p) => p.period === semester);
        const semT = allTesis.filter((t) => t.period === semester);
        const ptegStats = { total: semP.length, checked: semP.filter((p) => p.status === "checked").length, pending: semP.filter((p) => p.status === "pending").length, rejected: semP.filter((p) => p.status === "rejected").length };
        const tegStats = { total: semT.length, checked: semT.filter((t) => t.status === "checked").length, pending: semT.filter((t) => t.status === "pending").length };
        const semPending = [...semP, ...semT].filter((p) => p.status === "pending");
        const projectsToReview = semPending.sort((a, b) => new Date(b.submittedDate).getTime() - new Date(a.submittedDate).getTime()).slice(0, 5).map((p) => ({ id: p.id, student: p.student, title: p.title, date: p.submittedDate, type: "stage1Passed" in p ? "TEG" : "PTEG", status: p.status }));

        const feedEvents: { date: string; type: "submitted" | "reviewed"; project: Project }[] = [];
        [...semP, ...semT].forEach((p) => {
          if (p.submittedDate) feedEvents.push({ date: p.submittedDate, type: "submitted", project: p });
          if (p.reviewDate) feedEvents.push({ date: p.reviewDate, type: "reviewed", project: p });
        });
        const progressFeed = feedEvents.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()).slice(0, 4).map((e, i) => {
          const diffDays = Math.floor((Date.now() - new Date(e.date).getTime()) / 86400000);
          const time = diffDays === 0 ? "Hoy" : diffDays === 1 ? "Ayer" : `${diffDays}d`;
          if (e.type === "submitted") return { id: i, icon: <FileText className="w-4 h-4 text-blue-500" />, text: `Nueva entrega de ${e.project.student}`, time };
          if (e.project.status === "checked") return { id: i, icon: <CheckCircle className="w-4 h-4 text-emerald-500" />, text: `Proyecto de ${e.project.student} aprobado`, time };
          if (e.project.status === "rejected") return { id: i, icon: <XCircle className="w-4 h-4 text-red-500" />, text: `Correcciones para ${e.project.student}`, time };
          return { id: i, icon: <MessageSquare className="w-4 h-4 text-blue-500" />, text: `Comentarios en proyecto de ${e.project.student}`, time };
        });
        setDashboardData({ ptegStats, tegStats, projectsToReview, progressFeed });
      } catch (err) { console.error("Failed to fetch projects", err); }
    };
    load();
  }, [semester, isStudent]);

  useEffect(() => {
    const available = getAvailableSemesters(apiProjects, semesterOptions);
    if (available.length > 0 && !available.includes(semester)) { setSemester(available[0]); setStoredSemester(available[0]); }
  }, [apiProjects, semesterOptions, semester]);

  // ─── Orchestrated entrance — CSS-only, no GSAP ───

  const stats = useMemo(() => {
    if (!dashboardData) return [];
    if (isStudent) {
      const hasProject = dashboardData.projectsToReview.length > 0;
      const status = dashboardData.projectsToReview[0]?.status;
      const mainLabel = !hasProject ? "Sube tu proyecto" : status === "checked" ? "Aprobado" : status === "rejected" ? "Requiere correcciones" : "En revisión";
      return [{
        title: hasProject ? "Mi Proyecto" : "Proyecto",
        mainValue: hasProject ? "1" : "0",
        mainLabel,
        icon: <FileText className="w-6 h-6 text-white" />,
        secondaryStats: [],
        bgClass: "bg-gradient-to-br from-usm-blue via-blue-700 to-indigo-900 border border-white/10",
        accentFrom: "#0066ff",
        accentTo: "#60a5fa",
      }];
    }
    return [
      {
        title: "Proyectos (PTEG)", mainValue: dashboardData.ptegStats.total.toString(), mainLabel: `${dashboardData.ptegStats.pending} en revisión`,
        icon: <FileText className="w-6 h-6 text-white" />,
        secondaryStats: [{ label: "Aprobados", value: dashboardData.ptegStats.checked, color: "#34d399", icon: <Check size={16} /> }, { label: "Rechazados", value: dashboardData.ptegStats.rejected, color: "#f87171", icon: <XCircle size={16} /> }],
        bgClass: "bg-gradient-to-br from-[#0a1628] via-[#0f2040] to-[#1a365d] border border-white/10",
        accentFrom: "#0066ff", accentTo: "#38bdf8",
      },
      {
        title: "Tesis (TEG)", mainValue: dashboardData.tegStats.total.toString(), mainLabel: `${dashboardData.tegStats.pending} pendientes`,
        icon: <BookOpen className="w-6 h-6 text-white" />,
        secondaryStats: [{ label: "Completadas", value: dashboardData.tegStats.checked, color: "#34d399", icon: <Check size={16} /> }, { label: "Pend. Jurado", value: dashboardData.tegStats.pending, color: "#fbbf24", icon: <Clock size={16} /> }],
        bgClass: "bg-gradient-to-br from-[#1a0a2e] via-[#2d1b4e] to-[#1e293b] border border-white/10",
        accentFrom: "#ff6b35", accentTo: "#fbbf24",
      },
    ];
  }, [dashboardData, isStudent]);

  const handleProjectClick = useCallback((project: { id: number; type: string }) => {
    router.push(project.type === "TEG" ? `/dashboard/tesis/${project.id}` : `/dashboard/proyectos/${project.id}`);
  }, [router]);

  if (!semester) return null;

  const greeting = (() => {
    const h = new Date().getHours();
    if (h < 12) return "Buenos días";
    if (h < 18) return "Buenas tardes";
    return "Buenas noches";
  })();

  return (
    <>
      <DashboardHeader pageTitle="Dashboard" />

      <main className="flex-1 p-3 sm:p-4 md:p-6 lg:p-8 overflow-y-auto bg-slate-50/80">
        <div className="max-w-7xl mx-auto space-y-6">

          {/* ─── Welcome bar ─── */}
          <div className="welcome-bar flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <h1 className="text-xl sm:text-2xl md:text-3xl font-extrabold text-slate-900 tracking-tight">
                {greeting}, <span className="text-usm-blue">{userName}</span>
              </h1>
              <p className="text-sm text-slate-500 mt-1">
                {isStudent ? "Aquí está el resumen de tu trabajo." : "Resumen general del período académico."}
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-usm-blue/10 text-usm-blue text-xs font-bold border border-usm-blue/20">
                <Sparkles className="w-3 h-3" />
                {user?.role || "Usuario"}
              </span>
            </div>
          </div>

          {/* ─── Semester indicator ─── */}
          <div className="semester-bar flex items-center gap-4 bg-[#0a1628] p-4 sm:p-5 rounded-2xl border border-[#1a2744] shadow-xl relative overflow-hidden">
            <div className="absolute inset-x-0 top-0 h-[2px] bg-gradient-to-r from-usm-orange via-usm-yellow to-usm-orange" />
            <div className="absolute -top-8 -right-8 w-24 h-24 rounded-full bg-usm-orange/10 blur-2xl" />
            <div className="w-11 h-11 bg-white/10 rounded-xl flex items-center justify-center border border-white/5 backdrop-blur-sm">
              <Calendar className="w-5 h-5 text-usm-orange" />
            </div>
            <div className="flex-1">
              <p className="text-[11px] font-bold text-slate-500 uppercase tracking-widest">Período Activo</p>
              <p className="text-lg sm:text-xl font-extrabold text-white tracking-tight">{semester}</p>
            </div>
            <div className="hidden sm:flex items-center gap-1.5 text-xs text-slate-500">
              <TrendingUp className="w-3.5 h-3.5 text-emerald-400" />
              <span className="font-medium text-emerald-400">En curso</span>
            </div>
          </div>

          {!dashboardData ? (
            /* ─── Skeleton ─── */
            <div className="space-y-6">
              <div className={`grid grid-cols-1 ${isStudent ? "" : "lg:grid-cols-2"} gap-5`}>
                {Array.from({ length: isStudent ? 1 : 2 }).map((_, i) => (
                  <div key={i} className="h-44 rounded-2xl bg-slate-200/50 animate-pulse" />
                ))}
              </div>
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
                <div className="lg:col-span-2 h-72 rounded-2xl bg-slate-100/80 animate-pulse" />
                <div className="lg:col-span-1 h-72 rounded-2xl bg-slate-100/80 animate-pulse" />
              </div>
            </div>
          ) : (
            <>
              {/* ─── Stat Cards ─── */}
              <div className={`grid grid-cols-1 ${isStudent ? "" : "lg:grid-cols-2"} gap-5`}>
                {stats.map((stat, i) => (
                  <StatCard key={i} {...stat} />
                ))}
              </div>

              {/* ─── Content Grid: Projects + Activity Feed ─── */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
                {/* Projects panel — 2/3 width */}
                <div className="content-section lg:col-span-2 bg-white rounded-2xl p-5 sm:p-6 shadow-sm border border-slate-100 flex flex-col">
                  <div className="flex items-center justify-between mb-5">
                    <h3 className="text-base sm:text-lg font-bold text-slate-900 tracking-tight flex items-center gap-2">
                      <div className="w-8 h-8 rounded-lg bg-usm-blue/10 flex items-center justify-center">
                        <FileText className="w-4 h-4 text-usm-blue" />
                      </div>
                      {isStudent ? "Mi Proyecto" : "Proyectos Pendientes"}
                    </h3>
                    <span className="text-xs font-bold text-slate-400 bg-slate-50 px-2.5 py-1 rounded-lg border border-slate-100">
                      {dashboardData.projectsToReview.length} {dashboardData.projectsToReview.length === 1 ? "item" : "items"}
                    </span>
                  </div>

                  <div className="space-y-3 flex-1">
                    {dashboardData.projectsToReview.length === 0 ? (
                      <div className="flex flex-col items-center justify-center py-10 text-center">
                        <div className="w-14 h-14 rounded-2xl bg-emerald-50 flex items-center justify-center mb-3">
                          <CheckCircle className="w-7 h-7 text-emerald-400" />
                        </div>
                        <p className="text-slate-700 font-bold">{isStudent ? "Sin proyectos registrados" : "¡Todo al día!"}</p>
                        <p className="text-slate-400 text-sm mt-1">{isStudent ? "Registra tu proyecto para comenzar." : "No hay proyectos pendientes de revisión."}</p>
                      </div>
                    ) : (
                      dashboardData.projectsToReview.map((project) => (
                        <ProjectRow
                          key={project.id}
                          project={project}
                          isStudent={isStudent}
                          onClick={() => handleProjectClick(project)}
                          onHover={() => router.prefetch(project.type === "TEG" ? `/dashboard/tesis/${project.id}` : `/dashboard/proyectos/${project.id}`)}
                        />
                      ))
                    )}
                  </div>
                </div>

                {/* Activity feed — 1/3 width */}
                <div className="content-section lg:col-span-1 bg-white rounded-2xl p-5 sm:p-6 shadow-sm border border-slate-100 flex flex-col">
                  <div className="flex items-center gap-2 mb-5">
                    <div className="w-8 h-8 rounded-lg bg-usm-orange/10 flex items-center justify-center">
                      <Clock className="w-4 h-4 text-usm-orange" />
                    </div>
                    <h3 className="text-base sm:text-lg font-bold text-slate-900 tracking-tight">Actividad Reciente</h3>
                  </div>

                  {dashboardData.progressFeed.length === 0 ? (
                    <div className="flex flex-col items-center justify-center py-10 text-center flex-1">
                      <div className="w-14 h-14 rounded-2xl bg-slate-50 flex items-center justify-center mb-3">
                        <Clock className="w-7 h-7 text-slate-300" />
                      </div>
                      <p className="text-slate-500 font-medium text-sm">Sin actividad reciente</p>
                    </div>
                  ) : (
                    <div className="space-y-1 flex-1">
                      {dashboardData.progressFeed.map((event) => (
                        <div key={event.id} className="feed-item flex items-start gap-3 p-3 rounded-xl hover:bg-slate-50 transition-colors duration-150">
                          <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-slate-50 border border-slate-100 flex items-center justify-center mt-0.5">
                            {event.icon}
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm text-slate-700 font-medium leading-snug">{event.text}</p>
                            <p className="text-[11px] text-slate-400 font-medium mt-1">{event.time}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </>
          )}
        </div>
      </main>
    </>
  );
};

export default Dashboard;
