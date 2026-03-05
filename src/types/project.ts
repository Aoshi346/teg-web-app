export interface ProjectFile {
  name: string;
  url: string;
  type: "pdf" | "word";
  date: string;
}

export type ProjectStatus = "checked" | "pending" | "rejected";
export type ProjectType = "proyecto" | "tesis";

export interface Comment {
  id: number;
  project: number;
  author: number;
  authorName: string;
  content: string;
  createdAt: string;
}

export interface Project {
  id: number;
  title: string;
  student: string; // display name
  advisor: string;
  advisorNames?: string[];
  advisors?: number[];
  partner?: number;
  partnerName?: string;
  submittedDate: string;
  reviewDate?: string;
  status: ProjectStatus;
  score?: number;
  diagramacionScore?: number;
  contenidoScore?: number;
  stage1Passed?: boolean;
  period: string; // Academic period e.g., "2026-02"
  type?: ProjectType;
  files?: ProjectFile[];
  failedAttempts?: number;
}

