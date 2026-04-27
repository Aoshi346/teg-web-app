export function planificacionRoleView(
  role: string,
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  _viewerId?: number
): "admin" | "reviewer" | "student" {
  if (role === "Tutor" || role === "Jurado") return "reviewer";
  if (role === "Estudiante") return "student";
  return "admin";
}
