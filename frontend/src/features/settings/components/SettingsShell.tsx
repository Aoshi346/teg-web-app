"use client";
import React, { useState, useMemo } from "react";
import { User, Lock, Bell, UserCog } from "lucide-react";
import { getUserRole } from "@features/auth/api/clientAuth";
import { cn } from "@shared/lib/utils";
import type { SettingsTabId } from "../types/settings";
import { SecurityTab } from "./security/SecurityTab";
import { NotificationsTab } from "./notifications/NotificationsTab";
import { ProfileTab } from "./profile/ProfileTab";
import { AdminTab } from "./admin/AdminTab";

interface TabDef {
  id: SettingsTabId;
  label: string;
  icon: React.ComponentType<{ size?: number; className?: string }>;
  count?: number;
}

export function SettingsShell() {
  const role = getUserRole();
  const [active, setActive] = useState<SettingsTabId>("profile");

  const tabs: TabDef[] = useMemo(() => {
    const base: TabDef[] = [
      { id: "profile", label: "Perfil", icon: User },
      { id: "security", label: "Seguridad", icon: Lock },
      { id: "notifications", label: "Notificaciones", icon: Bell },
    ];
    if (role === "Administrador") {
      base.push({ id: "admin", label: "Administración", icon: UserCog });
    }
    return base;
  }, [role]);

  return (
    <main className="w-full px-4 sm:px-6 lg:px-8 py-6 pb-16">
      <div className="mb-6">
        <h1 className="text-2xl sm:text-[28px] font-extrabold tracking-tight text-text-strong leading-tight mb-1.5">
          Configuración
        </h1>
        <p className="text-sm text-text-muted max-w-[70ch]">
          Administra tu perfil, gestiona usuarios pendientes y semestres académicos del programa.
        </p>
      </div>

      <div
        role="tablist"
        aria-label="Secciones de configuración"
        className="flex flex-wrap items-center gap-0.5 p-1 bg-surface border border-border-subtle rounded-[10px] shadow-[0_1px_2px_rgba(15,23,42,0.03)] mb-6 w-fit max-w-full"
      >
        {tabs.map((t) => {
          const isActive = active === t.id;
          return (
            <button
              key={t.id}
              role="tab"
              aria-selected={isActive}
              onClick={() => setActive(t.id)}
              className={cn(
                "inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-[7px] text-[13px] font-medium leading-none transition-colors border border-transparent",
                isActive
                  ? "bg-[rgba(0,102,255,0.08)] text-primary font-semibold border-[rgba(0,102,255,0.18)]"
                  : "text-text-muted hover:text-text-strong hover:bg-surface-sunken"
              )}
            >
              <t.icon className="w-3.5 h-3.5" />
              <span>{t.label}</span>
              {t.count !== undefined && (
                <span
                  className={cn(
                    "ml-0.5 text-[11px] font-semibold px-1.5 py-px rounded-full",
                    isActive
                      ? "bg-[rgba(0,102,255,0.14)] text-primary"
                      : "bg-surface-sunken text-text-default"
                  )}
                >
                  {t.count}
                </span>
              )}
            </button>
          );
        })}
      </div>

      <div role="tabpanel">
        {active === "profile" && <ProfileTab />}
        {active === "security" && <SecurityTab />}
        {active === "notifications" && <NotificationsTab />}
        {active === "admin" && <AdminTab />}
      </div>
    </main>
  );
}
