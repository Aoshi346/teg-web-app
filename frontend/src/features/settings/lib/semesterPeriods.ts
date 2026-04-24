export const MONTH_NAMES = [
  "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
  "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
];

export function defaultMonthsForPeriod(period: "01" | "02"): { startMonth: number; endMonth: number } {
  return period === "01" ? { startMonth: 1, endMonth: 6 } : { startMonth: 9, endMonth: 1 };
}

export function previewLabel(year: number, period: "01" | "02", startMonth: number, endMonth: number): string {
  const startYear = year;
  const endYear = endMonth < startMonth ? year + 1 : year;
  return `${year}-${period} — ${MONTH_NAMES[startMonth - 1]} ${startYear} a ${MONTH_NAMES[endMonth - 1]} ${endYear}`;
}
