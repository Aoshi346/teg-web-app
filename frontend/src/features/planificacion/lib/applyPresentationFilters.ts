import type { PresentationDay } from "../types/planificacion";

export type PeriodFilter = "all" | "today" | "week" | "month" | "semester";

export interface PresentationFilters {
  search: string;
  modality: "all" | "proyecto" | "tesis";
  period: PeriodFilter;
}

export const DEFAULT_FILTERS: PresentationFilters = {
  search: "",
  modality: "all",
  period: "all",
};

/**
 * Convierte un Date local a string YYYY-MM-DD sin desfase de zona horaria.
 */
function toDateStr(date: Date): string {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

/**
 * Calcula el string YYYY-MM-DD del último día del mes de una fecha dada.
 */
function endOfMonthStr(date: Date): string {
  const y = date.getFullYear();
  const m = date.getMonth();
  const last = new Date(y, m + 1, 0);
  return toDateStr(last);
}

/**
 * Aplica los filtros de búsqueda, modalidad y período a la lista de días.
 * Retorna solo los días que tengan al menos una presentación que cumpla todos los criterios.
 * Los días resultantes son copias shallow — el array original no se muta.
 *
 * Reglas de período:
 * - today: solo días cuya fecha coincide exactamente con la fecha de `now`.
 * - week: días desde `now` hasta `now + 7 días` (inclusive).
 * - month: días desde `now` hasta el último día del mes de `now` (inclusive).
 * - semester: sin filtrado de período (misma conducta que `all` por ahora).
 * - all: sin filtrado de período.
 */
export function applyPresentationFilters(
  days: PresentationDay[],
  filters: PresentationFilters,
  now?: Date,
): PresentationDay[] {
  const effective = now ?? new Date();
  const todayStr = toDateStr(effective);

  const weekEnd = new Date(effective.getFullYear(), effective.getMonth(), effective.getDate() + 7);
  const weekEndStr = toDateStr(weekEnd);

  const monthEndStr = endOfMonthStr(effective);

  const q = filters.search.toLowerCase();

  return days
    .map((day) => {
      // Period filter
      if (filters.period === "today" && day.date !== todayStr) return null;
      if (filters.period === "week" && (day.date < todayStr || day.date > weekEndStr)) return null;
      if (filters.period === "month" && (day.date < todayStr || day.date > monthEndStr)) return null;

      // Presentation-level filters
      const filtered = day.presentations.filter((p) => {
        const matchesSearch =
          q === "" ||
          p.project_title.toLowerCase().includes(q) ||
          p.student_name.toLowerCase().includes(q) ||
          (p.tutor_name ?? "").toLowerCase().includes(q);

        const matchesModality =
          filters.modality === "all" || p.project_type === filters.modality;

        return matchesSearch && matchesModality;
      });

      if (filtered.length === 0) return null;

      return { ...day, presentations: filtered };
    })
    .filter((d): d is PresentationDay => d !== null);
}

/**
 * Cuenta el total de presentaciones y los subtotales por modalidad (PTEG / TEG)
 * a través de todos los días. PTEG = project_type === "proyecto".
 */
export function countByModality(days: PresentationDay[]): {
  total: number;
  pteg: number;
  teg: number;
} {
  let total = 0;
  let pteg = 0;
  let teg = 0;

  for (const day of days) {
    for (const p of day.presentations) {
      total++;
      if (p.project_type === "proyecto") pteg++;
      else teg++;
    }
  }

  return { total, pteg, teg };
}

/**
 * Aplica solo el filtro de período y cuenta el total de presentaciones resultantes.
 * Usado para mostrar los conteos por opción en el popover de período.
 */
export function countForPeriod(
  days: PresentationDay[],
  period: PeriodFilter,
  now?: Date,
): number {
  const filtered = applyPresentationFilters(
    days,
    { ...DEFAULT_FILTERS, period },
    now,
  );
  return filtered.reduce((sum, d) => sum + d.presentations.length, 0);
}

/**
 * Determina si algún campo del filtro difiere de DEFAULT_FILTERS.
 */
export function isFiltersActive(filters: PresentationFilters): boolean {
  return (
    filters.search !== DEFAULT_FILTERS.search ||
    filters.modality !== DEFAULT_FILTERS.modality ||
    filters.period !== DEFAULT_FILTERS.period
  );
}
