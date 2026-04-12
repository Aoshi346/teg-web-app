import { api, postForm } from "@/lib/api";
import { Project } from "@/types/project";

// P2: Module-level cache for GET requests — expires after 30 seconds
const cache = new Map<string, { data: unknown; expiresAt: number }>();
const CACHE_TTL = 30_000;

function getCached<T>(key: string): T | null {
  const entry = cache.get(key);
  if (!entry) return null;
  if (Date.now() > entry.expiresAt) { cache.delete(key); return null; }
  return entry.data as T;
}

function setCache<T>(key: string, data: T): void {
  cache.set(key, { data, expiresAt: Date.now() + CACHE_TTL });
}

function invalidateCache(pattern?: string): void {
  if (!pattern) { cache.clear(); return; }
  for (const key of cache.keys()) { if (key.includes(pattern)) cache.delete(key); }
}

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
  advisors?: number[];
  advisor_names?: string[];
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
  const cached = getCached<Project[]>("projects_all");
  if (cached) return cached;
  try {
    const response = await api.get<ApiProject[]>("/projects/");
    const projects = response.map(mapApiProject);
    setCache("projects_all", projects);
    return projects;
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
    advisors: p.advisors,
    advisorNames: p.advisor_names,
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

export interface ApiComment {
  id: number;
  project: number;
  author: number;
  author_name: string;
  content: string;
  created_at: string;
}

export async function getComments(projectId: number): Promise<ApiComment[]> {
  try {
    return await api.get<ApiComment[]>(`/comments/?project=${projectId}`);
  } catch (error) {
    console.error(`Failed to fetch comments for project ${projectId}`, error);
    return [];
  }
}

export async function createComment(projectId: number, content: string): Promise<ApiComment> {
  return api.post<ApiComment>(`/comments/`, { project: projectId, content });
}

export async function reassignStudent(id: number, payload: { student?: number; student_email?: string }): Promise<ApiProject> {
  return api.post<ApiProject>(`/projects/${id}/reassign_student/`, payload);
}


