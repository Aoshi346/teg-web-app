"use client";
import React, { useEffect, useState } from "react";
import {
  getPreferences,
  updatePreferences,
  getUserRole,
  type UserPreferences,
} from "@features/auth/api/clientAuth";
import { NotificationsPage } from "@features/notifications";
import { NotificationPreferencesCard } from "./NotificationPreferencesCard";

type PrefKey = keyof UserPreferences;

// Mapeo de rol a claves de preferencia visibles (el orden determina el render)
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
    return () => {
      cancelled = true;
    };
  }, []);

  async function handleToggle(key: PrefKey) {
    if (!prefs) return;
    const oldValue = prefs[key];
    const newValue = !oldValue;

    // Actualización optimista
    setPrefs((prev) => (prev ? { ...prev, [key]: newValue } : prev));
    setError(null);

    try {
      await updatePreferences({ [key]: newValue });
    } catch {
      setPrefs((prev) => (prev ? { ...prev, [key]: oldValue } : prev));
      setError("No se pudo guardar el cambio. Intenta nuevamente.");
    }
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-[2fr_1fr] gap-5 items-start">
      <NotificationsPage />
      <NotificationPreferencesCard
        prefs={prefs}
        visibleKeys={visibleKeys}
        loading={loading}
        error={error}
        onToggle={handleToggle}
      />
    </div>
  );
}
