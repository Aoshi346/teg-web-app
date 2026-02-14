export interface ProjectFile {
  name: string;
  url: string;
  type: "pdf" | "word";
  date: string;
}

export type ProjectStatus = "checked" | "pending" | "rejected";
export type ProjectType = "proyecto" | "tesis";

export interface Project {
  id: number;
  title: string;
  student: string; // display name
  advisor: string;
  submittedDate: string;
  reviewDate?: string;
  status: ProjectStatus;
  score?: number;
  diagramacionScore?: number;
  contenidoScore?: number;
  stage1Passed?: boolean;
  semester: string; // e.g., "2026-02"
  type?: ProjectType;
  files?: ProjectFile[];
  failedAttempts?: number;
}
