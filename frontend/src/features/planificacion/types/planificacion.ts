export interface Presentation {
  id: number;
  day: number;
  project: number;
  project_title: string;
  project_type: "tesis" | "proyecto";
  student_name: string;
  student_email: string;
  tutor: number | null;
  tutor_name: string | null;
  jurado: number[];
  jurado_names: string[];
  start_time: string;
  duration_minutes: number;
  order: number;
}

export interface PresentationDay {
  id: number;
  date: string;
  semester?: number;
  notes: string;
  created_at?: string;
  created_by?: number | null;
  presentations: Presentation[];
}

export interface PresentationDayPatch {
  date?: string;
  semester?: number;
  notes?: string;
}

export interface PresentationCreate {
  project: number;
  start_time: string;
  jurado: number[];
  tutor?: number | null;
  duration_minutes?: number;
  order?: number;
}

export interface BulkCreatePayload {
  dates: string[];
  semester: number;
  notes?: string;
}

export type SelectionMode = "rango" | "individual";
