import { api } from "@shared/api/api";
import {
  PresentationDay,
  PresentationDayPatch,
  Presentation,
  PresentationCreate,
  BulkCreatePayload,
} from "../types/planificacion";

export function listDays(params?: {
  from?: string;
  to?: string;
  semester?: number;
}): Promise<PresentationDay[]> {
  const qs = new URLSearchParams();
  if (params?.from) qs.set("from", params.from);
  if (params?.to) qs.set("to", params.to);
  if (params?.semester !== undefined) qs.set("semester", String(params.semester));
  const query = qs.toString() ? `?${qs.toString()}` : "";
  return api.get<PresentationDay[]>(`/planificacion/days/${query}`);
}

export function bulkCreateDays(payload: BulkCreatePayload): Promise<PresentationDay[]> {
  return api.post<PresentationDay[]>("/planificacion/days/bulk/", payload);
}

export function updateDay(id: number, patch: Partial<PresentationDayPatch>): Promise<PresentationDay> {
  return api.patch<PresentationDay>(`/planificacion/days/${id}/`, patch);
}

export function deleteDay(id: number): Promise<void> {
  return api.delete<void>(`/planificacion/days/${id}/`);
}

export function createPresentation(dayId: number, payload: PresentationCreate): Promise<Presentation> {
  return api.post<Presentation>(`/planificacion/days/${dayId}/presentations/`, payload);
}

export function updatePresentation(id: number, patch: Partial<PresentationCreate>): Promise<Presentation> {
  return api.patch<Presentation>(`/planificacion/presentations/${id}/`, patch);
}

export function deletePresentation(id: number): Promise<void> {
  return api.delete<void>(`/planificacion/presentations/${id}/`);
}
