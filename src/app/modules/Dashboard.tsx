"use client";

import React, {
  useEffect,
  useState,
  useRef,
  useMemo,
  useCallback,
  memo,
} from "react";
import { gsap } from "gsap";
import {
  Bell,
  AlertTriangle,
  CheckCircle,
  FileText,
  BookOpen,
  ChevronDown,
  XCircle,
  Clock,
  Check,
  MessageSquare,
  Menu,
  ChevronsLeft,
} from "lucide-react";
import Sidebar from "./Sidebar";
import LoginLoading from "@/components/ui/LoginLoading";

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

      const counter = { value: 0 };
      const targetValue = parseInt(mainValue, 10);

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
              counter.value
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
      className={`kbi-card rounded-2xl p-4 sm:p-6 shadow-lg shadow-gray-900/10 ${
          isColorful
            ? `${
                bgClass ??
                "bg-gradient-to-br from-emerald-500 via-emerald-600 to-green-700"
              } border border-transparent ring-1 ring-white/20`
            : "bg-white border border-gray-200/80 ring-1 ring-gray-200/80"
        }`}
      >
        <div className="flex items-center gap-3 sm:gap-5">
          <div
            className={`flex-shrink-0 w-10 h-10 sm:w-12 sm:h-12 rounded-xl flex items-center justify-center shadow-inner ${
              isColorful ? "bg-white/15 text-white" : "bg-blue-50 text-blue-600"
            }`}
          >
            {icon}
          </div>
          <div className="flex-1 min-w-0">
            <h3
              className={`text-xs sm:text-sm md:text-base font-semibold truncate ${
                isColorful ? "text-white/90" : "text-gray-600"
              }`}
            >
              {title}
            </h3>
            <div className="flex items-baseline gap-1 sm:gap-2 mt-1 sm:mt-2">
              <p
                ref={mainValueRef}
                className={`text-2xl sm:text-3xl md:text-4xl xl:text-5xl font-bold leading-tight ${
                  isColorful ? "text-white" : "text-gray-800"
                }`}
              >
                {mainValue}
              </p>
              <p
                className={`text-xs sm:text-sm font-medium ${
                  isColorful ? "text-white/80" : "text-gray-600"
                }`}
              >
                {mainLabel}
              </p>
            </div>
          </div>
        </div>
        <div
          className={`mt-4 sm:mt-6 pt-3 sm:pt-4 grid grid-cols-2 gap-3 sm:flex sm:flex-row sm:justify-around sm:gap-4 ${
            isColorful
              ? "border-t border-white/20"
              : "border-t border-gray-200/75"
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
                  className={`text-base sm:text-lg font-bold ${
                    isColorful ? "text-white" : "text-gray-700"
                  }`}
                >
                  {stat.value}
                </span>
                <span
                  className={`text-xs sm:text-sm truncate ${
                    isColorful ? "text-white/80" : "text-gray-500"
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
  }
);

StatCard.displayName = "StatCard";

