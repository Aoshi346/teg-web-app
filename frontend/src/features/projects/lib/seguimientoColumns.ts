export type { Role } from "./cardAction";

export type SeguimientoColumnKey =
  | "title"
  | "estudiante"
  | "tutorJurado"
  | "jurado"
  | "estado"
  | "fase"
  | "recibido"
  | "ultimaActividad"
  | "action";

import type { Role } from "./cardAction";

const COLUMNS: Record<Role, SeguimientoColumnKey[]> = {
  Administrador: ["title", "estudiante", "tutorJurado", "estado", "fase", "recibido", "action"],
  Jurado:        ["title", "estudiante", "tutorJurado", "estado", "recibido", "action"],
  Tutor:         ["title", "estudiante", "jurado", "estado", "ultimaActividad", "action"],
  Estudiante:    [],
};

export function seguimientoColumnsFor(role: Role): SeguimientoColumnKey[] {
  return COLUMNS[role];
}
