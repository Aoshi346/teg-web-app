"use client";

import * as React from "react";
import CommentsSection from "@features/projects/components/CommentsSection";
import type { Project } from "@features/projects/types/project";

export interface CommentsTabProps {
  project: Project;
}

export function CommentsTab({ project }: CommentsTabProps) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-8">
      <div className="space-y-5">
        <div className="dsec">
          <div className="dsec-head">
            <h3 className="dsec-title">Conversación del proyecto</h3>
          </div>
          <CommentsSection projectId={project.id} />
        </div>
      </div>
      <aside className="space-y-4">
        <div className="dsec">
          <div className="dsec-head"><h3 className="dsec-title">Visibilidad</h3></div>
          <p className="text-[11.5px] text-text-muted font-medium leading-relaxed">
            Los comentarios son visibles para el estudiante, el tutor y el jurado asignados.
          </p>
        </div>
      </aside>
    </div>
  );
}
