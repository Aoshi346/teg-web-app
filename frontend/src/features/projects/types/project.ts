export interface ProjectFile {
  name: string;
  url: string;
  type: "pdf" | "word";
  date: string;
}

export type ProjectType = "proyecto" | "tesis";

export type ProjectState =
  | "pending_review_1"
  | "pending_review_2"
  | "pending_defense"
  | "pending_articulo"
  | "pending_entrega"
  | "pending_defensa"
  | "approved"
  | "failed_final";

export const PTEG_STATES = [
  "pending_review_1",
  "pending_review_2",
  "pending_defense",
  "approved",
  "failed_final",
] as const satisfies readonly ProjectState[];

export const TEG_STATES = [
  "pending_articulo",
  "pending_entrega",
  "pending_defensa",
  "approved",
  "failed_final",
] as const satisfies readonly ProjectState[];

export interface Comment {
  id: number;
  project: number;
  author: number;
  authorName: string;
  content: string;
  createdAt: string;
}

export interface StateOverride {
  id: number;
  fromState: ProjectState;
  toState: ProjectState;
  reason: string;
  adminName: string;
  createdAt: string;
}

export interface Project {
  id: number;
  title: string;
  student: string;
  advisorNames?: string[];
  advisors?: number[];
  reviewer?: number | null;
  reviewerName?: string | null;
  partner?: number;
  partnerName?: string;
  submittedDate: string;
  reviewDate?: string;
  state: ProjectState;
  score?: number;
  diagramacionScore?: number;
  contenidoScore?: number;
  period: string;
  type?: ProjectType;
  files?: ProjectFile[];
  failedAttempts?: number;
  stateOverrides?: StateOverride[];
}
