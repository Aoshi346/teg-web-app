import type { ProjectState } from "@features/projects/types/project";

export const STATE_CONFIG: Record<
  ProjectState,
  { label: string; pillClass: string }
> = {
  pending_review_1: {
    label: "Pendiente 1ra revisión",
    pillClass: "text-slate-700 bg-slate-50 border border-slate-200",
  },
  pending_review_2: {
    label: "Intento 2 de 2 — Pendiente revisión",
    pillClass: "text-amber-700 bg-amber-50 border border-amber-200",
  },
  pending_defense: {
    label: "Pendiente defensa oral",
    pillClass: "text-blue-700 bg-blue-50 border border-blue-200",
  },
  pending_articulo: {
    label: "Pendiente Artículo",
    pillClass: "text-slate-700 bg-slate-50 border border-slate-200",
  },
  pending_entrega: {
    label: "Pendiente Entrega Ejemplar",
    pillClass: "text-amber-700 bg-amber-50 border border-amber-200",
  },
  pending_defensa: {
    label: "Pendiente Defensa Oral",
    pillClass: "text-blue-700 bg-blue-50 border border-blue-200",
  },
  approved: {
    label: "Aprobado",
    pillClass: "text-emerald-700 bg-emerald-50 border border-emerald-200",
  },
  failed_final: {
    label: "Reprobado (sin más intentos)",
    pillClass: "text-red-700 bg-red-50 border border-red-200",
  },
};

export const STATE_FALLBACK = {
  label: "Estado desconocido",
  pillClass: "text-gray-600 bg-gray-50 border border-gray-200",
} as const;
