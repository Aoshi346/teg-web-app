"use client";
import React from "react";
import { Bell } from "lucide-react";

export function NotificationsTab() {
  return (
    <section
      aria-labelledby="notifications-heading"
      className="bg-surface border border-border-subtle rounded-[14px] p-8 text-center shadow-[0_1px_2px_rgba(15,23,42,0.03)]"
    >
      <div className="w-14 h-14 rounded-[14px] bg-gradient-to-br from-[rgba(0,102,255,0.08)] to-[rgba(255,107,53,0.08)] text-primary inline-flex items-center justify-center mb-3.5">
        <Bell className="w-[26px] h-[26px]" />
      </div>
      <h2 id="notifications-heading" className="text-lg font-extrabold text-text-strong tracking-tight mb-1.5">
        Notificaciones
      </h2>
      <p className="text-[13.5px] text-text-muted max-w-[48ch] mx-auto mb-4 leading-[1.55]">
        Las preferencias de notificaciones (email, recordatorios de fechas, alertas de evaluación) llegarán pronto. Por ahora, todas las notificaciones del sistema están activadas por defecto.
      </p>
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[rgba(0,102,255,0.08)] text-primary text-[11.5px] font-bold tracking-[0.04em] uppercase">
        Próximamente · Fase 2
      </span>
    </section>
  );
}
