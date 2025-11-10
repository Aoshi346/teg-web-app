"use client";

import React, { useState, useEffect, useRef, useMemo } from "react";
import { gsap } from "gsap";
import {
  Search,
  CheckCircle,
  Clock,
  Calendar,
  User,
  FileText,
} from "lucide-react";
import DashboardHeader from "@/components/layout/DashboardHeader";
import PageTransition from "@/components/ui/PageTransition";

interface Project {
  id: number;
  title: string;
  student: string;
  advisor: string;
  submittedDate: string;
  reviewDate?: string;
  status: "checked" | "pending";
  score?: number;
}

interface TesisPageProps {
  handleSidebarCollapse?: () => void;
  handleMobileSidebarToggle?: () => void;
  isSidebarCollapsed?: boolean;
  isMobileSidebarOpen?: boolean;
}

export default function TesisPage({ handleSidebarCollapse = () => {}, handleMobileSidebarToggle = () => {}, isSidebarCollapsed = false, isMobileSidebarOpen = false }: TesisPageProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [filterStatus, setFilterStatus] = useState<"all" | "checked" | "pending">("all");
  const animationsRef = useRef<gsap.core.Tween[]>([]);

  // Mock data for TEG projects
  const allProjects = useMemo<Project[]>(
    () => [
      { id: 1, title: "Impacto de la IA en la farmacovigilancia", student: "Ana Pérez", advisor: "Dr. Carlos Medina", submittedDate: "2024-05-10", reviewDate: "2024-05-15", status: "checked", score: 95 },
      { id: 2, title: "Desarrollo de un nuevo agente antibacteriano", student: "Luis Rodríguez", advisor: "Dra. María González", submittedDate: "2024-05-09", reviewDate: "2024-05-14", status: "checked", score: 88 },
      { id: 3, title: "Análisis de la adherencia terapéutica en pacientes crónicos", student: "Carla Gómez", advisor: "Dr. Roberto Silva", submittedDate: "2024-05-09", status: "pending" },
      { id: 4, title: "Evaluación farmacoeconómica de nuevos tratamientos oncológicos", student: "Miguel Torres", advisor: "Dra. Laura Ramírez", submittedDate: "2024-05-08", status: "pending" },
      { id: 5, title: "Optimización de formulaciones de liberación controlada", student: "Sofia Martínez", advisor: "Dr. Pedro Álvarez", submittedDate: "2024-05-07", reviewDate: "2024-05-12", status: "checked", score: 92 },
      { id: 6, title: "Estudio de interacciones medicamentosas en terapias combinadas", student: "Daniel Castro", advisor: "Dra. Isabel Fernández", submittedDate: "2024-05-06", status: "pending" },
    ],
    []
  );

  const filteredProjects = useMemo(() => {
    return allProjects.filter((project) => {
      const matchesSearch =
        project.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        project.student.toLowerCase().includes(searchQuery.toLowerCase()) ||
        project.advisor.toLowerCase().includes(searchQuery.toLowerCase());

      const matchesFilter = filterStatus === "all" || project.status === filterStatus;
      return matchesSearch && matchesFilter;
    });
  }, [allProjects, searchQuery, filterStatus]);

  const checkedProjects = useMemo(
    () => filteredProjects.filter((p) => p.status === "checked"),
    [filteredProjects]
  );

  const pendingProjects = useMemo(
    () => filteredProjects.filter((p) => p.status === "pending"),
    [filteredProjects]
  );

  // Entrance animations - only on initial mount, not on filter changes
  const hasAnimatedRef = useRef(false);
  
  useEffect(() => {
    // Skip if already animated (for instant display on navigation)
    if (hasAnimatedRef.current) return;
    
    // Check if we just navigated - skip animations for instant display
    let skipAnimations = false;
    try {
      const justLoggedIn = sessionStorage.getItem("justLoggedIn");
      if (justLoggedIn) {
        skipAnimations = true;
      }
    } catch {}

    // Wait for DOM to be ready
    const timer = setTimeout(() => {
      animationsRef.current.forEach((tween) => tween.kill());
      animationsRef.current = [];

      const cards = gsap.utils.toArray<HTMLElement>(".project-card");
      const sections = gsap.utils.toArray<HTMLElement>(".section-container");

      // Always ensure elements are visible first
      cards.forEach((card) => {
        if (card) gsap.set(card, { opacity: 1, y: 0 });
      });
      sections.forEach((section) => {
        if (section) gsap.set(section, { opacity: 1, y: 0 });
      });

      // If skipping animations or no elements found, we're done
      if (skipAnimations || (cards.length === 0 && sections.length === 0)) {
        hasAnimatedRef.current = true;
        return;
      }

      // Set initial state for animation
      gsap.set([...cards, ...sections], { opacity: 0, y: 20 });

      if (sections.length > 0) {
        const sectionsTween = gsap.to(sections, {
          opacity: 1,
          y: 0,
          duration: 0.4,
          stagger: 0.1,
          ease: "power2.out",
          delay: 0.05,
        });
        animationsRef.current.push(sectionsTween);
      }

      if (cards.length > 0) {
        const cardsTween = gsap.to(cards, {
          opacity: 1,
          y: 0,
          duration: 0.4,
          stagger: 0.06,
          ease: "power2.out",
          delay: 0.2,
        });
        animationsRef.current.push(cardsTween);
      }

      hasAnimatedRef.current = true;
    }, 10); // Small delay to ensure DOM is ready

    return () => {
      clearTimeout(timer);
      animationsRef.current.forEach((tween) => tween.kill());
      animationsRef.current = [];
    };
  }, []); // Only run once on mount

  return (
    <>
      <DashboardHeader
        pageTitle="Trabajo Especial de Grado (TEG)"
        isSidebarCollapsed={isSidebarCollapsed}
        isMobileSidebarOpen={isMobileSidebarOpen}
        onMobileSidebarToggle={handleMobileSidebarToggle}
        onSidebarCollapse={handleSidebarCollapse}
      />

      <PageTransition>
          {/* Main Content */}
          <main className="flex-1 p-3 sm:p-4 md:p-6 lg:p-8 overflow-y-auto bg-gray-50">
            <div className="max-w-7xl mx-auto">
              {/* Search and Filter Bar */}
              <div className="section-container mb-6 sm:mb-8 flex flex-col sm:flex-row gap-3 sm:gap-4">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Buscar por título, estudiante o tutor..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full pl-10 pr-4 py-2.5 sm:py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all text-sm sm:text-base"
                  />
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => setFilterStatus("all")}
                    className={`px-4 py-2.5 rounded-lg text-sm font-medium transition-all touch-manipulation ${
                      filterStatus === "all"
                        ? "bg-blue-600 text-white shadow-md"
                        : "bg-white text-gray-700 border border-gray-300 hover:bg-gray-50"
                    }`}
                  >
                    Todos
                  </button>
                  <button
                    onClick={() => setFilterStatus("checked")}
                    className={`px-4 py-2.5 rounded-lg text-sm font-medium transition-all touch-manipulation ${
                      filterStatus === "checked"
                        ? "bg-green-600 text-white shadow-md"
                        : "bg-white text-gray-700 border border-gray-300 hover:bg-gray-50"
                    }`}
                  >
                    Revisados
                  </button>
                  <button
                    onClick={() => setFilterStatus("pending")}
                    className={`px-4 py-2.5 rounded-lg text-sm font-medium transition-all touch-manipulation ${
                      filterStatus === "pending"
                        ? "bg-amber-600 text-white shadow-md"
                        : "bg-white text-gray-700 border border-gray-300 hover:bg-gray-50"
                    }`}
                  >
                    Pendientes
                  </button>
                </div>
              </div>

              {/* Checked Projects Section */}
              {(filterStatus === "all" || filterStatus === "checked") && checkedProjects.length > 0 && (
                <div className="section-container mb-8">
                  <div className="flex items-center justify-between mb-4 sm:mb-6">
                    <h3 className="text-xl sm:text-2xl font-bold text-gray-900 flex items-center gap-2">
                      <CheckCircle className="w-6 h-6 text-green-600" />
                      Proyectos Revisados
                    </h3>
                    <span className="text-sm sm:text-base text-gray-600 font-medium">
                      {checkedProjects.length} proyectos
                    </span>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6">
                    {checkedProjects.map((project) => (
                      <div
                        key={project.id}
                        className="project-card bg-white rounded-xl p-4 sm:p-6 shadow-md shadow-gray-900/5 border border-gray-200 hover:shadow-lg hover:border-green-300 transition-all duration-200 cursor-pointer group"
                      >
                        <div className="flex items-start justify-between mb-3">
                          <div className="flex-1 min-w-0">
                            <h4 className="text-base sm:text-lg font-bold text-gray-900 line-clamp-2 group-hover:text-green-600 transition-colors">
                              {project.title}
                            </h4>
                          </div>
                          {project.score && (
                            <span className="ml-2 flex-shrink-0 px-3 py-1 bg-green-100 text-green-800 text-sm font-bold rounded-full">
                              {project.score}
                            </span>
                          )}
                        </div>
                        <div className="space-y-2 text-sm text-gray-600">
                          <div className="flex items-center gap-2">
                            <User className="w-4 h-4 text-gray-400 flex-shrink-0" />
                            <span className="truncate"><strong>Estudiante:</strong> {project.student}</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <FileText className="w-4 h-4 text-gray-400 flex-shrink-0" />
                            <span className="truncate"><strong>Tutor:</strong> {project.advisor}</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <Calendar className="w-4 h-4 text-gray-400 flex-shrink-0" />
                            <span><strong>Revisado:</strong> {project.reviewDate}</span>
                          </div>
                        </div>
                        <button className="mt-4 w-full bg-green-600 text-white py-2.5 rounded-lg text-sm font-semibold hover:bg-green-700 active:bg-green-800 transition-all duration-200 shadow-md touch-manipulation">
                          Ver Detalles
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Pending Projects Section */}
              {(filterStatus === "all" || filterStatus === "pending") && pendingProjects.length > 0 && (
                <div className="section-container">
                  <div className="flex items-center justify-between mb-4 sm:mb-6">
                    <h3 className="text-xl sm:text-2xl font-bold text-gray-900 flex items-center gap-2">
                      <Clock className="w-6 h-6 text-amber-600" />
                      Proyectos Pendientes
                    </h3>
                    <span className="text-sm sm:text-base text-gray-600 font-medium">
                      {pendingProjects.length} proyectos
                    </span>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6">
                    {pendingProjects.map((project) => (
                      <div
                        key={project.id}
                        className="project-card bg-white rounded-xl p-4 sm:p-6 shadow-md shadow-gray-900/5 border border-gray-200 hover:shadow-lg hover:border-amber-300 transition-all duration-200 cursor-pointer group"
                      >
                        <div className="flex items-start justify-between mb-3">
                          <div className="flex-1 min-w-0">
                            <h4 className="text-base sm:text-lg font-bold text-gray-900 line-clamp-2 group-hover:text-amber-600 transition-colors">
                              {project.title}
                            </h4>
                          </div>
                          <span className="ml-2 flex-shrink-0 px-3 py-1 bg-amber-100 text-amber-800 text-xs font-semibold rounded-full">
                            Pendiente
                          </span>
                        </div>
                        <div className="space-y-2 text-sm text-gray-600">
                          <div className="flex items-center gap-2">
                            <User className="w-4 h-4 text-gray-400 flex-shrink-0" />
                            <span className="truncate"><strong>Estudiante:</strong> {project.student}</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <FileText className="w-4 h-4 text-gray-400 flex-shrink-0" />
                            <span className="truncate"><strong>Tutor:</strong> {project.advisor}</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <Calendar className="w-4 h-4 text-gray-400 flex-shrink-0" />
                            <span><strong>Entregado:</strong> {project.submittedDate}</span>
                          </div>
                        </div>
                        <button className="mt-4 w-full bg-blue-600 text-white py-2.5 rounded-lg text-sm font-semibold hover:bg-blue-700 active:bg-blue-800 transition-all duration-200 shadow-md touch-manipulation">
                          Revisar Ahora
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Empty State */}
              {filteredProjects.length === 0 && (
                <div className="section-container text-center py-12">
                  <FileText className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                  <h3 className="text-xl font-semibold text-gray-700 mb-2">
                    No se encontraron proyectos
                  </h3>
                  <p className="text-gray-500">
                    Intenta ajustar los filtros o la búsqueda
                  </p>
                </div>
              )}
            </div>
          </main>
      </PageTransition>
    </>
  );
}
