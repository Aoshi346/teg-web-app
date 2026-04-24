"use client";
import React, { useState } from "react";
import type { AdminSubTabId } from "../../types/settings";
import { SemesterListPanel } from "./semesters/SemesterListPanel";

export function AdminTab() {
  const [sub, setSub] = useState<AdminSubTabId>("semesters");

  return (
    <div className="flex flex-col gap-4">
      <div role="tablist" aria-label="Sub-secciones" className="flex gap-2 border-b border-gray-200">
        {(["pending", "directory", "semesters"] as AdminSubTabId[]).map((id) => (
          <button
            key={id}
            role="tab"
            aria-selected={sub === id}
            onClick={() => setSub(id)}
            className={`px-4 py-2 text-sm font-medium ${sub === id ? "text-blue-600 border-b-2 border-blue-600" : "text-gray-600"}`}
          >
            {id === "pending" ? "Pendientes" : id === "directory" ? "Directorio" : "Semestres"}
          </button>
        ))}
      </div>
      <div role="tabpanel">
        {sub === "pending" && <div data-testid="pending-placeholder" className="p-6 bg-white rounded-lg border border-gray-200 text-gray-500 text-sm">Pendientes (placeholder — Task 7)</div>}
        {sub === "directory" && <div data-testid="directory-placeholder" className="p-6 bg-white rounded-lg border border-gray-200 text-gray-500 text-sm">Directorio (placeholder — Task 6)</div>}
        {sub === "semesters" && <SemesterListPanel />}
      </div>
    </div>
  );
}
