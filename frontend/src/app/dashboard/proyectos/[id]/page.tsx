"use client";

import React from "react";
import { useRouter, useParams } from "next/navigation";
import { AlertTriangle, RefreshCw } from "lucide-react";
import DashboardHeader from "@/components/layout/DashboardHeader";
import PageTransition from "@/components/ui/PageTransition";
import ProjectDetailView from "@/components/dashboard/ProjectDetailView";
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
  const userRole = React.useMemo(() => getUserRole(), []);

  const [project, setProject] = React.useState<Project | null>(null);
  const [evaluations, setEvaluations] = React.useState<ApiEvaluation[]>([]);
  const [isUploading, setIsUploading] = React.useState(false);
  const [uploadError, setUploadError] = React.useState<string | null>(null);

  // Reassign state
  const [showReassign, setShowReassign] = React.useState(false);
  const [studentOptions, setStudentOptions] = React.useState<{ id: number; label: string }[]>([]);
  const [selectedStudentId, setSelectedStudentId] = React.useState<number | "">("");
  const [isReassigning, setIsReassigning] = React.useState(false);
  const [reassignError, setReassignError] = React.useState<string | null>(null);

  React.useEffect(() => {
    let mounted = true;
    (async () => {
      const p = await getProject(id);
      if (mounted && p && p.type === "proyecto") {
        setProject(p);
        const evals = await getEvaluationsByProject(id);
        setEvaluations(evals.sort((a, b) => new Date(b.graded_at).getTime() - new Date(a.graded_at).getTime()));
      }
    })();
    return () => { mounted = false; };
  }, [id]);

  React.useEffect(() => {
    if (userRole !== "Administrador" || !showReassign) return;
    (async () => {
      const users = await getAllUsers();
      setStudentOptions(
        users.filter((u: AuthUser) => u.role === "Estudiante" && typeof u.id === "number")
          .map((u: AuthUser) => ({ id: u.id!, label: u.fullName?.trim() ? u.fullName! : u.email })),
      );
    })();
  }, [userRole, showReassign]);

  const handleReassign = async () => {
    if (!selectedStudentId || !project) return;
    setIsReassigning(true);
    setReassignError(null);
    try {
      await reassignStudent(id, { student: selectedStudentId as number });
      const refreshed = await getProject(id);
      if (refreshed) setProject(refreshed);
      setShowReassign(false);
      setSelectedStudentId("");
    } catch (err) {
      setReassignError(err instanceof Error ? err.message : "Error al reasignar.");
    } finally {
      setIsReassigning(false);
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
        <div className="w-8 h-8 rounded-full border-3 border-gray-200 border-t-blue-600 animate-spin" />
      </div>
    );
  }

  const failedAttempts = project.failedAttempts || 0;
  const canRetry = project.status === "rejected" && failedAttempts < 2;
  const isFinalRejection = project.status === "rejected" && failedAttempts >= 2;

  return (
    <>
      <DashboardHeader pageTitle="Detalles del Proyecto" />
      <PageTransition>
        <main className="flex-1 p-4 sm:p-5 lg:p-6 overflow-y-auto bg-gray-50/50">
          <ProjectDetailView
            project={project}
            evaluations={evaluations}
            variant="proyecto"
            userRole={userRole}
            onFileUpload={handleFileUpload}
            isUploading={isUploading}
            uploadError={uploadError}
            showReassign={showReassign}
            setShowReassign={setShowReassign}
            studentOptions={studentOptions}
            selectedStudentId={selectedStudentId}
            setSelectedStudentId={setSelectedStudentId}
            onReassign={handleReassign}
            isReassigning={isReassigning}
            reassignError={reassignError}
            setReassignError={setReassignError}
            actions={
              <>
                {project.status === "pending" && (
                  <button
                    onClick={() => router.push(`/dashboard/proyectos/${project.id}/evaluar`)}
                    className="w-full sm:w-auto px-6 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-lg font-semibold text-sm hover:shadow-lg transition-all"
                  >
                    Evaluar Proyecto
                  </button>
                )}
                {canRetry && (
                  <button
                    onClick={() => router.push(`/dashboard/proyectos/${project.id}/evaluar`)}
                    className="w-full sm:w-auto px-6 py-2.5 bg-gradient-to-r from-amber-500 to-orange-500 text-white rounded-lg font-semibold text-sm hover:shadow-lg transition-all flex items-center gap-1.5"
                  >
                    <RefreshCw className="w-4 h-4" /> Evaluar Nuevamente
                  </button>
                )}
                {isFinalRejection && (
                  <span className="px-4 py-2.5 bg-gray-100 text-gray-500 rounded-lg font-semibold text-sm border border-gray-200 flex items-center gap-1.5">
                    <AlertTriangle className="w-4 h-4" /> Proyecto Finalizado
                  </span>
                )}
              </>
            }
          />
        </main>
      </PageTransition>
    </>
  );
}
