"use client";

import React, { useState, useEffect } from "react";
import type { PresentationDay } from "../types/planificacion";
import { formatMonthYear, toDateStr } from "../lib/formatDate";

export interface UnifiedCalendarProps {
  days: PresentationDay[];
  mode: "view" | "create";
  monthAnchor: string;             // YYYY-MM-DD anchor inside the month to render
  onMonthChange: (anchor: string) => void;
  onDayClick?: (date: string) => void;
  allowCreate?: boolean;           // controls visibility of mode toggle
  onModeChange?: (m: "view" | "create") => void;
  selectionMode?: "rango" | "individual";
  onSelectionModeChange?: (m: "rango" | "individual") => void;
  selectedDates?: Set<string>;
  onToggleDate?: (date: string) => void;
  onRangeSelect?: (startDate: string, endDate: string) => void;
  onCreate?: (dates: string[]) => void;
  onClear?: () => void;
  mineDates?: Set<string>;
  todayOverride?: string;          // for testing — defaults to today
}

const WEEKDAY_HEADERS = ["Lu", "Ma", "Mi", "Ju", "Vi", "Sá", "Do"];

/**
 * Construye la grilla 6×7 del mes que contiene `monthAnchor`.
 * La semana comienza en lunes (ISO). Las celdas fuera del mes
 * provienen del mes anterior o siguiente y llevan la clase `dim`.
 */
function buildGrid(monthAnchor: string): string[] {
  const [y, m] = monthAnchor.split("-").map(Number);
  const firstOfMonth = new Date(y, m - 1, 1);
  const lastOfMonth = new Date(y, m, 0);

  // ISO weekday: Mon=1 ... Sun=7. We need 0-based index Mon=0.
  const firstDow = firstOfMonth.getDay();
  // JS: 0=Sun, 1=Mon, ..., 6=Sat → convert to Mon=0 ... Sun=6
  const leadingDays = (firstDow === 0 ? 7 : firstDow) - 1;

  const cells: string[] = [];

  // Leading overflow days from previous month
  for (let i = leadingDays; i > 0; i--) {
    const d = new Date(y, m - 1, 1 - i);
    cells.push(toDateStr(d));
  }

  // Current month days
  for (let d = 1; d <= lastOfMonth.getDate(); d++) {
    cells.push(toDateStr(new Date(y, m - 1, d)));
  }

  // Trailing overflow to fill a 6×7 = 42-cell grid
  const trailing = 42 - cells.length;
  for (let i = 1; i <= trailing; i++) {
    cells.push(toDateStr(new Date(y, m, i)));
  }

  return cells;
}

/**
 * Retorna el primer día del mes adyacente al `monthAnchor`.
 * `direction` = 1 para avanzar, -1 para retroceder.
 */
function adjacentMonthAnchor(monthAnchor: string, direction: 1 | -1): string {
  const [y, m] = monthAnchor.split("-").map(Number);
  const next = new Date(y, m - 1 + direction, 1);
  return toDateStr(next);
}

/**
 * Formatea el rango de fechas seleccionadas para el sub-label del footer committed.
 * Ejemplo: "1-9 marzo"
 */
function formatCommittedRange(dates: Set<string>): string {
  if (dates.size === 0) return "";
  const sorted = Array.from(dates).sort();
  const first = sorted[0];
  const last = sorted[sorted.length - 1];
  const [, , d1] = first.split("-").map(Number);
  const [, m2, d2] = last.split("-").map(Number);
  const MONTHS = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"];
  return `${d1}-${d2} ${MONTHS[m2 - 1]}`;
}

/**
 * Calcula el tamaño del rango de preview (celdas entre rangeStart y hoverDate inclusive).
 */
function previewRangeSize(rangeStart: string, hoverDate: string): number {
  const start = rangeStart < hoverDate ? rangeStart : hoverDate;
  const end = rangeStart < hoverDate ? hoverDate : rangeStart;
  const s = new Date(start);
  const e = new Date(end);
  return Math.round((e.getTime() - s.getTime()) / 86400000) + 1;
}

