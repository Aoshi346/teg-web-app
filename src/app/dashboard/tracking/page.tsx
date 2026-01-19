"use client";

import React, { useEffect, useState, useMemo } from "react";
import { useRouter } from "next/navigation";
import DashboardHeader from "@/components/layout/DashboardHeader";
import PageTransition from "@/components/ui/PageTransition";
import TrackingTable from "@/components/ui/TrackingTable";
import SemesterSelector from "@/components/ui/SemesterSelector";
import { getProyectos, getTesis, Project, mockProyectos, mockTesis } from "@/lib/data/mockData";
import { getAvailableSemesters, getStoredSemester, setStoredSemester } from "@/lib/semesters";
import { LayoutDashboard, Filter } from "lucide-react";

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
    const [items, setItems] = useState<Project[]>([]);
    const [filter, setFilter] = useState<"all" | "pteg" | "teg">("all");
    const [semester, setSemester] = useState<string>("");
    const [currentPage, setCurrentPage] = useState(1);

    useEffect(() => {
        // Initialize semester
        setSemester(getStoredSemester());
    }, []);

    useEffect(() => {
        if (!semester) return;

        // Load data from mock sources (which read from localStorage)
        const proyectos = getProyectos();
        const tesis = getTesis();

        // Mark types for filtering
        const pWithMeta = proyectos.map((p) => ({ ...p, _type: "pteg" }));
        const tWithMeta = tesis.map((t) => ({ ...t, _type: "teg" }));

        // Merge and filter for Pending AND Semester
        const allPending = [...pWithMeta, ...tWithMeta].filter(
            (item) => item.status === "pending" && item.semester === semester
        );

        // Sort by Date (Suspense: newest first)
        allPending.sort(
            (a, b) =>
                new Date(b.submittedDate).getTime() - new Date(a.submittedDate).getTime()
        );

        setItems(allPending);
        setCurrentPage(1); // Reset page on semester change
    }, [semester]);

    const filteredItems = useMemo(() => {
        if (filter === "all") return items;
        return items.filter((item: any) => item._type === filter);
    }, [items, filter]);

    // Pagination Logic
    const totalPages = Math.ceil(filteredItems.length / ITEMS_PER_PAGE);
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
                                    Evaluaciones Pendientes
                                </h2>
                                <p className="text-gray-500 mt-1">
                                    Gestiona y revisa las entregas que requieren tu atención inmediata.
                                </p>
                            </div>

                            <div className="flex flex-col sm:flex-row gap-3">
                                <SemesterSelector
                                    selectedSemester={semester}
                                    availableSemesters={getAvailableSemesters([...mockTesis, ...mockProyectos])}
                                    onSemesterChange={(sem) => {
                                        setStoredSemester(sem);
                                        setSemester(sem);
                                    }}
                                />

                                {/* Filter Tabs (Segmented Control Style) */}
                                <div className="flex items-center bg-gray-100/80 p-1 rounded-xl self-start sm:self-auto">
                                    <button
                                        onClick={() => handleFilterChange("all")}
                                        className={`px-4 py-2 text-sm font-semibold rounded-lg transition-all duration-200 ${filter === "all"
                                                ? "bg-white text-gray-900 shadow-sm ring-1 ring-black/5"
                                                : "text-gray-500 hover:text-gray-700 hover:bg-gray-200/50"
                                            }`}
                                    >
                                        Todos
                                    </button>
                                    <button
                                        onClick={() => handleFilterChange("pteg")}
                                        className={`px-4 py-2 text-sm font-semibold rounded-lg transition-all duration-200 ${filter === "pteg"
                                                ? "bg-white text-blue-700 shadow-sm ring-1 ring-black/5"
                                                : "text-gray-500 hover:text-gray-700 hover:bg-gray-200/50"
                                            }`}
                                    >
                                        PTEG
                                    </button>
                                    <button
                                        onClick={() => handleFilterChange("teg")}
                                        className={`px-4 py-2 text-sm font-semibold rounded-lg transition-all duration-200 ${filter === "teg"
                                                ? "bg-white text-purple-700 shadow-sm ring-1 ring-black/5"
                                                : "text-gray-500 hover:text-gray-700 hover:bg-gray-200/50"
                                            }`}
                                    >
                                        TEG
                                    </button>
                                </div>
                            </div>
                        </div>

                        <TrackingTable
                            items={paginatedItems}
                            pagination={{
                                currentPage,
                                totalPages,
                                onPageChange: setCurrentPage
                            }}
                            onReview={(item) => {
                                // Determine if it's TEG or PTEG based on stage1Passed property or _type if available
                                const isTesis = "stage1Passed" in item || (item as any)._type === "teg";

                                if (isTesis) {
                                    router.push(`/dashboard/tesis/${item.id}`);
                                } else {
                                    router.push(`/dashboard/proyectos/${item.id}`);
                                }
                            }}
                        />
                    </div>
                </main>
            </PageTransition>
        </>
    );
}
