"use client";

import React, { use, useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import DashboardHeader from "@/components/layout/DashboardHeader";
import DocumentForm from "@/components/dashboard/DocumentForm";
import { Project } from "@/types/project";
import { getProject } from "@/features/projects/projectService";
import { ArrowLeft } from "lucide-react";

export default function EditarProyectoPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const router = useRouter();
  const { id } = use(params);
  const [project, setProject] = useState<Project | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (id) {
      (async () => {
        const apiProject = await getProject(parseInt(id));
        if (apiProject && apiProject.type === "proyecto") {
          setProject(apiProject as Project);
        }
      })();
    }
    setIsLoading(false);
  }, [id]);

  if (isLoading) {
    return (
      <div className="p-8 flex items-center justify-center">
        <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!project) {
    return (
      <div className="p-8 text-center text-gray-500">
        Proyecto no encontrado
      </div>
    );
  }

  return (
    <>
      <DashboardHeader pageTitle="Editar Proyecto" />
        
        <main className="flex-1 p-4 sm:p-6 lg:p-8 overflow-y-auto bg-gray-50">
          <div className="max-w-5xl mx-auto space-y-6">
            <button
              onClick={() => router.back()}
              className="flex items-center text-gray-600 hover:text-gray-900 transition-colors mb-2"
            >
              <ArrowLeft className="w-5 h-5 mr-2" />
              Volver
            </button>

            <DocumentForm
              mode="edit"
              forcedType="proyecto"
              initialData={project}
            />
          </div>
        </main>
        
    </>
  );
}
