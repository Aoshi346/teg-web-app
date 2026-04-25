import type { Project, ProjectState } from "@features/projects/types/project";
import { STATE_CONFIG, STATE_FALLBACK } from "@features/projects/lib/stateConfig";
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

const BUCKET_LABEL = {
  approved: "aprobados",
  pending: "en revisión",
  rejected: "rechazados",
} as const;

function bucket(p: Project): "approved" | "rejected" | "pending" {
  if (p.state === "approved") return "approved";
  if (p.state === "failed_final") return "rejected";
  return "pending";
}

const STATE_SEGMENT_LABEL: Record<ProjectState, string> = {
  pending_review_1: "Rev 1",
  pending_review_2: "Rev 2",
  pending_defense: "Defensa",
  pending_articulo: "Artículo",
  pending_entrega: "Entrega",
  pending_defensa: "Defensa",
  approved: "Aprobados",
  failed_final: "Reprobados",
};

const PTEG_STATES_FOR_CHIPS: ProjectState[] = [
  "pending_review_1",
  "pending_review_2",
  "pending_defense",
  "approved",
  "failed_final",
];

const TEG_STATES_FOR_CHIPS: ProjectState[] = [
  "pending_articulo",
  "pending_entrega",
  "pending_defensa",
  "approved",
  "failed_final",
];

function emptyCounts(): Record<ProjectState, number> {
  return {
    pending_review_1: 0,
    pending_review_2: 0,
    pending_defense: 0,
    pending_articulo: 0,
    pending_entrega: 0,
    pending_defensa: 0,
    approved: 0,
    failed_final: 0,
  };
}

function ptegStateChips(pteg: Project[]): ChipSegment[] {
  const counts = emptyCounts();
  for (const p of pteg) counts[p.state]++;
  return PTEG_STATES_FOR_CHIPS
    .filter((s) => counts[s] > 0)
    .map((s) => ({
      label: STATE_SEGMENT_LABEL[s],
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

function tegStateChips(teg: Project[]): ChipSegment[] {
  const counts = emptyCounts();
  for (const p of teg) counts[p.state]++;
  return TEG_STATES_FOR_CHIPS
    .filter((s) => counts[s] > 0)
    .map((s) => ({
      label: STATE_SEGMENT_LABEL[s],
      count: counts[s],
      href: `/dashboard/tesis?state=${s}`,
    }));
}

function tegStateSegments(teg: Project[]): BreakdownSegment[] {
  return tegStateChips(teg).map((c) => ({
    label: c.label,
    count: c.count,
    href: c.href ?? "",
  }));
}

function buildBreakdown(list: Project[]): string {
  const approved = list.filter((p) => bucket(p) === "approved").length;
  const pending = list.filter((p) => bucket(p) === "pending").length;
  const rejected = list.filter((p) => bucket(p) === "rejected").length;
  return `${approved} ${BUCKET_LABEL.approved} · ${pending} ${BUCKET_LABEL.pending} · ${rejected} ${BUCKET_LABEL.rejected}`;
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
    state: p.state,
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
        p.state === "approved" ? "reviewed" : p.state === "failed_final" ? "rejected" : "commented";
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
    teg.filter((p) => p.state !== "approved" && p.state !== "failed_final").length;

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
      chips: tegStateChips(teg),
      segments: tegStateSegments(teg),
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
    .filter((p) => bucket(p) === "pending")
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
          value: "Sin registrar",
          breakdown: `Tienes ${days} días para registrar tu ${isTesisStudent ? "tesis" : "proyecto"} en este período.`,
          href: "/dashboard/agregar",
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

  const cfg = STATE_CONFIG[mine.state] ?? STATE_FALLBACK;
  const heroValue = cfg.label;
  const heroBreakdown =
    mine.state === "approved"
      ? "Todo listo."
      : mine.state === "failed_final"
        ? "No hay más intentos disponibles."
        : "Espera el resultado de la siguiente fase.";

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
    listItems: [{ ...toListRow(mine), hint: heroBreakdown }],
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
  const attention = mine.filter((p) => bucket(p) === "pending" || bucket(p) === "rejected").length;
  const approved = mine.filter((p) => bucket(p) === "approved").length;
  const rejected = mine.filter((p) => bucket(p) === "rejected").length;
  const defensas = pendingDefenseCount(mine);

  const chips: ChipSegment[] = [];
  if (pteg.length > 0) chips.push({ label: "PTEG", count: pteg.length });
  if (teg.length > 0) chips.push({ label: "TEG", count: teg.length });
  if (approved > 0) chips.push({ label: "Aprobados", count: approved });
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
      .filter((p) => bucket(p) === "pending" || bucket(p) === "rejected")
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
  const pending = inSem.filter((p) => bucket(p) === "pending");
  const evaluated = inSem.filter((p) => bucket(p) !== "pending");
  const defensas = pendingDefenseCount(inSem);

  const counts = emptyCounts();
  for (const p of inSem.filter((x) => x.type === "proyecto")) counts[p.state]++;
  const chips: ChipSegment[] = PTEG_STATES_FOR_CHIPS
    .filter((s) => counts[s] > 0)
    .map((s) => ({ label: STATE_SEGMENT_LABEL[s], count: counts[s] }));

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
