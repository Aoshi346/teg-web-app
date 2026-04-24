"use client";
import React, { useState, useMemo } from "react";
import { User, Lock, Bell, UserCog } from "lucide-react";
import { getUserRole } from "@features/auth/api/clientAuth";
import type { SettingsTabId } from "../types/settings";
import { SecurityTab } from "./security/SecurityTab";
import { NotificationsTab } from "./notifications/NotificationsTab";
import { ProfileTab } from "./profile/ProfileTab";
import { AdminTab } from "./admin/AdminTab";

interface TabDef {
  id: SettingsTabId;
  label: string;
  icon: React.ComponentType<{ size?: number }>;
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
    <div className="grid grid-cols-1 lg:grid-cols-[240px_1fr] gap-6">
      <nav role="tablist" aria-label="Secciones de configuración" className="flex flex-col gap-1">
        {tabs.map((t) => (
          <button
            key={t.id}
            role="tab"
            aria-selected={active === t.id}
            onClick={() => setActive(t.id)}
            className={`flex items-center gap-2 px-3 py-2 rounded-md text-left text-sm ${
              active === t.id ? "bg-blue-50 text-blue-700 font-semibold" : "text-gray-700 hover:bg-gray-50"
            }`}
          >
            <t.icon size={16} />
            {t.label}
          </button>
        ))}
      </nav>
      <main role="tabpanel">
        {active === "profile" && <ProfileTab />}
        {active === "security" && <SecurityTab />}
        {active === "notifications" && <NotificationsTab />}
        {active === "admin" && <AdminTab />}
      </main>
    </div>
  );
}
