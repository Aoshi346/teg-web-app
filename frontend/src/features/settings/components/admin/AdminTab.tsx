"use client";
import React, { useState } from "react";
import { Clock, Users, Calendar, Info } from "lucide-react";
import { cn } from "@shared/lib/utils";
import type { AdminSubTabId } from "../../types/settings";
import { SemesterListPanel } from "./semesters/SemesterListPanel";
import { UserDirectoryPanel } from "./directory/UserDirectoryPanel";
import { PendingUsersPanel } from "./pending/PendingUsersPanel";

interface SubTabDef {
  id: AdminSubTabId;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  help: string;
}

const SUB_TABS: SubTabDef[] = [
  {
    id: "pending",
    label: "Pendientes",
    icon: Clock,
    help: "Aprueba o rechaza usuarios pendientes. Los rechazados no podrán iniciar sesión hasta ser reactivados.",
  },
  {
    id: "directory",
    label: "Directorio",
    icon: Users,
    help: "Gestiona todos los usuarios. Activar/desactivar es reversible; eliminar es permanente.",
  },
  {
    id: "semesters",
    label: "Semestres",
    icon: Calendar,
    help: "Sólo un semestre puede estar activo a la vez. Cada proyecto se asigna automáticamente al semestre activo.",
  },
];

export function AdminTab() {
  const [sub, setSub] = useState<AdminSubTabId>("semesters");
  const current = SUB_TABS.find((t) => t.id === sub) ?? SUB_TABS[0];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[240px_1fr] gap-7 items-start">
      <aside className="bg-surface border border-border-subtle rounded-[14px] p-3.5 shadow-[0_1px_2px_rgba(15,23,42,0.03)] lg:sticky lg:top-[88px]">
        <div className="text-[11px] tracking-[0.08em] uppercase font-bold text-text-muted px-2.5 pt-1.5 pb-2.5">
          Administración
        </div>
        <div role="tablist" aria-label="Sub-secciones" className="flex flex-col gap-px">
          {SUB_TABS.map((t) => {
            const Icon = t.icon;
            const isActive = sub === t.id;
            return (
              <button
                key={t.id}
                role="tab"
                aria-selected={isActive}
                onClick={() => setSub(t.id)}
                className={cn(
                  "flex items-center justify-between px-2.5 py-2.5 rounded-lg text-[13.5px] font-medium text-left transition-colors",
                  isActive
                    ? "bg-[rgba(0,102,255,0.08)] text-primary font-semibold"
                    : "text-text-default hover:bg-surface-sunken hover:text-text-strong"
                )}
              >
                <span className="inline-flex items-center gap-[9px]">
                  <Icon className="w-3.5 h-3.5" />
                  {t.label === "Pendientes" ? "Pendientes" : t.label === "Directorio" ? "Directorio" : "Semestres"}
                </span>
              </button>
            );
          })}
        </div>
        <div className="mt-3.5 p-3.5 rounded-[10px] border border-border-subtle bg-gradient-to-br from-[rgba(0,102,255,0.04)] to-[rgba(255,107,53,0.04)]">
          <div className="flex items-center gap-1.5 font-bold text-[12.5px] text-text-strong mb-1">
            <span className="w-[22px] h-[22px] rounded-md bg-[rgba(0,102,255,0.1)] text-primary flex items-center justify-center">
              <Info className="w-3 h-3" />
            </span>
            ¿Cómo funciona?
          </div>
          <p className="text-xs text-text-muted leading-[1.5]">{current.help}</p>
        </div>
      </aside>

      <div role="tabpanel">
        {sub === "pending" && <PendingUsersPanel />}
        {sub === "directory" && <UserDirectoryPanel />}
        {sub === "semesters" && <SemesterListPanel />}
      </div>
    </div>
  );
}
