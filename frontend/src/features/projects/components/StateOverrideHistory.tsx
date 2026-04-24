"use client";

import React from "react";
import type { StateOverride } from "@features/projects/types/project";
import { PTEG_STATE_CONFIG } from "@features/projects/lib/ptegStateConfig";

interface Props {
  overrides?: StateOverride[];
}

function formatRelative(iso: string): string {
  const date = new Date(iso);
  return date.toLocaleString("es-VE", {
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function StateOverrideHistory({ overrides }: Props) {
  if (overrides === undefined) return null;

  return (
    <section className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
      <h3 className="text-sm font-semibold mb-3">
        Historial de cambios manuales (admin)
      </h3>
      {overrides.length === 0 ? (
        <p className="text-sm text-gray-500">Sin cambios manuales registrados.</p>
      ) : (
        <ul className="flex flex-col gap-3">
          {overrides.map((o) => {
            const from = PTEG_STATE_CONFIG[o.fromState];
            const to = PTEG_STATE_CONFIG[o.toState];
            return (
              <li
                key={o.id}
                className="border rounded-lg p-3 flex flex-col gap-2 text-sm"
              >
                <div className="flex items-center gap-2 flex-wrap">
                  <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${from.pillClass}`}>
                    {from.label}
                  </span>
                  <span aria-hidden>→</span>
                  <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${to.pillClass}`}>
                    {to.label}
                  </span>
                </div>
                <blockquote className="text-sm text-gray-700 pl-3 border-l-2 border-slate-200">
                  {o.reason}
                </blockquote>
                <div className="text-xs text-gray-500">
                  — {o.adminName} · {formatRelative(o.createdAt)}
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}
