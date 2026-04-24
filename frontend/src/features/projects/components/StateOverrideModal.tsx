"use client";

import React, { useState } from "react";
import type { ProjectState } from "@features/projects/types/project";
import { PTEG_STATE_CONFIG } from "@features/projects/lib/ptegStateConfig";

const ALL_STATES = Object.keys(PTEG_STATE_CONFIG) as ProjectState[];

interface Props {
  open: boolean;
  currentState: ProjectState;
  onClose: () => void;
  onSubmit: (payload: { state: ProjectState; reason: string }) => Promise<void>;
}

export default function StateOverrideModal({
  open,
  currentState,
  onClose,
  onSubmit,
}: Props) {
  const [target, setTarget] = useState<ProjectState | "">("");
  const [reason, setReason] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!open) return null;

  const trimmed = reason.trim();
  const canSubmit = target !== "" && trimmed.length >= 10 && !submitting;
  const targetLabel = target ? PTEG_STATE_CONFIG[target].label : "";

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!canSubmit || !target) return;
    setSubmitting(true);
    setError(null);
    try {
      await onSubmit({ state: target as ProjectState, reason: trimmed });
      setTarget("");
      setReason("");
      onClose();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Error al forzar el estado.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  const availableStates = ALL_STATES.filter((s) => s !== currentState);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40"
      onClick={submitting ? undefined : onClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="state-override-title"
    >
      <div
        className="w-full max-w-md bg-white rounded-2xl p-6 shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 id="state-override-title" className="text-lg font-bold mb-4">Forzar estado del proyecto</h2>
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <label className="flex flex-col gap-1 text-sm">
            Estado destino
            <select
              aria-label="Estado destino"
              value={target}
              onChange={(e) =>
                setTarget(e.target.value as ProjectState | "")
              }
              className="border rounded px-2 py-1"
              required
            >
              <option value="">— Selecciona —</option>
              {availableStates.map((s) => (
                <option key={s} value={s}>
                  {PTEG_STATE_CONFIG[s].label}
                </option>
              ))}
            </select>
          </label>

          <label className="flex flex-col gap-1 text-sm">
            Razón (mínimo 10 caracteres)
            <textarea
              aria-label="Razón"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              maxLength={500}
              rows={4}
              className="border rounded px-2 py-1 resize-none"
              required
            />
            <span className="text-xs text-muted">{trimmed.length}/500</span>
          </label>

          {error && (
            <div className="text-sm text-red-700 bg-red-50 border border-red-200 rounded px-2 py-1">
              {error}
            </div>
          )}

          <div className="flex justify-end gap-2">
            <button
              type="button"
              onClick={onClose}
              disabled={submitting}
              className="px-3 py-1.5 text-sm rounded border"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={!canSubmit}
              className="px-3 py-1.5 text-sm rounded bg-primary text-white disabled:opacity-50"
            >
              Forzar{targetLabel ? ` a ${targetLabel}` : ""}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
