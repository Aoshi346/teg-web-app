"use client";

import React from "react";
import { useRouter, useParams } from "next/navigation";
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
  Sparkles,
  UserCog,
} from "lucide-react";
import DashboardHeader from "@/components/layout/DashboardHeader";
import PageTransition from "@/components/ui/PageTransition";
import CommentsSection from "@/components/dashboard/CommentsSection";
import { Project } from "@/types/project";
import {
  getProject,
  getEvaluationsByProject,
  ApiEvaluation,
  uploadProjectFile,
  reassignStudent,
} from "@/features/projects/projectService";
import { getUserRole, getAllUsers } from "@/features/auth/clientAuth";
import type { User as AuthUser } from "@/features/auth/clientAuth";

export default function ProyectoDetailsPage() {
  const router = useRouter();
  const params = useParams();
  const id = Number(params.id);

  const [project, setProject] = React.useState<Project | null>(null);
  const [evaluations, setEvaluations] = React.useState<ApiEvaluation[]>([]);
  const [isUploading, setIsUploading] = React.useState(false);
  const [uploadError, setUploadError] = React.useState<string | null>(null);
  const userRole = React.useMemo(() => getUserRole(), []);

  // Reassign student state (admin only)
  const [showReassign, setShowReassign] = React.useState(false);
  const [studentOptions, setStudentOptions] = React.useState<
    { id: number; label: string }[]
  >([]);
  const [selectedStudentId, setSelectedStudentId] = React.useState<number | "">(
    "",
  );
  const [isReassigning, setIsReassigning] = React.useState(false);
  const [reassignError, setReassignError] = React.useState<string | null>(null);

  React.useEffect(() => {
    let mounted = true;
    (async () => {
      const apiProject = await getProject(id);
      if (mounted && apiProject && apiProject.type === "proyecto") {
        setProject(apiProject);
        const evals = await getEvaluationsByProject(id);
        setEvaluations(
          evals.sort(
            (a, b) =>
              new Date(b.graded_at).getTime() - new Date(a.graded_at).getTime(),
          ),
        );
      }
    })();
    return () => {
      mounted = false;
    };
  }, [id]);

  // Load student options when admin opens reassign
  React.useEffect(() => {
    if (userRole !== "Administrador" || !showReassign) return;
    (async () => {
      const users = await getAllUsers();
      setStudentOptions(
        users
          .filter(
            (u: AuthUser) =>
              u.role === "Estudiante" && typeof u.id === "number",
          )
          .map((u: AuthUser) => ({
            id: u.id!,
            label: u.fullName?.trim() ? u.fullName! : u.email,
          })),
      );
    })();
  }, [userRole, showReassign]);

  const handleReassign = async () => {
    if (!selectedStudentId || !project) return;
    setIsReassigning(true);
    setReassignError(null);
    try {
      await reassignStudent(id, {
        student: selectedStudentId as number,
      });
      // Refresh the project with new student name
      const refreshed = await getProject(id);
      if (refreshed) setProject(refreshed);
      setShowReassign(false);
      setSelectedStudentId("");
    } catch (err) {
      setReassignError(
        err instanceof Error ? err.message : "Error al reasignar estudiante.",
      );
    } finally {
      setIsReassigning(false);
    }
  };

  const handleFileUpload = async (file: File) => {
    setUploadError(null);
    setIsUploading(true);
    try {
      const uploaded = await uploadProjectFile(id, file);
      setProject((prev) => {
        if (!prev) return prev;
        const updatedFiles = [
          ...(prev.files || []),
          {
            name: uploaded.name,
            url: uploaded.url,
            type: uploaded.file_type,
            date: uploaded.date,
          },
        ];
        return { ...prev, files: updatedFiles };
      });
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Error al subir el archivo.";
      setUploadError(message);
    } finally {
      setIsUploading(false);
    }
  };

  if (!project) {
    return (
      <div className="flex items-center justify-center h-screen bg-gradient-to-br from-gray-50 to-gray-100">
        <div className="text-center bg-white p-8 rounded-2xl shadow-lg">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <XCircle className="w-8 h-8 text-red-500" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            Proyecto no encontrado
          </h2>
          <p className="text-gray-500 mb-4">
            El proyecto solicitado no existe.
          </p>
          <button
            onClick={() => router.back()}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors"
          >
            Volver
          </button>
        </div>
      </div>
    );
  }

  const getStatusConfig = () => {
    switch (project.status) {
      case "checked":
        return {
          bg: "bg-gradient-to-r from-emerald-500 to-teal-500",
          text: "text-white",
          icon: <CheckCircle className="w-4 h-4" />,
          label: "Aprobado",
        };
      case "pending":
        return {
          bg: "bg-gradient-to-r from-amber-400 to-orange-400",
          text: "text-white",
          icon: <Clock className="w-4 h-4" />,
          label: "Pendiente",
        };
      case "rejected":
        return {
          bg: "bg-gradient-to-r from-rose-500 to-red-500",
          text: "text-white",
          icon: <XCircle className="w-4 h-4" />,
          label: "Rechazado",
        };
      default:
        return {
          bg: "bg-gray-500",
          text: "text-white",
          icon: null,
          label: "Desconocido",
        };
    }
  };

  const statusConfig = getStatusConfig();
  const failedAttempts =
    project.failedAttempts || (project.status === "rejected" ? 1 : 0);
  const canRetry = project.status === "rejected" && failedAttempts < 2;
  const isFinalRejection = project.status === "rejected" && failedAttempts >= 2;
  const attemptsUsed = Math.min(
    project.failedAttempts || evaluations.length || 0,
    2,
  );

  return (
    <>
      <DashboardHeader pageTitle="Detalles del Proyecto" />
      <PageTransition>
        <main className="flex-1 p-4 md:p-8 overflow-y-auto bg-gradient-to-br from-slate-50 via-white to-blue-50/30">
          <div className="max-w-5xl mx-auto">
            {/* Back Button */}
            <button
              onClick={() => router.back()}
              className="flex items-center gap-2 text-gray-500 hover:text-gray-900 mb-6 transition-colors group"
            >
              <ArrowLeft className="w-5 h-5 group-hover:-translate-x-1 transition-transform" />
              <span className="font-medium">Volver</span>
            </button>

            {/* Main Card */}
            <div className="bg-white rounded-3xl shadow-2xl shadow-gray-200/50 border border-gray-100 overflow-hidden">
              {/* Header Section - Clean White with Colorful Accents */}
              <div className="relative p-6 md:p-8 border-b border-gray-100">
                {/* Decorative gradient accent */}
                <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-blue-400 via-sky-400 to-cyan-400" />

                <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-6">
                  {/* Title and Status */}
                  <div className="flex-1 min-w-0">
                    {/* Project Label */}
                    <div className="flex items-center gap-3 mb-4">
                      <div className="p-2.5 bg-gradient-to-br from-blue-400 to-sky-400 rounded-xl text-white shadow-lg shadow-blue-400/20">
                        <GraduationCap className="w-5 h-5" />
                      </div>
                      <div>
                        <span className="text-xs font-bold text-blue-600 uppercase tracking-wider">
                          Proyecto #{project.id}
                        </span>
                        <div className="flex items-center gap-2 text-gray-400 text-xs mt-0.5">
                          <Sparkles className="w-3 h-3" />
                          <span>Semestre {project.period}</span>
                        </div>
                      </div>
                    </div>

                    {/* Title */}
                    <h1 className="text-2xl md:text-3xl font-black text-gray-900 mb-5 leading-tight">
                      {project.title}
                    </h1>

                    {/* Status Badges Row */}
                    <div className="flex flex-wrap items-center gap-3">
                      <div
                        className={`inline-flex items-center gap-2 px-4 py-2 rounded-full ${statusConfig.bg} ${statusConfig.text} font-semibold text-sm shadow-lg`}
                      >
                        {statusConfig.icon}
                        <span>{statusConfig.label}</span>
                      </div>

                      {project.status === "rejected" && (
                        <div
                          className={`inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-semibold ${
                            isFinalRejection
                              ? "bg-gray-100 text-gray-600 border border-gray-200"
                              : "bg-amber-50 text-amber-700 border border-amber-200"
                          }`}
                        >
                          {isFinalRejection ? (
                            <AlertTriangle className="w-4 h-4" />
                          ) : (
                            <RefreshCw className="w-4 h-4" />
                          )}
                          <span>
                            {isFinalRejection
                              ? "Sin intentos (2/2)"
                              : `Intento ${failedAttempts}/2 - Puede reintentar`}
                          </span>
                        </div>
                      )}
                      {project.type === "proyecto" && (
                        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-100">
                          Intentos usados: {attemptsUsed}/2
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Score Card */}
                  {project.score !== undefined && (
                    <div className="flex-shrink-0">
                      <div
                        className={`rounded-2xl p-6 text-center min-w-[140px] border-2 ${
                          project.score >= 10
                            ? "bg-gradient-to-br from-emerald-50 to-teal-50 border-emerald-200"
                            : "bg-gradient-to-br from-rose-50 to-red-50 border-rose-200"
                        }`}
                      >
                        <span className="text-xs text-gray-500 font-bold uppercase tracking-wider block mb-1">
                          Calificación
                        </span>
                        <div className="flex items-baseline justify-center">
                          <span
                            className={`text-5xl font-black ${
                              project.score >= 10
                                ? "text-emerald-600"
                                : "text-rose-600"
                            }`}
                          >
                            {project.score.toFixed(2)}
                          </span>
                          <span className="text-xl font-bold text-gray-400 ml-1">
                            /20
                          </span>
                        </div>

                        {/* Section Scores */}
                        {(project.diagramacionScore !== undefined ||
                          project.contenidoScore !== undefined) && (
                          <div className="mt-4 pt-3 border-t border-gray-200 space-y-2">
                            {project.diagramacionScore !== undefined && (
                              <div className="flex items-center justify-between text-xs">
                                <span className="text-gray-500 font-medium">
                                  Diagramación
                                </span>
                                <span className="font-bold text-blue-600">
                                  {project.diagramacionScore.toFixed(2)}/5
                                </span>
                              </div>
                            )}
                            {project.contenidoScore !== undefined && (
                              <div className="flex items-center justify-between text-xs">
                                <span className="text-gray-500 font-medium">
                                  Contenido
                                </span>
                                <span className="font-bold text-purple-600">
                                  {project.contenidoScore.toFixed(2)}/15
                                </span>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Content Grid */}
              <div className="p-6 md:p-8 bg-gradient-to-b from-gray-50/50 to-white">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Left Column */}
                  <div className="space-y-5">
                    {/* Student Info */}
                    <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm hover:shadow-md transition-shadow">
                      <h3 className="text-xs font-bold text-blue-600 uppercase tracking-wider mb-4 flex items-center gap-2">
                        <User className="w-4 h-4" />
                        Información del Estudiante
                      </h3>
                      <div className="flex items-center gap-4">
                        <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-blue-400 to-sky-400 flex items-center justify-center text-white text-xl font-bold shadow-lg shadow-blue-400/20">
                          {project.student.charAt(0)}
                        </div>
                        <div className="flex-1">
                          <p className="font-bold text-gray-900 text-lg">
                            {project.student}
                          </p>
                          <p className="text-sm text-gray-500">Estudiante</p>
                        </div>
                        {userRole === "Administrador" && (
                          <button
                            onClick={() => setShowReassign(!showReassign)}
                            className="p-2 text-purple-600 hover:bg-purple-50 rounded-lg transition-colors"
                            title="Reasignar estudiante"
                          >
                            <UserCog className="w-5 h-5" />
                          </button>
                        )}
                      </div>
                      {showReassign && userRole === "Administrador" && (
                        <div className="mt-4 pt-4 border-t border-gray-100 space-y-3">
                          <label className="text-xs font-semibold text-purple-700 block">
                            Reasignar a otro estudiante
                          </label>
                          <select
                            value={selectedStudentId}
                            onChange={(e) =>
                              setSelectedStudentId(
                                e.target.value ? Number(e.target.value) : "",
                              )
                            }
                            className="w-full px-3 py-2.5 bg-white border border-gray-200 rounded-lg shadow-sm focus:border-purple-500 focus:ring-4 focus:ring-purple-500/10 transition-all text-sm font-medium"
                          >
                            <option value="">Seleccione un estudiante</option>
                            {studentOptions.map((s) => (
                              <option key={s.id} value={s.id}>
                                {s.label}
                              </option>
                            ))}
                          </select>
                          <div className="flex items-center gap-2">
                            <button
                              onClick={handleReassign}
                              disabled={!selectedStudentId || isReassigning}
                              className="px-4 py-2 text-xs font-bold text-white bg-purple-600 hover:bg-purple-700 rounded-lg shadow-sm transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                              {isReassigning ? "Reasignando..." : "Confirmar"}
                            </button>
                            <button
                              onClick={() => {
                                setShowReassign(false);
                                setReassignError(null);
                              }}
                              className="px-4 py-2 text-xs font-medium text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                            >
                              Cancelar
                            </button>
                          </div>
                          {reassignError && (
                            <p className="text-xs text-red-600 font-semibold">
                              {reassignError}
                            </p>
                          )}
                        </div>
                      )}
                    </div>

                    {/* Advisor Info */}
                    <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm hover:shadow-md transition-shadow">
                      <h3 className="text-xs font-bold text-sky-600 uppercase tracking-wider mb-4 flex items-center gap-2">
                        <GraduationCap className="w-4 h-4" />
                        Tutor Académico
                      </h3>
                      <div className="flex items-center gap-4">
                        <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-sky-400 to-blue-400 flex items-center justify-center text-white text-xl font-bold shadow-lg shadow-sky-400/20">
                          {(project.advisorNames?.[0] || "?").charAt(0)}
                        </div>
                        <div>
                          <p className="font-bold text-gray-900 text-lg">
                            {project.advisorNames?.[0] || "Sin tutor"}
                          </p>
                          <p className="text-sm text-gray-500">Tutor</p>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Right Column */}
                  <div className="space-y-5">
                    {/* Important Dates */}
                    <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm hover:shadow-md transition-shadow">
                      <h3 className="text-xs font-bold text-emerald-600 uppercase tracking-wider mb-4 flex items-center gap-2">
                        <Calendar className="w-4 h-4" />
                        Fechas Importantes
                      </h3>
                      <div className="space-y-3">
                        <div className="flex items-center justify-between p-3 bg-gray-50 rounded-xl">
                          <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-xl bg-emerald-100 flex items-center justify-center">
                              <Calendar className="w-5 h-5 text-emerald-600" />
                            </div>
                            <span className="text-gray-700 font-medium">
                              Fecha de Entrega
                            </span>
                          </div>
                          <span className="font-bold text-gray-900 bg-white px-3 py-1.5 rounded-lg text-sm border border-gray-200">
                            {project.submittedDate}
                          </span>
                        </div>
                        {project.reviewDate && (
                          <div className="flex items-center justify-between p-3 bg-gray-50 rounded-xl">
                            <div className="flex items-center gap-3">
                              <div className="w-10 h-10 rounded-xl bg-emerald-100 flex items-center justify-center">
                                <CheckCircle className="w-5 h-5 text-emerald-600" />
                              </div>
                              <span className="text-gray-700 font-medium">
                                Fecha de Revisión
                              </span>
                            </div>
                            <span className="font-bold text-gray-900 bg-white px-3 py-1.5 rounded-lg text-sm border border-gray-200">
                              {project.reviewDate}
                            </span>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Attached Files */}
                    <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm hover:shadow-md transition-shadow">
                      <h3 className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-4 flex items-center gap-2">
                        <FileText className="w-4 h-4" />
                        Documentos Adicionales
                      </h3>
                      {project.files && project.files.length > 0 ? (
                        <div className="space-y-3">
                          {project.files.map((file, index) => (
                            <a
                              key={index}
                              href={file.url}
                              className="flex items-center gap-3 p-3 bg-gray-50 rounded-xl hover:bg-blue-50 border border-transparent hover:border-blue-200 transition-all group"
                            >
                              <div
                                className={`p-2.5 rounded-xl ${
                                  file.type === "pdf"
                                    ? "bg-rose-100 text-rose-600"
                                    : "bg-blue-100 text-blue-600"
                                }`}
                              >
                                <FileText className="w-5 h-5" />
                              </div>
                              <div className="flex-1 min-w-0">
                                <p className="font-semibold text-gray-900 truncate group-hover:text-blue-600 transition-colors">
                                  {file.name}
                                </p>
                                <div className="flex items-center gap-2 text-xs text-gray-500">
                                  <span className="uppercase font-medium">
                                    {file.type}
                                  </span>
                                  <span>•</span>
                                  <span>{file.date}</span>
                                </div>
                              </div>
                            </a>
                          ))}
                        </div>
                      ) : (
                        <div className="p-6 border-2 border-dashed border-gray-200 rounded-xl text-center">
                          <FileText className="w-8 h-8 text-gray-300 mx-auto mb-2" />
                          <p className="text-sm text-gray-400 font-medium">
                            No hay documentos adjuntos.
                          </p>
                        </div>
                      )}

                      {userRole === "Estudiante" && (
                        <div className="mt-4 space-y-2">
                          <input
                            type="file"
                            accept="application/pdf"
                            id="project-file-upload"
                            className="hidden"
                            onChange={(e) => {
                              const file = e.target.files?.[0];
                              if (file) {
                                handleFileUpload(file);
                              }
                            }}
                          />
                          <label
                            htmlFor="project-file-upload"
                            className="flex items-center justify-center gap-2 w-full py-2.5 bg-gray-50 text-gray-700 font-semibold rounded-xl hover:bg-gray-100 border border-gray-200 cursor-pointer transition-colors"
                          >
                            {isUploading ? "Subiendo..." : "Subir Documento"}
                          </label>
                          {uploadError && (
                            <p className="text-xs text-red-600 font-semibold">
                              {uploadError}
                            </p>
                          )}
                        </div>
                      )}
                    </div>

                    {/* Evaluations History */}
                    {project.type === "proyecto" && (
                      <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm hover:shadow-md transition-shadow">
                        <h3 className="text-xs font-bold text-purple-600 uppercase tracking-wider mb-4 flex items-center gap-2">
                          <CheckCircle className="w-4 h-4" />
                          Historial de Evaluaciones
                        </h3>
                        {evaluations.length === 0 ? (
                          <p className="text-sm text-gray-500">
                            Aún no hay evaluaciones registradas.
                          </p>
                        ) : (
                          <div className="space-y-4">
                            {evaluations.map((ev, idx) => (
                              <div
                                key={ev.id}
                                className="border border-gray-100 rounded-xl p-4 bg-gray-50/70"
                              >
                                <div className="flex items-center justify-between gap-3">
                                  <div className="flex items-center gap-2">
                                    <div
                                      className={`px-3 py-1 rounded-full text-xs font-semibold ${
                                        ev.pass_status === "Pass"
                                          ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                                          : "bg-rose-50 text-rose-700 border border-rose-200"
                                      }`}
                                    >
                                      {ev.pass_status === "Pass"
                                        ? "Aprobado"
                                        : "Rechazado"}
                                    </div>
                                    <span className="text-xs text-gray-500">
                                      {new Date(
                                        ev.graded_at,
                                      ).toLocaleDateString()}
                                    </span>
                                  </div>
                                  <span className="text-sm font-bold text-gray-900">
                                    Puntaje: {ev.score}/20
                                  </span>
                                </div>
                                {ev.section_scores && (
                                  <div className="mt-3 grid grid-cols-2 gap-2 text-xs text-gray-600">
                                    {"diagramacion" in ev.section_scores && (
                                      <div className="flex items-center justify-between bg-white px-3 py-2 rounded-lg border border-gray-100">
                                        <span>Diagramación</span>
                                        <span className="font-semibold text-blue-600">
                                          {ev.section_scores.diagramacion}/5
                                        </span>
                                      </div>
                                    )}
                                    {"contenido" in ev.section_scores && (
                                      <div className="flex items-center justify-between bg-white px-3 py-2 rounded-lg border border-gray-100">
                                        <span>Contenido</span>
                                        <span className="font-semibold text-purple-600">
                                          {ev.section_scores.contenido}/15
                                        </span>
                                      </div>
                                    )}
                                  </div>
                                )}
                                {ev.comments && (
                                  <div className="mt-3 p-3 bg-white rounded-lg border border-gray-100 text-sm text-gray-700">
                                    <span className="font-semibold text-gray-900">
                                      Comentario:
                                    </span>
                                    <p className="mt-1 whitespace-pre-wrap">
                                      {typeof ev.comments === "string"
                                        ? ev.comments
                                        : String(
                                            (
                                              ev.comments as Record<
                                                string,
                                                unknown
                                              >
                                            ).general || "Sin comentarios",
                                          )}
                                    </p>
                                  </div>
                                )}
                                <div className="mt-2 text-xs text-gray-500">
                                  Intento {idx + 1}/2
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Action Footer */}
              <div className="p-6 bg-gray-50 border-t border-gray-100">
                <div className="flex flex-col sm:flex-row items-center justify-end gap-4">
                  {project.status === "pending" && (
                    <button
                      onClick={() =>
                        router.push(
                          `/dashboard/proyectos/${project.id}/evaluar`,
                        )
                      }
                      className="w-full sm:w-auto px-8 py-3 bg-gradient-to-r from-blue-500 to-sky-500 text-white rounded-xl font-semibold hover:from-blue-600 hover:to-sky-600 transition-all shadow-lg shadow-blue-400/20 hover:shadow-xl hover:shadow-blue-400/20 transform hover:-translate-y-0.5"
                    >
                      Evaluar Proyecto
                    </button>
                  )}
                  {canRetry && (
                    <div className="flex flex-col sm:flex-row items-center gap-3 w-full sm:w-auto">
                      <span className="text-sm text-amber-600 font-medium">
                        Puede ser re-evaluado
                      </span>
                      <button
                        onClick={() =>
                          router.push(
                            `/dashboard/proyectos/${project.id}/evaluar`,
                          )
                        }
                        className="w-full sm:w-auto px-8 py-3 bg-gradient-to-r from-amber-500 to-orange-500 text-white rounded-xl font-semibold hover:from-amber-600 hover:to-orange-600 transition-all shadow-lg shadow-amber-500/25 hover:shadow-xl transform hover:-translate-y-0.5"
                      >
                        Evaluar Nuevamente
                      </button>
                    </div>
                  )}
                  {isFinalRejection && (
                    <div className="px-6 py-3 bg-gray-100 text-gray-500 rounded-xl font-semibold border border-gray-200 cursor-not-allowed flex items-center gap-2">
                      <AlertTriangle className="w-5 h-5" />
                      Proyecto Finalizado (Reprobado)
                    </div>
                  )}
                </div>
              </div>
              <CommentsSection projectId={project.id} />
            </div>
          </div>
        </main>
      </PageTransition>
    </>
  );
}
