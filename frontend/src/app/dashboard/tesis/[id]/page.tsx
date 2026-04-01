"use client";

import React from "react";
import { useRouter, useParams } from "next/navigation";
import CommentsSection from "@/components/dashboard/CommentsSection";
import {
  ArrowLeft,
  Calendar,
  User,
  FileText,
  CheckCircle,
  XCircle,
  Clock,
  GraduationCap,
  BookOpen,
  Sparkles,
  Upload,
} from "lucide-react";
import DashboardHeader from "@/components/layout/DashboardHeader";
import PageTransition from "@/components/ui/PageTransition";
import { Project } from "@/types/project";
import {
  getProject,
  getEvaluationsByProject,
  ApiEvaluation,
  uploadProjectFile,
} from "@/features/projects/projectService";
import { getUserRole } from "@/features/auth/clientAuth";

export default function TesisDetailsPage() {
  const router = useRouter();
  const params = useParams();
  const id = Number(params.id);
  const userRole = React.useMemo(() => getUserRole(), []);

  const [project, setProject] = React.useState<Project | null>(null);
  const [evaluations, setEvaluations] = React.useState<ApiEvaluation[]>([]);
  const [isUploading, setIsUploading] = React.useState(false);
  const [uploadError, setUploadError] = React.useState<string | null>(null);

  React.useEffect(() => {
    let mounted = true;
    (async () => {
      const apiProject = await getProject(id);
      if (mounted && apiProject && apiProject.type === "tesis") {
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
            Tesis no encontrada
          </h2>
          <p className="text-gray-500 mb-4">La tesis solicitada no existe.</p>
          <button
            onClick={() => router.back()}
            className="px-6 py-2 bg-emerald-600 text-white rounded-lg font-medium hover:bg-emerald-700 transition-colors"
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

  return (
    <>
      <DashboardHeader pageTitle="Detalles de Tesis" />
      <PageTransition>
        <main className="flex-1 p-4 md:p-8 overflow-y-auto bg-gradient-to-br from-slate-50 via-white to-emerald-50/30">
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
                <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-emerald-500 via-teal-500 to-cyan-500" />

                <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-6">
                  {/* Title and Status */}
                  <div className="flex-1 min-w-0">
                    {/* Thesis Label */}
                    <div className="flex items-center gap-3 mb-4">
                      <div className="p-2.5 bg-gradient-to-br from-emerald-500 to-teal-500 rounded-xl text-white shadow-lg shadow-emerald-500/25">
                        <BookOpen className="w-5 h-5" />
                      </div>
                      <div>
                        <span className="text-xs font-bold text-emerald-600 uppercase tracking-wider">
                          Tesis #{project.id}
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

                      {project.stage1Passed !== undefined && (
                        <div
                          className={`inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-semibold ${
                            project.stage1Passed
                              ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                              : "bg-amber-50 text-amber-700 border border-amber-200"
                          }`}
                        >
                          {project.stage1Passed ? (
                            <CheckCircle className="w-4 h-4" />
                          ) : (
                            <Clock className="w-4 h-4" />
                          )}
                          <span>
                            Fase 1:{" "}
                            {project.stage1Passed ? "Aprobada" : "Pendiente"}
                          </span>
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
                      <h3 className="text-xs font-bold text-emerald-600 uppercase tracking-wider mb-4 flex items-center gap-2">
                        <User className="w-4 h-4" />
                        Información del Estudiante
                      </h3>
                      <div className="flex items-center gap-4">
                        <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-500 flex items-center justify-center text-white text-xl font-bold shadow-lg shadow-emerald-500/25">
                          {project.student.charAt(0)}
                        </div>
                        <div>
                          <p className="font-bold text-gray-900 text-lg">
                            {project.student}
                          </p>
                          <p className="text-sm text-gray-500">Estudiante</p>
                        </div>
                      </div>
                    </div>

                    {/* Advisor Info */}
                    <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm hover:shadow-md transition-shadow">
                      <h3 className="text-xs font-bold text-teal-600 uppercase tracking-wider mb-4 flex items-center gap-2">
                        <GraduationCap className="w-4 h-4" />
                        Tutor Académico
                      </h3>
                      <div className="flex items-center gap-4">
                        <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-teal-500 to-cyan-500 flex items-center justify-center text-white text-xl font-bold shadow-lg shadow-teal-500/25">
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
                      <h3 className="text-xs font-bold text-cyan-600 uppercase tracking-wider mb-4 flex items-center gap-2">
                        <Calendar className="w-4 h-4" />
                        Fechas Importantes
                      </h3>
                      <div className="space-y-3">
                        <div className="flex items-center justify-between p-3 bg-gray-50 rounded-xl">
                          <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-xl bg-cyan-100 flex items-center justify-center">
                              <Calendar className="w-5 h-5 text-cyan-600" />
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
                              <div className="w-10 h-10 rounded-xl bg-cyan-100 flex items-center justify-center">
                                <CheckCircle className="w-5 h-5 text-cyan-600" />
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
                              className="flex items-center gap-3 p-3 bg-gray-50 rounded-xl hover:bg-emerald-50 border border-transparent hover:border-emerald-200 transition-all group"
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
                                <p className="font-semibold text-gray-900 truncate group-hover:text-emerald-600 transition-colors">
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

                      {/* Upload Button for Students */}
                      {userRole === "Estudiante" && (
                        <div className="mt-4 space-y-2">
                          <input
                            type="file"
                            id="file-upload"
                            accept="application/pdf"
                            className="hidden"
                            onChange={(e) => {
                              const file = e.target.files?.[0];
                              if (file) {
                                handleFileUpload(file);
                              }
                            }}
                          />
                          <label
                            htmlFor="file-upload"
                            className="flex items-center justify-center gap-2 w-full py-2.5 bg-gray-50 text-gray-700 font-semibold rounded-xl hover:bg-gray-100 border border-gray-200 cursor-pointer transition-colors"
                          >
                            <Upload className="w-4 h-4" />
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
                    {project.type === "tesis" && (
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
                                  <div className="mt-3 p-3.5 bg-amber-50/60 rounded-lg border border-amber-200 text-sm">
                                    <div className="flex items-center gap-2 mb-1.5">
                                      <svg className="w-4 h-4 text-amber-600 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" /></svg>
                                      <span className="font-bold text-amber-900 text-xs uppercase tracking-wide">
                                        Comentarios del evaluador
                                      </span>
                                      {ev.reviewer_name && (
                                        <span className="text-[11px] text-amber-700 font-medium">
                                          — {ev.reviewer_name}
                                        </span>
                                      )}
                                    </div>
                                    <p className="whitespace-pre-wrap text-gray-700 leading-relaxed">
                                      {typeof ev.comments === "string"
                                        ? ev.comments
                                        : (
                                            ev.comments as Record<
                                              string,
                                              string
                                            >
                                          ).general || "Sin comentarios"}
                                    </p>
                                  </div>
                                )}
                                <div className="mt-2 text-xs text-gray-500">
                                  Evaluación #{idx + 1}
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
                        router.push(`/dashboard/tesis/${project.id}/evaluar`)
                      }
                      className="w-full sm:w-auto px-8 py-3 bg-gradient-to-r from-emerald-600 to-teal-600 text-white rounded-xl font-semibold hover:from-emerald-700 hover:to-teal-700 transition-all shadow-lg shadow-emerald-500/25 hover:shadow-xl hover:shadow-emerald-500/30 transform hover:-translate-y-0.5"
                    >
                      Evaluar Tesis
                    </button>
                  )}

                  {project.stage1Passed && (
                    <button
                      onClick={() =>
                        router.push(
                          `/dashboard/tesis/${project.id}/evaluar/fase2`,
                        )
                      }
                      className="w-full sm:w-auto px-8 py-3 bg-gradient-to-r from-violet-600 to-indigo-600 text-white rounded-xl font-semibold hover:from-violet-700 hover:to-indigo-700 transition-all shadow-lg shadow-violet-500/25 hover:shadow-xl hover:shadow-violet-500/30 transform hover:-translate-y-0.5 flex items-center justify-center gap-2"
                    >
                      <Sparkles className="w-5 h-5" />
                      Evaluación Fase 2
                    </button>
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
