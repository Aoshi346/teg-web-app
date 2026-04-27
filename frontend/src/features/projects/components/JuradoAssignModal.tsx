"use client";

import * as React from "react";
import Combobox from "@/app/dashboard/agregar/components/Combobox";
import { getJurados, type User as AuthUser } from "@features/auth/api/clientAuth";
import { assignReviewer } from "@features/projects/api/projectService";
import { getProject } from "@features/projects/api/projectService";
import type { Project } from "@features/projects/types/project";

export interface JuradoAssignModalProps {
  open: boolean;
  project: Project;
  onClose: () => void;
  onSuccess: (updated: Project) => void;
}

export default function JuradoAssignModal({ open, project, onClose, onSuccess }: JuradoAssignModalProps) {
  const [options, setOptions] = React.useState<{ id: number; label: string }[]>([]);
  const [selectedId, setSelectedId] = React.useState<number | "">("");
  const [busy, setBusy] = React.useState(false);
  const [err, setErr] = React.useState<string | null>(null);

  React.useEffect(() => {
    if (!open) return;
    (async () => {
      const jurados = await getJurados();
      setOptions(
        jurados
          .filter((u: AuthUser) => typeof u.id === "number")
          .map((u: AuthUser) => ({ id: u.id!, label: u.fullName?.trim() ? u.fullName! : u.email })),
      );
    })();
  }, [open]);

  if (!open) return null;

  const submit = async (newId: number | null) => {
    setBusy(true); setErr(null);
    try {
      await assignReviewer(project.id, newId);
      const refreshed = await getProject(project.id);
      if (refreshed) onSuccess(refreshed);
      onClose();
      setSelectedId("");
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Error al asignar.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={onClose} />
      <div className="detail-modal relative w-full max-w-sm bg-surface rounded-2xl shadow-2xl ring-1 ring-black/5 overflow-hidden">
        <div className="p-5 border-b border-border-subtle">
          <h3 className="text-base font-extrabold text-text-strong">Jurado asignado</h3>
          <p className="text-xs text-text-muted mt-0.5">
            {project.reviewerName ? `Jurado actual: ${project.reviewerName}` : "Sin jurado asignado"}
          </p>
        </div>
        <div className="p-5 space-y-4">
          <Combobox
            options={options}
            value={selectedId}
            onChange={(v) => setSelectedId(v as number | "")}
            placeholder="Buscar jurado..."
            emptyLabel="Sin jurados disponibles"
          />
          {err && <p className="text-[11px] text-destructive font-semibold">{err}</p>}
        </div>
        <div className="flex flex-col gap-2 p-5 pt-0">
          <button
            type="button"
            onClick={() => typeof selectedId === "number" && submit(selectedId)}
            disabled={!selectedId || busy}
            className="w-full px-4 py-2.5 text-sm font-bold text-white bg-text-strong hover:bg-[#0a1424] rounded-xl disabled:opacity-50 transition-colors"
          >
            {busy ? "Guardando..." : "Guardar"}
          </button>
          {project.reviewerName && (
            <button
              type="button"
              onClick={() => submit(null)}
              disabled={busy}
              className="w-full px-4 py-2.5 text-sm font-bold text-destructive bg-red-50 hover:bg-red-100 border border-red-200 rounded-xl disabled:opacity-50 transition-colors"
            >
              Quitar asignación
            </button>
          )}
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
