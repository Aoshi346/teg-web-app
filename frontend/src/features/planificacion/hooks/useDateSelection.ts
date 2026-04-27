import { useState, useCallback } from "react";
import { SelectionMode } from "../types/planificacion";

interface UseDateSelectionReturn {
  mode: SelectionMode;
  setMode: (mode: SelectionMode) => void;
  /** Conjunto de fechas YYYY-MM-DD seleccionadas (both modes) */
  selected: Set<string>;
  toggleDay: (dateStr: string) => void;
  /** Reemplaza el Set completo con el arreglo de fechas dado (usado por modo rango) */
  setRange: (dates: string[]) => void;
  clearAll: () => void;
}

/**
 * Gestiona la selección de fechas del calendario de Planificación.
 *
 * La lógica de rango (primer clic / segundo clic) vive en UnifiedCalendar,
 * que es la única fuente de verdad para el estado rangeStart. Este hook
 * expone únicamente el Set de fechas confirmadas y dos operaciones:
 *   - toggleDay: agrega o elimina una fecha individual (modo individual).
 *   - setRange: reemplaza el Set con un arreglo de fechas (modo rango, llamado
 *     por PlanAdminView cuando UnifiedCalendar dispara onRangeSelect).
 *
 * Este estado es efímero (UI únicamente). Las fechas confirmadas se envían
 * al backend mediante bulkCreateDays().
 */
export function useDateSelection(): UseDateSelectionReturn {
  const [mode, setModeState] = useState<SelectionMode>("rango");
  const [selected, setSelected] = useState<Set<string>>(new Set());

  const setMode = useCallback((newMode: SelectionMode) => {
    setModeState(newMode);
    setSelected(new Set());
  }, []);

  const toggleDay = useCallback((dateStr: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(dateStr)) {
        next.delete(dateStr);
      } else {
        next.add(dateStr);
      }
      return next;
    });
  }, []);

  const setRange = useCallback((dates: string[]) => {
    setSelected(new Set(dates));
  }, []);

  const clearAll = useCallback(() => {
    setSelected(new Set());
  }, []);

  return { mode, setMode, selected, toggleDay, setRange, clearAll };
}
