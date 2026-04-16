export { default as PlanificacionView } from "./components/PlanificacionView";
export { listDays, bulkCreateDays, updateDay, deleteDay, createPresentation, updatePresentation, deletePresentation } from "./api/planificacionService";
export type { PresentationDay, Presentation, PresentationCreate, BulkCreatePayload, SelectionMode } from "./types/planificacion";
