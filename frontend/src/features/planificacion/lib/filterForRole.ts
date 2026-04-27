import type { PresentationDay } from "@features/planificacion/types/planificacion";

export interface FilterOptions {
  viewerId?: number;
  viewerEmail?: string;
}

export function filterPresentationsForRole(
  days: PresentationDay[],
  role: string,
  options: FilterOptions
): PresentationDay[] {
  if (role === "Tutor") {
    if (options.viewerId === undefined) return [];
    const id = options.viewerId;
    return days
      .map((day) => ({
        ...day,
        presentations: day.presentations.filter((p) => p.tutor === id),
      }))
      .filter((day) => day.presentations.length > 0);
  }

  if (role === "Jurado") {
    if (options.viewerId === undefined) return [];
    const id = options.viewerId;
    return days
      .map((day) => ({
        ...day,
        presentations: day.presentations.filter((p) => p.jurado.includes(id)),
      }))
      .filter((day) => day.presentations.length > 0);
  }

  if (role === "Estudiante") {
    if (options.viewerEmail === undefined) return [];
    const email = options.viewerEmail;
    for (const day of days) {
      const matched = day.presentations.filter(
        (p) => p.student_email === email
      );
      if (matched.length > 0) {
        return [{ ...day, presentations: matched }];
      }
    }
    return [];
  }

  return days;
}
