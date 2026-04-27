"use client";

import * as React from "react";
import Combobox from "@/app/dashboard/agregar/components/Combobox";
import { getAllUsers, type User as AuthUser } from "@features/auth/api/clientAuth";
import { reassignStudent, getProject } from "@features/projects/api/projectService";
import type { Project } from "@features/projects/types/project";

export interface StudentReassignModalProps {
  open: boolean;
  project: Project;
  onClose: () => void;
  onSuccess: (updated: Project) => void;
}

export default function StudentReassignModal({ open, project, onClose, onSuccess }: StudentReassignModalProps) {
  const [options, setOptions] = React.useState<{ id: number; label: string }[]>([]);
  const [selectedId, setSelectedId] = React.useState<number | "">("");
  const [busy, setBusy] = React.useState(false);
  const [err, setErr] = React.useState<string | null>(null);

  React.useEffect(() => {
    if (!open) return;
    (async () => {
      const users = await getAllUsers();
      setOptions(
        users
          .filter((u: AuthUser) => u.role === "Estudiante" && typeof u.id === "number")
          .map((u: AuthUser) => ({ id: u.id!, label: u.fullName?.trim() ? u.fullName! : u.email })),
      );
    })();
  }, [open]);

  if (!open) return null;

  const submit = async () => {
    if (typeof selectedId !== "number") return;
    setBusy(true); setErr(null);
    try {
      await reassignStudent(project.id, { student: selectedId });
      const refreshed = await getProject(project.id);
      if (refreshed) onSuccess(refreshed);
      onClose();
      setSelectedId("");
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Error al reasignar.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={onClose} />
      <div className="detail-modal relative w-full max-w-sm bg-surface rounded-2xl shadow-2xl ring-1 ring-black/5 overflow-hidden">
        <div className="p-5 border-b border-border-subtle">
          <h3 className="text-base font-extrabold text-text-strong">Reasignar estudiante</h3>
          <p className="text-xs text-text-muted mt-0.5">Estudiante actual: {project.student}</p>
        </div>
        <div className="p-5 space-y-4">
          <Combobox
            options={options}
            value={selectedId}
            onChange={(v) => setSelectedId(v as number | "")}
            placeholder="Buscar estudiante..."
            emptyLabel="Sin estudiantes disponibles"
          />
          {err && <p className="text-[11px] text-destructive font-semibold">{err}</p>}
        </div>
        <div className="flex flex-col gap-2 p-5 pt-0">
          <button
            type="button"
            onClick={submit}
            disabled={!selectedId || busy}
            className="w-full px-4 py-2.5 text-sm font-bold text-white bg-text-strong hover:bg-[#0a1424] rounded-xl disabled:opacity-50 transition-colors"
          >
            {busy ? "Guardando..." : "Confirmar"}
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
