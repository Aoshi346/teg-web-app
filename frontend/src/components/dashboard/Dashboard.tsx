"use client";

import React, { useEffect, useRef, useMemo, memo, useState } from "react";
import { gsap } from "gsap";
import {
  CheckCircle,
  FileText,
  BookOpen,
  XCircle,
  Clock,
  Check,
  MessageSquare,
  Calendar,
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
  delay: number;
  variant?: "default" | "colorful";
  bgClass?: string;
}

const StatCard: React.FC<StatCardProps> = memo(
  ({ title, mainValue, mainLabel, secondaryStats, icon, delay, variant = "default", bgClass }) => {
    const mainValueRef = useRef<HTMLParagraphElement>(null);
    const animRef = useRef<gsap.core.Tween | null>(null);

    useEffect(() => {
      if (!mainValueRef.current) return;
      const target = parseInt(mainValue, 10);
      if (isNaN(target)) {
        mainValueRef.current.textContent = mainValue;
        return;
      }
      const counter = { value: 0 };
      animRef.current?.kill();
      animRef.current = gsap.to(counter, {
        value: target,
        duration: 1.2,
        ease: "power3.out",
        delay: 0.3 + delay / 1000,
        onUpdate: () => {
          if (mainValueRef.current) mainValueRef.current.textContent = Math.round(counter.value).toString();
        },
      });
      return () => { animRef.current?.kill(); };
    }, [mainValue, delay]);

    const isColorful = variant === "colorful";

    return (
      <div
        className={`stat-card relative rounded-2xl p-4 sm:p-6 shadow-lg overflow-hidden group transition-all duration-300 ${
          isColorful
            ? `${bgClass ?? "bg-gradient-to-br from-indigo-600 via-indigo-700 to-slate-900"} border border-white/10 ring-1 ring-black/5 hover:-translate-y-1 hover:shadow-xl`
            : "bg-white border border-gray-100 ring-1 ring-gray-900/5 hover:-translate-y-1 hover:shadow-xl hover:border-gray-200"
        }`}
      >
        {/* Shimmer */}
        <div className="absolute inset-0 -translate-x-full group-hover:animate-[shine_1.5s_ease-out] bg-gradient-to-r from-transparent via-white/10 to-transparent pointer-events-none" />

        <div className="relative z-10 flex items-center gap-3 sm:gap-5">
          <div className={`flex-shrink-0 w-10 h-10 sm:w-12 sm:h-12 rounded-xl flex items-center justify-center shadow-inner ${isColorful ? "bg-white/15 text-white" : "bg-blue-50 text-blue-600"}`}>
            {icon}
          </div>
          <div className="flex-1 min-w-0">
            <h3 className={`text-xs sm:text-sm md:text-base font-bold truncate ${isColorful ? "text-white/90" : "text-slate-600"}`}>
              {title}
            </h3>
            <div className="flex items-baseline gap-1 sm:gap-2 mt-1 sm:mt-2">
              <p ref={mainValueRef} className={`text-2xl sm:text-3xl md:text-5xl font-extrabold tracking-tight leading-tight ${isColorful ? "text-white drop-shadow-sm" : "text-slate-800"}`}>
                {mainValue}
              </p>
              <p className={`text-xs sm:text-sm font-semibold ${isColorful ? "text-white/80" : "text-slate-500"}`}>
                {mainLabel}
              </p>
            </div>
          </div>
        </div>

        {secondaryStats.length > 0 && (
          <div className={`relative z-10 mt-4 sm:mt-6 pt-3 sm:pt-4 grid grid-cols-2 gap-3 sm:flex sm:flex-row sm:justify-around sm:gap-4 ${isColorful ? "border-t border-white/10" : "border-t border-slate-100"}`}>
            {secondaryStats.map((stat) => (
              <div key={stat.label} className="flex items-center gap-1.5 sm:gap-2">
                <div style={{ color: isColorful ? "white" : stat.color }} className="flex-shrink-0">{stat.icon}</div>
                <div className="flex flex-col sm:flex-row sm:items-center sm:gap-1 min-w-0">
                  <span className={`text-base sm:text-lg font-bold ${isColorful ? "text-white" : "text-slate-700"}`}>{stat.value}</span>
                  <span className={`text-xs sm:text-sm font-medium truncate ${isColorful ? "text-white/70" : "text-slate-500"}`}>{stat.label}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }
);
StatCard.displayName = "StatCard";

// ─── Dashboard ───

const Dashboard: React.FC = () => {
  const mainRef = useRef<HTMLDivElement>(null);
  const router = useRouter();
  const user = useMemo(() => getUser(), []);
  const isStudent = user?.role === "Estudiante";

  const [semester, setSemester] = useState("");
  const [apiProjects, setApiProjects] = useState<Project[]>([]);
  const [semesterOptions, setSemesterOptions] = useState<string[]>([]);
  const [dashboardData, setDashboardData] = useState<{
    ptegStats: { total: number; checked: number; pending: number; rejected: number };
    tegStats: { total: number; checked: number; pending: number };
    projectsToReview: { id: number; student: string; title: string; date: string; type: string; status?: string }[];
    progressFeed: { id: number; icon: React.ReactNode; text: string; time: string }[];
  } | null>(null);

  // Init semester
  useEffect(() => {
    fetchActiveSemester().then((active) => {
      setSemester(active ? active.period : getStoredSemester());
    });
  }, []);

  // Fetch data
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

          setDashboardData({
            ptegStats, tegStats, projectsToReview,
            progressFeed: feedEvents.map((e, i) => ({
              id: i,
              icon: <FileText className="w-5 h-5 text-blue-600" />,
              text: e.type === "submitted" ? "Has enviado tu proyecto." : "Tu proyecto ha sido revisado.",
              time: e.date,
            })),
          });
          return;
        }

        // Admin/Tutor view
        const semP = allProyectos.filter((p) => p.period === semester);
        const semT = allTesis.filter((t) => t.period === semester);
        const ptegStats = { total: semP.length, checked: semP.filter((p) => p.status === "checked").length, pending: semP.filter((p) => p.status === "pending").length, rejected: semP.filter((p) => p.status === "rejected").length };
        const tegStats = { total: semT.length, checked: semT.filter((t) => t.status === "checked").length, pending: semT.filter((t) => t.status === "pending").length };

        const semPending = [...semP, ...semT].filter((p) => p.status === "pending");
        const projectsToReview = semPending
          .sort((a, b) => new Date(b.submittedDate).getTime() - new Date(a.submittedDate).getTime())
          .slice(0, 5)
          .map((p) => ({ id: p.id, student: p.student, title: p.title, date: p.submittedDate, type: "stage1Passed" in p ? "TEG" : "PTEG", status: p.status }));

        const feedEvents: { date: string; type: "submitted" | "reviewed"; project: Project }[] = [];
        [...semP, ...semT].forEach((p) => {
          if (p.submittedDate) feedEvents.push({ date: p.submittedDate, type: "submitted", project: p });
          if (p.reviewDate) feedEvents.push({ date: p.reviewDate, type: "reviewed", project: p });
        });

        const progressFeed = feedEvents
          .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
          .slice(0, 3)
          .map((e, i) => {
            const diffDays = Math.floor((Date.now() - new Date(e.date).getTime()) / 86400000);
            const time = diffDays === 0 ? "Hoy" : diffDays === 1 ? "Ayer" : `${diffDays}d`;
            if (e.type === "submitted") {
              return { id: i, icon: <FileText className="w-5 h-5 text-blue-600" />, text: `Nueva entrega de '${e.project.student}'.`, time };
            }
            if (e.project.status === "checked") return { id: i, icon: <CheckCircle className="w-5 h-5 text-green-600" />, text: `Proyecto de '${e.project.student}' aprobado.`, time };
            if (e.project.status === "rejected") return { id: i, icon: <XCircle className="w-5 h-5 text-red-600" />, text: `Proyecto de '${e.project.student}' requiere correcciones.`, time };
            return { id: i, icon: <MessageSquare className="w-5 h-5 text-blue-600" />, text: `Comentarios en proyecto de '${e.project.student}'.`, time };
          });

        setDashboardData({ ptegStats, tegStats, projectsToReview, progressFeed });
      } catch (err) {
        console.error("Failed to fetch projects", err);
      }
    };
    load();
  }, [semester, isStudent]);

  // Validate semester against available
  useEffect(() => {
    const available = getAvailableSemesters(apiProjects, semesterOptions);
    if (available.length > 0 && !available.includes(semester)) {
      setSemester(available[0]);
      setStoredSemester(available[0]);
    }
  }, [apiProjects, semesterOptions, semester]);

  // GSAP stagger entrance for cards and content sections
  useEffect(() => {
    if (!dashboardData || !mainRef.current) return;

    // Skip if already visited this session
    try {
      if (sessionStorage.getItem("visited_dashboard_page")) return;
      sessionStorage.setItem("visited_dashboard_page", "true");
    } catch { return; }

    // Also skip if just logged in (LoginLoading handles that)
    try {
      const j = sessionStorage.getItem("justLoggedIn");
      if (j) { sessionStorage.removeItem("justLoggedIn"); return; }
    } catch {}

    const ctx = gsap.context(() => {
      const cards = gsap.utils.toArray<HTMLElement>(".stat-card");
      const sections = gsap.utils.toArray<HTMLElement>(".content-section");

      if (cards.length > 0) {
        gsap.fromTo(cards, { opacity: 0, y: 20, scale: 0.97 }, {
          opacity: 1, y: 0, scale: 1,
          duration: 0.5, stagger: 0.08,
          ease: "power3.out",
        });
      }
      if (sections.length > 0) {
        gsap.fromTo(sections, { opacity: 0, y: 24 }, {
          opacity: 1, y: 0,
          duration: 0.5, stagger: 0.1,
          delay: 0.2,
          ease: "power3.out",
        });
      }
    }, mainRef);

    return () => ctx.revert();
  }, [dashboardData]);

  const stats = useMemo(() => {
    if (!dashboardData) return [];
    if (isStudent) {
      const hasProject = dashboardData.projectsToReview.length > 0;
      const status = dashboardData.projectsToReview[0]?.status;
      const mainLabel = !hasProject ? "Sube tu proyecto para comenzar" : status === "checked" ? "Aprobado" : status === "rejected" ? "Requiere correcciones" : "En espera de revisión";
      return [{ title: hasProject ? "Mi Proyecto" : "Proyecto", mainValue: hasProject ? "Activo" : "Sin Proyecto", mainLabel, icon: <FileText className="w-8 h-8 sm:w-10 sm:h-10 text-white" />, secondaryStats: [], variant: "colorful" as const, bgClass: "bg-gradient-to-br from-blue-500 via-indigo-600 to-purple-500" }];
    }
    return [
      { title: "Proyectos (PTEG)", mainValue: dashboardData.ptegStats.pending.toString(), mainLabel: "En Revisión", icon: <FileText className="w-8 h-8 sm:w-10 sm:h-10 text-white" />, secondaryStats: [{ label: "Aprobados", value: dashboardData.ptegStats.checked, color: "#10B981", icon: <Check size={18} /> }, { label: "Rechazados", value: dashboardData.ptegStats.rejected, color: "#EF4444", icon: <XCircle size={18} /> }], variant: "colorful" as const, bgClass: "bg-gradient-to-br from-sky-500 via-blue-600 to-cyan-500" },
      { title: "Tesis (TEG)", mainValue: dashboardData.tegStats.total.toString(), mainLabel: "En Progreso", icon: <BookOpen className="w-8 h-8 sm:w-10 sm:h-10 text-white" />, secondaryStats: [{ label: "Completadas", value: dashboardData.tegStats.checked, color: "#10B981", icon: <Check size={18} /> }, { label: "Pend. Jurado", value: dashboardData.tegStats.pending, color: "#F59E0B", icon: <Clock size={18} /> }], variant: "colorful" as const, bgClass: "bg-gradient-to-br from-[#0f172a] via-[#1e293b] to-[#334155]" },
    ];
  }, [dashboardData, isStudent]);

  if (!semester) return null;

  return (
    <>
      <DashboardHeader pageTitle="Dashboard" />

      <main ref={mainRef} className="flex-1 p-3 sm:p-4 md:p-6 lg:p-8 overflow-y-auto bg-gray-50">
        <div className="max-w-7xl mx-auto">
          {/* Semester indicator */}
          <div className="mb-6 flex items-center gap-4 bg-[#0f172a] p-4 sm:p-5 rounded-2xl border border-[#1e293b] shadow-lg relative overflow-hidden">
            <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-usm-orange to-usm-yellow" />
            <div className="w-10 h-10 sm:w-12 sm:h-12 bg-white/10 rounded-xl flex items-center justify-center border border-white/5">
              <Calendar className="w-5 h-5 sm:w-6 sm:h-6 text-white" />
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Período Actual</p>
              <p className="text-lg sm:text-xl font-bold text-white">{semester}</p>
            </div>
          </div>

          {!dashboardData ? (
            /* Skeleton loader */
            <div className="space-y-6">
              <div className={`grid grid-cols-1 ${isStudent ? "" : "lg:grid-cols-2"} gap-4 sm:gap-6`}>
                {[1, 2].slice(0, isStudent ? 1 : 2).map((i) => (
                  <div key={i} className="h-40 rounded-2xl bg-slate-200/60 animate-pulse" />
                ))}
              </div>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
                <div className="h-64 rounded-3xl bg-slate-100 animate-pulse" />
                <div className="h-64 rounded-3xl bg-slate-100 animate-pulse" />
              </div>
            </div>
          ) : (
            <>
              {/* Stat cards */}
              <div className={`grid grid-cols-1 ${isStudent ? "" : "lg:grid-cols-2"} gap-4 sm:gap-6 lg:gap-8 mb-6 sm:mb-8`}>
                {stats.map((stat, i) => (
                  <StatCard key={i} {...stat} delay={i * 100} />
                ))}
              </div>

              {/* Content sections */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6 lg:gap-8">
                {/* Projects to review */}
                <div className="content-section bg-white rounded-3xl p-5 sm:p-7 shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-slate-100 hover:shadow-[0_8px_30px_rgb(0,0,0,0.08)] transition-shadow duration-300 flex flex-col">
                  <h3 className="text-lg md:text-xl font-bold text-slate-900 tracking-tight mb-4 sm:mb-6">
                    {isStudent ? "Mi Proyecto" : "Revisión de Proyectos"}
                  </h3>
                  <div className="space-y-3 sm:space-y-4 flex-1">
                    {dashboardData.projectsToReview.length === 0 ? (
                      <div className="flex flex-col items-center justify-center py-8 text-center">
                        <CheckCircle className="w-12 h-12 text-green-400 mb-3" />
                        <p className="text-gray-600 font-medium">{isStudent ? "No tienes proyectos registrados." : "¡Todo al día!"}</p>
                        {!isStudent && <p className="text-gray-400 text-sm mt-1">No tienes proyectos pendientes de revisión.</p>}
                      </div>
                    ) : (
                      dashboardData.projectsToReview.map((project, i) => (
                        <div key={i} className="flex flex-col sm:flex-row sm:items-center gap-4 p-4 sm:p-5 rounded-2xl border border-slate-100 bg-slate-50/50 hover:bg-white hover:shadow-lg hover:shadow-blue-900/5 hover:-translate-y-0.5 hover:border-blue-100 transition-all duration-200 group">
                          <div className="flex-1 min-w-0">
                            <p className="text-sm sm:text-base font-bold text-slate-800 line-clamp-2 group-hover:text-blue-700 transition-colors">{project.title}</p>
                            <div className="flex flex-wrap items-center gap-2 text-xs sm:text-sm text-slate-500 mt-2">
                              <span className="font-medium text-slate-600">{project.student}</span>
                              <span className="hidden sm:inline text-slate-300">&middot;</span>
                              <span className="text-[11px] sm:text-xs font-medium px-2 py-0.5 bg-slate-100 rounded-md text-slate-600">{project.date}</span>
                              <span className="px-2 py-0.5 rounded-md text-[11px] sm:text-xs font-bold bg-indigo-50 text-indigo-700 border border-indigo-100">{project.type}</span>
                            </div>
                          </div>
                          <button
                            onClick={() => router.push(project.type === "TEG" ? `/dashboard/tesis/${project.id}` : `/dashboard/proyectos/${project.id}`)}
                            className="w-full sm:w-auto flex-shrink-0 bg-white text-slate-700 border border-slate-200 px-4 py-2.5 rounded-xl text-sm font-semibold hover:text-blue-700 hover:border-blue-200 hover:bg-blue-50 transition-all duration-200 shadow-sm touch-manipulation"
                          >
                            {isStudent ? "Ver Detalles" : "Revisar Ahora"}
                          </button>
                        </div>
                      ))
                    )}
                  </div>
                </div>

                {/* Thesis tracking (admin/tutor only) */}
                {!isStudent && (
                  <div className="content-section bg-white rounded-3xl p-5 sm:p-7 shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-slate-100 hover:shadow-[0_8px_30px_rgb(0,0,0,0.08)] transition-shadow duration-300 flex flex-col">
                    <h3 className="text-lg md:text-xl font-bold text-slate-900 tracking-tight mb-4 sm:mb-6">
                      Seguimiento de Tesis
                    </h3>
                    <div className="space-y-3 sm:space-y-4 flex-1">
                      {dashboardData.projectsToReview.length === 0 ? (
                        <div className="flex flex-col items-center justify-center py-8 text-center">
                          <CheckCircle className="w-12 h-12 text-green-400 mb-3" />
                          <p className="text-gray-600 font-medium">¡Excelente trabajo!</p>
                          <p className="text-gray-400 text-sm mt-1">Todas las tesis están revisadas.</p>
                        </div>
                      ) : (
                        dashboardData.projectsToReview.map((project, i) => (
                          <div key={i} className="flex flex-col sm:flex-row sm:items-center gap-3 sm:gap-4 p-4 sm:p-5 rounded-2xl border border-amber-100/50 bg-gradient-to-r from-amber-50/50 to-orange-50/50 hover:shadow-md hover:-translate-y-0.5 transition-all duration-200 group">
                            <div className="flex-shrink-0 w-10 h-10 bg-amber-100 rounded-full flex items-center justify-center text-amber-600 group-hover:bg-amber-500 group-hover:text-white transition-colors duration-200 shadow-sm">
                              <Clock className="w-5 h-5" />
                            </div>
                            <div className="flex-1 min-w-0">
                              <p className="text-sm sm:text-base font-bold text-slate-800 truncate group-hover:text-amber-900 transition-colors">{project.title}</p>
                              <div className="flex flex-wrap items-center gap-2 text-xs text-slate-500 mt-1">
                                <span className="font-medium text-slate-600">{project.student}</span>
                                <span className="hidden sm:inline text-slate-300">&middot;</span>
                                <span className="text-[11px] font-medium px-2 py-0.5 bg-white/60 rounded-md text-slate-600 border border-slate-100">{project.date}</span>
                              </div>
                            </div>
                            <div className="flex items-center gap-2 mt-2 sm:mt-0">
                              <span className={`px-2.5 py-1 rounded-lg text-xs font-bold border ${project.type === "TEG" ? "bg-purple-50 text-purple-700 border-purple-100" : "bg-blue-50 text-blue-700 border-blue-100"}`}>{project.type}</span>
                              <span className="px-2.5 py-1 rounded-lg text-xs font-bold bg-amber-100 text-amber-700 border border-amber-200">Pendiente</span>
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      </main>
    </>
  );
};

export default Dashboard;
