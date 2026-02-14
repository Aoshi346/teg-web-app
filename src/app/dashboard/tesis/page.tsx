"use client";

import React, { useState, useEffect, useRef, useMemo } from "react";
import { gsap } from "gsap";
import { Search, CheckCircle, Clock, XCircle, FileText } from "lucide-react";
import { useRouter } from "next/navigation";
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
} from "@/lib/semesters";
import ProjectCard from "@/components/dashboard/ProjectCard";
import { getUserRole } from "@/features/auth/clientAuth";

interface TesisPageProps {
  handleSidebarCollapse?: () => void;
  handleMobileSidebarToggle?: () => void;
  isSidebarCollapsed?: boolean;
  isMobileSidebarOpen?: boolean;
}

export default function TesisPage(props: TesisPageProps = {}) {
  const {
    handleSidebarCollapse,
    handleMobileSidebarToggle,
    isSidebarCollapsed,
    isMobileSidebarOpen,
  } = props;
  const router = useRouter();
  const userRole = useMemo(() => getUserRole(), []);
  const isStudent = userRole === "Estudiante";
  const [searchQuery, setSearchQuery] = useState("");
  const [filterStatus, setFilterStatus] = useState<
    "all" | "checked" | "pending" | "rejected"
  >("all");

  // Load tesis including user-added ones
  const [allProjects, setAllProjects] = useState<Project[]>([]);
  const [semesterOptions, setSemesterOptions] = useState<string[]>([]);

  useEffect(() => {
    let mounted = true;
    (async () => {
      const [apiProjects, semestersFromApi] = await Promise.all([
        getAllProjects(),
        getSemesters(),
      ]);
      const onlyTesis = apiProjects.filter((p) => p.type === "tesis");
      if (mounted) {
        setAllProjects(onlyTesis);
        setSemesterOptions(semestersFromApi.map((s) => s.period));
      }
    })();
    return () => {
      mounted = false;
    };
  }, [isStudent]);

  // Semester state - persisted in localStorage
  const availableSemesters = useMemo(
    () => getAvailableSemesters(allProjects, semesterOptions),
    [allProjects, semesterOptions],
  );
  const [selectedSemester, setSelectedSemester] = useState(() => {
    const stored = getStoredSemester();
    // If stored semester is not available in this data, use first available
    return availableSemesters.includes(stored)
      ? stored
      : availableSemesters[0] || stored;
  });

  useEffect(() => {
    if (availableSemesters.length === 0) return;
    if (!availableSemesters.includes(selectedSemester)) {
      setSelectedSemester(availableSemesters[0]);
      setStoredSemester(availableSemesters[0]);
    }
  }, [availableSemesters, selectedSemester]);

  const handleSemesterChange = (semester: string) => {
    setSelectedSemester(semester);
    setStoredSemester(semester);
  };

  // Filter by semester first, then by search/status
  const semesterProjects = useMemo<Project[]>(
    () =>
      selectedSemester
        ? allProjects.filter((p) => p.semester === selectedSemester)
        : allProjects,
    [selectedSemester, allProjects],
  );

  const filteredProjects = useMemo(() => {
    return semesterProjects.filter((project) => {
      const matchesSearch =
        project.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        project.student.toLowerCase().includes(searchQuery.toLowerCase()) ||
        project.advisor.toLowerCase().includes(searchQuery.toLowerCase());

      const matchesFilter =
        filterStatus === "all" || project.status === filterStatus;
      return matchesSearch && matchesFilter;
    });
  }, [semesterProjects, searchQuery, filterStatus]);

  const checkedProjects = useMemo(
    () => filteredProjects.filter((p) => p.status === "checked"),
    [filteredProjects],
  );

  const pendingProjects = useMemo(
    () => filteredProjects.filter((p) => p.status === "pending"),
    [filteredProjects],
  );

  const rejectedProjects = useMemo(
    () => filteredProjects.filter((p) => p.status === "rejected"),
    [filteredProjects],
  );

  // Entrance animations - only on first visit per session, not on navigation
  const hasAnimatedRef = useRef(false);

  useEffect(() => {
    // Skip if already animated this session
    if (hasAnimatedRef.current) return;

    // Check if we've already visited this page in this session
    const sessionKey = "visited_tesis_page";
    const hasVisitedBefore = sessionStorage.getItem(sessionKey);

    // Check if we just logged in or navigating within dashboard
    let skipAnimations = false;
    try {
      const justLoggedIn = sessionStorage.getItem("justLoggedIn");
      if (justLoggedIn || hasVisitedBefore) {
        skipAnimations = true;
      }
    } catch {}

    // Mark as visited for future navigations
    try {
      sessionStorage.setItem(sessionKey, "true");
    } catch {}

    const cards = gsap.utils.toArray<HTMLElement>(".project-card");
    const sections = gsap.utils.toArray<HTMLElement>(".section-container");

    // Always ensure elements are visible immediately
    cards.forEach((card) => {
      if (card) gsap.set(card, { opacity: 1, y: 0 });
    });
    sections.forEach((section) => {
      if (section) gsap.set(section, { opacity: 1, y: 0 });
    });

    hasAnimatedRef.current = true;

    // Skip animations for instant navigation
    if (skipAnimations || (cards.length === 0 && sections.length === 0)) {
      return;
    }

    // Only animate on very first visit - quick fade in
    gsap.set([...cards, ...sections], { opacity: 0.8 });
    gsap.to([...sections, ...cards], {
      opacity: 1,
      duration: 0.15,
      stagger: 0.02,
      ease: "power2.out",
    });
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
            {/* Modern Unified Header with Semester + Search + Filters */}
            <div className="section-container mb-8">
              {/* Top Row: Semester Selector with higher z-index */}
              <div className="relative z-50 mb-5">
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                  <SemesterSelector
                    selectedSemester={selectedSemester}
                    availableSemesters={availableSemesters}
                    onSemesterChange={handleSemesterChange}
                  />
                  <div className="flex items-center gap-3">
                    {userRole === "Estudiante" && (
                      <button
                        onClick={() => router.push("/dashboard/agregar")}
                        className="px-4 py-2.5 rounded-xl text-sm font-semibold bg-emerald-600 text-white hover:bg-emerald-700 transition-all shadow-md shadow-emerald-500/20"
                      >
                        Subir Tesis
                      </button>
                    )}
                    <div className="flex items-center gap-2 px-4 py-2.5 bg-gradient-to-r from-emerald-50 to-teal-50 rounded-xl border border-emerald-200/60">
                      <div className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse shadow-sm shadow-emerald-500/50" />
                      <span className="text-sm font-semibold text-emerald-700">
                        {semesterProjects.length} tesis
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Bottom Row: Search and Filters with lower z-index */}
              <div className="relative z-10 bg-white/80 backdrop-blur-sm rounded-2xl border border-gray-200/80 shadow-sm p-4">
                <div className="flex flex-col lg:flex-row gap-4">
                  {/* Modern Search Input */}
                  <div className="relative flex-1 group">
                    <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                      <Search className="w-5 h-5 text-gray-400 group-focus-within:text-blue-500 transition-colors" />
                    </div>
                    <input
                      type="text"
                      placeholder="Buscar por título, estudiante o tutor..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="w-full pl-12 pr-4 py-3.5 bg-gray-50/80 border-2 border-gray-200/80 rounded-xl focus:bg-white focus:border-blue-400 focus:ring-4 focus:ring-blue-100 transition-all text-sm placeholder:text-gray-400"
                    />
                  </div>

                  {/* Modern Filter Pills */}
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider mr-1 hidden sm:block">
                      Filtrar:
                    </span>
                    <button
                      onClick={() => setFilterStatus("all")}
                      className={`px-4 py-2.5 rounded-xl text-sm font-semibold transition-all duration-200 ${
                        filterStatus === "all"
                          ? "bg-gradient-to-r from-blue-500 to-indigo-600 text-white shadow-lg shadow-blue-500/30 scale-[1.02]"
                          : "bg-gray-100 text-gray-600 hover:bg-gray-200 hover:text-gray-800"
                      }`}
                    >
                      Todos
                    </button>
                    <button
                      onClick={() => setFilterStatus("checked")}
                      className={`px-4 py-2.5 rounded-xl text-sm font-semibold transition-all duration-200 flex items-center gap-1.5 ${
                        filterStatus === "checked"
                          ? "bg-gradient-to-r from-emerald-500 to-green-600 text-white shadow-lg shadow-emerald-500/30 scale-[1.02]"
                          : "bg-gray-100 text-gray-600 hover:bg-emerald-50 hover:text-emerald-700"
                      }`}
                    >
                      <CheckCircle className="w-4 h-4" />
                      Revisados
                    </button>
                    <button
                      onClick={() => setFilterStatus("pending")}
                      className={`px-4 py-2.5 rounded-xl text-sm font-semibold transition-all duration-200 flex items-center gap-1.5 ${
                        filterStatus === "pending"
                          ? "bg-gradient-to-r from-amber-500 to-orange-600 text-white shadow-lg shadow-amber-500/30 scale-[1.02]"
                          : "bg-gray-100 text-gray-600 hover:bg-amber-50 hover:text-amber-700"
                      }`}
                    >
                      <Clock className="w-4 h-4" />
                      Pendientes
                    </button>
                    <button
                      onClick={() => setFilterStatus("rejected")}
                      className={`px-4 py-2.5 rounded-xl text-sm font-semibold transition-all duration-200 flex items-center gap-1.5 ${
                        filterStatus === "rejected"
                          ? "bg-gradient-to-r from-red-500 to-rose-600 text-white shadow-lg shadow-red-500/30 scale-[1.02]"
                          : "bg-gray-100 text-gray-600 hover:bg-red-50 hover:text-red-700"
                      }`}
                    >
                      <XCircle className="w-4 h-4" />
                      Rechazados
                    </button>
                  </div>
                </div>
              </div>
            </div>

            {/* Checked Projects Section */}
            {(filterStatus === "all" || filterStatus === "checked") &&
              checkedProjects.length > 0 && (
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
                  <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6 auto-rows-fr">
                    {checkedProjects.map((project) => (
                      <ProjectCard
                        key={project.id}
                        project={project}
                        type="tesis"
                        primaryLabel="Ver Detalles"
                        primaryHref={`/dashboard/tesis/${project.id}`}
                        canEdit={!isStudent}
                      />
                    ))}
                  </div>
                </div>
              )}

            {/* Pending Projects Section */}
            {(filterStatus === "all" || filterStatus === "pending") &&
              pendingProjects.length > 0 && (
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
                  <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6 auto-rows-fr">
                    {pendingProjects.map((project) => (
                      <ProjectCard
                        key={project.id}
                        project={project}
                        type="tesis"
                        primaryHref={
                          isStudent
                            ? `/dashboard/tesis/${project.id}`
                            : `/dashboard/tesis/${project.id}/evaluar`
                        }
                        primaryLabel={
                          isStudent ? "Ver Detalles" : "Revisar Ahora"
                        }
                        canEdit={!isStudent}
                      />
                    ))}
                  </div>
                </div>
              )}

            {/* Rejected Projects Section */}
            {(filterStatus === "all" || filterStatus === "rejected") &&
              rejectedProjects.length > 0 && (
                <div className="section-container mt-8">
                  <div className="flex items-center justify-between mb-4 sm:mb-6">
                    <h3 className="text-xl sm:text-2xl font-bold text-gray-900 flex items-center gap-2">
                      <XCircle className="w-6 h-6 text-red-600" />
                      Proyectos Rechazados
                    </h3>
                    <span className="text-sm sm:text-base text-gray-600 font-medium">
                      {rejectedProjects.length} proyectos
                    </span>
                  </div>
                  <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6 auto-rows-fr">
                    {rejectedProjects.map((project) => (
                      <ProjectCard
                        key={project.id}
                        project={project}
                        type="tesis"
                        primaryLabel="Ver Motivo"
                        primaryHref={`/dashboard/tesis/${project.id}`}
                        canEdit={!isStudent}
                      />
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
