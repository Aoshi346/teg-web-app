"use client";

import * as React from "react";

export type DetailTabKey =
  | "informacion"
  | "evaluaciones"
  | "comentarios"
  | "archivos"
  | "historial";

const TAB_LABEL: Record<DetailTabKey, string> = {
  informacion:  "Información",
  evaluaciones: "Evaluaciones",
  comentarios:  "Comentarios",
  archivos:     "Archivos",
  historial:    "Historial",
};

export const DETAIL_TAB_KEYS: DetailTabKey[] = [
  "informacion", "evaluaciones", "comentarios", "archivos", "historial",
];

export interface DetailTabsProps {
  active: DetailTabKey;
  counts: Partial<Record<DetailTabKey, number>>;
  onChange: (next: DetailTabKey) => void;
}

export function DetailTabs({ active, counts, onChange }: DetailTabsProps) {
  return (
    <div role="tablist" className="detail-tab-strip flex items-center gap-2 border-b border-border-subtle">
      {DETAIL_TAB_KEYS.map((key) => (
        <button
          key={key}
          role="tab"
          type="button"
          data-tab={key}
          data-active={active === key}
          aria-selected={active === key}
          onClick={() => onChange(key)}
          className="tab"
        >
          {TAB_LABEL[key]}
          {counts[key] != null && counts[key]! > 0 && (
            <span className="text-[10px] font-bold text-text-muted ml-0.5">{counts[key]}</span>
          )}
        </button>
      ))}
    </div>
  );
}

export function parseTabKey(value: string | null | undefined): DetailTabKey {
  if (value && (DETAIL_TAB_KEYS as string[]).includes(value)) return value as DetailTabKey;
  return "informacion";
}
