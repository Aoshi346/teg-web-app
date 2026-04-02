"use client";

import React, { useState, useEffect, useMemo } from "react";
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

export default function ProyectosPage() {
  const router = useRouter();
  const userRole = useMemo(() => getUserRole(), []);
  const isStudent = userRole === "Estudiante";
  const [searchQuery, setSearchQuery] = useState("");
  const [filterStatus, setFilterStatus] = useState<
    "all" | "checked" | "pending" | "rejected"
  >("all");

  // Load proyectos including user-added ones
  const [allProjects, setAllProjects] = useState<Project[]>([]);
  const [semesterOptions, setSemesterOptions] = useState<string[]>([]);
  const [isDataLoaded, setIsDataLoaded] = useState(false);

  useEffect(() => {
    let mounted = true;
    (async () => {
      // Small delay to ensure the React router drops the Page skeleton immediately
      await new Promise(resolve => setTimeout(resolve, 0));
      
      const [apiProjects, semestersFromApi] = await Promise.all([
        getAllProjects(),
        getSemesters(),
      ]);
      const onlyProyectos = apiProjects.filter((p) => p.type === "proyecto");
      if (mounted) {
        setAllProjects(onlyProyectos);
        setSemesterOptions(semestersFromApi.map((s) => s.period));
        setIsDataLoaded(true);
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
    return availableSemesters.includes(stored)
      ? stored
      : availableSemesters[0] || stored;
  });

  useEffect(() => {
    if (availableSemesters.length === 0) return;
    if (!availableSemesters.includes(selectedSemester)) {
      const next = availableSemesters[0];
      setSelectedSemester(next);
      setStoredSemester(next);
    }
  }, [availableSemesters, selectedSemester]);

  const handleSemesterChange = (semester: string) => {
    setSelectedSemester(semester);
    setStoredSemester(semester);
  };

  // Filter by semester first, then by search/status
  const semesterProjects = useMemo<Project[]>(
    () => allProjects.filter((p) => p.period === selectedSemester),
    [selectedSemester, allProjects],
  );

  const filteredProjects = useMemo(() => {
    return semesterProjects.filter((project) => {
      const matchesSearch =
        project.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        project.student.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (project.advisorNames || []).some(n => n.toLowerCase().includes(searchQuery.toLowerCase()));

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

  // Entrance animations removed in favor of instantaneous module rendering
  // Data still fetches gracefully via the useEffect below.
  useEffect(() => {
    // Component mounts instantly without visual fade block.
  }, []); // Only run once on mount

  return (
    <>
      <DashboardHeader pageTitle="Proyectos" />

      <PageTransition>
        <main className="flex-1 p-3 sm:p-4 md:p-6 lg:p-8 overflow-y-auto bg-gray-50">
          <div className="max-w-7xl mx-auto">
            {/* Premium Header Layout */}
            <div className="mb-10">
              <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-6">
                <div className="space-y-1">
                  <h2 className="text-3xl font-extrabold text-gray-900 tracking-tight">Explorar Proyectos</h2>
                  <p className="text-gray-500 font-medium">Gestiona y revisa los proyectos académicos del período.</p>
                </div>
                
                <div className="flex flex-wrap items-center gap-4">
                  <div className="relative z-50">
                    <SemesterSelector
                      selectedSemester={selectedSemester}
                      availableSemesters={availableSemesters}
                      onSemesterChange={handleSemesterChange}
                    />
                  </div>

                  <div className="h-10 w-px bg-gray-200 hidden sm:block mx-1" />

                  <div className="flex items-center gap-3">
                    {userRole === "Estudiante" && (
                      <button
                        onClick={() => router.push("/dashboard/agregar")}
                        className="group relative px-5 py-2.5 rounded-xl text-sm font-bold bg-[#0f172a] text-white hover:bg-[#1e293b] transition-all shadow-lg shadow-slate-900/10 flex items-center gap-2 overflow-hidden"
                      >
                        <div className="absolute inset-0 bg-gradient-to-r from-blue-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                        <FileText className="w-4 h-4 text-blue-400" />
                        <span>Subir Proyecto</span>
                      </button>
                    )}
                    <div className="flex items-center gap-2.5 px-4 py-2.5 bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl border border-blue-100/50 shadow-sm">
                      <div className="relative">
                        <div className="w-2.5 h-2.5 rounded-full bg-blue-500 animate-pulse" />
                        <div className="absolute inset-0 w-2.5 h-2.5 rounded-full bg-blue-500/50 animate-ping" />
                      </div>
                      <span className="text-sm font-bold text-blue-700">
                        {semesterProjects.length} {semesterProjects.length === 1 ? 'Proyecto' : 'Proyectos'}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Modernized Search and Filters */}
            <div className="bg-white/60 backdrop-blur-xl rounded-[2rem] border border-gray-200/60 shadow-xl shadow-slate-200/40 p-5 sm:p-6 mb-12">
              <div className="flex flex-col xl:flex-row gap-6">
                {/* Visualistic Search Bar */}
                <div className="relative flex-1 group">
                  <div className="absolute inset-y-0 left-0 pl-5 flex items-center pointer-events-none">
                    <Search className="w-5 h-5 text-gray-400 group-focus-within:text-blue-500 transition-colors duration-300" />
                  </div>
                  <input
                    type="text"
                    placeholder="Buscar por título, estudiante o tutor..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full pl-13 pr-6 py-4 bg-white/50 border border-gray-200 rounded-2xl focus:bg-white focus:border-blue-400 focus:ring-4 focus:ring-blue-100/50 transition-all duration-300 text-sm font-medium placeholder:text-gray-400 shadow-inner"
                    style={{ paddingLeft: '3.25rem' }}
                  />
                  <div className="absolute right-3 top-1/2 -translate-y-1/2 px-2 py-1 bg-gray-100 rounded-md text-[10px] font-bold text-gray-400 uppercase tracking-widest border border-gray-200 opacity-0 group-focus-within:opacity-100 transition-opacity">
                    ESC
                  </div>
                </div>

                {/* Refined Filter Pills with unique Hues */}
                <div className="flex items-center gap-2 p-1.5 bg-gray-100/50 rounded-2xl border border-gray-100 self-start">
                  <button
                    onClick={() => setFilterStatus("all")}
                    className={`px-5 py-2.5 rounded-xl text-sm font-bold transition-all duration-300 ${
                      filterStatus === "all"
                        ? "bg-white text-blue-600 shadow-md ring-1 ring-black/5 scale-[1.02]"
                        : "text-gray-500 hover:text-gray-900 hover:bg-white/50"
                    }`}
                  >
                    Todos
                  </button>
                  
                  <div className="w-px h-6 bg-gray-200 mx-1" />

                  <button
                    onClick={() => setFilterStatus("checked")}
                    className={`px-5 py-2.5 rounded-xl text-sm font-bold transition-all duration-300 flex items-center gap-2 ${
                      filterStatus === "checked"
                        ? "bg-[#ecfdf5] text-[#059669] shadow-sm ring-1 ring-[#10b981]/20"
                        : "text-gray-500 hover:text-[#059669] hover:bg-[#ecfdf5]/50"
                    }`}
                  >
                    <div className={`w-2 h-2 rounded-full ${filterStatus === "checked" ? "bg-[#059669]" : "bg-gray-300"}`} />
                    Revisados
                  </button>

                  <button
                    onClick={() => setFilterStatus("pending")}
                    className={`px-5 py-2.5 rounded-xl text-sm font-bold transition-all duration-300 flex items-center gap-2 ${
                      filterStatus === "pending"
                        ? "bg-[#fffbeb] text-[#d97706] shadow-sm ring-1 ring-[#f59e0b]/20"
                        : "text-gray-500 hover:text-[#d97706] hover:bg-[#fffbeb]/50"
                    }`}
                  >
                    <div className={`w-2 h-2 rounded-full ${filterStatus === "pending" ? "bg-[#d97706]" : "bg-gray-300"}`} />
                    Pendientes
                  </button>

                  <button
                    onClick={() => setFilterStatus("rejected")}
                    className={`px-5 py-2.5 rounded-xl text-sm font-bold transition-all duration-300 flex items-center gap-2 ${
                      filterStatus === "rejected"
                        ? "bg-[#fef2f2] text-[#dc2626] shadow-sm ring-1 ring-[#ef4444]/20"
                        : "text-gray-500 hover:text-[#dc2626] hover:bg-[#fef2f2]/50"
                    }`}
                  >
                    <div className={`w-2 h-2 rounded-full ${filterStatus === "rejected" ? "bg-[#dc2626]" : "bg-gray-300"}`} />
                    Rechazados
                  </button>
                </div>
              </div>
            </div>

            {!isDataLoaded && (
              <div className="flex justify-center items-center py-20">
                <div className="w-8 h-8 rounded-full border-4 border-slate-200 border-t-blue-600 animate-spin" />
              </div>
            )}

            {isDataLoaded && (filterStatus === "all" || filterStatus === "checked") &&
              checkedProjects.length > 0 && (
                <div className="section-container mb-12">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 rounded-2xl bg-emerald-50 flex items-center justify-center text-emerald-600 shadow-sm border border-emerald-100">
                        <CheckCircle className="w-6 h-6" />
                      </div>
                      <div>
                        <h3 className="text-2xl font-bold text-gray-900 tracking-tight">Proyectos Revisados</h3>
                        <p className="text-sm text-gray-500 font-medium">Proyectos que ya cuentan con una calificación.</p>
                      </div>
                    </div>
                    <div className="px-4 py-1.5 bg-emerald-50 rounded-full border border-emerald-100/50 self-start sm:self-center">
                      <span className="text-sm font-bold text-emerald-700">
                        {checkedProjects.length} {checkedProjects.length === 1 ? 'proyecto' : 'proyectos'}
                      </span>
                    </div>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-8">
                    {checkedProjects.map((project) => (
                      <ProjectCard
                        key={project.id}
                        project={project}
                        type="proyecto"
                        primaryLabel="Ver Detalles"
                        primaryHref={`/dashboard/proyectos/${project.id}`}
                        canEdit={!isStudent}
                      />
                    ))}
                  </div>
                </div>
              )}

            {isDataLoaded && (filterStatus === "all" || filterStatus === "pending") &&
              pendingProjects.length > 0 && (
                <div className="section-container mb-12">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 rounded-2xl bg-amber-50 flex items-center justify-center text-amber-600 shadow-sm border border-amber-100">
                        <Clock className="w-6 h-6" />
                      </div>
                      <div>
                        <h3 className="text-2xl font-bold text-gray-900 tracking-tight">Proyectos Pendientes</h3>
                        <p className="text-sm text-gray-500 font-medium">Proyectos que requieren revisión por parte de un tutor.</p>
                      </div>
                    </div>
                    <div className="px-4 py-1.5 bg-amber-50 rounded-full border border-amber-100/50 self-start sm:self-center">
                      <span className="text-sm font-bold text-amber-700">
                        {pendingProjects.length} {pendingProjects.length === 1 ? 'proyecto' : 'proyectos'}
                      </span>
                    </div>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-8">
                    {pendingProjects.map((project) => (
                      <ProjectCard
                        key={project.id}
                        project={project}
                        type="proyecto"
                        primaryHref={
                          isStudent
                            ? `/dashboard/proyectos/${project.id}`
                            : `/dashboard/proyectos/${project.id}/evaluar`
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

            {isDataLoaded && (filterStatus === "all" || filterStatus === "rejected") &&
              rejectedProjects.length > 0 && (
                <div className="section-container mb-12">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 rounded-2xl bg-red-50 flex items-center justify-center text-red-600 shadow-sm border border-red-100">
                        <XCircle className="w-6 h-6" />
                      </div>
                      <div>
                        <h3 className="text-2xl font-bold text-gray-900 tracking-tight">Proyectos Rechazados</h3>
                        <p className="text-sm text-gray-500 font-medium">Proyectos que no cumplen con los requisitos mínimos.</p>
                      </div>
                    </div>
                    <div className="px-4 py-1.5 bg-red-50 rounded-full border border-red-100/50 self-start sm:self-center">
                      <span className="text-sm font-bold text-red-700">
                        {rejectedProjects.length} {rejectedProjects.length === 1 ? 'proyecto' : 'proyectos'}
                      </span>
                    </div>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-8">
                    {rejectedProjects.map((project) => (
                      <ProjectCard
                        key={project.id}
                        project={project}
                        type="proyecto"
                        primaryLabel="Ver Motivo"
                        primaryHref={`/dashboard/proyectos/${project.id}`}
                        canEdit={!isStudent}
                      />
                    ))}
                  </div>
                </div>
              )}

            {isDataLoaded && filteredProjects.length === 0 && (
              <div className="bg-white/40 backdrop-blur-sm rounded-[2.5rem] border border-dashed border-gray-300 py-20 text-center relative overflow-hidden">
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-64 h-64 bg-blue-50/50 rounded-full blur-3xl -z-10" />
                <div className="w-20 h-20 bg-gray-50 rounded-3xl flex items-center justify-center mx-auto mb-6 shadow-inner border border-gray-100">
                  <FileText className="w-10 h-10 text-gray-300" />
                </div>
                <h3 className="text-2xl font-bold text-gray-900 mb-2">
                  No se encontraron proyectos
                </h3>
                <p className="text-gray-500 font-medium max-w-sm mx-auto">
                  Parece que no hay resultados que coincidan con tus criterios de búsqueda o filtros actuales.
                </p>
                <button 
                  onClick={() => { setSearchQuery(""); setFilterStatus("all"); }}
                  className="mt-8 px-6 py-2.5 bg-white text-gray-700 font-bold text-sm rounded-xl border border-gray-200 hover:bg-gray-50 transition-all shadow-sm"
                >
                  Restablecer filtros
                </button>
              </div>
            )}
          </div>
        </main>
      </PageTransition>
    </>
  );
}
