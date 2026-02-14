"use client";

import React, { useEffect, useState, useMemo } from "react";
import { useRouter } from "next/navigation";
import DashboardHeader from "@/components/layout/DashboardHeader";
import PageTransition from "@/components/ui/PageTransition";
import TrackingTable from "@/components/ui/TrackingTable";
import SemesterSelector from "@/components/ui/SemesterSelector";
import {
  getAvailableSemesters,
  getStoredSemester,
  setStoredSemester,
  getCurrentSemester,
  getSemesters,
} from "@/lib/semesters";
import { getAllProjects } from "@/features/projects/projectService";
import { Project } from "@/types/project";
import { getUserRole } from "@/features/auth/clientAuth";

const ITEMS_PER_PAGE = 5;

export default function TrackingPage({
  handleSidebarCollapse,
  handleMobileSidebarToggle,
  isSidebarCollapsed,
  isMobileSidebarOpen,
}: {
  handleSidebarCollapse?: () => void;
  handleMobileSidebarToggle?: () => void;
  isSidebarCollapsed?: boolean;
  isMobileSidebarOpen?: boolean;
}) {
  const router = useRouter();
  const [projects, setProjects] = useState<Project[]>([]);
  const [filter, setFilter] = useState<"all" | "pteg" | "teg">("all");
  const [semester, setSemester] = useState<string>("");
  const [availableSemesters, setAvailableSemesters] = useState<string[]>([]);
  const [currentPage, setCurrentPage] = useState(1);
  const userRole = useMemo(() => getUserRole(), []);
  const isStudent = userRole === "Estudiante";

  useEffect(() => {
    const fetchData = async () => {
      const [apiProjects, semestersFromApi] = await Promise.all([
        getAllProjects(),
        getSemesters(),
      ]);
      setProjects(apiProjects);

      const semesters = getAvailableSemesters(
        apiProjects,
        semestersFromApi.map((s) => s.period),
      );
      const stored = getStoredSemester();
      const fallback = getCurrentSemester();
      const chosen = semesters.length
        ? semesters.includes(stored)
          ? stored
          : semesters[0]
        : stored || fallback;

      setAvailableSemesters(semesters.length ? semesters : [chosen]);
      if (semesters.length > 0) {
        setSemester(semesters.includes(stored) ? stored : semesters[0]);
      } else {
        setSemester(chosen);
      }
    };

    fetchData();
  }, []);

  // Re-run pagination reset when semester changes
  useEffect(() => {
    if (semester) {
      setCurrentPage(1);
    }
  }, [semester]);

  const semesterProjects = useMemo(() => {
    return projects
      .filter((p) => !semester || p.period === semester)
      .sort(
        (a, b) =>
          new Date(b.submittedDate).getTime() -
          new Date(a.submittedDate).getTime(),
      );
  }, [projects, semester]);

  const filteredItems = useMemo(() => {
    const base = isStudent
      ? semesterProjects
      : semesterProjects.filter((p) => p.status === "pending");

    if (filter === "all") return base;
    return base.filter((item) =>
      filter === "teg" ? item.type === "tesis" : item.type === "proyecto",
    );
  }, [semesterProjects, filter, isStudent]);

  // Pagination Logic
  const totalPages = Math.max(
    1,
    Math.ceil(filteredItems.length / ITEMS_PER_PAGE),
  );
  const paginatedItems = useMemo(() => {
    const start = (currentPage - 1) * ITEMS_PER_PAGE;
    return filteredItems.slice(start, start + ITEMS_PER_PAGE);
  }, [filteredItems, currentPage]);

  // Handle filter change with page reset
  const handleFilterChange = (newFilter: "all" | "pteg" | "teg") => {
    setFilter(newFilter);
    setCurrentPage(1);
  };

  return (
    <>
      <DashboardHeader
        pageTitle="Seguimiento"
        isSidebarCollapsed={isSidebarCollapsed}
        isMobileSidebarOpen={isMobileSidebarOpen}
        onMobileSidebarToggle={handleMobileSidebarToggle}
        onSidebarCollapse={handleSidebarCollapse}
      />

      <PageTransition>
        <main className="flex-1 p-3 sm:p-4 md:p-6 lg:p-8 overflow-y-auto bg-gray-50/50">
          <div className="max-w-7xl mx-auto space-y-6">
            <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-4">
              <div>
                <h2 className="text-2xl font-bold text-gray-900 tracking-tight">
                  {isStudent
                    ? "Estado de mi trabajo"
                    : "Evaluaciones Pendientes"}
                </h2>
                <p className="text-gray-500 mt-1">
                  {isStudent
                    ? "Consulta el estado y los detalles de tu proyecto o tesis."
                    : "Gestiona y revisa las entregas que requieren tu atención inmediata."}
                </p>
              </div>

              <div className="flex flex-col sm:flex-row gap-3">
                <SemesterSelector
                  selectedSemester={semester}
                  availableSemesters={availableSemesters}
                  onSemesterChange={(sem) => {
                    setStoredSemester(sem);
                    setSemester(sem);
                  }}
                />

                {/* Filter Tabs (Segmented Control Style) */}
                <div className="flex items-center bg-gray-100/80 p-1 rounded-xl self-start sm:self-auto">
                  <button
                    onClick={() => handleFilterChange("all")}
                    className={`px-4 py-2 text-sm font-semibold rounded-lg transition-all duration-200 ${
                      filter === "all"
                        ? "bg-white text-gray-900 shadow-sm ring-1 ring-black/5"
                        : "text-gray-500 hover:text-gray-700 hover:bg-gray-200/50"
                    }`}
                  >
                    Todos
                  </button>
                  <button
                    onClick={() => handleFilterChange("pteg")}
                    className={`px-4 py-2 text-sm font-semibold rounded-lg transition-all duration-200 ${
                      filter === "pteg"
                        ? "bg-white text-blue-700 shadow-sm ring-1 ring-black/5"
                        : "text-gray-500 hover:text-gray-700 hover:bg-gray-200/50"
                    }`}
                  >
                    PTEG
                  </button>
                  <button
                    onClick={() => handleFilterChange("teg")}
                    className={`px-4 py-2 text-sm font-semibold rounded-lg transition-all duration-200 ${
                      filter === "teg"
                        ? "bg-white text-purple-700 shadow-sm ring-1 ring-black/5"
                        : "text-gray-500 hover:text-gray-700 hover:bg-gray-200/50"
                    }`}
                  >
                    TEG
                  </button>
                </div>
              </div>
            </div>

            {filteredItems.length === 0 ? (
              <div className="p-6 bg-white border border-gray-200 rounded-2xl text-center shadow-sm">
                <p className="text-base font-semibold text-gray-800">
                  No hay entregas que coincidan.
                </p>
                <p className="text-sm text-gray-500 mt-1">
                  Ajusta el semestre o los filtros para ver más resultados.
                </p>
              </div>
            ) : (
              <TrackingTable
                items={paginatedItems}
                userRole={userRole}
                pagination={{
                  currentPage,
                  totalPages,
                  onPageChange: setCurrentPage,
                }}
                onView={(item) => {
                  const isTesis = item.type === "tesis";
                  const basePath = isTesis
                    ? "/dashboard/tesis"
                    : "/dashboard/proyectos";
                  router.push(`${basePath}/${item.id}`);
                }}
                onReview={
                  isStudent
                    ? undefined
                    : (item) => {
                        const isTesis = item.type === "tesis";
                        const basePath = isTesis
                          ? "/dashboard/tesis"
                          : "/dashboard/proyectos";
                        router.push(`${basePath}/${item.id}`);
                      }
                }
              />
            )}
          </div>
        </main>
      </PageTransition>
    </>
  );
}
