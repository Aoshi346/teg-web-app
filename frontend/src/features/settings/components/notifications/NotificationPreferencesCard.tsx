"use client";
import React from "react";
import { SlidersHorizontal, Mail, Info, type LucideIcon } from "lucide-react";
import { getKindMeta } from "@features/notifications/lib/kindMeta";
import type { UserPreferences } from "@features/auth/api/clientAuth";

type PrefKey = keyof UserPreferences;

const PREF_LABELS: Record<PrefKey, string> = {
  notify_evaluation_received: "Recibir una evaluación",
  notify_state_change: "Cambios de estado",
  notify_assignment: "Asignaciones de jurado",
  notify_comment_added: "Comentarios nuevos",
  notify_semester_changes: "Cambios de semestre",
  email_enabled: "Correo electrónico",
};

const PREF_HINTS: Record<PrefKey, string> = {
  notify_evaluation_received: "Cuando un jurado registra una evaluación.",
  notify_state_change: "Avances en el ciclo del proyecto.",
  notify_assignment: "Cuando te asignan a un proyecto.",
  notify_comment_added: "Hilos en tus proyectos.",
  notify_semester_changes: "Cuando se activa un periodo.",
  email_enabled: "Recibe una copia por email además del aviso en la app.",
};

// Mapeo entre clave de preferencia y el `kind` del backend, para reusar
// la paleta y el ícono de kindMeta. email_enabled no tiene kind asociado.
const PREF_KIND: Partial<Record<PrefKey, string>> = {
  notify_evaluation_received: "evaluation_received",
  notify_state_change: "state_change",
  notify_assignment: "assignment",
  notify_comment_added: "comment_added",
  notify_semester_changes: "semester_activated",
};

interface PrefRowVisual {
  IconComponent: LucideIcon;
  tintBg: string;
  tintFg: string;
}

function getRowVisual(key: PrefKey): PrefRowVisual {
  if (key === "email_enabled") {
    return {
      IconComponent: Mail,
      tintBg: "bg-slate-100",
      tintFg: "text-slate-500",
    };
  }
  const kind = PREF_KIND[key];
  const meta = getKindMeta(kind ?? "");
  return {
    IconComponent: meta.IconComponent,
    tintBg: meta.tintBg,
    tintFg: meta.tintFg,
  };
}

interface NotificationPreferencesCardProps {
  prefs: UserPreferences | null;
  visibleKeys: PrefKey[];
  loading: boolean;
  error: string | null;
  onToggle: (key: PrefKey) => void;
}

export function NotificationPreferencesCard({
  prefs,
  visibleKeys,
  loading,
  error,
  onToggle,
}: NotificationPreferencesCardProps) {
  // Separar email_enabled (Canal) del resto (Eventos)
  const eventKeys = visibleKeys.filter((k) => k !== "email_enabled");
  const channelKeys = visibleKeys.filter((k) => k === "email_enabled");

  return (
    <section
      aria-labelledby="prefs-heading"
      className="bg-surface border border-border-subtle rounded-[14px] shadow-[0_1px_2px_rgba(15,23,42,0.03)] overflow-hidden lg:sticky lg:top-6"
    >
      <header className="px-7 pt-6 pb-5 border-b border-border-subtle flex items-center gap-3">
        <div className="w-10 h-10 rounded-[10px] bg-gradient-to-br from-[rgba(0,102,255,0.08)] to-[rgba(255,107,53,0.08)] text-primary inline-flex items-center justify-center shrink-0">
          <SlidersHorizontal className="w-[18px] h-[18px]" />
        </div>
        <div className="min-w-0">
          <h3
            id="prefs-heading"
            className="text-[15px] font-extrabold text-text-strong tracking-tight leading-tight"
          >
            Preferencias
          </h3>
          <p className="text-[12.5px] text-text-muted leading-tight mt-0.5">
            Elige qué te avisamos.
          </p>
        </div>
      </header>

      {loading ? (
        <div className="px-7 py-6" role="status" aria-label="Cargando preferencias">
          <p className="text-[13.5px] text-text-muted">Cargando…</p>
        </div>
      ) : !prefs ? null : (
        <div className="px-7 py-6 space-y-5">
          {error && (
            <p className="text-[12.5px] text-destructive font-medium">{error}</p>
          )}

          {eventKeys.length > 0 && (
            <div>
              <p className="text-[11.5px] font-bold text-text-muted uppercase tracking-[0.06em] mb-3">
                Eventos
              </p>
              <div className="space-y-3.5">
                {eventKeys.map((key) => (
                  <PreferenceToggleRow
                    key={key}
                    prefKey={key}
                    label={PREF_LABELS[key]}
                    hint={PREF_HINTS[key]}
                    checked={prefs[key]}
                    visual={getRowVisual(key)}
                    onToggle={() => onToggle(key)}
                  />
                ))}
              </div>
            </div>
          )}

          {eventKeys.length > 0 && channelKeys.length > 0 && (
            <div className="h-px bg-gradient-to-r from-[rgba(0,102,255,0.15)] via-[rgba(255,107,53,0.15)] to-transparent" />
          )}

          {channelKeys.length > 0 && (
            <div>
              <p className="text-[11.5px] font-bold text-text-muted uppercase tracking-[0.06em] mb-3">
                Canal
              </p>
              <div className="space-y-3.5">
                {channelKeys.map((key) => (
                  <PreferenceToggleRow
                    key={key}
                    prefKey={key}
                    label={PREF_LABELS[key]}
                    hint={PREF_HINTS[key]}
                    checked={prefs[key]}
                    visual={getRowVisual(key)}
                    onToggle={() => onToggle(key)}
                  />
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      <div className="px-7 py-3.5 border-t border-border-subtle bg-[#fafbfd] flex items-center gap-2 text-[11.5px] text-text-muted">
        <Info className="w-3.5 h-3.5 shrink-0" aria-hidden="true" />
        <span>Los cambios se guardan automáticamente.</span>
      </div>
    </section>
  );
}

function PreferenceToggleRow({
  prefKey,
  label,
  hint,
  checked,
  visual,
  onToggle,
}: {
  prefKey: PrefKey;
  label: string;
  hint: string;
  checked: boolean;
  visual: PrefRowVisual;
  onToggle: () => void;
}) {
  const { IconComponent, tintBg, tintFg } = visual;
  return (
    <div className="flex items-center justify-between gap-3">
      <div className="flex items-start gap-2.5 min-w-0">
        <div
          className={`w-7 h-7 rounded-[8px] inline-flex items-center justify-center shrink-0 mt-0.5 ${tintBg} ${tintFg}`}
          aria-hidden="true"
        >
          <IconComponent className="w-3.5 h-3.5" />
        </div>
        <div className="min-w-0">
          <p className="text-[13px] font-semibold text-text-default leading-tight">{label}</p>
          <p className="text-[11.5px] text-text-muted leading-tight mt-0.5">{hint}</p>
        </div>
      </div>
      <button
        role="switch"
        aria-checked={checked}
        aria-label={label}
        data-pref-key={prefKey}
        onClick={onToggle}
        type="button"
        className={[
          "relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent",
          "transition-colors duration-200 ease-in-out focus:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2",
          checked ? "bg-primary" : "bg-[var(--color-surface-sunken,#e8eaf0)]",
        ].join(" ")}
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
