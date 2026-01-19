"use client";

import React, { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Calendar, Clock, XCircle, Pencil } from "lucide-react";
import { Project } from "@/lib/data/mockData";

interface ProjectCardProps {
  project: Project;
  primaryHref?: string;
  primaryLabel?: string;
  className?: string;
  type?: "proyecto" | "tesis";
}

export default function ProjectCard({
  project,
  primaryHref,
  primaryLabel,
  className,
  type = "proyecto",
}: ProjectCardProps) {
  const router = useRouter();

  // Prefetch the target route on mount for instant navigation
  useEffect(() => {
    if (primaryHref) {
      router.prefetch(primaryHref);
    }
  }, [primaryHref, router]);

  const handlePrimary = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (primaryHref) router.push(primaryHref);
  };

  const handleEdit = (e: React.MouseEvent) => {
    e.stopPropagation();
    // Navigate to edit page (even if it doesn't exist yet, this is the correct route pattern)
    // Assuming /dashboard/proyectos/[id]/editar or /dashboard/tesis/[id]/editar
    const baseUrl =
      type === "tesis" ? "/dashboard/tesis" : "/dashboard/proyectos";
    router.push(`${baseUrl}/${project.id}/editar`);
  };

  const getStatusConfig = () => {
    switch (project.status) {
      case "checked":
        return {
          wrapper: "hover:border-emerald-300 hover:shadow-emerald-500/10",
          title: "group-hover:text-emerald-700",
          ringGradient: ["#10B981", "#34D399"], // Emerald 500 -> 400
          scoreText: "text-emerald-600",
          button:
            "bg-gradient-to-r from-emerald-500 to-teal-500 text-white shadow-lg shadow-emerald-500/30 hover:shadow-emerald-500/40 hover:-translate-y-0.5 border-transparent",
          iconBg: "bg-emerald-50 text-emerald-600",
        };
      case "pending":
        return {
          wrapper: "hover:border-amber-300 hover:shadow-amber-500/10",
          title: "group-hover:text-amber-700",
          ringGradient: ["#F59E0B", "#FBBF24"], // Amber 500 -> 400
          scoreText: "text-amber-600",
          button:
            "bg-gradient-to-r from-amber-500 to-orange-500 text-white shadow-lg shadow-amber-500/30 hover:shadow-amber-500/40 hover:-translate-y-0.5 border-transparent",
          iconBg: "bg-amber-50 text-amber-600",
        };
      case "rejected":
        return {
          wrapper: "hover:border-red-300 hover:shadow-red-500/10",
          title: "group-hover:text-red-700",
          ringGradient: ["#EF4444", "#F87171"], // Red 500 -> 400
          scoreText: "text-red-600",
          button:
            "bg-gradient-to-r from-red-600 to-rose-600 text-white shadow-lg shadow-red-500/30 hover:shadow-red-500/40 hover:-translate-y-0.5 border-transparent",
          iconBg: "bg-red-50 text-red-600",
        };
      default:
        return {
          wrapper: "hover:border-blue-300 hover:shadow-blue-500/10",
          title: "group-hover:text-blue-700",
          ringGradient: ["#3B82F6", "#60A5FA"],
          scoreText: "text-blue-600",
          button:
            "bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg shadow-blue-500/30 hover:shadow-blue-500/40 hover:-translate-y-0.5 border-transparent",
          iconBg: "bg-blue-50 text-blue-600",
        };
    }
  };

  const config = getStatusConfig();
  const gradientId = `grad-${project.id}`; // Unique ID for SVG gradient

  // Helper to get initials
  const getInitials = (name: string) => {
    return name
      .split(" ")
      .map((n) => n[0])
      .slice(0, 2)
      .join("")
      .toUpperCase();
  };

  return (
    <div
      onClick={handlePrimary}
      // Reduced padding from p-6 to pi-5
      className={`project-card relative h-full flex flex-col bg-white rounded-3xl p-5 border border-gray-100 transition-all duration-300 shadow-sm hover:shadow-xl cursor-pointer group ${config.wrapper} ${className ?? ""}`}
    >
      {/* Edit Button (Absolute Top Right) */}
      <button
        onClick={handleEdit}
        className="absolute top-4 right-4 p-2 rounded-full bg-gray-50 text-gray-400 hover:bg-blue-50 hover:text-blue-600 transition-all duration-200 z-10 opacity-0 group-hover:opacity-100 transform translate-x-2 group-hover:translate-x-0"
        title="Editar Proyecto"
      >
        <Pencil className="w-4 h-4" />
      </button>

      {/* Header with Title and Score/Status */}
      <div className="flex items-start justify-between gap-3 mb-5 pr-8">
        <h4
          // Slightly smaller text and tighter leading
          className={`text-lg font-extrabold text-gray-900 leading-snug line-clamp-3 transition-colors duration-300 ${config.title}`}
          title={project.title}
        >
          {project.title}
        </h4>

        {/* Abstract Status Indicator - Circular for Score or Icon for others */}
        <div className="flex-shrink-0">
          {project.status === "checked" && typeof project.score === "number" ? (
            // Reduced size from w-16 h-16 to w-14 h-14
            <div className="relative w-14 h-14 flex items-center justify-center">
              <svg
                className="absolute inset-0 w-full h-full -rotate-90 drop-shadow-sm"
                viewBox="0 0 36 36"
              >
                <defs>
                  <linearGradient
                    id={gradientId}
                    x1="0%"
                    y1="0%"
                    x2="100%"
                    y2="100%"
                  >
                    <stop offset="0%" stopColor={config.ringGradient[0]} />
                    <stop offset="100%" stopColor={config.ringGradient[1]} />
                  </linearGradient>
                </defs>
                {/* Track */}
                <path
                  className="text-gray-100"
                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="3"
                />
                {/* Progress */}
                <path
                  stroke={`url(#${gradientId})`}
                  strokeDasharray={`${(project.score / 20) * 100}, 100`}
                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                  fill="none"
                  strokeWidth="3"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
              <div className="flex flex-col items-center justify-center leading-none">
                <span className={`text-lg font-bold ${config.scoreText}`}>
                  {project.score}
                </span>
                <span className="text-[9px] uppercase font-bold text-gray-400 mt-0.5">
                  /20
                </span>
              </div>
            </div>
          ) : (
            // Reduced size from w-14 h-14 to w-12 h-12
            <div
              className={`w-12 h-12 rounded-2xl flex items-center justify-center shadow-inner ${config.iconBg}`}
            >
              {project.status === "pending" && <Clock className="w-6 h-6" />}
              {project.status === "rejected" && <XCircle className="w-6 h-6" />}
              {!["pending", "rejected"].includes(project.status) && (
                <Calendar className="w-6 h-6" />
              )}
            </div>
          )}
        </div>
      </div>

      {/* Metadata Sections - Compact spacing */}
      <div className="flex-1 space-y-4 mb-6">
        {/* Student */}
        <div className="flex items-center gap-3 group/item">
          {/* Reduced avatar size from w-12 h-12 to w-10 h-10 */}
          <div className="w-10 h-10 rounded-xl bg-gray-50 border border-gray-100 flex items-center justify-center text-xs font-bold text-gray-500 group-hover/item:bg-white group-hover/item:shadow-md group-hover/item:scale-110 transition-all duration-300">
            {getInitials(project.student)}
          </div>
          <div>
            <p className="text-[10px] uppercase tracking-wider font-bold text-gray-400 mb-0.5">
              ESTUDIANTE
            </p>
            <p className="font-bold text-gray-900 text-sm">{project.student}</p>
          </div>
        </div>

        {/* Tutor */}
        <div className="flex items-center gap-3 group/item">
          <div className="w-10 h-10 rounded-xl bg-gray-50 border border-gray-100 flex items-center justify-center text-xs font-bold text-gray-500 group-hover/item:bg-white group-hover/item:shadow-md group-hover/item:scale-110 transition-all duration-300">
            {getInitials(project.advisor)}
          </div>
          <div>
            <p className="text-[10px] uppercase tracking-wider font-bold text-gray-400 mb-0.5">
              TUTOR
            </p>
            <p className="font-bold text-gray-900 text-sm">{project.advisor}</p>
          </div>
        </div>

        {/* Date */}
        <div className="flex items-center gap-3 group/item">
          <div className="w-10 h-10 rounded-xl bg-gray-50 border border-gray-100 flex items-center justify-center group-hover/item:bg-white group-hover/item:shadow-md group-hover/item:scale-110 transition-all duration-300">
            <Calendar className="w-4 h-4 text-gray-400" />
          </div>
          <div>
            <p className="text-[10px] uppercase tracking-wider font-bold text-gray-400 mb-0.5">
              {project.status === "rejected"
                ? "RECHAZADO"
                : project.reviewDate
                  ? "REVISADO"
                  : "ENTREGADO"}
            </p>
            <p className="font-bold text-gray-900 text-sm">
              {project.reviewDate ?? project.submittedDate}
            </p>
          </div>
        </div>
      </div>

      {/* Action Button - Slightly reduced padding */}
      <button
        onClick={handlePrimary}
        className={`mt-auto w-full py-3 rounded-xl text-sm font-bold border transition-all duration-300 active:scale-[0.98] ${config.button}`}
      >
        {primaryLabel ??
          (project.status === "checked"
            ? "Ver Detalles"
            : project.status === "pending"
              ? "Evaluar Proyecto"
              : "Ver Motivo")}
      </button>
    </div>
  );
}
