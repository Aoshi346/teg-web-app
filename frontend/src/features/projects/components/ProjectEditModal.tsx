"use client";

import * as React from "react";
import { updateProject, getProject } from "@features/projects/api/projectService";
import type { Project } from "@features/projects/types/project";

export interface ProjectEditModalProps {
  open: boolean;
  project: Project;
  onClose: () => void;
  onSuccess: (updated: Project) => void;
}

export default function ProjectEditModal({ open, project, onClose, onSuccess }: ProjectEditModalProps) {
  const [title, setTitle] = React.useState(project.title);
  const [busy, setBusy] = React.useState(false);
  const [err, setErr] = React.useState<string | null>(null);

  React.useEffect(() => {
    if (open) {
      setTitle(project.title);
      setErr(null);
    }
  }, [open, project.title]);

  if (!open) return null;

  const submit = async () => {
    const trimmed = title.trim();
    if (!trimmed) {
      setErr("El título no puede estar vacío.");
      return;
    }
    if (trimmed === project.title) {
      onClose();
      return;
    }
    setBusy(true);
    setErr(null);
    try {
      await updateProject(project.id, { title: trimmed });
      const fresh = await getProject(project.id);
      if (fresh) onSuccess(fresh);
      onClose();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Error al guardar.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={onClose} />
      <div className="relative w-full max-w-md bg-surface rounded-2xl shadow-2xl ring-1 ring-black/5 overflow-hidden">
        <div className="p-5 border-b border-border-subtle">
          <h3 className="text-base font-extrabold text-text-strong">Editar proyecto</h3>
          <p className="text-xs text-text-muted mt-0.5">Modifica el título del proyecto.</p>
        </div>
        <div className="p-5 space-y-3">
          <label className="block">
            <span className="text-[10px] uppercase tracking-wider text-text-muted font-extrabold mb-1.5 block">Título</span>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              maxLength={200}
              className="w-full px-3 py-2.5 bg-surface border border-border-subtle rounded-xl text-[14px] font-semibold text-text-strong focus:outline-none focus:border-primary transition-colors"
            />
          </label>
          {err && <p className="text-[11px] text-destructive font-semibold">{err}</p>}
        </div>
        <div className="flex flex-col gap-2 p-5 pt-0">
          <button
            type="button"
            onClick={submit}
            disabled={busy}
            className="w-full px-4 py-2.5 text-sm font-bold text-white bg-text-strong hover:bg-[#0a1424] rounded-xl disabled:opacity-50 transition-colors"
          >
            {busy ? "Guardando..." : "Guardar cambios"}
          </button>
          <button
            type="button"
            onClick={onClose}
            className="w-full px-4 py-2.5 text-sm font-semibold text-text-muted hover:bg-surface-muted rounded-xl transition-colors"
          >
            Cancelar
          </button>
        </div>
      </div>
    </div>
  );
}
