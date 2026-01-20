import React from "react";
import { Project } from "@/types/project";
import { FileText, BookOpen, Clock, Calendar, CheckCircle, XCircle, ChevronLeft, ChevronRight, User } from "lucide-react";

interface TrackingTableProps {
    items: Project[];
    onReview?: (project: Project) => void;
    pagination?: {
        currentPage: number;
        totalPages: number;
        onPageChange: (page: number) => void;
    };
}

const Avatar: React.FC<{ name: string }> = ({ name }) => {
    const initials = name
        .split(" ")
        .map((n) => n[0])
        .slice(0, 2)
        .join("")
        .toUpperCase();

    // Deterministic color generation based on name
    const colors = [
        "bg-red-100 text-red-600",
        "bg-orange-100 text-orange-600",
        "bg-amber-100 text-amber-600",
        "bg-green-100 text-green-600",
        "bg-emerald-100 text-emerald-600",
        "bg-teal-100 text-teal-600",
        "bg-cyan-100 text-cyan-600",
        "bg-sky-100 text-sky-600",
        "bg-blue-100 text-blue-600",
        "bg-indigo-100 text-indigo-600",
        "bg-violet-100 text-violet-600",
        "bg-purple-100 text-purple-600",
        "bg-fuchsia-100 text-fuchsia-600",
        "bg-pink-100 text-pink-600",
        "bg-rose-100 text-rose-600",
    ];
    const colorIndex = name.length % colors.length;
    const colorClass = colors[colorIndex];

    return (
        <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold ${colorClass}`}>
            {initials}
        </div>
    );
};

const TrackingTable: React.FC<TrackingTableProps> = ({ items, onReview, pagination }) => {
    if (items.length === 0) {
        return (
            <div className="text-center py-16 bg-white rounded-2xl border border-gray-100 shadow-sm flex flex-col items-center">
                <div className="w-16 h-16 bg-gray-50 rounded-full flex items-center justify-center mb-4">
                    <CheckCircle className="w-8 h-8 text-gray-400" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900">
                    Todo al día
                </h3>
                <p className="text-gray-500 mt-1 max-w-sm">
                    No hay evaluaciones pendientes en este momento para el filtro seleccionado.
                </p>
            </div>
        );
    }

    return (
        <div className="bg-white rounded-2xl border border-gray-200/60 shadow-sm overflow-hidden flex flex-col">
            <div className="overflow-x-auto">
                <table className="w-full text-left text-sm whitespace-nowrap">
                    <thead>
                        <tr className="bg-gray-50/50 border-b border-gray-100 text-gray-500 font-medium text-xs uppercase tracking-wider">
                            <th className="px-6 py-4 pl-8">Proyecto / Tesis</th>
                            <th className="px-6 py-4">Estudiante</th>
                            <th className="px-6 py-4">Tipo</th>
                            <th className="px-6 py-4">Fecha Entrega</th>
                            <th className="px-6 py-4">Estado</th>
                            <th className="px-6 py-4 text-right pr-8">Acción</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100 bg-white">
                        {items.map((item) => {
                            const isTesis = "stage1Passed" in item;
                            const typeLabel = isTesis ? "TEG" : "PTEG";
                            const typeColor = isTesis
                                ? "bg-purple-50 text-purple-700 ring-1 ring-purple-600/20"
                                : "bg-blue-50 text-blue-700 ring-1 ring-blue-600/20";
                            const Icon = isTesis ? BookOpen : FileText;

                            // Date formatting
                            const dateObj = new Date(item.submittedDate);
                            const dateStr = dateObj.toLocaleDateString('es-ES', { day: 'numeric', month: 'short', year: 'numeric' });

                            return (
                                <tr
                                    key={`${isTesis ? 'teg' : 'pteg'}-${item.id}`}
                                    className="hover:bg-gray-50/80 transition-colors group"
                                >
                                    <td className="px-6 py-4 pl-8">
                                        <div className="flex items-start gap-3.5">
                                            <div className={`p-2.5 rounded-xl flex-shrink-0 mt-0.5 ${isTesis ? 'bg-purple-50 text-purple-600' : 'bg-blue-50 text-blue-600'}`}>
                                                <Icon className="w-5 h-5" />
                                            </div>
                                            <div className="min-w-0">
                                                <p className="font-semibold text-gray-900 truncate max-w-[280px]" title={item.title}>
                                                    {item.title}
                                                </p>
                                                <p className="text-xs text-gray-500 mt-1 flex items-center gap-1.5 truncate max-w-[280px]">
                                                    <User className="w-3 h-3" />
                                                    <span>Tutor: {item.advisor}</span>
                                                </p>
                                            </div>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4">
                                        <div className="flex items-center gap-3">
                                            <Avatar name={item.student} />
                                            <span className="font-medium text-gray-700">{item.student}</span>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4">
                                        <span
                                            className={`inline-flex items-center px-2.5 py-1 rounded-md text-xs font-semibold ${typeColor}`}
                                        >
                                            {typeLabel}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 text-gray-600">
                                        <div className="flex items-center gap-2">
                                            <Calendar className="w-4 h-4 text-gray-400" />
                                            <span className="capitalize">{dateStr}</span>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4">
                                        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-amber-50 text-amber-700 ring-1 ring-amber-600/20">
                                            <span className="relative flex h-2 w-2">
                                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75"></span>
                                                <span className="relative inline-flex rounded-full h-2 w-2 bg-amber-500"></span>
                                            </span>
                                            Pendiente
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 text-right pr-8">
                                        <button
                                            onClick={() => onReview?.(item)}
                                            className="inline-flex items-center justify-center px-4 py-2 text-sm font-medium rounded-lg text-blue-700 bg-blue-50 hover:bg-blue-100 active:bg-blue-200 transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
                                        >
                                            Revisar
                                        </button>
                                    </td>
                                </tr>
                            );
                        })}
                    </tbody>
                </table>
            </div>

            {/* Pagination Footer */}
            {pagination && pagination.totalPages > 1 && (
                <div className="flex items-center justify-between px-6 py-4 border-t border-gray-200 bg-gray-50/40">
                    <div className="text-sm text-gray-500 hidden sm:block">
                        Página <span className="font-medium text-gray-900">{pagination.currentPage}</span> de <span className="font-medium text-gray-900">{pagination.totalPages}</span>
                    </div>

                    <div className="flex items-center gap-2 mx-auto sm:mx-0">
                        <button
                            onClick={() => pagination.onPageChange(Math.max(1, pagination.currentPage - 1))}
                            disabled={pagination.currentPage === 1}
                            className="p-2 rounded-lg border border-gray-200 bg-white text-gray-600 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-sm"
                            aria-label="Página anterior"
                        >
                            <ChevronLeft className="w-4 h-4" />
                        </button>

                        {/* Simple page numbers for small sets, or just current/total */}
                        <div className="flex items-center gap-1">
                            {Array.from({ length: Math.min(5, pagination.totalPages) }, (_, i) => {
                                // Very simple pagination logic for demo - improves with robust algo
                                let pageNum = i + 1;
                                if (pagination.totalPages > 5 && pagination.currentPage > 3) {
                                    pageNum = pagination.currentPage - 2 + i;
                                    // clamp
                                    if (pageNum > pagination.totalPages) pageNum = pagination.totalPages - (4 - i);
                                }

                                if (pageNum <= 0) return null; // safety

                                return (
                                    <button
                                        key={pageNum}
                                        onClick={() => pagination.onPageChange(pageNum)}
                                        className={`w-8 h-8 flex items-center justify-center rounded-lg text-sm font-medium transition-all ${pagination.currentPage === pageNum
                                                ? "bg-blue-600 text-white shadow-md shadow-blue-500/20"
                                                : "text-gray-600 hover:bg-gray-100"
                                            }`}
                                    >
                                        {pageNum}
                                    </button>
                                )
                            })}
                        </div>

                        <button
                            onClick={() => pagination.onPageChange(Math.min(pagination.totalPages, pagination.currentPage + 1))}
                            disabled={pagination.currentPage === pagination.totalPages}
                            className="p-2 rounded-lg border border-gray-200 bg-white text-gray-600 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-sm"
                            aria-label="Página siguiente"
                        >
                            <ChevronRight className="w-4 h-4" />
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
};

export default TrackingTable;