export default function UnifiedCalendar({
  days,
  mode,
  monthAnchor,
  onMonthChange,
  onDayClick,
  allowCreate,
  onModeChange,
  selectionMode = "individual",
  onSelectionModeChange,
  selectedDates,
  onToggleDate,
  onRangeSelect,
  onCreate,
  onClear,
  mineDates,
  todayOverride,
}: UnifiedCalendarProps) {
  const todayStr = todayOverride ?? toDateStr(new Date());
  const [rangeStart, setRangeStart] = useState<string | null>(null);
  const [hoverDate, setHoverDate] = useState<string | null>(null);

  // Cuando selectedDates queda vacío, limpiamos el rangeStart pendiente.
  useEffect(() => {
    if (!selectedDates || selectedDates.size === 0) {
      setRangeStart(null);
    }
  }, [selectedDates]);

  // Build a lookup map: date → PresentationDay
  const dayMap = new Map<string, PresentationDay>();
  for (const d of days) {
    dayMap.set(d.date, d);
  }

  const [anchorYear, anchorMonth] = monthAnchor.split("-").map(Number);
  const grid = buildGrid(monthAnchor);
  const monthLabel = formatMonthYear(monthAnchor);

  /**
   * Calcula el rango de preview cuando el usuario está en modo rango,
   * ya hizo el primer click y está sobrevolando la grilla.
   */
  function getPreviewRange(): { previewStart: string; previewEnd: string } | null {
    if (
      mode !== "create" ||
      selectionMode !== "rango" ||
      rangeStart === null ||
      hoverDate === null
    ) {
      return null;
    }
    const previewStart = rangeStart < hoverDate ? rangeStart : hoverDate;
    const previewEnd = rangeStart < hoverDate ? hoverDate : rangeStart;
    return { previewStart, previewEnd };
  }

  const previewRange = getPreviewRange();

  function handleDayClick(dateStr: string) {
    if (mode === "view") {
      onDayClick?.(dateStr);
      return;
    }
    // create mode
    if (selectionMode === "individual") {
      onToggleDate?.(dateStr);
    } else {
      // rango
      if (rangeStart === null) {
        // Si ya hay una selección previa confirmada, limpiarla y empezar de nuevo.
        if (selectedDates && selectedDates.size > 0) {
          onClear?.();
        }
        setRangeStart(dateStr);
      } else {
        const start = rangeStart < dateStr ? rangeStart : dateStr;
        const end = rangeStart < dateStr ? dateStr : rangeStart;
        setRangeStart(null);
        setHoverDate(null);
        onRangeSelect?.(start, end);
      }
    }
  }

  function handleMouseEnter(dateStr: string) {
    if (mode === "create" && selectionMode === "rango" && rangeStart !== null) {
      setHoverDate(dateStr);
    }
  }

  function handleMouseLeave() {
    setHoverDate(null);
  }

  function handleClear() {
    setRangeStart(null);
    setHoverDate(null);
    onClear?.();
  }

  const selectedCount = selectedDates?.size ?? 0;
  const hasMineDates = mineDates && mineDates.size > 0;

  // ── Footer state machine ────────────────────────────────────────────────────
  // empty: nothing selected and no rangeStart
  // anchored: rangeStart set but no hover
  // preview: rangeStart set and hovering (rango mode)
  // committed: selectedDates.size > 0 and rangeStart === null
  type FootState = "empty" | "anchored" | "preview" | "committed";

  function getFootState(): FootState {
    if (selectedCount > 0 && rangeStart === null) return "committed";
    if (rangeStart !== null && hoverDate !== null) return "preview";
    if (rangeStart !== null && hoverDate === null) return "anchored";
    return "empty";
  }

  const footState = getFootState();

  const footClass =
    footState === "empty" ? "c4-foot empty"
    : footState === "committed" ? "c4-foot committed"
    : "c4-foot";

  const iconVariant =
    footState === "empty" ? "empty-state"
    : footState === "committed" ? "committed"
    : "";

  const textVariant = footState === "empty" ? "empty-state" : "";

  // Count shown in summary: preview size, anchored=1, committed=selectedCount, empty=0
  let summaryCount = 0;
  if (footState === "committed") summaryCount = selectedCount;
  else if (footState === "preview" && rangeStart !== null && hoverDate !== null) {
    summaryCount = previewRangeSize(rangeStart, hoverDate);
  } else if (footState === "anchored") summaryCount = 1;

  const topLabel =
    footState === "empty" ? "días seleccionados"
    : footState === "preview" ? "días en vista previa"
    : footState === "anchored" ? (summaryCount === 1 ? " día anclado" : " días anclados")
    : selectedCount === 1 ? " día seleccionado" : " días seleccionados";

  const subLabel =
    footState === "empty" ? "Selecciona un día para empezar"
    : footState === "preview" ? "Clic para confirmar el rango"
    : footState === "anchored" ? "Selecciona el día final"
    : selectedDates ? `${formatCommittedRange(selectedDates)} · listo para crear` : "";

  const isHintMode = footState === "preview" || footState === "anchored";

  const ctaDisabled = footState !== "committed";
  const showClear = footState !== "empty";
  // Always show the actions zone so the CTA is reachable in all states.
  // The divider only appears when there are non-CTA actions (preview/committed).
  const showActions = true;
  const showDivider = footState !== "empty";

  const ctaLabel = footState === "committed" ? "Crear" : "Crear días";
  const ctaCount = footState === "committed" ? selectedCount : null;

  return (
    <>
      {/* ── 1. Top toolbar: mode toggle (left) + month nav (right) ── */}
      <div className="cal-toolbar-top">
        {allowCreate ? (
          <div className="mode-pill" role="radiogroup">
            <button
              className={mode === "view" ? "active" : ""}
              onClick={() => onModeChange?.("view")}
            >
              Vista
            </button>
            <button
              className={mode === "create" ? "active" : ""}
              onClick={() => onModeChange?.("create")}
            >
              Crear días
            </button>
          </div>
        ) : (
          <span />
        )}

        <div className="cal-nav">
          <button
            aria-label="Anterior"
            onClick={() => onMonthChange(adjacentMonthAnchor(monthAnchor, -1))}
          >
            ‹
          </button>
          <span className="month">
            {monthLabel.charAt(0).toUpperCase() + monthLabel.slice(1)}
          </span>
          <button
            aria-label="Siguiente"
            onClick={() => onMonthChange(adjacentMonthAnchor(monthAnchor, 1))}
          >
            ›
          </button>
        </div>
      </div>

      {/* ── 2. Sub-toolbar: only when mode === "create" ── */}
      {mode === "create" && (
        <div className="subtoolbar">
          <span className="lbl">Modo</span>
          <div className="seg" role="radiogroup" aria-label="Modo de selección">
            <button
              role="radio"
              aria-checked={selectionMode === "rango"}
              className={selectionMode === "rango" ? "active" : ""}
              onClick={() => onSelectionModeChange?.("rango")}
            >
              Rango
            </button>
            <button
              role="radio"
              aria-checked={selectionMode === "individual"}
              className={selectionMode === "individual" ? "active" : ""}
              onClick={() => onSelectionModeChange?.("individual")}
            >
              Individual
            </button>
          </div>
        </div>
      )}

      {/* ── 3. Legend strip: only when mode === "view" ── */}
      {mode === "view" && (
        <div className="legend-bar">
          <span className="lbl">Leyenda</span>
          <span className="it">
            <span className="swatch sw-pteg" aria-hidden />
            <b>PTEG</b>
          </span>
          <span className="it">
            <span className="swatch sw-teg" aria-hidden />
            <b>TEG</b>
          </span>
          <span className="it">
            <span className="swatch sw-both" aria-hidden />
            Ambos
          </span>
          {hasMineDates && (
            <span className="it">
              <span className="swatch sw-mine" aria-hidden />
              Tu defensa
            </span>
          )}
        </div>
      )}

      {/* ── 4. Calendar grid ── */}
      <div className="cal-grid">
        {WEEKDAY_HEADERS.map((h) => (
          <div key={h} className="cal-dow">
            {h}
          </div>
        ))}

        {grid.map((dateStr) => {
          const [cellYear, cellMonth] = dateStr.split("-").map(Number);
          const isCurrentMonth =
            cellYear === anchorYear && cellMonth === anchorMonth;
          const presentationDay = dayMap.get(dateStr);
          const presentations = presentationDay?.presentations ?? [];

          const hasPteg = presentations.some((p) => p.project_type === "proyecto");
          const hasTeg = presentations.some((p) => p.project_type === "tesis");

          let modalityClass = "";
          if (presentations.length > 0) {
            if (hasPteg && hasTeg) {
              modalityClass = "has-both";
            } else if (hasPteg) {
              modalityClass = "has-pteg";
            } else if (hasTeg) {
              modalityClass = "has-teg";
            }
          }

          const isToday = dateStr === todayStr;
          const isMine = mineDates?.has(dateStr) ?? false;
          const isSelected = selectedDates?.has(dateStr) ?? false;
          const isRangeStart = dateStr === rangeStart;
          const isPreviewing =
            previewRange !== null &&
            !isRangeStart &&
            dateStr >= previewRange.previewStart &&
            dateStr <= previewRange.previewEnd;
          const isHoverEnd =
            previewRange !== null && dateStr === hoverDate && !isRangeStart;

          const classes = [
            "cal-day",
            !isCurrentMonth ? "dim" : "",
            isToday ? "today" : "",
            modalityClass,
            isMine ? "mine" : "",
            isSelected ? "selected" : "",
            isRangeStart ? "start" : "",
            isPreviewing ? "prev" : "",
            isHoverEnd ? "hover" : "",
          ]
            .filter(Boolean)
            .join(" ");

          return (
            <div
              key={dateStr}
              className={classes}
              data-date={dateStr}
              onClick={() => handleDayClick(dateStr)}
              onMouseEnter={() => handleMouseEnter(dateStr)}
              onMouseLeave={handleMouseLeave}
            >
              {Number(dateStr.split("-")[2])}
              {presentations.length > 0 && (
                <span className="cal-count">{presentations.length}</span>
              )}
            </div>
          );
        })}
      </div>

      {/* ── 5. Footer: only when mode === "create" ── */}
      {mode === "create" && (
        <div className={footClass}>
          <div className="c4-zones">
            <div className="c4-summary">
              <div className={`c4-icon${iconVariant ? ` ${iconVariant}` : ""}`}>
                {footState === "committed" ? (
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M20 6L9 17l-5-5" />
                  </svg>
                ) : (
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                    <rect x="3" y="4" width="18" height="18" rx="3" />
                    <path d="M16 2v4M8 2v4M3 10h18" />
                  </svg>
                )}
              </div>
              <div className={`c4-text${textVariant ? ` ${textVariant}` : ""}`}>
                <span className="top">
                  <span className="num">{summaryCount}</span>
                  {topLabel}
                </span>
                <span className={`sub${isHintMode ? " hint" : ""}`}>{subLabel}</span>
              </div>
            </div>

            {showDivider && <span className="c4-divider" aria-hidden />}

            {showActions && (
              <div className="c4-actions">
                {showClear && (
                  <button className="c4-clear" onClick={handleClear}>
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M3 6h18" />
                      <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6" />
                    </svg>
                    Limpiar
                  </button>
                )}
                <button
                  className="c4-cta"
                  disabled={ctaDisabled}
                  onClick={() => onCreate?.(Array.from(selectedDates ?? []))}
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M5 12h14M12 5v14" />
                  </svg>
                  {ctaLabel}
                  {ctaCount !== null && (
                    <span className="c4-cta-num">{ctaCount}</span>
                  )}
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </>
  );
}
