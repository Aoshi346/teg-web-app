/**
 * Formatea una fecha como texto relativo en español según la antigüedad:
 * - Menos de 60s  → "hace unos segundos"
 * - 1-59 min      → "hace X minutos"
 * - 1-23 h        → "hace X horas"
 * - 1-6 días      → "hace X días"
 * - 7 días o más  → fecha absoluta (ej: "10 abr. 2026")
 */
export function formatRelativeTime(date: Date, now: Date = new Date()): string {
  const diffMs = now.getTime() - date.getTime();
  const diffSeconds = Math.floor(diffMs / 1000);
  const diffMinutes = Math.floor(diffSeconds / 60);
  const diffHours = Math.floor(diffMinutes / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffSeconds < 60) {
    return "hace unos segundos";
  }

  if (diffMinutes < 60) {
    return `hace ${diffMinutes} minutos`;
  }

  if (diffHours < 24) {
    return `hace ${diffHours} horas`;
  }

  if (diffDays < 7) {
    return `hace ${diffDays} días`;
  }

  return date.toLocaleDateString("es-VE", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}
