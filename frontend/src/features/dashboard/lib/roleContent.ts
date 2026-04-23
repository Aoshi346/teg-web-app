import type { Project, ProjectStatus } from "@features/projects/types/project";
import type {
  DashboardContent,
  FeedItemData,
  ListRowData,
  StatTileData,
} from "./types";

type Role = "Administrador" | "Estudiante" | "Jurado" | "Tutor";

export interface BuildContentInput {
  role: Role | string | null | undefined;
  user: { role?: string; id?: number; semester?: string } | null;
  semester: string;
  projects: Project[];
  evaluations?: { id: number; projectId: number; reviewerId?: number; period?: string }[];
  presentations?: { id: number; projectTitle: string; date: string; jurorIds: number[] }[];
}

const STATUS_LABEL: Record<ProjectStatus, string> = {
  checked: "aprobados",
  pending: "en revisión",
  rejected: "rechazados",
};

function buildBreakdown(list: Project[]): string {
  const checked = list.filter((p) => p.status === "checked").length;
  const pending = list.filter((p) => p.status === "pending").length;
  const rejected = list.filter((p) => p.status === "rejected").length;
  return `${checked} ${STATUS_LABEL.checked} · ${pending} ${STATUS_LABEL.pending} · ${rejected} ${STATUS_LABEL.rejected}`;
}

function relTime(date: string, now: Date): string {
  const diffDays = Math.floor((now.getTime() - new Date(date).getTime()) / 86_400_000);
  if (diffDays <= 0) return "Hoy";
  if (diffDays === 1) return "Ayer";
  if (diffDays < 7) return `${diffDays}d`;
  const weeks = Math.floor(diffDays / 7);
  return `${weeks}sem`;
}

function toListRow(p: Project): ListRowData {
  return {
    id: p.id,
    title: p.title,
    subtitle: `${p.student} · ${p.submittedDate}`,
    type: p.type,
    status: p.status,
    href: p.type === "tesis" ? `/dashboard/tesis/${p.id}` : `/dashboard/proyectos/${p.id}`,
  };
}

function toFeedItems(projects: Project[], now: Date, limit = 6): FeedItemData[] {
  const events: FeedItemData[] = [];
  for (const p of projects) {
    if (p.submittedDate) {
      events.push({
        id: `s-${p.id}`,
        kind: "submitted",
        text: `Nueva entrega de ${p.student}`,
        time: relTime(p.submittedDate, now),
      });
    }
    if (p.reviewDate) {
      const kind: FeedItemData["kind"] =
        p.status === "checked" ? "reviewed" : p.status === "rejected" ? "rejected" : "commented";
      const text =
        kind === "reviewed"
          ? `Proyecto de ${p.student} aprobado`
          : kind === "rejected"
            ? `Correcciones para ${p.student}`
            : `Revisión en proyecto de ${p.student}`;
      events.push({ id: `r-${p.id}`, kind, text, time: relTime(p.reviewDate, now) });
    }
  }
  return events
    .sort((a, b) => (a.time < b.time ? 1 : -1))
    .slice(0, limit);
}

function adminContent(projects: Project[], semester: string, now: Date): DashboardContent {
  const inSem = projects.filter((p) => p.period === semester);
  const pteg = inSem.filter((p) => p.type === "proyecto");
  const teg = inSem.filter((p) => p.type === "tesis");

  const stats: StatTileData[] = [
    {
      tone: "primary",
      label: "Proyectos (PTEG)",
      value: String(pteg.length),
      breakdown: buildBreakdown(pteg),
      href: "/dashboard/proyectos",
    },
    {
      tone: "accent",
      label: "Tesis (TEG)",
      value: String(teg.length),
      breakdown: buildBreakdown(teg),
      href: "/dashboard/tesis",
    },
  ];

  const pending = inSem
    .filter((p) => p.status === "pending")
    .sort((a, b) => new Date(b.submittedDate).getTime() - new Date(a.submittedDate).getTime())
    .slice(0, 5)
    .map(toListRow);

  return {
    stats,
    listTitle: "Proyectos pendientes",
    listItems: pending,
    listEmpty: { text: "¡Todo al día!", hint: "No hay proyectos pendientes de revisión." },
    feedItems: toFeedItems(inSem, now),
  };
}

function studentContent(
  projects: Project[],
  user: BuildContentInput["user"],
  semester: string,
  now: Date
): DashboardContent {
  const inSem = projects.filter((p) => p.period === semester);
  const isTesisStudent = (user?.semester || "").includes("10");
  const mine = isTesisStudent
    ? inSem.find((p) => p.type === "tesis")
    : inSem.find((p) => p.type === "proyecto");

  if (!mine) {
    return {
      stats: [
        {
          tone: isTesisStudent ? "accent" : "primary",
          label: isTesisStudent ? "Mi Tesis (TEG)" : "Mi Proyecto (PTEG)",
          value: "—",
          breakdown: "Sin proyecto registrado",
        },
      ],
      listTitle: "Mi proyecto",
      listItems: [],
      listEmpty: { text: "Sin proyectos registrados", hint: "Registra tu proyecto para comenzar." },
      feedItems: [],
    };
  }

  const statusLabel =
    mine.status === "checked"
      ? "Aprobado"
      : mine.status === "rejected"
        ? "Requiere correcciones"
        : "En revisión";

  const breakdown =
    mine.type === "tesis"
      ? mine.stage1Passed
        ? "Fase 1 aprobada · pendiente defensa"
        : "Fase 1 en curso"
      : `Intento ${Math.min((mine.failedAttempts ?? 0) + 1, 2)} de 2`;

  const hint =
    mine.status === "pending"
      ? "Espera el resultado de la revisión."
      : mine.status === "rejected"
        ? "Revisa los comentarios y reenvía."
        : mine.type === "tesis" && !mine.stage1Passed
          ? "Prepárate para la defensa oral."
          : "Todo listo.";

  return {
    stats: [
      {
        tone: isTesisStudent ? "accent" : "primary",
        label: isTesisStudent ? "Mi Tesis (TEG)" : "Mi Proyecto (PTEG)",
        value: statusLabel,
        breakdown,
        href: mine.type === "tesis" ? `/dashboard/tesis/${mine.id}` : `/dashboard/proyectos/${mine.id}`,
      },
    ],
    listTitle: "Mi proyecto",
    listItems: [{ ...toListRow(mine), hint }],
    listEmpty: { text: "Sin proyectos registrados" },
    feedItems: toFeedItems([mine], now),
  };
}

export function buildDashboardContent(input: BuildContentInput): DashboardContent {
  const now = new Date();
  const role = (input.role ?? "Estudiante") as Role;

  if (role === "Estudiante") return studentContent(input.projects, input.user, input.semester, now);

  // Administrador, Tutor, Jurado — for this task all three fall back to admin-shape.
  // Tutor/Jurado get tailored branches in a later task.
  return adminContent(input.projects, input.semester, now);
}
