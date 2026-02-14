import { api, postForm } from "@/lib/api";
import { Project } from "@/types/project";

export interface ApiFile {
  id: number;
  name: string;
  url: string;
  file_type: "pdf" | "word";
  date: string;
}

export interface ApiProject {
  id: number;
  title: string;
  student: number; // ID
  student_name?: string; // From serializer
  partner?: number;
  partner_name?: string;
  advisor: string;
  submitted_date: string;
  review_date?: string;
  status: "checked" | "pending" | "rejected";
  score: number;
  diagramacion_score: number;
  contenido_score: number;
  stage1_passed: boolean;
  period: string;
  project_type: "proyecto" | "tesis";
  failed_attempts: number;
  files?: ApiFile[];
}

export interface ApiEvaluation {
  id: number;
  project: number;
  reviewer?: number | null;
  reviewer_name?: string;
  ratings: Record<string, number | string>;
  comments: Record<string, unknown> | string;
  score: number;
  pass_status: "Pass" | "Fail";
  section_scores?: Record<string, number>;
  graded_at: string;
}

export async function getAllProjects(): Promise<Project[]> {
  try {
    const response = await api.get<ApiProject[]>("/projects/");
    
    // Map API response to Frontend Project interface
    return response.map(mapApiProject);
  } catch (error) {
    console.error("Failed to fetch projects", error);
    return [];
  }
}

function mapApiProject(p: ApiProject): Project {
  const normalizedType = (p.project_type || "proyecto").toLowerCase() === "tesis"
    ? "tesis"
    : "proyecto";

  return {
    id: p.id,
    title: p.title,
    student: p.student_name || `Estudiante ${p.student}`,
    partner: p.partner,
    partnerName: p.partner_name,
    advisor: p.advisor,
    submittedDate: p.submitted_date,
    reviewDate: p.review_date,
    status: p.status,
    score: p.score,
    diagramacionScore: p.diagramacion_score,
    contenidoScore: p.contenido_score,
    stage1Passed: p.stage1_passed,
    period: p.period,
    type: normalizedType,
    files: p.files?.map(f => ({
      name: f.name,
      url: f.url,
      type: f.file_type,
      date: f.date
    })) || [],
    failedAttempts: p.failed_attempts
  };
}

// Create a new project (assigned to current user by backend)
export async function createProject(data: Partial<ApiProject>): Promise<ApiProject> {
  return api.post<ApiProject>("/projects/", data);
}

// Update an existing project by ID
export async function updateProject(id: number, data: Partial<ApiProject>): Promise<ApiProject> {
  return api.patch<ApiProject>(`/projects/${id}/`, data);
}

export async function createEvaluation(data: Omit<ApiEvaluation, "id" | "graded_at">): Promise<ApiEvaluation> {
  return api.post<ApiEvaluation>(`/evaluations/`, data);
}

export async function getEvaluationsByProject(projectId: number): Promise<ApiEvaluation[]> {
  try {
    return await api.get<ApiEvaluation[]>(`/evaluations/?project=${projectId}`);
  } catch (error) {
    console.error(`Failed to fetch evaluations for project ${projectId}`, error);
    return [];
  }
}

// Retrieve a single project by ID
export async function getProject(id: number): Promise<Project | null> {
  try {
    const p = await api.get<ApiProject>(`/projects/${id}/`);
    return mapApiProject(p);
  } catch {
    console.warn(`Project ${id} not found or inaccessible`);
    return null;
  }
}

// Delete a project by ID
export async function deleteProject(id: number): Promise<void> {
  await api.delete<void>(`/projects/${id}/`);
}

// Upload a file to a project
export async function uploadProjectFile(projectId: number, file: File): Promise<ApiFile> {
  const formData = new FormData();
  formData.append("file", file);
  return postForm<ApiFile>(`/projects/${projectId}/files/`, formData);
}

// Admin-only: Reassign student for a project
export async function reassignStudent(id: number, payload: { student?: number; student_email?: string }): Promise<ApiProject> {
  return api.post<ApiProject>(`/projects/${id}/reassign_student/`, payload);
}

