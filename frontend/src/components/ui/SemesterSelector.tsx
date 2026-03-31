"use client";

import React from "react";
import { createPortal } from "react-dom";
import { ChevronDown, Calendar, Check, X, Search } from "lucide-react";
import { formatSemesterLabel, parseSemester } from "@/lib/semesters";

interface SemesterSelectorProps {
    selectedSemester: string;
    availableSemesters: string[];
    onSemesterChange: (semester: string) => void;
    className?: string;
}

// Group semesters by year
function groupSemestersByYear(semesters: string[]): Map<number, string[]> {
    const groups = new Map<number, string[]>();
    for (const semester of semesters) {
        const { year } = parseSemester(semester);
        if (!groups.has(year)) groups.set(year, []);
        groups.get(year)!.push(semester);
    }
    return new Map([...groups.entries()].sort((a, b) => b[0] - a[0]));
}

export default function SemesterSelector({
    selectedSemester,
    availableSemesters,
    onSemesterChange,
    className = "",
}: SemesterSelectorProps) {
    const [isOpen, setIsOpen] = React.useState(false);
    const [mounted, setMounted] = React.useState(false);
    const [searchQuery, setSearchQuery] = React.useState("");
    const buttonRef = React.useRef<HTMLButtonElement>(null);
    const searchInputRef = React.useRef<HTMLInputElement>(null);

    React.useEffect(() => {
        setMounted(true);
    }, []);

    // Focus search on open
    React.useEffect(() => {
        if (isOpen) {
            setTimeout(() => {
                searchInputRef.current?.focus();
            }, 100);
        } else {
            setSearchQuery(""); // Reset search on close
        }
    }, [isOpen]);

    // Close on escape
    React.useEffect(() => {
        const handleEscape = (e: KeyboardEvent) => {
            if (e.key === "Escape") setIsOpen(false);
        };
        if (isOpen) {
            document.addEventListener("keydown", handleEscape);
            return () => document.removeEventListener("keydown", handleEscape);
        }
    }, [isOpen]);

    if (availableSemesters.length === 0) return null;

    // Filter semesters
    const filteredSemesters = availableSemesters.filter(sem => {
        if (!searchQuery) return true;
        const q = searchQuery.toLowerCase();
        const { period, year } = parseSemester(sem);
        const fullLabel = `semestre ${period}`;
        return (
            year.toString().includes(q) ||
            fullLabel.includes(q) ||
            sem.toLowerCase().includes(q)
        );
    });

    const groupedSemesters = groupSemestersByYear(filteredSemesters);

    // Modal/overlay content
    const modalContent = (
        <div
            className="fixed inset-0 z-[99999] flex items-center justify-center p-4 sm:p-6"
            onClick={() => setIsOpen(false)}
        >
            {/* Backdrop */}
            <div className="absolute inset-0 bg-black/25 backdrop-blur-sm transition-opacity" />

            {/* Modal */}
            <div
                className="relative bg-white rounded-2xl shadow-2xl w-full max-w-lg flex flex-col max-h-[85vh] animate-in fade-in zoom-in-95 duration-200"
                onClick={(e) => e.stopPropagation()}
            >
                {/* Header */}
                <div className="flex-none px-5 py-4 border-b border-gray-100 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-t-2xl">
                    <div className="flex items-start justify-between gap-4 mb-4">
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-500/30">
                                <Calendar className="w-5 h-5 text-white" />
                            </div>
                            <div>
                                <h3 className="text-lg font-bold text-gray-900">Seleccionar Período</h3>
                                <p className="text-xs text-gray-500">
                                    {filteredSemesters.length} {filteredSemesters.length === 1 ? 'resultado' : 'resultados'}
                                </p>
                            </div>
                        </div>
                        <button
                            onClick={() => setIsOpen(false)}
                            className="w-8 h-8 rounded-lg bg-white/60 hover:bg-white flex items-center justify-center transition-colors text-gray-500 hover:text-gray-700"
                        >
                            <X className="w-5 h-5" />
                        </button>
                    </div>

                    {/* Search Bar */}
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                        <input
                            ref={searchInputRef}
                            type="text"
                            placeholder="Buscar año o semestre..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="w-full pl-9 pr-4 py-2 bg-white/80 border border-blue-100 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all placeholder:text-gray-400"
                        />
                    </div>
                </div>

                {/* Semester Grid */}
                <div className="flex-1 overflow-y-auto p-4 sm:p-5">
                    {filteredSemesters.length === 0 ? (
                        <div className="text-center py-8 text-gray-500">
                            <p>No se encontraron semestres que coincidan con &quot;{searchQuery}&quot;</p>
                        </div>
                    ) : (
                        [...groupedSemesters.entries()].map(([year, semesters]) => (
                            <div key={year} className="mb-5 last:mb-0">
                                <div className="flex items-center gap-3 mb-2 px-1">
                                    <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">{year}</span>
                                    <div className="h-px bg-gray-100 flex-1" />
                                </div>
                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                                    {semesters.map((semester) => {
                                        const isSelected = semester === selectedSemester;
                                        const { period } = parseSemester(semester);
                                        return (
                                            <button
                                                key={semester}
                                                onClick={() => {
                                                    onSemesterChange(semester);
                                                    setIsOpen(false);
                                                }}
                                                className={`
                          relative p-3.5 rounded-xl text-left transition-all duration-200 group border
                          ${isSelected
                                                        ? "bg-blue-600 border-blue-600 text-white shadow-lg shadow-blue-500/25 ring-2 ring-blue-100 ring-offset-2"
                                                        : "bg-white border-gray-100 hover:border-blue-200 hover:shadow-md text-gray-700 hover:bg-blue-50/30"
                                                    }
                        `}
                                            >
                                                <div className="flex items-center justify-between mb-1">
                                                  <span className={`text-sm font-bold ${isSelected ? 'text-white' : 'text-gray-900'}`}>
                                                        Período {semester}
                                                    </span>
                                                    {isSelected && (
                                                        <div className="bg-white/20 p-1 rounded-full">
                                                            <Check className="w-3 h-3 text-white" strokeWidth={3} />
                                                        </div>
                                                    )}
                                                </div>
                                                <div className={`text-xs ${isSelected ? "text-blue-100" : "text-gray-400 group-hover:text-blue-500/70"}`}>
                                                    Semestre {period.toString().padStart(2, "0")} • {year}
                                                </div>
                                            </button>
                                        );
                                    })}
                                </div>
                            </div>
                        ))
                    )}
                </div>

                {/* Current Selection Footer */}
                <div className="flex-none px-5 py-3 border-t border-gray-100 bg-gray-50/50 rounded-b-2xl">
                    <div className="flex items-center justify-between">
                        <span className="text-xs text-gray-400 font-medium">Selección actual</span>
                        <span className="text-sm font-bold text-gray-700 bg-white px-2 py-1 rounded-md border border-gray-200 shadow-sm">
                            {formatSemesterLabel(selectedSemester)}
                        </span>
                    </div>
                </div>
            </div>
        </div>
    );

    return (
        <div className={`relative inline-block ${className}`}>
            {/* Compact trigger button */}
            <button
                ref={buttonRef}
                onClick={() => setIsOpen(!isOpen)}
                className={`
          flex items-center gap-2.5 px-4 py-2.5
          bg-white border border-gray-200 rounded-xl 
          shadow-sm hover:shadow-md hover:border-blue-300
          transition-all duration-200 ease-out
          text-sm font-medium text-gray-700
          ${isOpen ? "border-blue-400 shadow-md ring-2 ring-blue-100" : ""}
        `}
                aria-haspopup="dialog"
                aria-expanded={isOpen}
            >
                <Calendar className="w-4 h-4 text-blue-500" />
                <span className="font-semibold text-gray-900">{formatSemesterLabel(selectedSemester)}</span>
                <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform duration-200 ${isOpen ? "rotate-180" : ""}`} />
            </button>

            {/* Modal via portal */}
            {mounted && isOpen && createPortal(modalContent, document.body)}
        </div>
    );
}