const Dashboard: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);
  const mainContentRef = useRef<HTMLDivElement>(null);
  const animationsRef = useRef<gsap.core.Tween[]>([]);

  useEffect(() => {
    // If navigation came from the login modal, skip showing a second loader
    try {
      const just = sessionStorage.getItem("justLoggedIn");
      if (just) {
        sessionStorage.removeItem("justLoggedIn");
        setLoading(false);
        return;
      }
    } catch {}

    const timer = window.setTimeout(() => setLoading(false), 800);
    return () => window.clearTimeout(timer);
  }, []);

  useEffect(() => {
    if (loading) return;

    // Kill any existing animations
    animationsRef.current.forEach((tween) => tween.kill());
    animationsRef.current = [];

    const sidebar = document.querySelector(".sidebar-container");
    const header = document.querySelector(".header-container");
    const kbiCards = gsap.utils.toArray<HTMLElement>(".kbi-card");
    const contentSections = gsap.utils.toArray<HTMLElement>(".content-section");

    if (sidebar) {
      const sidebarTween = gsap.from(sidebar, {
        duration: 0.7,
        x: "-100%",
        ease: "power3.out",
      });
      animationsRef.current.push(sidebarTween);
    }

    if (header) {
      const headerTween = gsap.from(header, {
        duration: 0.7,
        y: "-100%",
        ease: "power3.out",
        delay: 0.2,
      });
      animationsRef.current.push(headerTween);
    }

    if (kbiCards.length > 0) {
      // Animate cards from invisible/offset into place — more robust when initial CSS differs
      const cardsTween = gsap.from(kbiCards, {
        opacity: 0,
        y: 20,
        duration: 0.8,
        stagger: 0.15,
        ease: "power3.out",
        delay: 0.4,
      });
      animationsRef.current.push(cardsTween);
    }

    if (contentSections.length > 0) {
      const sectionsTween = gsap.from(contentSections, {
        duration: 0.5,
        opacity: 0,
        y: 20,
        stagger: 0.2,
        ease: "power2.out",
        delay: 0.7,
      });
      animationsRef.current.push(sectionsTween);
    }

    return () => {
      animationsRef.current.forEach((tween) => tween.kill());
      animationsRef.current = [];
    };
  }, [loading]);

  // Memoize static data to prevent recreating on every render
  const stats = useMemo(
    () => [
      {
        title: "Proyectos de Tesis (PTEG)",
        mainValue: "12",
        mainLabel: "En Revisión",
        icon: <FileText className="w-8 h-8 sm:w-10 sm:h-10 text-white" />,
        secondaryStats: [
          {
            label: "Aprobados",
            value: 58,
            color: "#10B981",
            icon: <Check size={18} />,
          },
          {
            label: "Rechazados",
            value: 7,
            color: "#EF4444",
            icon: <XCircle size={18} />,
          },
        ],
        variant: "colorful" as const,
        bgClass: "bg-gradient-to-br from-sky-500 via-blue-600 to-cyan-500",
      },
      {
        title: "Tesis de Grado (TEG)",
        mainValue: "43",
        mainLabel: "En Progreso",
        icon: <BookOpen className="w-8 h-8 sm:w-10 sm:h-10 text-white" />,
        secondaryStats: [
          {
            label: "Completadas",
            value: 21,
            color: "#10B981",
            icon: <Check size={18} />,
          },
          {
            label: "Pend. Jurado",
            value: 9,
            color: "#F59E0B",
            icon: <Clock size={18} />,
          },
        ],
        variant: "colorful" as const,
        bgClass: "bg-gradient-to-br from-rose-500 via-red-600 to-orange-500",
      },
    ],
    []
  );

  const projectsToReview = useMemo(
    () => [
      {
        student: "Ana Pérez",
        title: "Impacto de la IA en la farmacovigilancia",
        date: "2024-05-10",
      },
      {
        student: "Luis Rodríguez",
        title: "Desarrollo de un nuevo agente antibacteriano",
        date: "2024-05-09",
      },
      {
        student: "Carla Gómez",
        title: "Análisis de la adherencia terapéutica en pacientes crónicos",
        date: "2024-05-09",
      },
    ],
    []
  );

  const progressFeed = useMemo(
    () => [
      {
        id: 1,
        icon: <CheckCircle className="w-5 h-5 text-green-600" />,
        text: "La tesis de 'Ana Pérez' ha sido Aprobada.",
        time: "1h ago",
      },
      {
        id: 2,
        icon: <MessageSquare className="w-5 h-5 text-blue-600" />,
        text: "Nuevo comentario del jurado en el proyecto de 'Luis Rodríguez'.",
        time: "3h ago",
      },
      {
        id: 3,
        icon: <AlertTriangle className="w-5 h-5 text-amber-600" />,
        text: "Entrega final de 'Carla Gómez' vence en 3 días.",
        time: "1d ago",
      },
    ],
    []
  );

  const handleSidebarCollapse = useCallback(() => {
    setIsSidebarCollapsed((prev) => !prev);
  }, []);

  const handleMobileSidebarToggle = useCallback(() => {
    setIsMobileSidebarOpen((prev) => !prev);
  }, []);

  if (loading) {
    // Use the same loading overlay used by the login modal for visual consistency across the app
    return <LoginLoading visible={true} message="Cargando panel..." />;
  }

  return (
    <>
      {/* Main dashboard layout - sidebar is the first child so desktop shows side-by-side */}
      <div className="min-h-screen w-full flex bg-gray-100">
        <Sidebar
          isCollapsed={isSidebarCollapsed}
          setIsCollapsed={setIsSidebarCollapsed}
          mobileOpen={isMobileSidebarOpen}
          setMobileOpen={setIsMobileSidebarOpen}
        />
        <div
          ref={mainContentRef}
          className="flex-1 flex flex-col overflow-hidden transition-all duration-300 lg:ml-0"
        >
        <header className="header-container bg-white border-b border-gray-200 sticky top-0 z-10 h-16 sm:h-20 md:h-[89px] flex-shrink-0">
          <div className="px-3 sm:px-4 md:px-6 lg:px-8 h-full flex items-center justify-between gap-2">
            <div className="flex items-center gap-2 sm:gap-3 min-w-0 flex-1">
              {/* Mobile menu toggle (hidden on large screens) */}
              <button
                className={`lg:hidden inline-flex items-center justify-center p-2 sm:p-3 rounded-md border transition-colors touch-manipulation ${
                  isMobileSidebarOpen
                    ? "bg-blue-600 border-blue-600 text-white"
                    : "bg-white border-gray-300 text-gray-700 hover:bg-gray-50 active:bg-gray-100"
                }`}
                aria-label={isMobileSidebarOpen ? "Cerrar menú" : "Abrir menú"}
                onClick={handleMobileSidebarToggle}
              >
                <Menu className="w-5 h-5 sm:w-6 sm:h-6" />
              </button>
              <button
                className="hidden lg:inline-flex items-center justify-center p-2 rounded-md hover:bg-gray-100 active:bg-gray-200 transition-colors touch-manipulation"
                aria-label="Colapsar barra lateral"
                onClick={handleSidebarCollapse}
                title={
                  isSidebarCollapsed
                    ? "Expandir barra lateral"
                    : "Colapsar barra lateral"
                }
              >
                <ChevronsLeft
                  className={`w-5 h-5 ${
                    isSidebarCollapsed
                      ? "rotate-180 transition-transform"
                      : "transition-transform"
                  }`}
                />
              </button>
              <h2 className="text-lg sm:text-xl md:text-2xl lg:text-3xl font-bold text-gray-900 truncate">
                Dashboard
              </h2>
            </div>
            <div className="flex items-center gap-1 sm:gap-2 bg-gray-100 p-1 sm:p-1.5 rounded-full flex-shrink-0">
              <button className="relative p-1.5 sm:p-2 rounded-full hover:bg-gray-200/70 active:bg-gray-300 transition-all duration-200 group touch-manipulation">
                <Bell className="w-4 h-4 sm:w-5 sm:h-5 text-gray-600 group-hover:text-blue-600 transition-colors" />
                <span className="absolute top-1 right-1 sm:top-2 sm:right-2 flex h-3 w-3 sm:h-4 sm:w-4 items-center justify-center">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 sm:h-3 sm:w-3 bg-red-500"></span>
                </span>
              </button>
              <div className="relative group">
                <button className="flex items-center gap-1 sm:gap-2 p-1 pr-1.5 sm:pr-2 rounded-full hover:bg-gray-200/70 active:bg-gray-300 transition-colors touch-manipulation">
                  <img
                    src="https://i.pravatar.cc/300"
                    alt="User avatar"
                    className="w-7 h-7 sm:w-8 sm:h-8 rounded-full border-2 border-white shadow-sm"
                  />
                  <ChevronDown className="w-3 h-3 sm:w-4 sm:h-4 text-gray-500 hidden sm:block" />
                </button>
              </div>
            </div>
          </div>
        </header>

        <main className="flex-1 p-3 sm:p-4 md:p-6 lg:p-8 overflow-y-auto bg-gray-50">
          <div className="max-w-7xl mx-auto">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6 lg:gap-8 mb-6 sm:mb-8">
              {stats.map((stat, index) => (
                <StatCard key={index} {...stat} delay={index * 100} />
              ))}
            </div>

            {/* Two equal columns for symmetry */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6 lg:gap-8">
              <div className="content-section bg-white rounded-xl sm:rounded-2xl p-3 sm:p-4 md:p-6 shadow-md shadow-gray-900/5 border border-gray-200/80">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 sm:gap-4 mb-4 sm:mb-6">
                  <h3 className="text-base sm:text-lg md:text-xl font-bold text-gray-900">
                    Revisión de Proyectos
                  </h3>
                  <button className="text-xs sm:text-sm text-blue-700 border border-blue-700 rounded-md px-2.5 sm:px-3 py-1.5 sm:py-2 font-semibold hover:bg-blue-700 hover:text-white active:bg-blue-800 transition-all duration-200 touch-manipulation whitespace-nowrap">
                    Ver todos
                  </button>
                </div>
                <div className="space-y-3 sm:space-y-4">
                  {projectsToReview.map((project, index) => (
                    <div
                      key={index}
                      className="flex flex-col gap-2 sm:gap-3 p-3 sm:p-4 rounded-lg sm:rounded-xl hover:bg-gray-100 active:bg-gray-200 transition-all duration-200 cursor-pointer group"
                    >
                      <div className="flex-1 min-w-0 w-full">
                        <p className="text-xs sm:text-sm font-semibold text-gray-800 line-clamp-2">
                          {project.title}
                        </p>
                        <p className="text-xs sm:text-sm text-gray-500 mt-1">
                          {project.student}{" "}
                          <span className="text-gray-400">•</span>{" "}
                          <span className="text-xs">{project.date}</span>
                        </p>
                      </div>
                      <button className="w-full bg-blue-600 text-white px-3 sm:px-4 py-2 sm:py-2.5 rounded-lg text-xs sm:text-sm font-semibold hover:bg-blue-700 active:bg-blue-800 transition-all duration-200 shadow-md shadow-blue-600/20 hover:shadow-lg transform hover:scale-[1.02] touch-manipulation">
                        Revisar Ahora
                      </button>
                    </div>
                  ))}
                </div>
              </div>

              <div className="content-section bg-white rounded-xl sm:rounded-2xl p-3 sm:p-4 md:p-6 shadow-md shadow-gray-900/5 border border-gray-200/80">
                <h3 className="text-base sm:text-lg md:text-xl font-bold text-gray-900 mb-3 sm:mb-4">
                  Seguimiento de Progreso
                </h3>
                <div className="space-y-4 sm:space-y-6">
                  {progressFeed.map((item) => (
                    <div
                      key={item.id}
                      className="flex items-start gap-2 sm:gap-4"
                    >
                      <div className="flex-shrink-0 mt-0.5 sm:mt-1 bg-gray-100 p-1.5 sm:p-2 rounded-full">
                        {item.icon}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-xs sm:text-sm text-gray-800 leading-relaxed">
                          {item.text}
                        </p>
                        <p className="text-xs text-gray-500 mt-1">
                          {item.time}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
    </>
  );
};

export default Dashboard;
