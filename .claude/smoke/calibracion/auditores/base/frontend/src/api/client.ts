// Cliente único de la API: base, empresa y errores en un solo sitio.
const BASE = "/api";

export interface ApiError {
  status: number;
  message: string;
}

export async function apiGet<T>(path: string, params: Record<string, string> = {}): Promise<T> {
  const company = window.localStorage.getItem("company") ?? "";
  const query = new URLSearchParams({ company, ...params }).toString();
  const res = await fetch(`${BASE}${path}?${query}`);
  if (!res.ok) {
    const err: ApiError = { status: res.status, message: await res.text() };
    throw err;
  }
  return (await res.json()) as T;
}
