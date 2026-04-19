import { useState, useCallback } from "react";
import { SelectionMode } from "../types/planificacion";
import { dateRange } from "../lib/formatDate";

interface UseDateSelectionReturn {
  mode: SelectionMode;
  setMode: (mode: SelectionMode) => void;
  /** Conjunto de fechas YYYY-MM-DD seleccionadas (both modes) */
  selected: Set<string>;
  /** En modo rango: primera fecha del rango o null */
  rangeStart: string | null;
  toggleDay: (dateStr: string) => void;
  setRangeStart: (dateStr: string) => void;
  clearAll: () => void;
}

/**
 * Gestiona la selección de fechas del calendario de Planificación.
 *
 * En modo "rango": el primer clic fija el inicio, el segundo fija el fin
 * y rellena el rango completo inclusive. Si el segundo clic es antes del
 * inicio, se intercambian los extremos.
 *
 * En modo "individual": cada clic agrega o elimina la fecha del Set.
 *
 * Este estado es efímero (UI únicamente). Las fechas confirmadas se envían
 * al backend mediante bulkCreateDays().
 */
export function useDateSelection(): UseDateSelectionReturn {
  const [mode, setModeState] = useState<SelectionMode>("rango");
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [rangeStart, setRangeStartState] = useState<string | null>(null);

  const setMode = useCallback((newMode: SelectionMode) => {
    setModeState(newMode);
    setSelected(new Set());
    setRangeStartState(null);
  }, []);

  const toggleDay = useCallback(
    (dateStr: string) => {
      if (mode === "individual") {
        setSelected((prev) => {
          const next = new Set(prev);
          if (next.has(dateStr)) {
            next.delete(dateStr);
          } else {
            next.add(dateStr);
          }
          return next;
        });
      } else {
        // Rango mode
        if (rangeStart === null) {
          // Nothing started yet — day click in calendar will call onToggleDay
          // with the first day. We just track it as rangeStart.
          setRangeStartState(dateStr);
          setSelected(new Set([dateStr]));
        } else {
          // rangeStart already set — this click completes the range
          const start = rangeStart < dateStr ? rangeStart : dateStr;
          const end = rangeStart < dateStr ? dateStr : rangeStart;
          setSelected(new Set(dateRange(start, end)));
          setRangeStartState(null);
        }
      }
    },
    [mode, rangeStart],
  );

  const setRangeStart = useCallback((dateStr: string) => {
    setRangeStartState(dateStr);
    setSelected(new Set([dateStr]));
  }, []);

  const clearAll = useCallback(() => {
    setSelected(new Set());
    setRangeStartState(null);
  }, []);

  return { mode, setMode, selected, rangeStart, toggleDay, setRangeStart, clearAll };
}
