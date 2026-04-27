"use client";

import React, { useState, useEffect } from "react";
import { Trash2 } from "lucide-react";
import { deleteProject } from "@features/projects/api/projectService";

export interface DeleteProjectModalProps {
  isOpen: boolean;
  projectTitle: string;
  projectId: number;
  projectType: "proyecto" | "tesis";
  onClose: () => void;
  onConfirmed: () => void;
}

export function DeleteProjectModal({
  isOpen,
  projectTitle,
  projectId,
  onClose,
  onConfirmed,
}: DeleteProjectModalProps) {
  const [confirmInput, setConfirmInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Resetear el input cuando el modal se abre o cierra
  useEffect(() => {
    if (!isOpen) {
      setConfirmInput("");
      setError(null);
      setLoading(false);
    }
  }, [isOpen]);

  useEffect(() => {
    if (!isOpen) return;
    function handleKey(e: KeyboardEvent) {
      if (e.key === "Escape" && !loading) onClose();
    }
    document.addEventListener("keydown", handleKey);
    return () => document.removeEventListener("keydown", handleKey);
  }, [isOpen, loading, onClose]);

  if (!isOpen) return null;

  const isConfirmed = confirmInput === projectTitle;

  function handleOverlayClick(e: React.MouseEvent<HTMLDivElement>) {
    if (e.target === e.currentTarget && !loading) onClose();
  }

  async function handleDelete() {
    if (!isConfirmed || loading) return;
    setLoading(true);
    setError(null);
    try {
      await deleteProject(projectId);
      onConfirmed();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al eliminar el proyecto.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="modal-overlay" onClick={handleOverlayClick}>
      <div
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="delete-project-title"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Band */}
        <div className="modal-band edit">
          <div className="band-icon" style={{ background: "linear-gradient(135deg, var(--destructive) 0%, #c0392b 100%)" }}>
            <Trash2 />
          </div>
          <div className="band-body">
            <p className="band-eyebrow">Acción irreversible</p>
            <h2 id="delete-project-title" className="band-title">
              Eliminar proyecto
            </h2>
            <span className="band-sub">{projectTitle}</span>
          </div>
          <button
            className="band-close"
            aria-label="Cerrar"
            onClick={onClose}
            disabled={loading}
          >
            ×
          </button>
        </div>

        {/* Body */}
        <div className="modal-body">
          {/* Section 01 — Confirmación */}
          <div className="section">
            <header className="section-h">
              <span className="section-num">01</span>
              <span className="section-title-h">Confirmación</span>
            </header>
            <div className="agg-field">
              <label className="agg-field-label" htmlFor="delete-confirm-input">
                Escriba el título del proyecto para confirmar
              </label>
              <input
                id="delete-confirm-input"
                type="text"
                className="agg-field-input"
                value={confirmInput}
                onChange={(e) => setConfirmInput(e.target.value)}
                placeholder={projectTitle}
                disabled={loading}
                autoComplete="off"
              />
            </div>
          </div>

          {/* Section 02 — Advertencia */}
          <div className="section">
            <header className="section-h">
              <span className="section-num">02</span>
              <span className="section-title-h">Advertencia</span>
            </header>
            <p style={{ fontSize: "13px", color: "var(--text-muted)", marginBottom: "10px" }}>
              Esta acción eliminará permanentemente:
            </p>
            <ul style={{ fontSize: "13px", color: "var(--text-muted)", paddingLeft: "18px", lineHeight: "1.8" }}>
              <li>Evaluaciones asociadas al proyecto</li>
              <li>Archivos subidos (PDFs y documentos)</li>
              <li>Comentarios del proyecto</li>
              <li>Presentaciones programadas</li>
            </ul>
          </div>

          {/* Error banner */}
          {error && (
            <div className="err-banner" role="alert">
              <span className="err-banner-msg">{error}</span>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="modal-foot">
          <div className="foot-actions" style={{ display: "flex", gap: "8px", marginLeft: "auto" }}>
            <button
              className="btn ghost"
              type="button"
              onClick={onClose}
              disabled={loading}
            >
              Cancelar
            </button>
            <button
              className="btn danger"
              type="button"
              onClick={handleDelete}
              disabled={!isConfirmed || loading}
            >
              <Trash2 />
              Eliminar definitivamente
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
