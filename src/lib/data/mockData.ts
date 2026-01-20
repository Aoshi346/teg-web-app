export interface AttachedFile {
  name: string;
  url: string;
  type: "pdf" | "word";
  date: string;
}

export interface Project {
  id: number;
  title: string;
  student: string;
  advisor: string;
  submittedDate: string;
  reviewDate?: string;
  status: "checked" | "pending" | "rejected";
  score?: number; // 0-20 scale
  stage1Passed?: boolean; // For Tesis flow
  semester: string; // Format: "YYYY-SS" (e.g., "2026-01", "2025-02")
  type?: "proyecto" | "tesis";
  files?: AttachedFile[];
  failedAttempts?: number;
}

// Test data with semesters from 2024-01 to 2026-02 (6 semesters)
export const mockProyectos: Project[] = [
  // 2026-01 (Current)
  {
    id: 1,
    title: "Optimización de cadena de suministro farmacéutica",
    student: "Ana Pérez",
    advisor: "Dr. Carlos Medina",
    submittedDate: "2026-01-10",
    reviewDate: "2026-01-15",
    status: "checked",
    score: 19,
    semester: "2026-01",
    files: [
      {
        name: "Propuesta_Proyecto.pdf",
        url: "#",
        type: "pdf",
        date: "2026-01-10",
      },
      {
        name: "Cronograma_Actividades.docx",
        url: "#",
        type: "word",
        date: "2026-01-10",
      },
    ],
  },
  {
    id: 2,
    title: "Plataforma web para gestión académica",
    student: "Luis Rodríguez",
    advisor: "Dra. María González",
    submittedDate: "2026-01-09",
    status: "pending",
    semester: "2026-01",
    files: [
       {
        name: "Borrador_Inicial.pdf",
        url: "#",
        type: "pdf",
        date: "2026-01-09",
      },
    ]
  },
  // 2025-02
  {
    id: 3,
    title: "Sistema de análisis de datos clínicos",
    student: "Carla Gómez",
    advisor: "Dr. Roberto Silva",
    submittedDate: "2025-09-15",
    reviewDate: "2025-09-25",
    status: "checked",
    score: 17,
    semester: "2025-02",
  },
  {
    id: 4,
    title: "Aplicación móvil para seguimiento terapéutico",
    student: "Miguel Torres",
    advisor: "Dra. Laura Ramírez",
    submittedDate: "2025-08-20",
    status: "pending",
    semester: "2025-02",
  },
  // 2025-01
  {
    id: 5,
    title: "Modelo predictivo de adherencia médica",
    student: "Sofia Martínez",
    advisor: "Dr. Pedro Álvarez",
    submittedDate: "2025-03-07",
    reviewDate: "2025-03-20",
    status: "checked",
    score: 18,
    semester: "2025-01",
  },
  {
    id: 6,
    title: "Automatización de reportes regulatorios",
    student: "Daniel Castro",
    advisor: "Dra. Isabel Fernández",
    submittedDate: "2025-02-15",
    reviewDate: "2025-03-01",
    status: "checked",
    score: 16,
    semester: "2025-01",
  },
  // 2024-02
  {
    id: 7,
    title: "Integración de sistemas hospitalarios",
    student: "María López",
    advisor: "Dr. Ernesto Díaz",
    submittedDate: "2024-10-05",
    reviewDate: "2024-10-20",
    status: "checked",
    score: 15,
    semester: "2024-02",
  },
  {
    id: 8,
    title: "Sistema de gestión de inventarios",
    student: "José Ramírez",
    advisor: "Dra. Patricia Suárez",
    submittedDate: "2024-09-15",
    reviewDate: "2024-09-28",
    status: "rejected",
    score: 8,
    semester: "2024-02",
  },
  // 2024-01
  {
    id: 9,
    title: "Análisis de costos farmacéuticos",
    student: "Elena Vargas",
    advisor: "Dr. Fernando Ruiz",
    submittedDate: "2024-04-10",
    reviewDate: "2024-04-25",
    status: "checked",
    score: 19,
    semester: "2024-01",
  },
  {
    id: 10,
    title: "Plataforma de telemedicina rural",
    student: "Ricardo Mendoza",
    advisor: "Dra. Carmen Ortiz",
    submittedDate: "2024-03-20",
    reviewDate: "2024-04-05",
    status: "checked",
    score: 17,
    semester: "2024-01",
  },
];

