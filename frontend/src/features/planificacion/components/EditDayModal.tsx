"use client";

import React, { useState, useEffect } from "react";
import type { PresentationDay } from "../types/planificacion";
import {
  formatDayNumeral,
  formatWeekday,
  formatMonth,
} from "../lib/formatDate";

export interface EditDayModalProps {
  day: PresentationDay | null;
  onClose: () => void;
  onSaved: () => Promise<void> | void;
}

export default function EditDayModal({
  day,
  onClose,
  onSaved,
}: EditDayModalProps): React.ReactElement | null {
  const [dateValue, setDateValue] = useState("");
  const [notesValue, setNotesValue] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (day) {
      setDateValue(day.date);
      setNotesValue(day.notes ?? "");
    }
  }, [day]);

  useEffect(() => {
    if (!day) return;
    function handleKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    document.addEventListener("keydown", handleKey);
    return () => document.removeEventListener("keydown", handleKey);
  }, [day, onClose]);

  if (!day) return null;

  const N = day.presentations.length;
  const weekday = formatWeekday(day.date);
  const dayNum = formatDayNumeral(day.date);
  const monthName = formatMonth(day.date);

  const bandTitle = `${weekday} ${dayNum} de ${monthName}`;
  const bandSub =
    N === 0
      ? "Sin presentaciones programadas"
      : N === 1
      ? "1 presentación programada"
      : `${N} presentaciones programadas`;

  const overlayClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget) onClose();
  };

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      const { updateDay } = await import("../api/planificacionService");
      await updateDay(day!.id, { date: dateValue, notes: notesValue });
      await onSaved();
      onClose();
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    if (!day) return;
    const confirmed = window.confirm(
      "¿Eliminar el día? Esto eliminará todas sus presentaciones."
    );
    if (!confirmed) return;
    const { deleteDay } = await import("../api/planificacionService");
    await deleteDay(day.id);
    await onSaved();
    onClose();
  }

  return (
    <div className="modal-overlay" onClick={overlayClick}>
      <div
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="edit-day-title"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Band */}
        <div className="modal-band edit">
          <div className="band-icon">
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
              <path d="m18.5 2.5 3 3L12 15l-4 1 1-4z" />
            </svg>
          </div>
          <div className="band-body">
            <p className="band-eyebrow">Editar día</p>
            <h2 id="edit-day-title" className="band-title">
              {bandTitle}
            </h2>
            <span className="band-sub">{bandSub}</span>
          </div>
          <button className="band-close" aria-label="Cerrar" onClick={onClose}>
            ×
          </button>
        </div>

        {/* Form body */}
        <form
          id="edit-day-form"
          className="modal-body"
          onSubmit={handleSubmit}
        >
          {/* Section 01 — Fecha */}
          <div className="section">
            <header className="section-h">
              <span className="section-num">01</span>
              <span className="section-title-h">Fecha</span>
            </header>
            <div className="agg-field">
              <label className="agg-field-label">
                <svg
                  className="agg-field-ic"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2.2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  aria-hidden
                >
                  <rect x="3" y="4" width="18" height="18" rx="3" />
                  <path d="M16 2v4M8 2v4M3 10h18" />
                </svg>
                Día <span className="agg-req">*</span>
              </label>
              <div className="date-display">
                <svg
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2.2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <rect x="3" y="4" width="18" height="18" rx="3" />
                  <path d="M16 2v4M8 2v4M3 10h18" />
                </svg>
                <input
                  type="date"
                  value={dateValue}
                  onChange={(e) => setDateValue(e.target.value)}
                />
              </div>
              <p className="field-help-soft">
                Cambiar la fecha mueve todas las presentaciones del día.
              </p>
            </div>
          </div>

          {/* Section 02 — Notas */}
          <div className="section">
            <header className="section-h">
              <span className="section-num">02</span>
              <span className="section-title-h">Notas</span>
              <span className="section-meta">Opcional</span>
            </header>
            <div className="agg-field">
              <label className="agg-field-label">
                <svg
                  className="agg-field-ic"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2.2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  aria-hidden
                >
                  <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
                  <path d="M18 2l4 4-12 12H6v-4z" />
                </svg>
                Notas internas
              </label>
              <textarea
                className="agg-field-input"
                rows={4}
                value={notesValue}
                onChange={(e) => setNotesValue(e.target.value)}
                placeholder="Aula, instrucciones, coordinador…"
              />
              <p className="field-help-soft">
                Visibles para los estudiantes/jurados del día.
              </p>
            </div>
          </div>
        </form>

        {/* Footer */}
        <div className="modal-foot">
          <button className="btn danger" type="button" onClick={handleDelete}>
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.4"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M3 6h18" />
              <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6" />
            </svg>
            Eliminar día
          </button>
          <div className="foot-actions">
            <button className="btn ghost" type="button" onClick={onClose}>
              Cancelar
            </button>
            <button
              className="btn primary"
              type="submit"
              form="edit-day-form"
              disabled={saving}
            >
              {saving ? "Guardando…" : "Guardar"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
