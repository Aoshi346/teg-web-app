"use client";

import React, { useState, useEffect } from "react";
import Combobox from "@/app/dashboard/agregar/components/Combobox";
import type { Presentation, PresentationCreate } from "../types/planificacion";
import type { Project } from "@features/projects/types/project";
import type { User } from "@features/auth/api/clientAuth";

export interface PresentationFormModalProps {
  isOpen: boolean;
  dayId: number;
  editTarget?: Presentation | null;
  dayDate?: string;
  onClose: () => void;
  onSave: (dayId: number, payload: PresentationCreate, editId?: number) => Promise<void>;
}

interface ComboOption {
  id: number;
  label: string;
}

export default function PresentationFormModal({
  isOpen,
  dayId,
  editTarget,
  dayDate,
  onClose,
  onSave,
}: PresentationFormModalProps): React.ReactElement | null {
  const [projects, setProjects] = useState<Project[]>([]);
  const [juradoUsers, setJuradoUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);

  const [selectedProjectId, setSelectedProjectId] = useState<number | "">(
    () => editTarget?.project ?? ""
  );
  const [juradoIds, setJuradoIds] = useState<number[]>(
    () => editTarget?.jurado ?? []
  );
  const [juradoPickValue, setJuradoPickValue] = useState<number | "">("");
  const [startTime, setStartTime] = useState(editTarget?.start_time ?? "09:00");
  const [duration, setDuration] = useState(
    editTarget?.duration_minutes ?? 30
  );
  const [saving, setSaving] = useState(false);

  // Load data on open
  useEffect(() => {
    if (!isOpen) return;
    setLoading(true);
    Promise.all([
      import("@features/projects/api/projectService").then((m) =>
        m.getAllProjects()
      ),
      import("@features/auth/api/clientAuth").then((m) => m.getAllUsers()),
    ]).then(([projs, users]) => {
      setProjects(projs);
      setJuradoUsers(
        users.filter((u: User) => u.role === "Jurado")
      );
      setLoading(false);
    });
  }, [isOpen]);

  // Re-initialize form on editTarget change
  useEffect(() => {
    setSelectedProjectId(editTarget?.project ?? "");
    setJuradoIds(editTarget?.jurado ?? []);
    setStartTime(editTarget?.start_time ?? "09:00");
    setDuration(editTarget?.duration_minutes ?? 30);
    setJuradoPickValue("");
  }, [editTarget, isOpen]);

  useEffect(() => {
    if (!isOpen) return;
    function handleKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    document.addEventListener("keydown", handleKey);
    return () => document.removeEventListener("keydown", handleKey);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const selectedProject =
    selectedProjectId !== ""
      ? projects.find((p) => p.id === selectedProjectId) ?? null
      : null;

  const projectOptions: ComboOption[] = projects.map((p) => ({
    id: p.id,
    label: `${p.title} — ${p.student}`,
  }));

  const juradoOptions: ComboOption[] = juradoUsers
    .filter((u) => u.id !== undefined && !juradoIds.includes(u.id as number))
    .map((u) => ({ id: u.id as number, label: u.fullName ?? u.email }));

  function addJurado(id: number | "") {
    if (id === "" || juradoIds.length >= 3) return;
    setJuradoIds((prev) => [...prev, id]);
    setJuradoPickValue("");
  }

  function removeJurado(id: number) {
    setJuradoIds((prev) => prev.filter((j) => j !== id));
  }

  function juradoName(id: number): string {
    return (
      juradoUsers.find((u) => u.id === id)?.fullName ??
      editTarget?.jurado_names?.[editTarget.jurado.indexOf(id)] ??
      `Jurado ${id}`
    );
  }

  const overlayClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget) onClose();
  };

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (selectedProjectId === "") return;
    setSaving(true);
    try {
      const tutorId =
        selectedProject?.advisors?.[0] ??
        editTarget?.tutor ??
        null;
      const payload: PresentationCreate = {
        project: selectedProjectId as number,
        start_time: startTime,
        jurado: juradoIds,
        tutor: tutorId,
        duration_minutes: duration,
      };
      await onSave(dayId, payload, editTarget?.id);
      onClose();
    } finally {
      setSaving(false);
    }
  }

  const eyebrow = editTarget ? "Editar presentación" : "Programar presentación";
  const titleText =
    editTarget
      ? (selectedProject?.title ?? editTarget.project_title ?? "Editar presentación")
      : "Programar presentación";

  return (
    <div className="modal-overlay" onClick={overlayClick}>
      <div
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="pres-modal-title"
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
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <path d="M14 2v6h6M16 13H8M16 17H8M10 9H8" />
            </svg>
          </div>
          <div className="band-body">
            <p className="band-eyebrow">{eyebrow}</p>
            <h2 id="pres-modal-title" className="band-title">
              {titleText}
            </h2>
            {dayDate && <span className="band-sub">{dayDate}</span>}
          </div>
          <button className="band-close" aria-label="Cerrar" onClick={onClose}>
            ×
          </button>
        </div>

        {/* Body */}
        <form
          id="pres-form"
          className="modal-body"
          onSubmit={handleSubmit}
        >
          {loading ? (
            <div
              role="status"
              style={{
                display: "flex",
                justifyContent: "center",
                padding: "32px",
              }}
            >
              <div
                style={{
                  width: 28,
                  height: 28,
                  borderRadius: "50%",
                  border: "3px solid var(--border-subtle)",
                  borderTopColor: "var(--brand-blue)",
                  animation: "spin 0.7s linear infinite",
                }}
              />
            </div>
          ) : (
            <>
              {/* Section 01 — Proyecto */}
              <div className="section">
                <header className="section-h">
                  <span className="section-num">01</span>
                  <span className="section-title-h">Proyecto</span>
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
                      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                      <path d="M14 2v6h6" />
                    </svg>
                    Proyecto / Tesis <span className="agg-req">*</span>
                  </label>
                  <Combobox
                    placeholder="Buscar proyecto o tesis…"
                    value={selectedProjectId}
                    onChange={(v) => setSelectedProjectId(v)}
                    options={projectOptions}
                  />
                  {selectedProject && (
                    <div
                      className={`proj-summary ${
                        selectedProject.type === "tesis" ? "teg" : "pteg"
                      }`}
                    >
                      <div className="proj-summary-row">
                        <span className="l">Estudiante</span>
                        <span className="v">{selectedProject.student}</span>
                      </div>
                      {selectedProject.advisorNames?.[0] && (
                        <div className="proj-summary-row">
                          <span className="l">Tutor</span>
                          <span className="v">
                            {selectedProject.advisorNames[0]}
                          </span>
                        </div>
                      )}
                      <div className="proj-summary-row">
                        <span className="l">Modalidad</span>
                        <span className="v">
                          <span
                            className={`spill ${
                              selectedProject.type === "tesis" ? "teg" : "pteg"
                            }`}
                          >
                            {selectedProject.type === "tesis" ? "TEG" : "PTEG"}
                          </span>
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Section 02 — Tribunal */}
              <div className="section">
                <header className="section-h">
                  <span className="section-num">02</span>
                  <span className="section-title-h">Tribunal</span>
                  <span className="section-meta">Hasta 3</span>
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
                      <path d="M16 16h6v-2a3 3 0 0 0-3-3h-2" />
                      <path d="M8 16H2v-2a3 3 0 0 1 3-3h2" />
                      <circle cx="12" cy="7" r="4" />
                      <path d="M16 16a4 4 0 0 0-8 0v6h8z" />
                    </svg>
                    Jurados
                  </label>

                  {juradoIds.length === 0 ? (
                    <div className="jur-empty">
                      Sin jurados asignados. Añade hasta 3.
                    </div>
                  ) : (
                    <div className="jur-chips">
                      {juradoIds.map((jid) => (
                        <span key={jid} className="jur-chip">
                          {juradoName(jid)}
                          <button
                            type="button"
                            aria-label={`Quitar ${juradoName(jid)}`}
                            onClick={() => removeJurado(jid)}
                          >
                            ×
                          </button>
                        </span>
                      ))}
                    </div>
                  )}

                  <div className="jur-add">
                    <Combobox
                      placeholder="Buscar jurado…"
                      value={juradoPickValue}
                      onChange={(v) => addJurado(v)}
                      options={juradoOptions}
                      disabled={juradoIds.length >= 3}
                    />
                    <button
                      type="button"
                      className="btn ghost"
                      disabled={juradoIds.length >= 3}
                      aria-label="Añadir jurado"
                      onClick={() => addJurado(juradoPickValue)}
                    >
                      + Añadir
                    </button>
                  </div>
                </div>
              </div>

              {/* Section 03 — Horario */}
              <div className="section">
                <header className="section-h">
                  <span className="section-num">03</span>
                  <span className="section-title-h">Horario</span>
                </header>
                <div className="row-2">
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
                        <circle cx="12" cy="12" r="10" />
                        <path d="M12 6v6l4 2" />
                      </svg>
                      Hora de inicio <span className="agg-req">*</span>
                    </label>
                    <input
                      type="time"
                      className="agg-field-input"
                      value={startTime}
                      onChange={(e) => setStartTime(e.target.value)}
                    />
                  </div>
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
                        <circle cx="12" cy="13" r="9" />
                        <path d="M12 9v4l2 2M9 2h6" />
                      </svg>
                      Duración (min)
                    </label>
                    <input
                      type="number"
                      className="agg-field-input"
                      value={duration}
                      min={5}
                      step={5}
                      onChange={(e) => setDuration(Number(e.target.value))}
                    />
                  </div>
                </div>
              </div>
            </>
          )}
        </form>

        {/* Footer */}
        <div className="modal-foot">
          <span className="foot-meta">
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.4"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <circle cx="12" cy="12" r="10" />
              <path d="M12 16v-4M12 8h.01" />
            </svg>
            Auto-asigna tutor desde el proyecto
          </span>
          <div className="foot-actions">
            <button
              className="btn ghost"
              type="button"
              onClick={onClose}
            >
              Cancelar
            </button>
            <button
              className="btn primary"
              type="submit"
              form="pres-form"
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
