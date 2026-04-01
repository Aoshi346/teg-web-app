"use client";

import React from "react";
import { useRouter } from "next/navigation";
import {
  ArrowLeft,
  Calendar,
  User,
  FileText,
  CheckCircle,
  XCircle,
  Clock,
  GraduationCap,
  AlertTriangle,
  RefreshCw,
  Upload,
  UserCog,
  MessageSquare,
  BookOpen,
  Sparkles,
} from "lucide-react";
import CommentsSection from "@/components/dashboard/CommentsSection";
import type { Project } from "@/types/project";
import type { ApiEvaluation } from "@/features/projects/projectService";

/* ─── Types ─── */
interface ProjectDetailViewProps {
  project: Project;
  evaluations: ApiEvaluation[];
  variant: "proyecto" | "tesis";
  userRole: string | null;
  /* File upload */
  onFileUpload: (file: File) => void;
  isUploading: boolean;
  uploadError: string | null;
  /* Reassign (proyecto only, admin) */
  showReassign?: boolean;
  setShowReassign?: (v: boolean) => void;
  studentOptions?: { id: number; label: string }[];
  selectedStudentId?: number | "";
  setSelectedStudentId?: (v: number | "") => void;
  onReassign?: () => void;
  isReassigning?: boolean;
  reassignError?: string | null;
  setReassignError?: (v: string | null) => void;
  /* Actions */
  actions?: React.ReactNode;
}

/* ─── Helpers ─── */
const STATUS_MAP = {
  checked: { bg: "bg-emerald-500", label: "Aprobado", Icon: CheckCircle },
  pending: { bg: "bg-amber-500", label: "Pendiente", Icon: Clock },
  rejected: { bg: "bg-rose-500", label: "Rechazado", Icon: XCircle },
} as const;

