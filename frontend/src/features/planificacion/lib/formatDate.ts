const LOCALE = "es-VE";

/**
 * Retorna el nombre del día de la semana en español para una fecha YYYY-MM-DD.
 * Usamos el offset local para evitar desfases de zona horaria.
 */
export function formatWeekday(dateStr: string): string {
  const [y, m, d] = dateStr.split("-").map(Number);
  const date = new Date(y, m - 1, d);
  return date.toLocaleDateString(LOCALE, { weekday: "long" });
}

/**
 * Retorna el mes y año en español para una fecha YYYY-MM-DD.
 */
export function formatMonthYear(dateStr: string): string {
  const [y, m, d] = dateStr.split("-").map(Number);
  const date = new Date(y, m - 1, d);
  return date.toLocaleDateString(LOCALE, { month: "long", year: "numeric" });
}

/**
 * Retorna solo el número del día (1-31) para una fecha YYYY-MM-DD.
 */
export function formatDayNumeral(dateStr: string): string {
  const [, , d] = dateStr.split("-");
  return String(Number(d));
}

/**
 * Retorna solo el nombre del mes en español para una fecha YYYY-MM-DD.
 */
export function formatMonth(dateStr: string): string {
  const [y, m, d] = dateStr.split("-").map(Number);
  const date = new Date(y, m - 1, d);
  return date.toLocaleDateString(LOCALE, { month: "long" });
}

/**
 * Retorna una abreviatura de 3 chars del mes en español para una fecha YYYY-MM-DD.
 * Ej: "Mar", "Abr", "Sep"
 */
export function formatMonthAbbr(dateStr: string): string {
  const [y, m, d] = dateStr.split("-").map(Number);
  const date = new Date(y, m - 1, d);
  const full = date.toLocaleDateString(LOCALE, { month: "short" });
  // Spanish locales include dot, e.g. "mar." — strip and capitalize
  const stripped = full.replace(".", "").trim();
  return stripped.charAt(0).toUpperCase() + stripped.slice(1);
}

/**
 * Retorna el nombre del mes y el año en español con capitalización correcta.
 */
export function formatMonthName(year: number, month: number): string {
  const date = new Date(year, month, 1);
  const str = date.toLocaleDateString(LOCALE, { month: "long", year: "numeric" });
  return str.charAt(0).toUpperCase() + str.slice(1);
}

/**
 * Retorna true si la fecha YYYY-MM-DD corresponde al día de hoy (local).
 */
export function isToday(dateStr: string): boolean {
  const today = new Date();
  const [y, m, d] = dateStr.split("-").map(Number);
  return (
    today.getFullYear() === y &&
    today.getMonth() + 1 === m &&
    today.getDate() === d
  );
}

/**
 * Retorna la fecha como string YYYY-MM-DD para un objeto Date local.
 */
export function toDateStr(date: Date): string {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

/**
 * Genera todos los string YYYY-MM-DD entre start y end (inclusive).
 */
export function dateRange(start: string, end: string): string[] {
  const result: string[] = [];
  const [sy, sm, sd] = start.split("-").map(Number);
  const [ey, em, ed] = end.split("-").map(Number);
  const current = new Date(sy, sm - 1, sd);
  const last = new Date(ey, em - 1, ed);
  while (current <= last) {
    result.push(toDateStr(current));
    current.setDate(current.getDate() + 1);
  }
  return result;
}
