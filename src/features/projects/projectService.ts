import { api } from "@/lib/api";
import { Project } from "@/lib/data/mockData";

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

export async function getAllProjects(): Promise<Project[]> {
  try {
    const response = await api.get<ApiProject[]>("/projects/");
    
    // Map API response to Frontend Project interface
    return response.map(p => ({
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
    }));
  } catch (error) {
    console.error("Failed to fetch projects", error);
    return [];
  }
}

// Create a new project (assigned to current user by backend)
export async function createProject(data: Partial<ApiProject>): Promise<ApiProject> {
  return api.post<ApiProject>("/projects/", data);
}

// Update an existing project by ID
export async function updateProject(id: number, data: Partial<ApiProject>): Promise<ApiProject> {
  return api.patch<ApiProject>(`/projects/${id}/`, data);
}

