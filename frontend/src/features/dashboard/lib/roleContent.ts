import type { Project, ProjectState, ProjectStatus } from "@features/projects/types/project";
import type {
  BreakdownSegment,
  ChipSegment,
  DashboardContent,
  FeedItemData,
  ListRowData,
  SemesterMiniStat,
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
  assignedProjectsCount?: number;
  semesterDaysRemaining?: number;
  totalProjects?: number;
  todaysDeliveries?: number;
}

const STATUS_LABEL: Record<ProjectStatus, string> = {
  checked: "aprobados",
  pending: "en revisión",
  rejected: "rechazados",
};

const PTEG_STATE_CONFIG: Record<
  ProjectState,
  { statusLabel: string; breakdown: string; hint: string }
> = {
  pending_review_1: {
    statusLabel: "En revisión",
    breakdown: "Intento 1 de 2",
    hint: "Espera el resultado de la revisión.",
  },
  pending_review_2: {
    statusLabel: "En revisión",
    breakdown: "Intento 2 de 2",
    hint: "Corrige los comentarios y reenvía.",
  },
  pending_defense: {
    statusLabel: "Defensa pendiente",
    breakdown: "Revisión aprobada",
    hint: "Prepárate para la defensa oral.",
  },
  approved: {
    statusLabel: "Aprobado",
    breakdown: "Defensa aprobada",
    hint: "Todo listo.",
  },
  failed_final: {
    statusLabel: "Reprobado",
    breakdown: "Sin más intentos",
    hint: "No hay más intentos disponibles.",
  },
};

const PTEG_STATE_SEGMENT_LABELS: Record<ProjectState, string> = {
  pending_review_1: "Rev 1",
  pending_review_2: "Rev 2",
  pending_defense: "Defensa",
  approved: "Aprobados",
  failed_final: "Reprobados",
};

function ptegStateChips(pteg: Project[]): ChipSegment[] {
  const counts: Record<ProjectState, number> = {
    pending_review_1: 0,
    pending_review_2: 0,
    pending_defense: 0,
    approved: 0,
    failed_final: 0,
  };
  for (const p of pteg) counts[p.state]++;
  return (Object.keys(counts) as ProjectState[])
    .filter((s) => counts[s] > 0)
    .map((s) => ({
      label: PTEG_STATE_SEGMENT_LABELS[s],
      count: counts[s],
      href: `/dashboard/proyectos?state=${s}`,
    }));
}

function ptegStateSegments(pteg: Project[]): BreakdownSegment[] {
  return ptegStateChips(pteg).map((c) => ({
    label: c.label,
    count: c.count,
    href: c.href ?? "",
  }));
}

function buildBreakdown(list: Project[]): string {
  const checked = list.filter((p) => p.status === "checked").length;
  const pending = list.filter((p) => p.status === "pending").length;
  const rejected = list.filter((p) => p.status === "rejected").length;
  return `${checked} ${STATUS_LABEL.checked} · ${pending} ${STATUS_LABEL.pending} · ${rejected} ${STATUS_LABEL.rejected}`;
}

function pendingDefenseCount(list: Project[]): number {
  return list.filter((p) => p.type === "proyecto" && p.state === "pending_defense").length;
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
  return events.sort((a, b) => (a.time < b.time ? 1 : -1)).slice(0, limit);
}

function adminContent(input: BuildContentInput, now: Date): DashboardContent {
  const inSem = input.projects.filter((p) => p.period === input.semester);
  const pteg = inSem.filter((p) => p.type === "proyecto");
  const teg = inSem.filter((p) => p.type === "tesis");
  const defensas = pendingDefenseCount(inSem);
  const action =
    pteg.filter((p) => p.state !== "approved" && p.state !== "failed_final").length +
    teg.filter((p) => p.status === "pending").length;

  const stats: StatTileData[] = [
    {
      tone: "hero",
      label: "Proyectos PTEG",
      value: String(pteg.length),
      chips: ptegStateChips(pteg),
      segments: ptegStateSegments(pteg),
      href: "/dashboard/proyectos",
    },
    {
      tone: "orange",
      label: "Tesis TEG",
      value: String(teg.length),
      breakdown: buildBreakdown(teg),
      href: "/dashboard/tesis",
    },
    {
      tone: "green",
      label: "Defensas próx.",
      value: String(defensas),
      breakdown: defensas === 0 ? "Sin defensas pendientes" : "en pending_defense",
      href: "/dashboard/proyectos?state=pending_defense",
    },
    {
      tone: "amber",
      label: "Tu acción",
      value: String(action),
      breakdown: action === 0 ? "Todo al día" : "pendientes de revisión",
      urgent: action > 0,
    },
  ];

  const pending = inSem
    .filter((p) => p.status === "pending")
    .sort((a, b) => new Date(b.submittedDate).getTime() - new Date(a.submittedDate).getTime())
    .slice(0, 5)
    .map(toListRow);

  const semesterStats: SemesterMiniStat[] = [
    { num: String(input.totalProjects ?? inSem.length), label: "Proyectos" },
    { num: String(input.todaysDeliveries ?? 0), label: "Hoy" },
    { num: String(input.semesterDaysRemaining ?? 0), label: "Días rest." },
  ];

  return {
    stats,
    listTitle: "Proyectos pendientes",
    listItems: pending,
    listEmpty: { text: "¡Todo al día!", hint: "No hay proyectos pendientes de revisión." },
    feedItems: toFeedItems(inSem, now),
    semesterStats,
  };
}

