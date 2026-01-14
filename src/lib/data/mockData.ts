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
}

// Current semester: 2026-01, Previous semester: 2025-02
export const mockProyectos: Project[] = [
  // Current semester (2026-01)
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
  },
  {
    id: 2,
    title: "Plataforma web para gestión académica",
    student: "Luis Rodríguez",
    advisor: "Dra. María González",
    submittedDate: "2026-01-09",
    reviewDate: "2026-01-14",
    status: "checked",
    score: 17,
    semester: "2026-01",
  },
  {
    id: 3,
    title: "Sistema de análisis de datos clínicos",
    student: "Carla Gómez",
    advisor: "Dr. Roberto Silva",
    submittedDate: "2026-01-09",
    status: "pending",
    semester: "2026-01",
  },
  {
    id: 4,
    title: "Aplicación móvil para seguimiento terapéutico",
    student: "Miguel Torres",
    advisor: "Dra. Laura Ramírez",
    submittedDate: "2026-01-08",
    status: "pending",
    semester: "2026-01",
  },
  // Previous semester (2025-02)
  {
    id: 5,
    title: "Modelo predictivo de adherencia médica",
    student: "Sofia Martínez",
    advisor: "Dr. Pedro Álvarez",
    submittedDate: "2025-10-07",
    reviewDate: "2025-10-12",
    status: "checked",
    score: 18,
    semester: "2025-02",
  },
  {
    id: 6,
    title: "Automatización de reportes regulatorios",
    student: "Daniel Castro",
    advisor: "Dra. Isabel Fernández",
    submittedDate: "2025-09-06",
    reviewDate: "2025-09-15",
    status: "checked",
    score: 16,
    semester: "2025-02",
  },
  {
    id: 7,
    title: "Integración fallida con sistema externo",
    student: "María López",
    advisor: "Dr. Ernesto Díaz",
    submittedDate: "2025-08-05",
    reviewDate: "2025-08-11",
    status: "rejected",
    score: 0,
    semester: "2025-02",
  },
  {
    id: 8,
    title: "Pruebas sin documentación suficiente",
    student: "José Ramírez",
    advisor: "Dra. Patricia Suárez",
    submittedDate: "2025-07-04",
    reviewDate: "2025-07-05",
    status: "rejected",
    score: 0,
    semester: "2025-02",
  },
];

export const mockTesis: Project[] = [
  // Current semester (2026-01)
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
  },
  {
    id: 2,
    title: "Desarrollo de un nuevo agente antibacteriano",
    student: "Luis Rodríguez",
    advisor: "Dra. María González",
    submittedDate: "2026-01-09",
    reviewDate: "2026-01-14",
    status: "checked",
    score: 17,
    stage1Passed: true,
    semester: "2026-01",
  },
  {
    id: 3,
    title: "Análisis de la adherencia terapéutica en pacientes crónicos",
    student: "Carla Gómez",
    advisor: "Dr. Roberto Silva",
    submittedDate: "2026-01-09",
    status: "pending",
    stage1Passed: false,
    semester: "2026-01",
  },
  {
    id: 4,
    title: "Evaluación farmacoeconómica de nuevos tratamientos oncológicos",
    student: "Miguel Torres",
    advisor: "Dra. Laura Ramírez",
    submittedDate: "2026-01-08",
    status: "pending",
    stage1Passed: true,
    semester: "2026-01",
  },
  // Previous semester (2025-02)
  {
    id: 5,
    title: "Optimización de formulaciones de liberación controlada",
    student: "Sofia Martínez",
    advisor: "Dr. Pedro Álvarez",
    submittedDate: "2025-10-07",
    reviewDate: "2025-10-12",
    status: "checked",
    score: 18,
    stage1Passed: true,
    semester: "2025-02",
  },
  {
    id: 6,
    title: "Estudio de interacciones medicamentosas en terapias combinadas",
    student: "Daniel Castro",
    advisor: "Dra. Isabel Fernández",
    submittedDate: "2025-09-06",
    reviewDate: "2025-09-20",
    status: "checked",
    score: 15,
    stage1Passed: true,
    semester: "2025-02",
  },
  {
    id: 7,
    title: "Ensayo de estabilidad no concluyente",
    student: "Lucía Herrera",
    advisor: "Dr. Álvaro Rivas",
    submittedDate: "2025-08-05",
    reviewDate: "2025-08-11",
    status: "rejected",
    score: 0,
    stage1Passed: false,
    semester: "2025-02",
  },
  {
    id: 8,
    title: "Metodología sin validez estadística",
    student: "Jorge Pérez",
    advisor: "Dra. Elena Duarte",
    submittedDate: "2025-07-04",
    reviewDate: "2025-07-05",
    status: "rejected",
    score: 0,
    stage1Passed: false,
    semester: "2025-02",
  },
];
