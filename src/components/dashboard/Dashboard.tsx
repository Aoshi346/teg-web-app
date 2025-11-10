"use client";

import React, {
  useEffect,
  useState,
  useRef,
  useMemo,
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
import DashboardHeader from "@/components/layout/DashboardHeader";
import PageTransition from "@/components/ui/PageTransition";
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

interface DashboardProps {
  handleSidebarCollapse?: () => void;
  handleMobileSidebarToggle?: () => void;
  isSidebarCollapsed?: boolean;
  isMobileSidebarOpen?: boolean;
}

const Dashboard: React.FC<DashboardProps> = ({
  handleSidebarCollapse = () => {},
  handleMobileSidebarToggle = () => {},
  isSidebarCollapsed = false,
  isMobileSidebarOpen = false,
}) => {
  const mainContentRef = useRef<HTMLDivElement>(null);
  const animationsRef = useRef<gsap.core.Tween[]>([]);
  const hasAnimatedRef = useRef(false);

  useEffect(() => {
    // Only animate on initial mount, not on subsequent navigations
    if (hasAnimatedRef.current) return;
    
    // Check if we just logged in - if so, skip animations for instant display
    let skipAnimations = false;
    try {
      const justLoggedIn = sessionStorage.getItem("justLoggedIn");
      if (justLoggedIn) {
        sessionStorage.removeItem("justLoggedIn");
        skipAnimations = true;
      }
    } catch {}

    // Wait for DOM to be ready
    const timer = setTimeout(() => {
      // Kill any existing animations
      animationsRef.current.forEach((tween) => tween.kill());
      animationsRef.current = [];

      const kbiCards = gsap.utils.toArray<HTMLElement>(".kbi-card");
      const contentSections = gsap.utils.toArray<HTMLElement>(".content-section");

      // Always ensure elements are visible first
      kbiCards.forEach((card) => {
        if (card) gsap.set(card, { opacity: 1, y: 0 });
      });
      contentSections.forEach((section) => {
        if (section) gsap.set(section, { opacity: 1, y: 0 });
      });

      // If skipping animations or no elements found, we're done
      if (skipAnimations || (kbiCards.length === 0 && contentSections.length === 0)) {
        hasAnimatedRef.current = true;
        return;
      }

      // Set initial state for animation
      gsap.set([...kbiCards, ...contentSections], { opacity: 0, y: 20 });

      if (kbiCards.length > 0) {
        const cardsTween = gsap.to(kbiCards, {
          opacity: 1,
          y: 0,
          duration: 0.5,
          stagger: 0.08,
          ease: "power3.out",
          delay: 0.05,
        });
        animationsRef.current.push(cardsTween);
      }

      if (contentSections.length > 0) {
        const sectionsTween = gsap.to(contentSections, {
          opacity: 1,
          y: 0,
          duration: 0.3,
          stagger: 0.08,
          ease: "power2.out",
          delay: 0.2,
        });
        animationsRef.current.push(sectionsTween);
      }

      hasAnimatedRef.current = true;
    }, 10); // Small delay to ensure DOM is ready

    return () => {
      clearTimeout(timer);
      animationsRef.current.forEach((tween) => tween.kill());
      animationsRef.current = [];
    };
  }, []); // Only run once on mount

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
      </PageTransition>
    </>
  );
};

export default Dashboard;