function studentContent(input: BuildContentInput, now: Date): DashboardContent {
  const inSem = input.projects.filter((p) => p.period === input.semester);
  const isTesisStudent = (input.user?.semester || "").includes("10");
  const mine = isTesisStudent
    ? inSem.find((p) => p.type === "tesis")
    : inSem.find((p) => p.type === "proyecto");

  const days = input.semesterDaysRemaining ?? 0;

  if (!mine) {
    return {
      stats: [
        {
          tone: "hero",
          label: isTesisStudent ? "Mi Tesis (TEG)" : "Mi Proyecto (PTEG)",
          value: "—",
          breakdown: "Sin proyecto registrado",
        },
        { tone: "blue", label: "Entregas", value: "0", breakdown: "Sin entregas" },
        { tone: "green", label: "Notas", value: "—", breakdown: "Sin actividad" },
        { tone: "amber", label: "Días para fin", value: String(days), breakdown: input.semester },
      ],
      listTitle: "Mi proyecto",
      listItems: [],
      listEmpty: { text: "Sin proyectos registrados", hint: "Registra tu proyecto para comenzar." },
      feedItems: [],
      semesterStats: [
        { num: String(days), label: "Días rest." },
      ],
    };
  }

  const isPTEG = mine.type === "proyecto";
  const pteg = isPTEG ? PTEG_STATE_CONFIG[mine.state] : null;

  const heroValue = pteg
    ? pteg.statusLabel
    : mine.status === "checked"
      ? "Aprobado"
      : mine.status === "rejected"
        ? "Requiere correcciones"
        : "En revisión";

  const heroBreakdown = pteg
    ? pteg.breakdown
    : mine.stage1Passed
      ? "Fase 1 aprobada"
      : "Fase 1 en curso";

  const entregas = mine.files?.length ?? (mine.submittedDate ? 1 : 0);

  const stats: StatTileData[] = [
    {
      tone: "hero",
      label: isTesisStudent ? "Mi TEG · Estado actual" : "Mi PTEG · Estado actual",
      value: heroValue,
      breakdown: heroBreakdown,
      href: mine.type === "tesis" ? `/dashboard/tesis/${mine.id}` : `/dashboard/proyectos/${mine.id}`,
    },
    { tone: "blue", label: "Entregas", value: String(entregas), breakdown: entregas === 0 ? "Sin entregas" : "subidas" },
    {
      tone: "green",
      label: "Notas",
      value: mine.reviewDate ? "1" : "—",
      breakdown: mine.reviewDate ? "Última revisión" : "Sin actividad",
    },
    { tone: "amber", label: "Días para fin", value: String(days), breakdown: `período ${input.semester}` },
  ];

  return {
    stats,
    listTitle: "Mi proyecto",
    listItems: [{ ...toListRow(mine), hint: pteg?.hint ?? "" }],
    listEmpty: { text: "Sin proyectos registrados" },
    feedItems: toFeedItems([mine], now),
    semesterStats: [
      { num: String(days), label: "Días rest." },
    ],
  };
}