export const mockTesis: Project[] = [
  // 2026-01 (Current)
  {
    id: 1,
    title: "Impacto de la IA en la farmacovigilancia",
    student: "Ana Pérez",
    advisor: "Dr. Carlos Medina",
    submittedDate: "2026-01-10",
    reviewDate: "2026-01-15",
    status: "checked",
    score: 19,
    stage1Passed: true,
    semester: "2026-01",
    files: [
      {
        name: "Informe_Final_Tesis.pdf",
        url: "#",
        type: "pdf",
        date: "2026-01-10",
      }
    ]
  },
  {
    id: 2,
    title: "Desarrollo de un nuevo agente antibacteriano",
    student: "Luis Rodríguez",
    advisor: "Dra. María González",
    submittedDate: "2026-01-09",
    status: "pending",
    stage1Passed: false,
    semester: "2026-01",
  },
  // 2025-02
  {
    id: 3,
    title: "Análisis de la adherencia terapéutica en pacientes crónicos",
    student: "Carla Gómez",
    advisor: "Dr. Roberto Silva",
    submittedDate: "2025-10-09",
    reviewDate: "2025-10-25",
    status: "checked",
    score: 18,
    stage1Passed: true,
    semester: "2025-02",
  },
  {
    id: 4,
    title: "Evaluación farmacoeconómica de nuevos tratamientos oncológicos",
    student: "Miguel Torres",
    advisor: "Dra. Laura Ramírez",
    submittedDate: "2025-09-08",
    status: "pending",
    stage1Passed: true,
    semester: "2025-02",
  },
  // 2025-01
  {
    id: 5,
    title: "Optimización de formulaciones de liberación controlada",
    student: "Sofia Martínez",
    advisor: "Dr. Pedro Álvarez",
    submittedDate: "2025-04-07",
    reviewDate: "2025-04-22",
    status: "checked",
    score: 18,
    stage1Passed: true,
    semester: "2025-01",
  },
  {
    id: 6,
    title: "Estudio de interacciones medicamentosas en terapias combinadas",
    student: "Daniel Castro",
    advisor: "Dra. Isabel Fernández",
    submittedDate: "2025-03-06",
    reviewDate: "2025-03-20",
    status: "checked",
    score: 15,
    stage1Passed: true,
    semester: "2025-01",
  },
  // 2024-02
  {
    id: 7,
    title: "Ensayo de estabilidad de fármacos termolábiles",
    student: "Lucía Herrera",
    advisor: "Dr. Álvaro Rivas",
    submittedDate: "2024-11-05",
    reviewDate: "2024-11-20",
    status: "checked",
    score: 16,
    stage1Passed: true,
    semester: "2024-02",
  },
  {
    id: 8,
    title: "Metodología para validación de métodos analíticos",
    student: "Jorge Pérez",
    advisor: "Dra. Elena Duarte",
    submittedDate: "2024-08-04",
    reviewDate: "2024-08-15",
    status: "rejected",
    score: 7,
    stage1Passed: false,
    semester: "2024-02",
  },
  // 2024-01
  {
    id: 9,
    title: "Síntesis de nuevos compuestos antifúngicos",
    student: "Valentina Moreno",
    advisor: "Dr. Alejandro Vega",
    submittedDate: "2024-05-10",
    reviewDate: "2024-05-28",
    status: "checked",
    score: 20,
    stage1Passed: true,
    semester: "2024-01",
  },
  {
    id: 10,
    title: "Estudio de biodisponibilidad de genéricos",
    student: "Andrés Jiménez",
    advisor: "Dra. Rocío Campos",
    submittedDate: "2024-02-15",
    reviewDate: "2024-03-01",
    status: "checked",
    score: 17,
    stage1Passed: true,
    semester: "2024-01",
  },
];

