import React, { useState, useEffect, useRef, useCallback } from "react";
import { X, ChevronDown, Search, Check } from "lucide-react";
import { Presentation, PresentationCreate } from "../types/planificacion";
import { getAllProjects } from "@features/projects/api/projectService";
import { getAllUsers } from "@features/auth/api/clientAuth";
import { Project } from "@features/projects/types/project";

interface PresentationFormModalProps {
  isOpen: boolean;
  dayId: number;
  editTarget?: Presentation | null;
  onClose: () => void;
  onSave: (dayId: number, payload: PresentationCreate, editId?: number) => Promise<void>;
}

const DEFAULT_DURATION = 30;

/**
 * Modal de creación/edición de presentaciones.
 * Carga proyectos y usuarios jurado de forma asíncrona al montarse.
 * El panel de resumen se auto-rellena al seleccionar un proyecto.
 * Los jurados se seleccionan con un multi-select con chips removibles.
 */
export default function PresentationFormModal({
  isOpen,
  dayId,
  editTarget,
  onClose,
  onSave,
}: PresentationFormModalProps) {
  const [projectId, setProjectId] = useState<number | null>(null);
  const [startTime, setStartTime] = useState("09:00");
  const [duration, setDuration] = useState(DEFAULT_DURATION);
  const [juradoIds, setJuradoIds] = useState<number[]>([]);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Data
  const [projects, setProjects] = useState<Project[]>([]);
  const [juradoUsers, setJuradoUsers] = useState<{ id: number; fullName: string; email: string }[]>([]);
  const [loadingData, setLoadingData] = useState(false);

  // Project combobox state
  const [projectOpen, setProjectOpen] = useState(false);
  const [projectQuery, setProjectQuery] = useState("");
  const projectTriggerRef = useRef<HTMLButtonElement>(null);
  const projectDropdownRef = useRef<HTMLDivElement>(null);
  const projectInputRef = useRef<HTMLInputElement>(null);

  // Jurado combobox state
  const [juradoOpen, setJuradoOpen] = useState(false);
  const [juradoQuery, setJuradoQuery] = useState("");
  const juradoTriggerRef = useRef<HTMLButtonElement>(null);
  const juradoDropdownRef = useRef<HTMLDivElement>(null);
  const juradoInputRef = useRef<HTMLInputElement>(null);

  const selectedProject = projects.find((p) => p.id === projectId) ?? null;

  const filteredProjects = projectQuery.trim()
    ? projects.filter((p) =>
        `${p.title} ${p.student}`.toLowerCase().includes(projectQuery.toLowerCase()),
      )
    : projects;

  const filteredJurados = juradoQuery.trim()
    ? juradoUsers.filter((u) =>
        `${u.fullName} ${u.email}`.toLowerCase().includes(juradoQuery.toLowerCase()),
      )
    : juradoUsers;

  // Load projects and jurado users on modal open
  useEffect(() => {
    if (!isOpen) return;
    setLoadingData(true);
    Promise.all([getAllProjects(), getAllUsers()]).then(([projs, users]) => {
      setProjects(projs);
      setJuradoUsers(
        users
          .filter((u) => u.role === "Jurado")
          .map((u) => ({ id: u.id!, fullName: u.fullName || u.email, email: u.email })),
      );
      setLoadingData(false);
    });
  }, [isOpen]);

  // Reset form on open/editTarget change
  useEffect(() => {
    if (editTarget) {
      setProjectId(editTarget.project);
      setStartTime(editTarget.start_time);
      setDuration(editTarget.duration_minutes);
      setJuradoIds(editTarget.jurado);
    } else {
      setProjectId(null);
      setStartTime("09:00");
      setDuration(DEFAULT_DURATION);
      setJuradoIds([]);
    }
    setError(null);
    setProjectQuery("");
    setJuradoQuery("");
  }, [editTarget, isOpen]);

  // Close project dropdown on outside click
  useEffect(() => {
    if (!projectOpen) return;
    function handleClick(e: MouseEvent) {
      const target = e.target as Node;
      if (
        projectTriggerRef.current?.contains(target) ||
        projectDropdownRef.current?.contains(target)
      )
        return;
      setProjectOpen(false);
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [projectOpen]);

  // Close jurado dropdown on outside click
  useEffect(() => {
    if (!juradoOpen) return;
    function handleClick(e: MouseEvent) {
      const target = e.target as Node;
      if (
        juradoTriggerRef.current?.contains(target) ||
        juradoDropdownRef.current?.contains(target)
      )
        return;
      setJuradoOpen(false);
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [juradoOpen]);

  // Focus project search on open
  useEffect(() => {
    if (projectOpen) {
      setTimeout(() => projectInputRef.current?.focus(), 30);
    } else {
      setProjectQuery("");
    }
  }, [projectOpen]);

  // Focus jurado search on open
  useEffect(() => {
    if (juradoOpen) {
      setTimeout(() => juradoInputRef.current?.focus(), 30);
    } else {
      setJuradoQuery("");
    }
  }, [juradoOpen]);

  const handleSelectProject = useCallback((id: number) => {
    setProjectId(id);
    setProjectOpen(false);
  }, []);

  const handleToggleJurado = useCallback((id: number) => {
    setJuradoIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
    );
  }, []);

  const handleRemoveJurado = useCallback((id: number) => {
    setJuradoIds((prev) => prev.filter((x) => x !== id));
  }, []);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!projectId || !startTime) {
      setError("El proyecto y la hora de inicio son obligatorios.");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await onSave(
        dayId,
        {
          project: projectId,
          start_time: startTime,
          duration_minutes: duration,
          jurado: juradoIds,
        },
        editTarget?.id,
      );
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al guardar");
    } finally {
      setSaving(false);
    }
  };

  const selectedJuradoUsers = juradoUsers.filter((u) => juradoIds.includes(u.id));

  return (
    <div className="fixed inset-0 z-[200] flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/40 backdrop-blur-sm animate-in fade-in duration-180"
        onClick={onClose}
      />
      {/* Panel */}
      <div
        className="relative w-full max-w-[560px] bg-white rounded-2xl shadow-2xl ring-1 ring-black/5 animate-in zoom-in-95 fade-in duration-180 overflow-hidden max-h-[90vh] overflow-y-auto"
        role="dialog"
        aria-modal="true"
        aria-label="Programar presentación"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 pt-6 pb-4 border-b border-gray-100">
          <h2 className="text-2xl font-bold text-gray-900 tracking-tight">
            {editTarget ? "Editar presentación" : "Programar presentación"}
          </h2>
          <button
            onClick={onClose}
            className="p-2 rounded-lg text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition-colors"
            aria-label="Cerrar"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="px-6 py-5 space-y-5">
          {error && (
            <p className="text-sm text-red-600 font-semibold">{error}</p>
          )}

          {/* Project combobox */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-1.5">
              Proyecto / Tesis
            </label>
            <div className="relative">
              <button
                ref={projectTriggerRef}
                type="button"
                onClick={() => setProjectOpen((o) => !o)}
                className={`w-full flex items-center gap-2 px-4 py-2.5 rounded-xl border bg-white text-sm font-medium text-left transition-all ${
                  projectOpen
                    ? "border-blue-400 ring-4 ring-blue-100/50"
                    : "border-gray-200 hover:border-gray-300"
                }`}
                disabled={loadingData}
              >
                <span className={`flex-1 truncate ${selectedProject ? "text-gray-900" : "text-gray-400"}`}>
                  {loadingData
                    ? "Cargando proyectos..."
                    : selectedProject
                    ? `${selectedProject.title} — ${selectedProject.student} (${selectedProject.type === "tesis" ? "TEG" : "PTEG"})`
                    : "Buscar proyecto o tesis..."}
                </span>
                <ChevronDown
                  className={`w-4 h-4 text-gray-400 flex-shrink-0 transition-transform ${projectOpen ? "rotate-180" : ""}`}
                />
              </button>

              {projectOpen && (
                <div
                  ref={projectDropdownRef}
                  className="absolute left-0 right-0 top-full mt-1 z-50 bg-white border border-gray-200 rounded-xl shadow-xl overflow-hidden animate-in fade-in slide-in-from-top-1 duration-150"
                >
                  <div className="flex items-center gap-2 px-3 py-2 border-b border-gray-100">
                    <Search className="w-4 h-4 text-gray-400 flex-shrink-0" />
                    <input
                      ref={projectInputRef}
                      type="text"
                      value={projectQuery}
                      onChange={(e) => setProjectQuery(e.target.value)}
                      placeholder="Buscar por título o estudiante..."
                      className="flex-1 text-sm outline-none bg-transparent placeholder:text-gray-400"
                    />
                    {projectQuery && (
                      <button type="button" onClick={() => setProjectQuery("")}>
                        <X className="w-3.5 h-3.5 text-gray-400 hover:text-gray-600" />
                      </button>
                    )}
                  </div>
                  <div className="max-h-52 overflow-y-auto overscroll-contain">
                    {filteredProjects.length === 0 ? (
                      <div className="px-3 py-4 text-center text-sm text-gray-400">
                        Sin proyectos disponibles
                      </div>
                    ) : (
                      filteredProjects.map((p) => {
                        const isSelected = p.id === projectId;
                        return (
                          <button
                            key={p.id}
                            type="button"
                            onClick={() => handleSelectProject(p.id)}
                            className={`w-full flex items-center gap-2 px-3 py-2.5 text-sm text-left transition-colors ${
                              isSelected
                                ? "bg-blue-50 text-blue-700 font-semibold"
                                : "text-gray-700 hover:bg-gray-50"
                            }`}
                          >
                            <span className="flex-1 truncate">
                              {p.title} — {p.student}{" "}
                              <span className="text-xs text-gray-400">
                                ({p.type === "tesis" ? "TEG" : "PTEG"})
                              </span>
                            </span>
                            {isSelected && (
                              <Check className="w-4 h-4 text-blue-500 flex-shrink-0" />
                            )}
                          </button>
                        );
                      })
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Auto-fill summary panel */}
          {selectedProject && (
            <div className="bg-blue-50/50 rounded-xl border border-blue-100 p-4 text-sm space-y-1.5">
              <div className="flex gap-2">
                <span className="text-gray-500 w-24 flex-shrink-0">Estudiante:</span>
                <span className="font-semibold text-gray-900">{selectedProject.student}</span>
              </div>
              <div className="flex gap-2">
                <span className="text-gray-500 w-24 flex-shrink-0">Tipo:</span>
                <span className="font-semibold text-gray-900">
                  {selectedProject.type === "tesis" ? "Tesis (TEG)" : "Proyecto (PTEG)"}
                </span>
              </div>
              {selectedProject.advisorNames && selectedProject.advisorNames.length > 0 && (
                <div className="flex gap-2">
                  <span className="text-gray-500 w-24 flex-shrink-0">Tutor:</span>
                  <span className="font-semibold text-gray-900">
                    {selectedProject.advisorNames[0]}
                  </span>
                </div>
              )}
            </div>
          )}

          {/* Jurado multi-select */}
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-1.5">
              Jurados{" "}
              <span className="text-gray-400 font-normal text-xs">(opcional)</span>
            </label>
            <div className="relative">
              <button
                ref={juradoTriggerRef}
                type="button"
                onClick={() => setJuradoOpen((o) => !o)}
                className={`w-full flex items-center gap-2 px-4 py-2.5 rounded-xl border bg-white text-sm font-medium text-left transition-all ${
                  juradoOpen
                    ? "border-blue-400 ring-4 ring-blue-100/50"
                    : "border-gray-200 hover:border-gray-300"
                }`}
                disabled={loadingData}
              >
                <span className="flex-1 text-gray-400">
                  {loadingData ? "Cargando jurados..." : "Agregar jurado..."}
                </span>
                <ChevronDown
                  className={`w-4 h-4 text-gray-400 flex-shrink-0 transition-transform ${juradoOpen ? "rotate-180" : ""}`}
                />
              </button>

              {juradoOpen && (
                <div
                  ref={juradoDropdownRef}
                  className="absolute left-0 right-0 top-full mt-1 z-50 bg-white border border-gray-200 rounded-xl shadow-xl overflow-hidden animate-in fade-in slide-in-from-top-1 duration-150"
                >
                  <div className="flex items-center gap-2 px-3 py-2 border-b border-gray-100">
                    <Search className="w-4 h-4 text-gray-400 flex-shrink-0" />
                    <input
                      ref={juradoInputRef}
                      type="text"
                      value={juradoQuery}
                      onChange={(e) => setJuradoQuery(e.target.value)}
                      placeholder="Buscar jurado..."
                      className="flex-1 text-sm outline-none bg-transparent placeholder:text-gray-400"
                    />
                    {juradoQuery && (
                      <button type="button" onClick={() => setJuradoQuery("")}>
                        <X className="w-3.5 h-3.5 text-gray-400 hover:text-gray-600" />
                      </button>
                    )}
                  </div>
                  <div className="max-h-48 overflow-y-auto overscroll-contain">
                    {filteredJurados.length === 0 ? (
                      <div className="px-3 py-4 text-center text-sm text-gray-400">
                        Sin jurados disponibles
                      </div>
                    ) : (
                      filteredJurados.map((u) => {
                        const isSelected = juradoIds.includes(u.id);
                        return (
                          <button
                            key={u.id}
                            type="button"
                            onClick={() => handleToggleJurado(u.id)}
                            className={`w-full flex items-center gap-2 px-3 py-2.5 text-sm text-left transition-colors ${
                              isSelected
                                ? "bg-blue-50 text-blue-700 font-semibold"
                                : "text-gray-700 hover:bg-gray-50"
                            }`}
                          >
                            <span className="flex-1 truncate">
                              {u.fullName} — {u.email}
                            </span>
                            {isSelected && (
                              <Check className="w-4 h-4 text-blue-500 flex-shrink-0" />
                            )}
                          </button>
                        );
                      })
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Selected jurado chips */}
            {selectedJuradoUsers.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-2">
                {selectedJuradoUsers.map((u) => (
                  <span
                    key={u.id}
                    className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-blue-50 text-blue-700 text-xs font-bold"
                  >
                    {u.fullName}
                    <button
                      type="button"
                      onClick={() => handleRemoveJurado(u.id)}
                      className="text-blue-400 hover:text-red-500 transition-colors"
                      aria-label={`Quitar jurado ${u.fullName}`}
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* Time + Duration */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1.5">
                Hora de inicio
              </label>
              <input
                type="time"
                value={startTime}
                onChange={(e) => setStartTime(e.target.value)}
                required
                className="w-full px-4 py-2.5 rounded-xl border border-gray-200 bg-white text-sm focus:bg-white focus:border-blue-400 focus:ring-4 focus:ring-blue-100/50 transition-all"
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1.5">
                Duración (min)
              </label>
              <input
                type="number"
                value={duration}
                onChange={(e) => setDuration(Number(e.target.value))}
                min={5}
                max={240}
                step={5}
                className="w-full px-4 py-2.5 rounded-xl border border-gray-200 bg-white text-sm focus:bg-white focus:border-blue-400 focus:ring-4 focus:ring-blue-100/50 transition-all"
              />
            </div>
          </div>

          {/* Footer */}
          <div className="flex justify-end gap-3 pt-2 border-t border-gray-100">
            <button
              type="button"
              onClick={onClose}
              className="px-5 py-2.5 rounded-xl text-sm font-semibold text-gray-600 hover:text-gray-900 hover:bg-gray-100 transition-all"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={saving}
              className="group relative px-5 py-2.5 rounded-xl text-sm font-bold bg-[#0f172a] text-white hover:bg-[#1e293b] transition-all shadow-lg shadow-slate-900/10 disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {saving ? "Guardando..." : "Guardar"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
