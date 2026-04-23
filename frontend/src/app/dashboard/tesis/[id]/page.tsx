"use client";

import React from "react";
import { useRouter, useParams } from "next/navigation";
import { Sparkles } from "lucide-react";
import DashboardHeader from "@widgets/header/DashboardHeader";
import ProjectDetailView from "@features/projects/components/ProjectDetailView";
import { Project } from "@features/projects/types/project";
import {
  getProject,
  getEvaluationsByProject,
  ApiEvaluation,
  uploadProjectFile,
  assignReviewer,
} from "@features/projects/api/projectService";
import { getUserRole, getJurados } from "@features/auth/api/clientAuth";
import type { User as AuthUser } from "@features/auth/api/clientAuth";

export default function TesisDetailsPage() {
  const router = useRouter();
  const params = useParams();
  const id = Number(params.id);
  const userRole = React.useMemo(() => getUserRole(), []);

  const [project, setProject] = React.useState<Project | null>(null);
  const [evaluations, setEvaluations] = React.useState<ApiEvaluation[]>([]);
  const [isUploading, setIsUploading] = React.useState(false);
  const [uploadError, setUploadError] = React.useState<string | null>(null);

  // Jurado assignment state
  const [showJuradoModal, setShowJuradoModal] = React.useState(false);
  const [juradoOptions, setJuradoOptions] = React.useState<{ id: number; label: string }[]>([]);
  const [selectedJuradoId, setSelectedJuradoId] = React.useState<number | "">("");
  const [isAssigningJurado, setIsAssigningJurado] = React.useState(false);
  const [juradoError, setJuradoError] = React.useState<string | null>(null);

  React.useEffect(() => {
    let mounted = true;
    (async () => {
      const p = await getProject(id);
      if (mounted && p && p.type === "tesis") {
        setProject(p);
        const evals = await getEvaluationsByProject(id);
        setEvaluations(evals.sort((a, b) => new Date(b.graded_at).getTime() - new Date(a.graded_at).getTime()));
      }
    })();
    return () => { mounted = false; };
  }, [id]);

  React.useEffect(() => {
    if (userRole !== "Administrador" || !showJuradoModal) return;
    (async () => {
      const jurados = await getJurados();
      setJuradoOptions(
        jurados
          .filter((u: AuthUser) => typeof u.id === "number")
          .map((u: AuthUser) => ({ id: u.id!, label: u.fullName?.trim() ? u.fullName! : u.email })),
      );
    })();
  }, [userRole, showJuradoModal]);

  const handleAssignJurado = async () => {
    if (!selectedJuradoId || !project) return;
    setIsAssigningJurado(true);
    setJuradoError(null);
    try {
      await assignReviewer(id, selectedJuradoId as number);
      const refreshed = await getProject(id);
      if (refreshed) setProject(refreshed);
      setShowJuradoModal(false);
      setSelectedJuradoId("");
    } catch (err) {
      setJuradoError(err instanceof Error ? err.message : "Error al asignar jurado.");
    } finally {
      setIsAssigningJurado(false);
    }
  };

  const handleRemoveJurado = async () => {
    if (!project) return;
    setIsAssigningJurado(true);
    setJuradoError(null);
    try {
      await assignReviewer(id, null);
      const refreshed = await getProject(id);
      if (refreshed) setProject(refreshed);
      setShowJuradoModal(false);
      setSelectedJuradoId("");
    } catch (err) {
      setJuradoError(err instanceof Error ? err.message : "Error al quitar jurado.");
    } finally {
      setIsAssigningJurado(false);
    }
  };

  const handleFileUpload = async (file: File) => {
    setUploadError(null);
    setIsUploading(true);
    try {
      const uploaded = await uploadProjectFile(id, file);
      setProject((prev) => prev ? { ...prev, files: [...(prev.files || []), { name: uploaded.name, url: uploaded.url, type: uploaded.file_type, date: uploaded.date }] } : prev);
    } catch (error) {
      setUploadError(error instanceof Error ? error.message : "Error al subir.");
    } finally {
      setIsUploading(false);
    }
  };

  if (!project) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="w-8 h-8 rounded-full border-3 border-gray-200 border-t-emerald-600 animate-spin" />
      </div>
    );
  }

  return (
    <>
      <DashboardHeader pageTitle="Detalles de Tesis" />
        
        <main className="flex-1 p-4 sm:p-5 lg:p-6 overflow-y-auto bg-gray-50/50">
          <ProjectDetailView
            project={project}
            evaluations={evaluations}
            variant="tesis"
            userRole={userRole}
            onFileUpload={handleFileUpload}
            isUploading={isUploading}
            uploadError={uploadError}
            showJuradoModal={showJuradoModal}
            setShowJuradoModal={setShowJuradoModal}
            juradoOptions={juradoOptions}
            selectedJuradoId={selectedJuradoId}
            setSelectedJuradoId={setSelectedJuradoId}
            onAssignJurado={handleAssignJurado}
            onRemoveJurado={handleRemoveJurado}
            isAssigningJurado={isAssigningJurado}
            juradoError={juradoError}
            actions={
              <>
                {project.status === "pending" && (
                  <button
                    onClick={() => router.push(`/dashboard/tesis/${project.id}/evaluar`)}
                    className="w-full sm:w-auto px-6 py-2.5 bg-gradient-to-r from-emerald-600 to-teal-600 text-white rounded-lg font-semibold text-sm hover:shadow-lg transition-all"
                  >
                    Evaluar Tesis
                  </button>
                )}
                {project.stage1Passed && (
                  <button
                    onClick={() => router.push(`/dashboard/tesis/${project.id}/evaluar/fase2`)}
                    className="w-full sm:w-auto px-6 py-2.5 bg-gradient-to-r from-violet-600 to-indigo-600 text-white rounded-lg font-semibold text-sm hover:shadow-lg transition-all flex items-center gap-1.5"
                  >
                    <Sparkles className="w-4 h-4" /> Evaluación Fase 2
                  </button>
                )}
              </>
            }
          />
        </main>
        
    </>
  );
}
