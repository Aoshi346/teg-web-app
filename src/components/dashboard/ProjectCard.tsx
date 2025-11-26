"use client";

import React from "react";
import { useRouter } from "next/navigation";
import { User, FileText, Calendar } from "lucide-react";
import { Project } from "@/lib/data/mockData";

interface ProjectCardProps {
  project: Project;
  primaryHref?: string;
  primaryLabel?: string;
  className?: string;
}

export default function ProjectCard({ project, primaryHref, primaryLabel, className }: ProjectCardProps) {
  const router = useRouter();

  const handlePrimary = () => {
    if (primaryHref) router.push(primaryHref);
  };

  const statusBadge = () => {
    if (project.status === "checked") {
      return (
        <span className="ml-2 flex-shrink-0 px-3 py-1 bg-green-100 text-green-800 text-sm font-bold rounded-full">
          {typeof project.score === "number" ? project.score : "Revisado"}
        </span>
      );
    }

    if (project.status === "pending") {
      return (
        <span className="ml-2 flex-shrink-0 px-3 py-1 bg-amber-100 text-amber-800 text-xs font-semibold rounded-full">
          Pendiente
        </span>
      );
    }

    return (
      <span className="ml-2 flex-shrink-0 px-3 py-1 bg-red-100 text-red-800 text-xs font-semibold rounded-full">
        Rechazado
      </span>
    );
  };

  const getButtonStyles = () => {
    switch (project.status) {
      case "checked":
        return "bg-green-600 hover:bg-green-700 active:bg-green-800 text-white";
      case "pending":
        return "bg-amber-600 hover:bg-amber-700 active:bg-amber-800 text-white";
      case "rejected":
        return "bg-red-600 hover:bg-red-700 active:bg-red-800 text-white";
      default:
        return "bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white";
    }
  };

  const getCardHoverStyles = () => {
    switch (project.status) {
      case "checked":
        return "hover:border-green-300";
      case "pending":
        return "hover:border-amber-300";
      case "rejected":
        return "hover:border-red-300";
      default:
        return "hover:border-blue-300";
    }
  };

  const getTitleHoverStyles = () => {
    switch (project.status) {
      case "checked":
        return "group-hover:text-green-600";
      case "pending":
        return "group-hover:text-amber-600";
      case "rejected":
        return "group-hover:text-red-600";
      default:
        return "group-hover:text-blue-600";
    }
  };

  return (
    <div
      key={project.id}
      className={`project-card bg-white rounded-xl p-4 sm:p-6 shadow-md shadow-gray-900/5 border border-gray-200 hover:shadow-lg transition-all duration-200 cursor-pointer group ${getCardHoverStyles()} ${className ?? ""}`}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1 min-w-0">
          <h4 className={`text-base sm:text-lg font-bold text-gray-900 line-clamp-2 transition-colors ${getTitleHoverStyles()}`}>
            {project.title}
          </h4>
        </div>
        {statusBadge()}
      </div>

      <div className="space-y-2 text-sm text-gray-600">
        <div className="flex items-center gap-2">
          <User className="w-4 h-4 text-gray-400 flex-shrink-0" />
          <span className="truncate"><strong>Estudiante:</strong> {project.student}</span>
        </div>
        <div className="flex items-center gap-2">
          <FileText className="w-4 h-4 text-gray-400 flex-shrink-0" />
          <span className="truncate"><strong>Tutor:</strong> {project.advisor}</span>
        </div>
        <div className="flex items-center gap-2">
          <Calendar className="w-4 h-4 text-gray-400 flex-shrink-0" />
          <span><strong>{project.reviewDate ? (project.status === "rejected" ? 'Rechazado:' : 'Revisado:') : 'Entregado:'}</strong> {project.reviewDate ?? project.submittedDate}</span>
        </div>
      </div>

      <button
        onClick={handlePrimary}
        className={`mt-4 w-full py-2.5 rounded-lg text-sm font-semibold transition-all duration-200 shadow-md touch-manipulation ${getButtonStyles()}`}
      >
        {primaryLabel ?? (project.status === "checked" ? "Ver Detalles" : project.status === "pending" ? "Revisar Ahora" : "Ver Motivo")}
      </button>
    </div>
  );
}