function StatusBadge({ status }: { status: string }) {
  const cfg = STATUS_MAP[status as keyof typeof STATUS_MAP] || STATUS_MAP.pending;
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold text-white ${cfg.bg}`}>
      <cfg.Icon className="w-3 h-3" />
      {cfg.label}
    </span>
  );
}

function InfoRow({ icon: Icon, label, value, color = "text-gray-900" }: { icon: React.ElementType; label: string; value: string; color?: string }) {
  return (
    <div className="flex items-center gap-2.5 py-2">
      <Icon className={`w-4 h-4 flex-shrink-0 ${color}`} />
      <span className="text-xs text-gray-500 font-medium w-24 flex-shrink-0">{label}</span>
      <span className="text-sm font-semibold text-gray-900 truncate">{value}</span>
    </div>
  );
}

function EvalComment({ ev }: { ev: ApiEvaluation }) {
  if (!ev.comments) return null;
  const text =
    typeof ev.comments === "string"
      ? ev.comments
      : String((ev.comments as Record<string, unknown>).general || "");
  if (!text.trim()) return null;
  return (
    <div className="mt-2 p-2.5 bg-amber-50/60 rounded-lg border border-amber-200 text-xs">
      <div className="flex items-center gap-1.5 mb-1">
        <MessageSquare className="w-3 h-3 text-amber-600" />
        <span className="font-bold text-amber-900 uppercase tracking-wide text-[10px]">Comentario</span>
        {ev.reviewer_name && <span className="text-amber-700 font-medium">— {ev.reviewer_name}</span>}
      </div>
      <p className="whitespace-pre-wrap text-gray-700 leading-relaxed">{text}</p>
    </div>
  );
}

/* ─── Main Component ─── */
export default function ProjectDetailView({
  project,
  evaluations,
  variant,
  userRole,
  onFileUpload,
  isUploading,
  uploadError,
  showReassign,
  setShowReassign,
  studentOptions,
  selectedStudentId,
  setSelectedStudentId,
  onReassign,
  isReassigning,
  reassignError,
  setReassignError,
  actions,
}: ProjectDetailViewProps) {
  const router = useRouter();
  const isProyecto = variant === "proyecto";
  const accent = isProyecto ? "blue" : "emerald";
  const TypeIcon = isProyecto ? GraduationCap : BookOpen;

  const failedAttempts = project.failedAttempts || 0;
  const isFinalRejection = isProyecto && project.status === "rejected" && failedAttempts >= 2;
  const canRetry = isProyecto && project.status === "rejected" && failedAttempts < 2;

  return (
    <div className="max-w-6xl mx-auto space-y-4">
      {/* Back */}
      <button
        onClick={() => router.back()}
        className="flex items-center gap-1.5 text-gray-500 hover:text-gray-900 transition-colors group text-sm font-medium"
      >
        <ArrowLeft className="w-4 h-4 group-hover:-translate-x-0.5 transition-transform" />
        Volver
      </button>

      {/* ─── Top Bar: Title + Status + Score ─── */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
        <div className={`h-1 rounded-t-xl bg-gradient-to-r ${isProyecto ? "from-blue-500 to-sky-400" : "from-emerald-500 to-teal-400"}`} />
        <div className="p-4 sm:p-5">
          <div className="flex flex-col sm:flex-row sm:items-start gap-4">
            {/* Left: icon + title + badges */}
            <div className="flex items-start gap-3 flex-1 min-w-0">
              <div className={`p-2 rounded-lg bg-${accent}-50 text-${accent}-600 flex-shrink-0 mt-0.5`}>
                <TypeIcon className="w-5 h-5" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap mb-1">
                  <span className={`text-[10px] font-bold text-${accent}-600 uppercase tracking-wider`}>
                    {isProyecto ? "Proyecto" : "Tesis"} #{project.id}
                  </span>
                  <span className="text-[10px] text-gray-400">· {project.period}</span>
                </div>
                <h1 className="text-lg sm:text-xl font-bold text-gray-900 leading-tight mb-2">
                  {project.title}
                </h1>
                <div className="flex flex-wrap items-center gap-2">
                  <StatusBadge status={project.status} />
                  {isProyecto && (
                    <span className="text-[10px] font-semibold text-gray-500 bg-gray-100 px-2 py-0.5 rounded-full">
                      Intentos: {Math.min(failedAttempts, 2)}/2
                    </span>
                  )}
                  {isProyecto && canRetry && (
                    <span className="text-[10px] font-semibold text-amber-700 bg-amber-50 border border-amber-200 px-2 py-0.5 rounded-full flex items-center gap-1">
                      <RefreshCw className="w-3 h-3" /> Puede reintentar
                    </span>
                  )}
                  {isProyecto && isFinalRejection && (
                    <span className="text-[10px] font-semibold text-gray-500 bg-gray-100 border border-gray-200 px-2 py-0.5 rounded-full flex items-center gap-1">
                      <AlertTriangle className="w-3 h-3" /> Finalizado
                    </span>
                  )}
                  {!isProyecto && project.stage1Passed !== undefined && (
                    <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full flex items-center gap-1 ${project.stage1Passed ? "text-emerald-700 bg-emerald-50 border border-emerald-200" : "text-amber-700 bg-amber-50 border border-amber-200"}`}>
                      {project.stage1Passed ? <CheckCircle className="w-3 h-3" /> : <Clock className="w-3 h-3" />}
                      Fase 1: {project.stage1Passed ? "Aprobada" : "Pendiente"}
                    </span>
                  )}
                </div>
              </div>
            </div>

            {/* Right: Score card (compact) */}
            {project.score !== undefined && project.score > 0 && (
              <div className={`flex-shrink-0 rounded-xl p-3 text-center border ${project.score >= 10 ? "bg-emerald-50 border-emerald-200" : "bg-rose-50 border-rose-200"}`}>
                <div className="flex items-baseline justify-center gap-0.5">
                  <span className={`text-3xl font-black ${project.score >= 10 ? "text-emerald-600" : "text-rose-600"}`}>
                    {project.score.toFixed(1)}
                  </span>
                  <span className="text-sm font-bold text-gray-400">/20</span>
                </div>
                {(project.diagramacionScore !== undefined || project.contenidoScore !== undefined) && (
                  <div className="mt-1.5 pt-1.5 border-t border-gray-200/60 flex gap-3 text-[10px]">
                    {project.diagramacionScore !== undefined && (
                      <span className="text-blue-600 font-bold">D: {project.diagramacionScore.toFixed(1)}/5</span>
                    )}
                    {project.contenidoScore !== undefined && (
                      <span className="text-purple-600 font-bold">C: {project.contenidoScore.toFixed(1)}/15</span>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ─── Content: 3-column grid ─── */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* Col 1: People */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4 space-y-3">
          <h3 className={`text-[10px] font-bold text-${accent}-600 uppercase tracking-widest`}>Personas</h3>

          {/* Student */}
          <div className="flex items-center gap-3">
            <div className={`w-9 h-9 rounded-lg bg-${accent}-100 text-${accent}-600 flex items-center justify-center text-sm font-bold flex-shrink-0`}>
              {project.student.charAt(0)}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold text-gray-900 truncate">{project.student}</p>
              <p className="text-[11px] text-gray-400">Estudiante</p>
            </div>
            {userRole === "Administrador" && setShowReassign && (
              <button onClick={() => setShowReassign(!showReassign)} className="p-1.5 text-purple-600 hover:bg-purple-50 rounded-lg transition-colors" title="Reasignar">
                <UserCog className="w-4 h-4" />
              </button>
            )}
          </div>

          {/* Reassign panel */}
          {showReassign && userRole === "Administrador" && setSelectedStudentId && onReassign && (
            <div className="pt-2 border-t border-gray-100 space-y-2">
              <select
                value={selectedStudentId}
                onChange={(e) => setSelectedStudentId(e.target.value ? Number(e.target.value) : "")}
                className="w-full px-2.5 py-2 bg-white border border-gray-200 rounded-lg text-sm focus:border-purple-500 focus:ring-2 focus:ring-purple-500/10"
              >
                <option value="">Seleccione estudiante</option>
                {studentOptions?.map((s) => <option key={s.id} value={s.id}>{s.label}</option>)}
              </select>
              <div className="flex gap-2">
                <button onClick={onReassign} disabled={!selectedStudentId || isReassigning} className="px-3 py-1.5 text-xs font-bold text-white bg-purple-600 hover:bg-purple-700 rounded-lg disabled:opacity-50">
                  {isReassigning ? "..." : "Confirmar"}
                </button>
                <button onClick={() => { setShowReassign?.(false); setReassignError?.(null); }} className="px-3 py-1.5 text-xs text-gray-600 hover:bg-gray-100 rounded-lg">
                  Cancelar
                </button>
              </div>
              {reassignError && <p className="text-[11px] text-red-600 font-semibold">{reassignError}</p>}
            </div>
          )}

          {/* Partner */}
          {project.partnerName && (
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-indigo-100 text-indigo-600 flex items-center justify-center text-sm font-bold flex-shrink-0">
                {project.partnerName.charAt(0)}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-gray-900 truncate">{project.partnerName}</p>
                <p className="text-[11px] text-gray-400">Compañero</p>
              </div>
            </div>
          )}

          {/* Advisors */}
          {project.advisorNames?.map((name, i) => (
            <div key={i} className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-teal-100 text-teal-600 flex items-center justify-center text-sm font-bold flex-shrink-0">
                {name.charAt(0)}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-gray-900 truncate">{name}</p>
                <p className="text-[11px] text-gray-400">Tutor {project.advisorNames!.length > 1 ? i + 1 : ""}</p>
              </div>
            </div>
          ))}

          {/* Dates — inline */}
          <div className="pt-2 border-t border-gray-100 space-y-1">
            <InfoRow icon={Calendar} label="Entrega" value={project.submittedDate} color="text-gray-400" />
            {project.reviewDate && <InfoRow icon={CheckCircle} label="Revisión" value={project.reviewDate} color="text-emerald-500" />}
          </div>
        </div>

        {/* Col 2: Files */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4 space-y-3">
          <h3 className="text-[10px] font-bold text-gray-500 uppercase tracking-widest">Documentos</h3>

          {project.files && project.files.length > 0 ? (
            <div className="space-y-1.5">
              {project.files.map((file, i) => (
                <a key={i} href={file.url} target="_blank" rel="noopener noreferrer" className="flex items-center gap-2.5 p-2.5 rounded-lg border border-gray-100 hover:border-blue-200 hover:bg-blue-50/50 transition-all group">
                  <div className={`p-1.5 rounded-lg ${file.type === "pdf" ? "bg-rose-100 text-rose-600" : "bg-blue-100 text-blue-600"}`}>
                    <FileText className="w-4 h-4" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate group-hover:text-blue-600">{file.name}</p>
                    <p className="text-[10px] text-gray-400">{file.type.toUpperCase()} · {file.date}</p>
                  </div>
                </a>
              ))}
            </div>
          ) : (
            <div className="p-4 border border-dashed border-gray-200 rounded-lg text-center">
              <FileText className="w-6 h-6 text-gray-300 mx-auto mb-1" />
              <p className="text-xs text-gray-400">Sin documentos</p>
            </div>
          )}

          {userRole === "Estudiante" && (
            <div className="pt-2">
              <input type="file" accept=".pdf,.doc,.docx" id={`upload-${project.id}`} className="hidden" onChange={(e) => { const f = e.target.files?.[0]; if (f) onFileUpload(f); }} />
              <label htmlFor={`upload-${project.id}`} className="flex items-center justify-center gap-1.5 w-full py-2 bg-gray-50 text-gray-600 text-sm font-semibold rounded-lg hover:bg-gray-100 border border-gray-200 cursor-pointer transition-colors">
                <Upload className="w-3.5 h-3.5" />
                {isUploading ? "Subiendo..." : "Subir archivo"}
              </label>
              {uploadError && <p className="text-[11px] text-red-600 font-semibold mt-1">{uploadError}</p>}
            </div>
          )}
        </div>

        {/* Col 3: Evaluation history */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4 space-y-3 md:col-span-2 lg:col-span-1">
          <h3 className="text-[10px] font-bold text-purple-600 uppercase tracking-widest">Evaluaciones</h3>

          {evaluations.length === 0 ? (
            <p className="text-xs text-gray-400 py-2">Sin evaluaciones registradas.</p>
          ) : (
            <div className="space-y-3">
              {evaluations.map((ev, idx) => (
                <div key={ev.id} className="border border-gray-100 rounded-lg p-3 bg-gray-50/50">
                  <div className="flex items-center justify-between gap-2 mb-1.5">
                    <div className="flex items-center gap-1.5">
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${ev.pass_status === "Pass" ? "bg-emerald-50 text-emerald-700 border border-emerald-200" : "bg-rose-50 text-rose-700 border border-rose-200"}`}>
                        {ev.pass_status === "Pass" ? "Aprobado" : "Rechazado"}
                      </span>
                      <span className="text-[10px] text-gray-400">{new Date(ev.graded_at).toLocaleDateString()}</span>
                    </div>
                    <span className="text-xs font-bold text-gray-900">{ev.score}/20</span>
                  </div>

                  {ev.section_scores && (
                    <div className="flex gap-2 text-[10px] mb-1.5">
                      {"diagramacion" in ev.section_scores && (
                        <span className="bg-white px-2 py-1 rounded border border-gray-100 text-blue-600 font-semibold">
                          D: {ev.section_scores.diagramacion}/5
                        </span>
                      )}
                      {"contenido" in ev.section_scores && (
                        <span className="bg-white px-2 py-1 rounded border border-gray-100 text-purple-600 font-semibold">
                          C: {ev.section_scores.contenido}/15
                        </span>
                      )}
                    </div>
                  )}

                  <EvalComment ev={ev} />

                  <p className="text-[10px] text-gray-400 mt-1.5">
                    {isProyecto ? `Intento ${idx + 1}/2` : `Evaluación #${idx + 1}`}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* ─── Actions ─── */}
      {actions && (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
          <div className="flex flex-col sm:flex-row items-center justify-end gap-3">
            {actions}
          </div>
        </div>
      )}

      {/* ─── Comments ─── */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        <CommentsSection projectId={project.id} />
      </div>
    </div>
  );
}
