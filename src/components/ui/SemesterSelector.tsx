"use client";

import React from "react";
import { createPortal } from "react-dom";
import { ChevronDown, Calendar, Check, Search } from "lucide-react";
import { formatSemesterLabel, parseSemester } from "@/lib/semesters";

interface SemesterSelectorProps {
    selectedSemester: string;
    availableSemesters: string[];
    onSemesterChange: (semester: string) => void;
    className?: string;
}

// Group semesters by year for better organization
function groupSemestersByYear(semesters: string[]): Map<number, string[]> {
    const groups = new Map<number, string[]>();
    for (const semester of semesters) {
        const { year } = parseSemester(semester);
        if (!groups.has(year)) {
            groups.set(year, []);
        }
        groups.get(year)!.push(semester);
    }
    // Sort years descending (newest first)
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
    const dropdownRef = React.useRef<HTMLDivElement>(null);
    const searchInputRef = React.useRef<HTMLInputElement>(null);
    const [position, setPosition] = React.useState({ top: 0, left: 0, width: 0 });

    // Ensure we're mounted on client before using portal
    React.useEffect(() => {
        setMounted(true);
    }, []);

    // Focus search input when opening
    React.useEffect(() => {
        if (isOpen && searchInputRef.current && availableSemesters.length > 5) {
            setTimeout(() => searchInputRef.current?.focus(), 100);
        }
    }, [isOpen, availableSemesters.length]);

    // Reset search when closing
    React.useEffect(() => {
        if (!isOpen) {
            setSearchQuery("");
        }
    }, [isOpen]);

    // Update position when opening or on scroll/resize
    const updatePosition = React.useCallback(() => {
        if (buttonRef.current) {
            const rect = buttonRef.current.getBoundingClientRect();
            setPosition({
                top: rect.bottom + window.scrollY + 8,
                left: rect.left + window.scrollX,
                width: Math.max(rect.width, 280),
            });
        }
    }, []);

    React.useEffect(() => {
        if (isOpen) {
            updatePosition();
            window.addEventListener("scroll", updatePosition, true);
            window.addEventListener("resize", updatePosition);
            return () => {
                window.removeEventListener("scroll", updatePosition, true);
                window.removeEventListener("resize", updatePosition);
            };
        }
    }, [isOpen, updatePosition]);

    // Close dropdown when clicking outside
    React.useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            const target = event.target as Node;
            if (
                dropdownRef.current &&
                !dropdownRef.current.contains(target) &&
                buttonRef.current &&
                !buttonRef.current.contains(target)
            ) {
                setIsOpen(false);
            }
        };
        if (isOpen) {
            document.addEventListener("mousedown", handleClickOutside);
            return () => document.removeEventListener("mousedown", handleClickOutside);
        }
    }, [isOpen]);

    // Close on escape key
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

    // Filter semesters by search query
    const filteredSemesters = searchQuery
        ? availableSemesters.filter((sem) =>
            formatSemesterLabel(sem).toLowerCase().includes(searchQuery.toLowerCase())
        )
        : availableSemesters;

    const groupedSemesters = groupSemestersByYear(filteredSemesters);
    const showSearch = availableSemesters.length > 5;
    const showYearGroups = availableSemesters.length > 4;

    const dropdownContent = (
        <div
            ref={dropdownRef}
            className="bg-white border border-gray-200 rounded-xl shadow-2xl overflow-hidden"
            style={{
                position: "absolute",
                top: position.top,
                left: position.left,
                width: position.width,
                zIndex: 99999,
            }}
        >
            {/* Header */}
            <div className="px-4 py-3 border-b border-gray-100 bg-gradient-to-r from-gray-50 to-white">
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
                    Seleccionar Semestre
                </p>
                <p className="text-[10px] text-gray-400 mt-0.5">
                    {availableSemesters.length} semestre{availableSemesters.length !== 1 ? "s" : ""} disponible{availableSemesters.length !== 1 ? "s" : ""}
                </p>
            </div>

            {/* Search - only show if more than 5 semesters */}
            {showSearch && (
                <div className="px-3 py-2 border-b border-gray-100">
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                        <input
                            ref={searchInputRef}
                            type="text"
                            placeholder="Buscar semestre..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="w-full pl-9 pr-3 py-2 text-sm border border-gray-200 rounded-lg focus:border-blue-400 focus:ring-2 focus:ring-blue-100 transition-all"
                        />
                    </div>
                </div>
            )}

            {/* Scrollable semester list */}
            <div
                className="overflow-y-auto overscroll-contain"
                style={{ maxHeight: "320px" }}
            >
                {filteredSemesters.length === 0 ? (
                    <div className="px-4 py-6 text-center text-gray-400 text-sm">
                        No se encontraron semestres
                    </div>
                ) : showYearGroups ? (
                    // Grouped by year
                    [...groupedSemesters.entries()].map(([year, semesters]) => (
                        <div key={year}>
                            <div className="px-4 py-2 bg-gray-50 border-b border-gray-100 sticky top-0">
                                <span className="text-xs font-bold text-gray-500">{year}</span>
                            </div>
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
                      w-full text-left px-4 py-3 text-sm transition-all duration-150
                      flex items-center justify-between gap-3
                      ${isSelected
                                                ? "bg-gradient-to-r from-blue-50 to-indigo-50 text-blue-700 font-semibold"
                                                : "text-gray-700 hover:bg-gray-50"
                                            }
                    `}
                                        role="option"
                                        aria-selected={isSelected}
                                    >
                                        <div className="flex items-center gap-3">
                                            <div className={`w-2 h-2 rounded-full ${isSelected ? "bg-blue-500" : "bg-gray-300"}`} />
                                            <span>Semestre {period.toString().padStart(2, "0")}</span>
                                            <span className="text-xs text-gray-400">
                                                ({period === 1 ? "Ene-Jun" : "Jul-Dic"})
                                            </span>
                                        </div>
                                        {isSelected && (
                                            <div className="w-5 h-5 bg-blue-500 rounded-full flex items-center justify-center">
                                                <Check className="w-3 h-3 text-white" strokeWidth={3} />
                                            </div>
                                        )}
                                    </button>
                                );
                            })}
                        </div>
                    ))
                ) : (
                    // Simple list (few semesters)
                    filteredSemesters.map((semester) => {
                        const isSelected = semester === selectedSemester;
                        return (
                            <button
                                key={semester}
                                onClick={() => {
                                    onSemesterChange(semester);
                                    setIsOpen(false);
                                }}
                                className={`
                  w-full text-left px-4 py-3 text-sm transition-all duration-150
                  flex items-center justify-between gap-3
                  ${isSelected
                                        ? "bg-gradient-to-r from-blue-50 to-indigo-50 text-blue-700 font-semibold"
                                        : "text-gray-700 hover:bg-gray-50"
                                    }
                `}
                                role="option"
                                aria-selected={isSelected}
                            >
                                <div className="flex items-center gap-3">
                                    <div className={`w-2 h-2 rounded-full ${isSelected ? "bg-blue-500" : "bg-gray-300"}`} />
                                    <span>{formatSemesterLabel(semester)}</span>
                                </div>
                                {isSelected && (
                                    <div className="w-5 h-5 bg-blue-500 rounded-full flex items-center justify-center">
                                        <Check className="w-3 h-3 text-white" strokeWidth={3} />
                                    </div>
                                )}
                            </button>
                        );
                    })
                )}
            </div>

            {/* Footer with quick info */}
            {availableSemesters.length > 3 && (
                <div className="px-4 py-2 border-t border-gray-100 bg-gray-50">
                    <p className="text-[10px] text-gray-400 text-center">
                        Usa ↑↓ para navegar • Enter para seleccionar • Esc para cerrar
                    </p>
                </div>
            )}
        </div>
    );

    return (
        <div className={`relative inline-block ${className}`}>
            <button
                ref={buttonRef}
                onClick={() => setIsOpen(!isOpen)}
                className={`
          flex items-center gap-3 px-5 py-3 
          bg-gradient-to-br from-white to-gray-50 
          border-2 border-gray-200 rounded-xl 
          shadow-sm hover:shadow-md hover:border-blue-300 hover:from-blue-50 hover:to-white
          transition-all duration-200 ease-out
          text-sm font-semibold text-gray-800
          ${isOpen ? "border-blue-400 shadow-md ring-2 ring-blue-100" : ""}
        `}
                aria-haspopup="listbox"
                aria-expanded={isOpen}
            >
                <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center shadow-inner">
                    <Calendar className="w-4 h-4 text-white" />
                </div>
                <div className="flex flex-col items-start">
                    <span className="text-[10px] uppercase tracking-wider text-gray-400 font-medium">Período</span>
                    <span className="text-gray-900">{formatSemesterLabel(selectedSemester)}</span>
                </div>
                <ChevronDown className={`w-5 h-5 text-gray-400 transition-transform duration-200 ${isOpen ? "rotate-180 text-blue-500" : ""}`} />
            </button>

            {/* Render dropdown via portal to body to escape all stacking contexts */}
            {mounted && isOpen && createPortal(dropdownContent, document.body)}
        </div>
    );
}
