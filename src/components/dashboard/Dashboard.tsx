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
import PageTransition from "@/components/ui/PageTransition";
import SemesterSelector from "@/components/ui/SemesterSelector";
import { Project } from "@/types/project";
import { getAllProjects } from "@/features/projects/projectService";
import {
  getAvailableSemesters,
  getSemesters,
  getStoredSemester,
  setStoredSemester,
  formatSemesterLabel,
} from "@/lib/semesters";
import { useRouter } from "next/navigation";
import { getUser } from "@/features/auth/clientAuth";

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
  ({
    title,
    mainValue,
    mainLabel,
    secondaryStats,
    icon,
    delay,
    variant = "default",
    bgClass,
  }) => {
    const cardRef = useRef<HTMLDivElement>(null);
    const mainValueRef = useRef<HTMLParagraphElement>(null);
    const animationRef = useRef<gsap.core.Tween | null>(null);

    useEffect(() => {
      if (!mainValueRef.current) return;

      const targetValue = parseInt(mainValue, 10);

      // If mainValue is not numeric (e.g. "Activo", "N/A"), skip counter animation
      if (isNaN(targetValue)) {
        mainValueRef.current.textContent = mainValue;
        return;
      }

      const counter = { value: 0 };

      // Kill previous animation if exists
      if (animationRef.current) {
        animationRef.current.kill();
      }

      animationRef.current = gsap.to(counter, {
        value: targetValue,
        duration: 1.5,
        ease: "power3.out",
        delay: 0.6 + delay / 1000,
        onUpdate: () => {
          if (mainValueRef.current) {
            mainValueRef.current.textContent = Math.round(
              counter.value,
            ).toString();
          }
        },
      });

      return () => {
        if (animationRef.current) {
          animationRef.current.kill();
          animationRef.current = null;
        }
      };
    }, [mainValue, delay]);

    const isColorful = variant === "colorful";

    return (
      <div
        ref={cardRef}
        className={`kbi-card relative rounded-2xl p-4 sm:p-6 shadow-lg overflow-hidden group transition-all duration-300 ${
          isColorful
            ? `${
                bgClass ??
                "bg-gradient-to-br from-indigo-600 via-indigo-700 to-slate-900"
              } border border-white/10 ring-1 ring-black/5 hover:-translate-y-1 hover:shadow-[0_8px_30px_rgb(0,0,0,0.12)]`
            : "bg-white border border-gray-100 ring-1 ring-gray-900/5 hover:-translate-y-1 hover:shadow-xl hover:border-gray-200"
        }`}
      >
        {/* Shimmer Effect */}
        <div className="absolute inset-0 -translate-x-full group-hover:animate-[shine_1.5s_ease-out] bg-gradient-to-r from-transparent via-white/10 to-transparent pointer-events-none" />

        <div className="relative z-10 flex items-center gap-3 sm:gap-5">
          <div
            className={`flex-shrink-0 w-10 h-10 sm:w-12 sm:h-12 rounded-xl flex items-center justify-center shadow-inner ${
              isColorful ? "bg-white/15 text-white" : "bg-blue-50 text-blue-600"
            }`}
          >
            {icon}
          </div>
          <div className="flex-1 min-w-0">
            <h3
              className={`text-xs sm:text-sm md:text-base font-bold font-montserrat truncate ${
                isColorful ? "text-white/90" : "text-slate-600"
              }`}
            >
              {title}
            </h3>
            <div className="flex items-baseline gap-1 sm:gap-2 mt-1 sm:mt-2">
              <p
                ref={mainValueRef}
                className={`text-2xl sm:text-3xl md:text-5xl font-extrabold font-montserrat tracking-tight leading-tight ${
                  isColorful ? "text-white drop-shadow-sm" : "text-slate-800"
                }`}
              >
                {mainValue}
              </p>
              <p
                className={`text-xs sm:text-sm font-semibold ${
                  isColorful ? "text-white/80" : "text-slate-500"
                }`}
              >
                {mainLabel}
              </p>
            </div>
          </div>
        </div>
        <div
          className={`relative z-10 mt-4 sm:mt-6 pt-3 sm:pt-4 grid grid-cols-2 gap-3 sm:flex sm:flex-row sm:justify-around sm:gap-4 ${
            isColorful
              ? "border-t border-white/10"
              : "border-t border-slate-100"
          }`}
        >
          {secondaryStats.map((stat) => (
            <div
              key={stat.label}
              className="flex items-center gap-1.5 sm:gap-2"
            >
              <div
                style={{ color: isColorful ? "white" : stat.color }}
                className="flex-shrink-0"
              >
                {stat.icon}
              </div>
              <div className="flex flex-col sm:flex-row sm:items-center sm:gap-1 min-w-0">
                <span
                  className={`text-base sm:text-lg font-bold font-montserrat ${
                    isColorful ? "text-white" : "text-slate-700"
                  }`}
                >
                  {stat.value}
                </span>
                <span
                  className={`text-xs sm:text-sm font-medium truncate ${
                    isColorful ? "text-white/70" : "text-slate-500"
                  }`}
                >
                  {stat.label}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  },
);

StatCard.displayName = "StatCard";

interface DashboardProps {
  handleSidebarCollapse?: () => void;
  handleMobileSidebarToggle?: () => void;
  isSidebarCollapsed?: boolean;
  isMobileSidebarOpen?: boolean;
}

const Dashboard: React.FC<DashboardProps> = (props) => {
  const {
    handleSidebarCollapse,
    handleMobileSidebarToggle,
    isSidebarCollapsed,
    isMobileSidebarOpen,
  } = props;
  const mainContentRef = useRef<HTMLDivElement>(null);
  const hasAnimatedRef = useRef(false);
  const router = useRouter();

  // Read user once to avoid effect loops caused by changing object references
  const user = useMemo(() => getUser(), []);
  const isStudent = user?.role === "Estudiante";

  // State for data
  const [semester, setSemester] = useState<string>("");
  const [apiProjects, setApiProjects] = useState<Project[]>([]);
  const [semesterOptions, setSemesterOptions] = useState<string[]>([]);
  const [dashboardData, setDashboardData] = useState<{
    ptegStats: {
      total: number;
      checked: number;
      pending: number;
      rejected: number;
    };
    tegStats: { total: number; checked: number; pending: number };
    projectsToReview: {
      id: number;
      student: string;
      title: string;
      date: string;
      type: string;
      status?: string;
    }[];
    progressFeed: {
      id: number;
      icon: React.ReactNode;
      text: string;
      time: string;
    }[];
  } | null>(null);

  // Load initial semester
  useEffect(() => {
    setSemester(getStoredSemester());
  }, []);

  // Load data when semester changes
  useEffect(() => {
    if (!semester) return;

    const fetchData = async () => {
      try {
        const [apiProjects, semestersFromApi] = await Promise.all([
          getAllProjects(),
          getSemesters(),
        ]);
        setApiProjects(apiProjects);
        setSemesterOptions(semestersFromApi.map((s) => s.period));

        // Categorize projects
        const allProyectos = apiProjects.filter((p) => p.type === "proyecto");
        const allTesis = apiProjects.filter((p) => p.type === "tesis");

        // Student View: Only their own project
        if (isStudent) {
          // Backend filters by user, so we just take what we have
          // Filter by selected semester:
          const myPteg = allProyectos.find((p) => p.period === semester);
          const myTeg = allTesis.find((p) => p.period === semester);

          const myProject = myTeg || myPteg;

          // Stats for student (e.g. My Deliverables)
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

          // My Project list (for the card)
          const projectsToReview = myProject
            ? [
                {
                  id: myProject.id,
                  student: myProject.student,
                  title: myProject.title,
                  date: myProject.submittedDate,
                  type: myTeg ? "TEG" : "PTEG",
                  status: myProject.status,
                },
              ]
            : [];

          // Feed for student
          const feedEvents: {
            date: string;
            type: "submitted" | "reviewed";
            project: Project;
          }[] = [];
          if (myProject) {
            if (myProject.submittedDate)
              feedEvents.push({
                date: myProject.submittedDate,
                type: "submitted",
                project: myProject,
              });
            if (myProject.reviewDate)
              feedEvents.push({
                date: myProject.reviewDate,
                type: "reviewed",
                project: myProject,
              });
          }

          const progressFeed = feedEvents.map((e, index) => {
            const icon = <FileText className="w-5 h-5 text-blue-600" />;
            const text =
              e.type === "submitted"
                ? "Has enviado tu proyecto."
                : "Tu proyecto ha sido revisado.";
            return { id: index, icon, text, time: e.date };
          });

          setDashboardData({
            ptegStats,
            tegStats,
            projectsToReview,
            progressFeed,
          });
          return;
        }

        // Admin/Tutor View: All projects
        // Filter by semester for stats
        const semProyectos = allProyectos.filter((p) => p.period === semester);
        const semTesis = allTesis.filter((t) => t.period === semester);

        // Calculate Stats
        const ptegStats = {
          total: semProyectos.length,
          checked: semProyectos.filter((p) => p.status === "checked").length,
          pending: semProyectos.filter((p) => p.status === "pending").length,
          rejected: semProyectos.filter((p) => p.status === "rejected").length,
        };

        const tegStats = {
          total: semTesis.length,
          checked: semTesis.filter((t) => t.status === "checked").length,
          pending: semTesis.filter((t) => t.status === "pending").length,
        };

        // Projects to review - filter by selected semester
        const semPending = [...semProyectos, ...semTesis].filter(
          (p) => p.status === "pending",
        );
        const projectsToReview = semPending
          .sort(
            (a, b) =>
              new Date(b.submittedDate).getTime() -
              new Date(a.submittedDate).getTime(),
          )
          .slice(0, 5)
          .map((p) => ({
            id: p.id,
            student: p.student,
            title: p.title,
            date: p.submittedDate,
            type: "stage1Passed" in p ? "TEG" : "PTEG",
            status: p.status,
          }));

        // detailed feed
        const feedEvents: {
          date: string;
          type: "submitted" | "reviewed";
          project: Project;
        }[] = [];
        [...semProyectos, ...semTesis].forEach((p) => {
          // Add submission event
          if (p.submittedDate) {
            feedEvents.push({
              date: p.submittedDate,
              type: "submitted",
              project: p,
            });
          }
          // Add review event
          if (p.reviewDate) {
            feedEvents.push({
              date: p.reviewDate,
              type: "reviewed",
              project: p,
            });
          }
        });

        const progressFeed = feedEvents
          .sort(
            (a, b) => new Date(b.date).getTime() - new Date(a.date).getTime(),
          )
          .slice(0, 3)
          .map((e, index) => {
            let icon;
            let text;

            // Calculate relative time (simple approximation)
            const diffDays = Math.floor(
              (new Date().getTime() - new Date(e.date).getTime()) /
                (1000 * 3600 * 24),
            );
            const timeStr =
              diffDays === 0
                ? "Hoy"
                : diffDays === 1
                  ? "Ayer"
                  : `${diffDays}d ago`;

            if (e.type === "submitted") {
              icon = <FileText className="w-5 h-5 text-blue-600" />;
              text = `Nueva entrega de '${e.project.student}' (${"stage1Passed" in e.project ? "TEG" : "PTEG"}).`;
            } else {
              // Reviewed
              if (e.project.status === "checked") {
                icon = <CheckCircle className="w-5 h-5 text-green-600" />;
                text = `El proyecto de '${e.project.student}' ha sido Aprobado.`;
              } else if (e.project.status === "rejected") {
                icon = <XCircle className="w-5 h-5 text-red-600" />;
                text = `El proyecto de '${e.project.student}' requiere correcciones.`;
              } else {
                icon = <MessageSquare className="w-5 h-5 text-blue-600" />;
                text = `Comentarios agregados al proyecto de '${e.project.student}'.`;
              }
            }

            return {
              id: index,
              icon,
              text,
              time: timeStr,
            };
          });

        setDashboardData({
          ptegStats,
          tegStats,
          projectsToReview,
          progressFeed,
        });
      } catch (error) {
        console.error("Failed to fetch projects", error);
      }
    };

    fetchData();
  }, [semester, isStudent]);

  useEffect(() => {
    // Skip if already animated this session
    if (hasAnimatedRef.current) return;

    // Check if we've already visited dashboard in this session
    const sessionKey = "visited_dashboard_page";
    const hasVisitedBefore = sessionStorage.getItem(sessionKey);

    // Check if we just logged in - skip animations for instant display
    let skipAnimations = false;
    try {
      const justLoggedIn = sessionStorage.getItem("justLoggedIn");
      if (justLoggedIn) {
        sessionStorage.removeItem("justLoggedIn");
        skipAnimations = true;
      }
      if (hasVisitedBefore) {
        skipAnimations = true;
      }
    } catch {}

    // Mark as visited for future navigations
    try {
      sessionStorage.setItem(sessionKey, "true");
    } catch {}

    const kbiCards = gsap.utils.toArray<HTMLElement>(".kbi-card");
    const contentSections = gsap.utils.toArray<HTMLElement>(".content-section");

    // Always ensure elements are visible immediately
    kbiCards.forEach((card) => {
      if (card) gsap.set(card, { opacity: 1, y: 0 });
    });
    contentSections.forEach((section) => {
      if (section) gsap.set(section, { opacity: 1, y: 0 });
    });

    hasAnimatedRef.current = true;

    // Skip animations for instant navigation
    if (
      skipAnimations ||
      (kbiCards.length === 0 && contentSections.length === 0)
    ) {
      return;
    }
    
    // Elements are already set to full opacity & translation 0 above
  }, []); // Only run once on mount

  useEffect(() => {
    const available = getAvailableSemesters(apiProjects, semesterOptions);
    if (available.length === 0) return;
    if (!available.includes(semester)) {
      setSemester(available[0]);
      setStoredSemester(available[0]);
    }
  }, [apiProjects, semesterOptions, semester]);

  // Build stats cards from data
  const stats = useMemo(() => {
    if (!dashboardData) return [];

    if (isStudent) {
      const hasProject = dashboardData.projectsToReview.length > 0;
      const projectStatus = dashboardData.projectsToReview[0]?.status;

      let mainLabel = "Sube tu proyecto para comenzar";
      if (hasProject) {
        mainLabel =
          projectStatus === "checked"
            ? "Aprobado ✓"
            : projectStatus === "rejected"
              ? "Requiere correcciones"
              : "En espera de revisión";
      }

      return [
        {
          title: hasProject ? "Mi Proyecto" : "Proyecto",
          mainValue: hasProject ? "Activo" : "Sin Proyecto",
          mainLabel,
          icon: <FileText className="w-8 h-8 sm:w-10 sm:h-10 text-white" />,
          secondaryStats: [],
          variant: "colorful" as const,
          bgClass:
            "bg-gradient-to-br from-blue-500 via-indigo-600 to-purple-500",
        },
      ];
    }

    // Admin/Tutor Stats
    return [
      {
        title: "Proyectos de Tesis (PTEG)",
        mainValue: dashboardData.ptegStats.pending.toString(),
        mainLabel: "En Revisión",
        icon: <FileText className="w-8 h-8 sm:w-10 sm:h-10 text-white" />,
        secondaryStats: [
          {
            label: "Aprobados",
            value: dashboardData.ptegStats.checked,
            color: "#10B981",
            icon: <Check size={18} />,
          },
          {
            label: "Rechazados",
            value: dashboardData.ptegStats.rejected,
            color: "#EF4444",
            icon: <XCircle size={18} />,
          },
        ],
        variant: "colorful" as const,
        bgClass: "bg-gradient-to-br from-sky-500 via-blue-600 to-cyan-500",
      },
      {
        title: "Tesis de Grado (TEG)",
        mainValue: dashboardData.tegStats.total.toString(),
        mainLabel: "En Progreso",
        icon: <BookOpen className="w-8 h-8 sm:w-10 sm:h-10 text-white" />,
        secondaryStats: [
          {
            label: "Completadas",
            value: dashboardData.tegStats.checked,
            color: "#10B981",
            icon: <Check size={18} />,
          },
          {
            label: "Pend. Jurado",
            value: dashboardData.tegStats.pending,
            color: "#F59E0B",
            icon: <Clock size={18} />,
          },
        ],
        variant: "colorful" as const,
        bgClass: "bg-gradient-to-br from-[#0f172a] via-[#1e293b] to-[#334155]", // Dark Slate theme
      },
    ];
  }, [dashboardData, isStudent]);

  if (!semester) {
    return null; // Or skeleton
  }

  return (
    <>
      <DashboardHeader
        pageTitle="Dashboard"
        isSidebarCollapsed={isSidebarCollapsed}
        isMobileSidebarOpen={isMobileSidebarOpen}
        onMobileSidebarToggle={handleMobileSidebarToggle}
        onSidebarCollapse={handleSidebarCollapse}
      />

      <PageTransition>
        <main
          ref={mainContentRef}
          className="flex-1 p-3 sm:p-4 md:p-6 lg:p-8 overflow-y-auto bg-gray-50"
          style={{ opacity: 1 }}
        >
          <div className="max-w-7xl mx-auto">
            {/* Current Semester Indicator */}
            <div className="mb-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 bg-[#0f172a] p-5 rounded-2xl border border-[#1e293b] shadow-lg shadow-slate-900/10 relative overflow-hidden group">
              {/* Decorative accent glow */}
              <div 
                className="absolute inset-x-0 top-0 h-1"
                style={{ background: "linear-gradient(90deg, var(--accent-start, #f97316), var(--accent-end, #f59e0b))" }}
              />
              
              <div className="flex items-center gap-4 relative z-10">
                <div className="w-12 h-12 bg-white/10 rounded-xl flex items-center justify-center backdrop-blur-sm border border-white/5">
                  <Calendar className="w-6 h-6 text-white" />
                </div>
                <div>
                  <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Período Actual</p>
                  <p className="text-xl font-bold text-white font-montserrat">
                    {formatSemesterLabel(semester)}
                  </p>
                </div>
              </div>
              <SemesterSelector
                selectedSemester={semester}
                availableSemesters={getAvailableSemesters(
                  apiProjects,
                  semesterOptions,
                )}
                onSemesterChange={(sem) => {
                  setStoredSemester(sem);
                  setSemester(sem);
                }}
              />
            </div>

            {!dashboardData ? (
              <div className="flex justify-center items-center py-24">
                <div className="w-10 h-10 rounded-full border-4 border-slate-200 border-t-blue-600 animate-spin shadow-sm" />
              </div>
            ) : (
              <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
                <div
                  className={`grid grid-cols-1 ${isStudent ? "lg:grid-cols-1" : "lg:grid-cols-2"} gap-4 sm:gap-6 lg:gap-8 mb-6 sm:mb-8`}
                >
              {stats.map((stat, index) => (
                <StatCard key={index} {...stat} delay={index * 100} />
              ))}
            </div>

            {/* Two equal columns for symmetry */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6 lg:gap-8">
              <div className="content-section bg-white rounded-3xl p-5 sm:p-7 shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-slate-100 transition-all duration-300 hover:shadow-[0_8px_30px_rgb(0,0,0,0.08)] flex flex-col h-full">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 sm:gap-4 mb-4 sm:mb-6">
                  <h3 className="text-lg md:text-xl font-bold text-slate-900 font-montserrat tracking-tight">
                    {isStudent ? "Mi Proyecto" : "Revisión de Proyectos"}
                  </h3>
                </div>
                <div className="space-y-3 sm:space-y-4">
                  {dashboardData?.projectsToReview.length === 0 ? (
                    <div className="flex flex-col items-center justify-center py-8 text-center">
                      <CheckCircle className="w-12 h-12 text-green-400 mb-3" />
                      <p className="text-gray-600 font-medium">
                        {isStudent
                          ? "No tienes proyectos registrados."
                          : "¡Todo al día!"}
                      </p>
                      <p className="text-gray-400 text-sm mt-1">
                        {isStudent
                          ? ""
                          : "No tienes proyectos pendientes de revisión."}
                      </p>
                    </div>
                  ) : (
                    dashboardData?.projectsToReview.map((project, index) => (
                      <div
                        key={index}
                        className="flex flex-col sm:flex-row sm:items-center gap-4 p-4 sm:p-5 rounded-2xl border border-slate-100 bg-slate-50/50 hover:bg-white hover:shadow-lg hover:shadow-blue-900/5 hover:-translate-y-1 hover:border-blue-100 transition-all duration-300 group"
                      >
                        <div className="flex-1 min-w-0 w-full rounded-xl">
                          <p className="text-sm sm:text-base font-bold text-slate-800 line-clamp-2 font-montserrat group-hover:text-blue-700 transition-colors">
                            {project.title}
                          </p>
                          <div className="flex flex-wrap items-center gap-2 text-xs sm:text-sm text-slate-500 mt-2">
                            <span className="font-medium text-slate-600">{project.student}</span>
                            <span className="hidden sm:inline text-slate-300">•</span>
                            <span className="text-[11px] sm:text-xs font-medium px-2 py-0.5 bg-slate-100 rounded-md text-slate-600">{project.date}</span>
                            <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[11px] sm:text-xs font-bold bg-indigo-50 text-indigo-700 border border-indigo-100">
                              {project.type}
                            </span>
                          </div>
                        </div>
                        <button
                          onClick={() => {
                            const route =
                              project.type === "TEG"
                                ? `/dashboard/tesis/${project.id}`
                                : `/dashboard/proyectos/${project.id}`;
                            router.push(route);
                          }}
                          className="w-full sm:w-auto flex-shrink-0 bg-white text-slate-700 border border-slate-200 px-4 py-2.5 rounded-xl text-sm font-semibold hover:text-blue-700 hover:border-blue-200 hover:bg-blue-50 active:bg-blue-100 transition-all duration-200 shadow-sm touch-manipulation group-hover:shadow-md"
                        >
                          {isStudent ? "Ver Detalles" : "Revisar Ahora"}
                        </button>
                      </div>
                    ))
                  )}
                </div>
              </div>

              {!isStudent && (
                <div className="content-section bg-white rounded-3xl p-5 sm:p-7 shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-slate-100 transition-all duration-300 hover:shadow-[0_8px_30px_rgb(0,0,0,0.08)] flex flex-col h-full">
                  <h3 className="text-lg md:text-xl font-bold text-slate-900 font-montserrat tracking-tight mb-4 sm:mb-6">
                    Seguimiento de Tesis
                  </h3>
                  <div className="space-y-3 sm:space-y-4">
                    {dashboardData?.projectsToReview.length === 0 ? (
                      <div className="flex flex-col items-center justify-center py-8 text-center">
                        <CheckCircle className="w-12 h-12 text-green-400 mb-3" />
                        <p className="text-gray-600 font-medium">
                          ¡Excelente trabajo!
                        </p>
                        <p className="text-gray-400 text-sm mt-1">
                          Todas las tesis están revisadas.
                        </p>
                      </div>
                    ) : (
                      dashboardData?.projectsToReview.map((project, index) => (
                        <div
                          key={index}
                          className="flex flex-col sm:flex-row sm:items-center gap-3 sm:gap-4 p-4 sm:p-5 rounded-2xl border border-amber-100/50 bg-gradient-to-r from-amber-50/50 to-orange-50/50 hover:to-orange-50 hover:shadow-md hover:-translate-y-0.5 transition-all duration-300 group"
                        >
                          <div className="flex-shrink-0 w-10 h-10 bg-amber-100 rounded-full flex items-center justify-center text-amber-600 group-hover:bg-amber-500 group-hover:text-white transition-colors duration-300 shadow-sm">
                            <Clock className="w-5 h-5" />
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm border-b border-transparent sm:text-base font-bold text-slate-800 truncate font-montserrat group-hover:text-amber-900 transition-colors">
                              {project.title}
                            </p>
                            <div className="flex flex-wrap items-center gap-2 text-xs text-slate-500 mt-1 sm:mt-1.5">
                              <span className="font-medium text-slate-600">{project.student}</span>
                              <span className="hidden sm:inline text-slate-300">•</span>
                              <span className="text-[11px] font-medium px-2 py-0.5 bg-white/60 rounded-md text-slate-600 border border-slate-100">{project.date}</span>
                            </div>
                          </div>
                          <div className="flex-shrink-0 flex items-center gap-2 mt-2 sm:mt-0">
                            <span
                              className={`inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-bold border ${
                                project.type === "TEG"
                                  ? "bg-purple-50 text-purple-700 border-purple-100"
                                  : "bg-blue-50 text-blue-700 border-blue-100"
                              }`}
                            >
                              {project.type}
                            </span>
                            <span className="inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-bold bg-amber-100 text-amber-700 border border-amber-200 shadow-sm">
                              Pendiente
                            </span>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )}
            </div>
              </div>
            )}
          </div>
        </main>
      </PageTransition>
    </>
  );
};

export default Dashboard;
