"use client";
import React, { useEffect, useState } from "react";
import { Bell } from "lucide-react";
import {
  getPreferences,
  updatePreferences,
  getUserRole,
  type UserPreferences,
} from "@features/auth/api/clientAuth";

type PrefKey = keyof UserPreferences;

const PREF_LABELS: Record<PrefKey, string> = {
  notify_evaluation_received: "Recibir notificación al ser evaluado",
  notify_state_change: "Notificar cambios de estado del proyecto",
  notify_assignment: "Notificar al ser asignado como jurado",
  notify_comment_added: "Notificar nuevos comentarios",
  notify_semester_changes: "Notificar cambios de semestre",
  email_enabled: "Recibir correos electrónicos",
};

// Mapeo de rol a claves de preferencia visibles (orden determina renderizado)
const ROLE_KEYS: Record<string, PrefKey[]> = {
  Administrador: [
    "notify_evaluation_received",
    "notify_state_change",
    "notify_assignment",
    "notify_comment_added",
    "notify_semester_changes",
    "email_enabled",
  ],
  Estudiante: [
    "notify_evaluation_received",
    "notify_state_change",
    "notify_comment_added",
    "email_enabled",
  ],
  Jurado: ["notify_assignment", "notify_comment_added", "email_enabled"],
  Tutor: ["notify_comment_added", "notify_state_change", "email_enabled"],
};

const DEFAULT_KEYS: PrefKey[] = [
  "notify_evaluation_received",
  "notify_state_change",
  "notify_assignment",
  "notify_comment_added",
  "notify_semester_changes",
  "email_enabled",
];

function getVisibleKeys(role: string | null): PrefKey[] {
  if (!role) return DEFAULT_KEYS;
  return ROLE_KEYS[role] ?? DEFAULT_KEYS;
}

export function NotificationsTab() {
  const [prefs, setPrefs] = useState<UserPreferences | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const role = getUserRole();
  const visibleKeys = getVisibleKeys(role);

  useEffect(() => {
    let cancelled = false;
    getPreferences().then((data) => {
      if (!cancelled) {
        setPrefs(data);
        setLoading(false);
      }
    });
    return () => { cancelled = true; };
  }, []);

  async function handleToggle(key: PrefKey) {
    if (!prefs) return;
    const oldValue = prefs[key];
    const newValue = !oldValue;

    // Actualización optimista
    setPrefs((prev) => prev ? { ...prev, [key]: newValue } : prev);
    setError(null);

    try {
      await updatePreferences({ [key]: newValue });
    } catch {
      // Revertir si falla
      setPrefs((prev) => prev ? { ...prev, [key]: oldValue } : prev);
      setError("No se pudo guardar el cambio. Intenta nuevamente.");
    }
  }

  if (loading) {
    return (
      <section
        aria-labelledby="notifications-heading"
        className="bg-surface border border-border-subtle rounded-[14px] shadow-[0_1px_2px_rgba(15,23,42,0.03)] overflow-hidden"
      >
        <div className="px-8 pt-7 pb-5 border-b border-border-subtle flex items-center gap-3">
          <div className="w-10 h-10 rounded-[10px] bg-gradient-to-br from-[rgba(0,102,255,0.08)] to-[rgba(255,107,53,0.08)] text-primary inline-flex items-center justify-center shrink-0">
            <Bell className="w-[18px] h-[18px]" />
          </div>
          <div>
            <h2
              id="notifications-heading"
              className="text-[15px] font-extrabold text-text-strong tracking-tight leading-tight"
            >
              Notificaciones
            </h2>
            <p className="text-[12.5px] text-text-muted leading-tight mt-0.5">
              Gestiona tus preferencias de notificación
            </p>
          </div>
        </div>
        <div className="px-8 py-6" role="status" aria-label="Cargando preferencias">
          <p className="text-[13.5px] text-text-muted">Cargando…</p>
        </div>
      </section>
    );
  }

  if (!prefs) return null;

  // Separar email_enabled (General) del resto (Eventos)
  const generalKeys = visibleKeys.filter((k) => k === "email_enabled");
  const eventKeys = visibleKeys.filter((k) => k !== "email_enabled");

  return (
    <section
      aria-labelledby="notifications-heading"
      className="bg-surface border border-border-subtle rounded-[14px] shadow-[0_1px_2px_rgba(15,23,42,0.03)] overflow-hidden"
    >
      <div className="px-8 pt-7 pb-5 border-b border-border-subtle flex items-center gap-3">
        <div className="w-10 h-10 rounded-[10px] bg-gradient-to-br from-[rgba(0,102,255,0.08)] to-[rgba(255,107,53,0.08)] text-primary inline-flex items-center justify-center shrink-0">
          <Bell className="w-[18px] h-[18px]" />
        </div>
        <div>
          <h2
            id="notifications-heading"
            className="text-[15px] font-extrabold text-text-strong tracking-tight leading-tight"
          >
            Notificaciones
          </h2>
          <p className="text-[12.5px] text-text-muted leading-tight mt-0.5">
            Gestiona tus preferencias de notificación
          </p>
        </div>
      </div>

      <div className="px-8 py-6 space-y-6">
        {error && (
          <p className="text-[13px] text-destructive font-medium">{error}</p>
        )}

        {generalKeys.length > 0 && (
          <div>
            <p className="text-[11.5px] font-bold text-text-muted uppercase tracking-[0.06em] mb-3">
              General
            </p>
            <div className="space-y-3">
              {generalKeys.map((key) => (
                <PrefToggleRow
                  key={key}
                  prefKey={key}
                  label={PREF_LABELS[key]}
                  checked={prefs[key]}
                  onToggle={() => handleToggle(key)}
                />
              ))}
            </div>
          </div>
        )}

        {eventKeys.length > 0 && (
          <div>
            <p className="text-[11.5px] font-bold text-text-muted uppercase tracking-[0.06em] mb-3">
              Eventos
            </p>
            <div className="space-y-3">
              {eventKeys.map((key) => (
                <PrefToggleRow
                  key={key}
                  prefKey={key}
                  label={PREF_LABELS[key]}
                  checked={prefs[key]}
                  onToggle={() => handleToggle(key)}
                />
              ))}
            </div>
          </div>
        )}
      </div>
    </section>
  );
}

function PrefToggleRow({
  prefKey,
  label,
  checked,
  onToggle,
}: {
  prefKey: PrefKey;
  label: string;
  checked: boolean;
  onToggle: () => void;
}) {
  return (
    <div className="flex items-center justify-between gap-4 py-1">
      <span className="text-[13.5px] font-medium text-text-default">{label}</span>
      <button
        role="switch"
        aria-checked={checked}
        aria-label={label}
        data-pref-key={prefKey}
        onClick={onToggle}
        className={[
          "relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent",
          "transition-colors duration-200 ease-in-out focus:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2",
          checked ? "bg-primary" : "bg-[var(--color-surface-sunken,#e8eaf0)]",
        ].join(" ")}
        type="button"
      >
        <span
          aria-hidden="true"
          className={[
            "pointer-events-none inline-block h-5 w-5 rounded-full bg-white shadow-md",
            "transform transition-transform duration-200 ease-in-out",
            checked ? "translate-x-5" : "translate-x-0",
          ].join(" ")}
        />
      </button>
    </div>
  );
}
