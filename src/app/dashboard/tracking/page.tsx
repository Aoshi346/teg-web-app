"use client";

import React, { useEffect, useState, useMemo } from "react";
import DashboardHeader from "@/components/layout/DashboardHeader";
import PageTransition from "@/components/ui/PageTransition";
import TrackingTable from "@/components/ui/TrackingTable";
import { getProyectos, getTesis, Project } from "@/lib/data/mockData";
import { LayoutDashboard, Filter } from "lucide-react";

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
    const [items, setItems] = useState<Project[]>([]);
    const [filter, setFilter] = useState<"all" | "pteg" | "teg">("all");

    useEffect(() => {
        // Load data from mock sources (which read from localStorage)
        const proyectos = getProyectos();
        const tesis = getTesis();

        // Mark types for filtering
        const pWithMeta = proyectos.map((p) => ({ ...p, _type: "pteg" }));
        const tWithMeta = tesis.map((t) => ({ ...t, _type: "teg" }));

        // Merge and filter for Pending
        const allPending = [...pWithMeta, ...tWithMeta].filter(
            (item) => item.status === "pending"
        );

        // Sort by Date (Suspense: newest first)
        allPending.sort(
            (a, b) =>
                new Date(b.submittedDate).getTime() - new Date(a.submittedDate).getTime()
        );

        setItems(allPending);
    }, []);

    const filteredItems = useMemo(() => {
        if (filter === "all") return items;
        return items.filter((item: any) => item._type === filter);
    }, [items, filter]);

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
                <main className="flex-1 p-3 sm:p-4 md:p-6 lg:p-8 overflow-y-auto bg-gray-50">
                    <div className="max-w-7xl mx-auto space-y-6">
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                            <div>
                                <h2 className="text-2xl font-bold text-gray-900">
                                    Evaluaciones Pendientes
                                </h2>
                                <p className="text-gray-500 mt-1">
                                    Gestiona y revisa las entregas que requieren tu atención inmediata.
                                </p>
                            </div>

                            {/* Filter Tabs */}
                            <div className="flex items-center bg-white p-1 rounded-lg border border-gray-200 shadow-sm">
                                <button
                                    onClick={() => setFilter("all")}
                                    className={`px-4 py-2 text-sm font-medium rounded-md transition-all ${filter === "all"
                                            ? "bg-gray-100 text-gray-900 shadow-sm"
                                            : "text-gray-600 hover:text-gray-900 hover:bg-gray-50"
                                        }`}
                                >
                                    Todos
                                </button>
                                <button
                                    onClick={() => setFilter("pteg")}
                                    className={`px-4 py-2 text-sm font-medium rounded-md transition-all ${filter === "pteg"
                                            ? "bg-blue-50 text-blue-700 shadow-sm"
                                            : "text-gray-600 hover:text-gray-900 hover:bg-gray-50"
                                        }`}
                                >
                                    Solo PTEG
                                </button>
                                <button
                                    onClick={() => setFilter("teg")}
                                    className={`px-4 py-2 text-sm font-medium rounded-md transition-all ${filter === "teg"
                                            ? "bg-purple-50 text-purple-700 shadow-sm"
                                            : "text-gray-600 hover:text-gray-900 hover:bg-gray-50"
                                        }`}
                                >
                                    Solo TEG
                                </button>
                            </div>
                        </div>

                        <TrackingTable
                            items={filteredItems}
                            onReview={(item) => {
                                alert(`Revisar proyecto ID: ${item.id} - ${item.title}`);
                                // Navigate to specific review page later
                            }}
                        />
                    </div>
                </main>
            </PageTransition>
        </>
    );
}