// Storage keys for user-added documents
const ADDED_PROYECTOS_KEY = "tesisfar_added_proyectos";
const ADDED_TESIS_KEY = "tesisfar_added_tesis";
const UPDATED_PROYECTOS_KEY = "tesisfar_updated_proyectos";
const UPDATED_TESIS_KEY = "tesisfar_updated_tesis";

// Helper to get next ID for a collection
function getNextId(projects: Project[]): number {
  const maxId = projects.reduce((max, p) => Math.max(max, p.id), 0);
  return maxId + 1;
}

// Helper to load items from localStorage
function loadItems<T>(key: string): T[] {
  if (typeof window === "undefined") return [];
  try {
    const stored = localStorage.getItem(key);
    return stored ? JSON.parse(stored) : [];
  } catch {
    return [];
  }
}

// Helper to save items to localStorage
function saveItems<T>(key: string, items: T[]): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(key, JSON.stringify(items));
  } catch {}
}

/**
 * Get all proyectos, merging static, added, and updated data
 */
export function getProyectos(): Project[] {
  const added = loadItems<Project>(ADDED_PROYECTOS_KEY);
  const updated = loadItems<Project>(UPDATED_PROYECTOS_KEY);
  
  // Create a map of updated projects for O(1) lookup
  const updatedMap = new Map(updated.map(p => [p.id, p]));

  // Combine static and added
  const allInitial = [...mockProyectos, ...added];
  
  // Apply updates
  return allInitial.map(p => updatedMap.get(p.id) || p);
}

/**
 * Get all tesis, merging static, added, and updated data
 */
export function getTesis(): Project[] {
  const added = loadItems<Project>(ADDED_TESIS_KEY);
  const updated = loadItems<Project>(UPDATED_TESIS_KEY);
  
  const updatedMap = new Map(updated.map(p => [p.id, p]));
  const allInitial = [...mockTesis, ...added];
  
  return allInitial.map(p => updatedMap.get(p.id) || p);
}

/**
 * Add a new proyecto
 */
export function addProyecto(data: Omit<Project, "id">): Project {
  const added = loadItems<Project>(ADDED_PROYECTOS_KEY);
  // Calculate next ID based on ALL current projects (mock + added) to avoid collisions
  // Note: This simple ID generation might still have collision issues if mock IDs overlap with added IDs 
  // but for this demo with static mocks 1-10, it's fine as long as we check max ID.
  const currentAll = [...mockProyectos, ...added];
  
  const newProyecto: Project = {
    ...data,
    id: getNextId(currentAll),
  };
  added.push(newProyecto);
  saveItems(ADDED_PROYECTOS_KEY, added);
  return newProyecto;
}

/**
 * Update an existing proyecto
 */
export function updateProyecto(project: Project): void {
  const updated = loadItems<Project>(UPDATED_PROYECTOS_KEY);
  const index = updated.findIndex(p => p.id === project.id);
  
  if (index >= 0) {
    updated[index] = project;
  } else {
    updated.push(project);
  }
  
  saveItems(UPDATED_PROYECTOS_KEY, updated);
}

/**
 * Add a new tesis
 */
export function addTesis(data: Omit<Project, "id">): Project {
  const added = loadItems<Project>(ADDED_TESIS_KEY);
  const currentAll = [...mockTesis, ...added];
  
  const newTesis: Project = {
    ...data,
    id: getNextId(currentAll),
    stage1Passed: false, // New tesis start with stage1 not passed
  };
  added.push(newTesis);
  saveItems(ADDED_TESIS_KEY, added);
  return newTesis;
}

/**
 * Update an existing tesis
 */
export function updateTesis(project: Project): void {
  const updated = loadItems<Project>(UPDATED_TESIS_KEY);
  const index = updated.findIndex(p => p.id === project.id);
  
  if (index >= 0) {
    updated[index] = project;
  } else {
    updated.push(project);
  }
  
  saveItems(UPDATED_TESIS_KEY, updated);
}
