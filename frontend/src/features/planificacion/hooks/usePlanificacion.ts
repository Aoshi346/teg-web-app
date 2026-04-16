import { useState, useEffect, useCallback, useRef } from "react";
import { PresentationDay } from "../types/planificacion";

interface UsePlanificacionReturn {
  days: PresentationDay[];
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}

/**
 * Recupera los días de presentación del semestre activo y los mantiene
 * en estado local. La importación del servicio se hace de forma dinámica
 * para evitar que el módulo sea resuelto estáticamente en tiempo de compilación,
 * lo que permite que los mocks de vitest intercepten correctamente las llamadas.
 */
export function usePlanificacion(params?: {
  from?: string;
  to?: string;
  semester?: number;
}): UsePlanificacionReturn {
  const [days, setDays] = useState<PresentationDay[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const paramsRef = useRef(params);
  paramsRef.current = params;

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const { listDays } = await import("../api/planificacionService");
      const data = await listDays(paramsRef.current);
      setDays(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al cargar los días");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { days, loading, error, refresh };
}
