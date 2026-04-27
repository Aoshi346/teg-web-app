"use client";

import React, { useState, useEffect, useRef } from "react";
import type { PresentationDay } from "../types/planificacion";
import {
  DEFAULT_FILTERS,
  countByModality,
  countForPeriod,
  isFiltersActive,
} from "../lib/applyPresentationFilters";
import type { PresentationFilters, PeriodFilter } from "../lib/applyPresentationFilters";

export interface PresentationFilterProps {
  days: PresentationDay[];
  filters: PresentationFilters;
  onChange: (next: PresentationFilters) => void;
  resultCount: number;
}

const PERIOD_LABELS: Record<PeriodFilter, string> = {
  all: "Todo el período",
  today: "Hoy",
  week: "Próxima semana",
  month: "Próximo mes",
  semester: "Este período",
};

const PERIOD_OPTIONS: Array<{ value: PeriodFilter; label: string; disabled?: boolean }> = [
  { value: "today", label: "Hoy" },
  { value: "week", label: "Próxima semana" },
  { value: "month", label: "Próximo mes" },
  { value: "semester", label: "Este período" },
];

export default function PresentationFilter({
  days,
  filters,
  onChange,
  resultCount,
}: PresentationFilterProps) {
  const [popoverOpen, setPopoverOpen] = useState(false);
  const popoverRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);

  const modCounts = countByModality(days);
  const totalCount = modCounts.total;
  const filtersActive = isFiltersActive(filters);

  // Close popover on outside click or ESC
  useEffect(() => {
    if (!popoverOpen) return;

    function handleMouseDown(e: MouseEvent) {
      if (
        popoverRef.current &&
        !popoverRef.current.contains(e.target as Node) &&
        triggerRef.current &&
        !triggerRef.current.contains(e.target as Node)
      ) {
        setPopoverOpen(false);
      }
    }

    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") setPopoverOpen(false);
    }

    document.addEventListener("mousedown", handleMouseDown);
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("mousedown", handleMouseDown);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [popoverOpen]);

  function handleSearchChange(value: string) {
    onChange({ ...filters, search: value });
  }

  function handleModalityChange(modality: PresentationFilters["modality"]) {
    onChange({ ...filters, modality });
  }

  function handlePeriodSelect(period: PeriodFilter) {
    onChange({ ...filters, period });
    setPopoverOpen(false);
  }

  function resetSearch() {
    onChange({ ...filters, search: "" });
  }

  function resetModality() {
    onChange({ ...filters, modality: DEFAULT_FILTERS.modality });
  }

  function resetPeriod() {
    onChange({ ...filters, period: DEFAULT_FILTERS.period });
  }

  return (
    <div className="pf-filter">
      {/* Zone 1 — Search */}
      <div className="pf-zone pf-zone-search">
        <span className="pf-zone-eyebrow">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
            <circle cx="11" cy="11" r="8" /><path d="m21 21-4.3-4.3" />
          </svg>
          Buscar
        </span>
        <div className="pf-search-row">
          <svg className="pf-search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
            <circle cx="11" cy="11" r="8" /><path d="m21 21-4.3-4.3" />
          </svg>
          <input
            className="pf-search-input"
            role="searchbox"
            aria-label="Buscar"
            placeholder="Proyecto, estudiante, tutor…"
            value={filters.search}
            onChange={(e) => handleSearchChange(e.target.value)}
          />
          {filters.search.length > 0 ? (
            <button
              className="pf-search-clear"
              aria-label="Limpiar búsqueda"
              onClick={resetSearch}
            >
              ×
            </button>
          ) : (
            <span className="pf-search-kbd">⌘ K</span>
          )}
        </div>
      </div>

      {/* Zone 2 — Modality */}
      <div className="pf-zone pf-zone-modality">
        <span className="pf-zone-eyebrow">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
            <rect x="3" y="3" width="7" height="7" rx="1" /><rect x="14" y="3" width="7" height="7" rx="1" />
          </svg>
          Modalidad
        </span>
        <div className="pf-modality-row">
          <button
            className={`pf-mod-chip${filters.modality === "all" ? " active" : ""}`}
            onClick={() => handleModalityChange("all")}
          >
            Todas <span className="pf-mod-count">{totalCount}</span>
          </button>
          <button
            className={`pf-mod-chip pteg${filters.modality === "proyecto" ? " active" : ""}`}
            onClick={() => handleModalityChange("proyecto")}
          >
            <span className="tdot pteg" aria-hidden />
            PTEG <span className="pf-mod-count">{modCounts.pteg}</span>
          </button>
          <button
            className={`pf-mod-chip teg${filters.modality === "tesis" ? " active" : ""}`}
            onClick={() => handleModalityChange("tesis")}
          >
            <span className="tdot teg" aria-hidden />
            TEG <span className="pf-mod-count">{modCounts.teg}</span>
          </button>
        </div>
      </div>

      {/* Zone 3 — Period */}
      <div className="pf-zone pf-zone-period" style={{ position: "relative" }}>
        <span className="pf-zone-eyebrow">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
            <rect x="3" y="4" width="18" height="18" rx="3" /><path d="M16 2v4M8 2v4M3 10h18" />
          </svg>
          Período
        </span>
        <button
          ref={triggerRef}
          className={`pf-period-trigger${popoverOpen ? " open" : ""}`}
          onClick={() => setPopoverOpen((v) => !v)}
          aria-haspopup="listbox"
          aria-expanded={popoverOpen}
        >
          <svg className="pf-cal-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
            <rect x="3" y="4" width="18" height="18" rx="3" /><path d="M16 2v4M8 2v4M3 10h18" />
          </svg>
          {PERIOD_LABELS[filters.period]}
          <svg className="pf-chev-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
            <path d="m6 9 6 6 6-6" />
          </svg>
        </button>

        {popoverOpen && (
          <div className="pf-period-popover" ref={popoverRef} role="listbox">
            {PERIOD_OPTIONS.map(({ value, label }) => {
              const count = countForPeriod(days, value);
              return (
                <div
                  key={value}
                  className={`pf-period-option${filters.period === value ? " selected" : ""}`}
                  role="option"
                  aria-selected={filters.period === value}
                  onClick={() => handlePeriodSelect(value)}
                >
                  <span>{label}</span>
                  <span className="pf-period-meta">{count}</span>
                </div>
              );
            })}
            <div
              className="pf-period-option disabled"
              role="option"
              aria-disabled="true"
              aria-selected={false}
            >
              <span>Personalizado…</span>
            </div>
          </div>
        )}
      </div>

      {/* Zone 4 — Result */}
      <div className="pf-zone pf-zone-result">
        <span className="pf-zone-eyebrow">Resultados</span>
        {filtersActive && resultCount < totalCount ? (
          <>
            <div className="pf-result-num">
              {resultCount}
              <span className="pf-result-of"> de {totalCount}</span>
            </div>
            <div className="pf-result-lbl">filtrados</div>
          </>
        ) : (
          <>
            <div className="pf-result-num">{totalCount}</div>
            <div className="pf-result-lbl">presentaciones</div>
          </>
        )}
      </div>

      {/* Active filters strip */}
      {filtersActive && (
        <div className="pf-active-filters">
          <span className="pf-af-lbl">Activos</span>

          {filters.search !== "" && (
            <span className="pf-af-chip search">
              <span className="pf-af-l">Búsqueda</span>
              &ldquo;{filters.search}&rdquo;
              <button className="pf-af-x" aria-label="Quitar búsqueda" onClick={resetSearch}>×</button>
            </span>
          )}

          {filters.modality !== "all" && (
            <span className={`pf-af-chip ${filters.modality === "proyecto" ? "pteg" : "teg"}`}>
              <span className="pf-af-l">Modalidad</span>
              {filters.modality === "proyecto" ? "PTEG" : "TEG"}
              <button className="pf-af-x" aria-label="Quitar modalidad" onClick={resetModality}>×</button>
            </span>
          )}

          {filters.period !== "all" && (
            <span className="pf-af-chip period">
              <span className="pf-af-l">Período</span>
              {PERIOD_LABELS[filters.period]}
              <button className="pf-af-x" aria-label="Quitar período" onClick={resetPeriod}>×</button>
            </span>
          )}

          <button
            className="pf-clear-all"
            onClick={() => onChange(DEFAULT_FILTERS)}
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" aria-hidden style={{ width: 11, height: 11 }}>
              <path d="M3 6h18" /><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6" />
            </svg>
            Limpiar todo
          </button>
        </div>
      )}
    </div>
  );
}
