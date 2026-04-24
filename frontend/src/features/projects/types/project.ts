export interface ProjectFile {
  name: string;
  url: string;
  type: "pdf" | "word";
  date: string;
}

export type ProjectStatus = "checked" | "pending" | "rejected";
export type ProjectType = "proyecto" | "tesis";

export type ProjectState =
  | "pending_review_1"
  | "pending_review_2"
  | "pending_defense"
  | "approved"
  | "failed_final";

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
  student: string; // display name
  advisorNames?: string[];
  advisors?: number[];
  reviewer?: number | null;
  reviewerName?: string | null;
  partner?: number;
  partnerName?: string;
  submittedDate: string;
  reviewDate?: string;
  status: ProjectStatus;
  state: ProjectState;
  score?: number;
  diagramacionScore?: number;
  contenidoScore?: number;
  stage1Passed?: boolean;
  period: string;
  type?: ProjectType;
  files?: ProjectFile[];
  failedAttempts?: number;
  stateOverrides?: StateOverride[];
}