function tutorContent(input: BuildContentInput, now: Date): DashboardContent {
  const userId = input.user?.id;
  const mine = input.projects.filter(
    (p) =>
      p.period === input.semester &&
      Array.isArray(p.advisors) &&
      userId != null &&
      p.advisors.includes(userId),
  );
  const pteg = mine.filter((p) => p.type === "proyecto");
  const teg = mine.filter((p) => p.type === "tesis");
  const attention = mine.filter((p) => p.status === "pending" || p.status === "rejected").length;
  const approved = mine.filter((p) => p.status === "checked").length;
  const defensas = pendingDefenseCount(mine);

  const chips: ChipSegment[] = [];
  if (pteg.length > 0) chips.push({ label: "PTEG", count: pteg.length });
  if (teg.length > 0) chips.push({ label: "TEG", count: teg.length });
  if (approved > 0) chips.push({ label: "Aprobados", count: approved });
  const rejected = mine.filter((p) => p.status === "rejected").length;
  if (rejected > 0) chips.push({ label: "Rechazados", count: rejected });

  const stats: StatTileData[] = [
    {
      tone: "hero",
      label: "Mis tutorías",
      value: String(mine.length),
      chips,
      breakdown: `${pteg.length} PTEG · ${teg.length} TEG`,
    },
    {
      tone: "amber",
      label: "Atención",
      value: String(attention),
      breakdown: attention === 0 ? "Todo al día" : "pendientes/rechazados",
      urgent: attention > 0,
    },
    {
      tone: "green",
      label: "Aprobados",
      value: String(approved),
      breakdown: mine.length === 0
        ? "Sin tutorías"
        : `${Math.round((approved / mine.length) * 100)}% tasa`,
    },
    {
      tone: "blue",
      label: "Defensas próx.",
      value: String(defensas),
      breakdown: defensas === 0 ? "Sin defensas" : "esta semana",
    },
  ];

  return {
    stats,
    listTitle: "Requieren atención",
    listItems: mine
      .filter((p) => p.status === "pending" || p.status === "rejected")
      .sort((a, b) => new Date(b.submittedDate).getTime() - new Date(a.submittedDate).getTime())
      .slice(0, 5)
      .map(toListRow),
    listEmpty: { text: "Todo al día", hint: "No hay proyectos que requieran tu atención." },
    feedItems: toFeedItems(mine, now),
    semesterStats: [
      { num: String(mine.length), label: "Tutorías" },
      { num: String(attention), label: "Atender" },
      { num: String(input.semesterDaysRemaining ?? 0), label: "Días rest." },
    ],
  };
}

function juradoContent(input: BuildContentInput, now: Date): DashboardContent {
  const inSem = input.projects.filter((p) => p.period === input.semester);
  const pending = inSem.filter((p) => p.status === "pending");
  const evaluated = inSem.filter((p) => p.status !== "pending");
  const defensas = pendingDefenseCount(inSem);

  const counts: Record<ProjectState, number> = {
    pending_review_1: 0,
    pending_review_2: 0,
    pending_defense: 0,
    approved: 0,
    failed_final: 0,
  };
  for (const p of inSem.filter((x) => x.type === "proyecto")) counts[p.state]++;
  const chips: ChipSegment[] = (Object.keys(counts) as ProjectState[])
    .filter((s) => counts[s] > 0)
    .map((s) => ({ label: PTEG_STATE_SEGMENT_LABELS[s], count: counts[s] }));

  const evaluatedPct = inSem.length === 0 ? 0 : Math.round((evaluated.length / inSem.length) * 100);

  const stats: StatTileData[] = [
    {
      tone: "hero",
      label: "Proyectos asignados",
      value: String(input.assignedProjectsCount ?? inSem.length),
      chips,
      breakdown: `${evaluated.length} evaluados · ${pending.length} por evaluar`,
    },
    {
      tone: "amber",
      label: "Por evaluar",
      value: String(pending.length),
      breakdown: pending.length === 0 ? "Todo evaluado" : "tu acción",
      urgent: pending.length > 0,
    },
    {
      tone: "green",
      label: "Evaluadas",
      value: String(evaluated.length),
      breakdown: `${evaluatedPct}% avance`,
    },
    {
      tone: "blue",
      label: "Defensas próx.",
      value: String(defensas),
      breakdown: defensas === 0 ? "Sin defensas" : "esta semana",
    },
  ];

  return {
    stats,
    listTitle: "Por evaluar",
    listItems: pending
      .sort((a, b) => new Date(b.submittedDate).getTime() - new Date(a.submittedDate).getTime())
      .slice(0, 5)
      .map(toListRow),
    listEmpty: { text: "Sin pendientes", hint: "No tienes evaluaciones pendientes." },
    feedItems: toFeedItems(inSem, now),
    semesterStats: [
      { num: String(input.assignedProjectsCount ?? inSem.length), label: "Asign." },
      { num: String(pending.length), label: "Por eval." },
      { num: String(defensas), label: "Defensas" },
    ],
  };
}

export function buildDashboardContent(input: BuildContentInput): DashboardContent {
  const now = new Date();
  const role = (input.role ?? "Estudiante") as Role;

  if (role === "Estudiante") return studentContent(input, now);
  if (role === "Tutor") return tutorContent(input, now);
  if (role === "Jurado") return juradoContent(input, now);

  return adminContent(input, now);
}
