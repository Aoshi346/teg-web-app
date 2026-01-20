import { api } from "@/lib/api";
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
  advisor: string;
  submitted_date: string;
  review_date?: string;
  status: "checked" | "pending" | "rejected";
  score: number;
  diagramacion_score: number;
  contenido_score: number;
  stage1_passed: boolean;
  semester: string;
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
  return {
    id: p.id,
    title: p.title,
    student: p.student_name || `Estudiante ${p.student}`,
    advisor: p.advisor,
    submittedDate: p.submitted_date,
    reviewDate: p.review_date,
    status: p.status,
    score: p.score,
    diagramacionScore: p.diagramacion_score,
    contenidoScore: p.contenido_score,
    stage1Passed: p.stage1_passed,
    semester: p.semester,
    type: p.project_type,
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
  } catch (error) {
    console.error(`Failed to fetch project ${id}`, error);
    return null;
  }
}

// Delete a project by ID
export async function deleteProject(id: number): Promise<void> {
  await api.delete<void>(`/projects/${id}/`);
}

// Admin-only: Reassign student for a project
export async function reassignStudent(id: number, payload: { student?: number; student_email?: string }): Promise<ApiProject> {
  return api.post<ApiProject>(`/projects/${id}/reassign_student/`, payload);
}

