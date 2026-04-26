"use client";

import * as React from "react";
import { useRouter, useSearchParams } from "next/navigation";

import type { Project, ProjectState } from "@features/projects/types/project";
import {
  DetailHero,
  DetailTabs,
  InfoTab,
  EvaluationsTab,
  CommentsTab,
  FilesTab,
  HistoryTab,
  parseTabKey,
  type DetailTabKey,
  type DetailEvaluation,
} from "@features/projects/components/detail";
import StateOverrideModal from "@features/projects/components/StateOverrideModal";
import JuradoAssignModal from "@features/projects/components/JuradoAssignModal";
import StudentReassignModal from "@features/projects/components/StudentReassignModal";
import ProjectEditModal from "@features/projects/components/ProjectEditModal";
import {
  overrideProjectState,
  getProject,
  getEvaluationsByProject,
  uploadProjectFile,
} from "@features/projects/api/projectService";
import { cardAction, type Role } from "@features/projects/lib/cardAction";

export interface ProjectDetailViewProps {
  project: Project;
  role: Role;
  viewerId?: number;
  initialEvaluations?: DetailEvaluation[];
  description?: string;
}

export default function ProjectDetailView({
  project: initialProject,
  role,
  viewerId,
  initialEvaluations,
  description,
}: ProjectDetailViewProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const tab: DetailTabKey = parseTabKey(searchParams?.get("tab"));

  const [project, setProject] = React.useState<Project>(initialProject);
  const [evaluations, setEvaluations] = React.useState<DetailEvaluation[]>(
    initialEvaluations ?? [],
  );
  const [overrideOpen, setOverrideOpen] = React.useState(false);
  const [juradoOpen, setJuradoOpen] = React.useState(false);
  const [reassignOpen, setReassignOpen] = React.useState(false);
  const [editOpen, setEditOpen] = React.useState(false);

  const canEdit =
    role === "Administrador" ||
    (role === "Estudiante" &&
      project.state !== "approved" &&
      project.state !== "failed_final");
  const [isUploading, setIsUploading] = React.useState(false);
  const [uploadError, setUploadError] = React.useState<string | null>(null);

  const handleFileUpload = async (file: File) => {
    setUploadError(null);
    setIsUploading(true);
    try {
      const uploaded = await uploadProjectFile(project.id, file);
      setProject((prev) => prev ? {
        ...prev,
        files: [...(prev.files || []), {
          name: uploaded.name,
          url: uploaded.url,
          type: uploaded.file_type,
          date: uploaded.date,
        }],
      } : prev);
    } catch (error) {
      setUploadError(error instanceof Error ? error.message : "Error al subir.");
    } finally {
      setIsUploading(false);
    }
  };

  const evaluarHref = React.useMemo(() => {
    if (project.state === "approved" || project.state === "failed_final") return undefined;
    const action = cardAction(role, project, viewerId);
    return action.intent === "primary" ? action.href : undefined;
  }, [project, role, viewerId]);

  React.useEffect(() => {
    setProject(initialProject);
  }, [initialProject]);

  React.useEffect(() => {
    if (initialEvaluations) return;
    let mounted = true;
    (async () => {
      try {
        const list = await getEvaluationsByProject(project.id);
        if (mounted) setEvaluations(list as unknown as DetailEvaluation[]);
      } catch {
        if (mounted) setEvaluations([]);
      }
    })();
    return () => {
      mounted = false;
    };
  }, [project.id, initialEvaluations]);

  const onOverrideSubmit = async (payload: { state: ProjectState; reason: string }) => {
    const updated = await overrideProjectState(project.id, payload);
    setProject(updated);
    try {
      const fresh = await getProject(project.id);
      if (fresh) setProject(fresh);
    } catch {
      /* keep optimistic update */
    }
  };

  const setTab = (next: DetailTabKey) => {
    const sp = new URLSearchParams(searchParams?.toString() ?? "");
    if (next === "informacion") sp.delete("tab");
    else sp.set("tab", next);
    const qs = sp.toString();
    const base =
      project.type === "tesis"
        ? `/dashboard/tesis/${project.id}`
        : `/dashboard/proyectos/${project.id}`;
    router.replace(qs ? `${base}?${qs}` : base);
  };

  const counts: Partial<Record<DetailTabKey, number>> = {
    evaluaciones: evaluations.length,
    archivos: project.files?.length ?? 0,
  };

  return (
    <main className="flex-1 p-4 sm:p-6 lg:p-8 overflow-y-auto bg-surface-muted">
      <div className="max-w-screen-2xl mx-auto">
        <DetailHero
          project={project}
          role={role}
          viewerId={viewerId}
          onOverrideClick={role === "Administrador" ? () => setOverrideOpen(true) : undefined}
          onEditClick={canEdit ? () => setEditOpen(true) : undefined}
          evaluarHref={evaluarHref}
          onAssignJuradoClick={role === "Administrador" ? () => setJuradoOpen(true) : undefined}
          onReassignStudentClick={role === "Administrador" ? () => setReassignOpen(true) : undefined}
        />

        <DetailTabs active={tab} counts={counts} onChange={setTab} />

        <div className="mt-6">
          {tab === "informacion" && (
            <InfoTab project={project} description={description ?? ""} />
          )}
          {tab === "evaluaciones" && <EvaluationsTab evaluations={evaluations} />}
          {tab === "comentarios" && <CommentsTab project={project} />}
          {tab === "archivos" && (
            <FilesTab
              project={project}
              canUpload={role !== "Jurado"}
              onUpload={handleFileUpload}
              isUploading={isUploading}
              uploadError={uploadError}
            />
          )}
          {tab === "historial" && (
            <HistoryTab project={project} evaluations={evaluations} role={role} />
          )}
        </div>
      </div>

      <ProjectEditModal
        open={editOpen}
        project={project}
        onClose={() => setEditOpen(false)}
        onSuccess={(p) => setProject(p)}
      />

      {role === "Administrador" && (
        <>
          <StateOverrideModal
            open={overrideOpen}
            currentState={project.state}
            projectType={project.type ?? "proyecto"}
            onClose={() => setOverrideOpen(false)}
            onSubmit={onOverrideSubmit}
          />
          <JuradoAssignModal
            open={juradoOpen}
            project={project}
            onClose={() => setJuradoOpen(false)}
            onSuccess={(p) => setProject(p)}
          />
          <StudentReassignModal
            open={reassignOpen}
            project={project}
            onClose={() => setReassignOpen(false)}
            onSuccess={(p) => setProject(p)}
          />
        </>
      )}
    </main>
  );
}
