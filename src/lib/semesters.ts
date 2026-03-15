/**
 * Semester utility functions for academic period management
 * Semester format: "YYYY-SS" where SS is 01 (Jan-Jun) or 02 (Jul-Dec)
 */

import { Project } from "@/types/project";
import { api } from "@/lib/api";

export interface Semester {
    id: number;
    period: string;
    is_active: boolean;
    created_at: string;
}

/**
 * Get the current semester based on the current date
 */
export function getCurrentSemester(): string {
    const now = new Date();
    const year = now.getFullYear();
    const month = now.getMonth() + 1; // 0-indexed
    // Semester 01: January - June, Semester 02: July - December
    const period = month <= 6 ? "01" : "02";
    return `${year}-${period}`;
}

/**
 * Parse a semester string into year and period components
 */
export function parseSemester(semester: string): { year: number; period: number } {
    const [yearStr, periodStr] = semester.split("-");
    return {
        year: parseInt(yearStr, 10),
        period: parseInt(periodStr, 10)
    };
}

/**
 * Format semester for display (e.g., "2026-01" -> "Semestre 01 - 2026")
 */
export function formatSemesterLabel(semester: string): string {
    return semester;
}

/**
 * Get all unique semesters from a list of projects, sorted newest first
 */
export function getAvailableSemesters(projects: Project[], extraSemesters: string[] = []): string[] {
    const semesters = [...new Set([...projects.map((p) => p.period), ...extraSemesters])];
    return semesters.sort((a, b) => {
        const aParsed = parseSemester(a);
        const bParsed = parseSemester(b);
        // Sort descending by year, then by period
        if (bParsed.year !== aParsed.year) {
            return bParsed.year - aParsed.year;
        }
        return bParsed.period - aParsed.period;
    });
}

/**
 * Compare two semesters (returns negative if a < b, 0 if equal, positive if a > b)
 */
export function compareSemesters(a: string, b: string): number {
    const aParsed = parseSemester(a);
    const bParsed = parseSemester(b);
    if (aParsed.year !== bParsed.year) {
        return aParsed.year - bParsed.year;
    }
    return aParsed.period - bParsed.period;
}

/**
 * Get the selected semester from localStorage, or return current semester as default
 */
export function getStoredSemester(): string {
    if (typeof window === "undefined") return getCurrentSemester();
    try {
        const stored = localStorage.getItem("selectedSemester");
        return stored || getCurrentSemester();
    } catch {
        return getCurrentSemester();
    }
}

/**
 * Save the selected semester to localStorage
 */
export function setStoredSemester(semester: string): void {
    if (typeof window === "undefined") return;
    try {
        localStorage.setItem("selectedSemester", semester);
    } catch { }
}

let semestersCache: Semester[] | null = null;

export async function getSemesters(): Promise<Semester[]> {
    if (semestersCache) return semestersCache;
    try {
        const data = await api.get<Semester[]>("/semesters/");
        semestersCache = data;
        return data;
    } catch (error) {
        console.error("Failed to fetch semesters", error);
        return [];
    }
}

export async function createSemester(period: string): Promise<Semester> {
    const s = await api.post<Semester>("/semesters/", { period });
    semestersCache = null;
    return s;
}

export async function deleteSemester(id: number): Promise<void> {
    await api.delete<void>(`/semesters/${id}/`);
    semestersCache = null;
}

/**
 * Get available semester periods for document submission
 * Returns periods from 2024-01 to current semester, sorted newest first
 */
export function getAvailableSemesterPeriods(): string[] {
    const current = getCurrentSemester();
    const { year: currentYear, period: currentPeriod } = parseSemester(current);
    
    const periods: string[] = [];
    
    // Generate periods from 2024-01 to current
    for (let year = 2024; year <= currentYear; year++) {
        for (let period = 1; period <= 2; period++) {
            // Don't include future periods
            if (year === currentYear && period > currentPeriod) break;
            periods.push(`${year}-${period.toString().padStart(2, "0")}`);
        }
    }
    
    // Sort newest first
    return periods.reverse();
}

export async function fetchActiveSemester(): Promise<Semester | null> {
    try {
        return await api.get<Semester>("/semesters/current/");
    } catch (error) {
        console.error("Failed to fetch active semester", error);
        return null;
    }
}

export async function setActiveSemester(id: number): Promise<Semester> {
    const s = await api.post<Semester>(`/semesters/${id}/set_active/`, {});
    semestersCache = null;
    return s;
}
