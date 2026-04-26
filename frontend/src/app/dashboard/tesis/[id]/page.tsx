"use client";

import React from "react";
import { useParams } from "next/navigation";
import DashboardHeader from "@widgets/header/DashboardHeader";
import ProjectDetailView from "@features/projects/components/ProjectDetailView";
import { Project } from "@features/projects/types/project";
import { getProject } from "@features/projects/api/projectService";
import { getUser, getUserRole } from "@features/auth/api/clientAuth";
import type { Role } from "@features/projects/lib/cardAction";

export default function TesisDetailsPage() {
  const params = useParams();
  const id = Number(params.id);

  const role: Role = React.useMemo(
    () => (getUserRole() as Role | null) ?? "Estudiante",
    [],
  );
  const viewerId = React.useMemo<number | undefined>(() => {
    const u = getUser();
    return typeof u?.id === "number" ? u.id : undefined;
  }, []);

  const [project, setProject] = React.useState<Project | null>(null);

  React.useEffect(() => {
    let mounted = true;
    (async () => {
      const p = await getProject(id);
      if (mounted && p && p.type === "tesis") setProject(p);
    })();
    return () => {
      mounted = false;
    };
  }, [id]);

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
      <ProjectDetailView
        project={project}
        role={role}
        viewerId={viewerId}
        description=""
      />
    </>
  );
}
