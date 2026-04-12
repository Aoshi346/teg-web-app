"use client";

import React, { useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  Calendar,
  Clock,
  CheckCircle,
  XCircle,
  Pencil,
  FileText,
  GraduationCap,
  ArrowRight,
} from "lucide-react";
import { Project } from "@/types/project";
import { cn } from "@/lib/utils";

interface ProjectCardProps {
  project: Project;
  primaryHref?: string;
  primaryLabel?: string;
  className?: string;
  type?: "proyecto" | "tesis";
  canEdit?: boolean;
}

const STATUS_LABELS: Record<string, string> = {
  checked: "Aprobado",
  pending: "Pendiente",
  rejected: "Rechazado",
  default: "En curso",
};

const STATUS_COLORS = {
  checked: {
    bg: "bg-emerald-50",
    text: "text-emerald-700",
    scoreRing: "text-emerald-500",
    scoreTrack: "text-gray-100",
    scoreText: "text-emerald-600",
    divider: "border-emerald-100",
    cta: "text-emerald-600 hover:text-emerald-700",
    ctaArrow: "group-hover:translate-x-0.5",
  },
  pending: {
    bg: "bg-amber-50",
    text: "text-amber-700",
    scoreRing: "text-amber-500",
    scoreTrack: "text-gray-100",
    scoreText: "text-amber-600",
    divider: "border-amber-100",
    cta: "text-amber-600 hover:text-amber-700",
    ctaArrow: "group-hover:translate-x-0.5",
  },
  rejected: {
    bg: "bg-red-50",
    text: "text-red-700",
    scoreRing: "text-red-500",
    scoreTrack: "text-gray-100",
    scoreText: "text-red-600",
    divider: "border-red-100",
    cta: "text-red-600 hover:text-red-700",
    ctaArrow: "group-hover:translate-x-0.5",
  },
  default: {
    bg: "bg-blue-50",
    text: "text-blue-700",
    scoreRing: "text-blue-500",
    scoreTrack: "text-gray-100",
    scoreText: "text-blue-600",
    divider: "border-blue-100",
    cta: "text-blue-600 hover:text-blue-700",
    ctaArrow: "group-hover:translate-x-0.5",
  },
};

export default function ProjectCard({
  project,
  primaryHref,
  primaryLabel,
  className,
  type = "proyecto",
  canEdit = true,
}: ProjectCardProps) {
  const router = useRouter();

  useEffect(() => {
    if (primaryHref) router.prefetch(primaryHref);
  }, [primaryHref, router]);

  const navigate = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (primaryHref) router.push(primaryHref);
  };

  const edit = (e: React.MouseEvent) => {
    e.stopPropagation();
    const base =
      type === "tesis" ? "/dashboard/tesis" : "/dashboard/proyectos";
    router.push(`${base}/${project.id}/editar`);
  };

  const statusKey =
    project.status === "checked" ||
    project.status === "pending" ||
    project.status === "rejected"
      ? project.status
      : "default";

  const colors = STATUS_COLORS[statusKey];

  const gradientId = `grad-${project.id}`;

  const dateLabel =
    statusKey === "rejected"
      ? "Rechazado"
      : project.reviewDate
      ? "Revisado"
      : "Entregado";

  const dateValue = project.reviewDate ?? project.submittedDate;

  return (
    <div
      onClick={navigate}
      role="article"
      aria-label={`${project.title} — ${STATUS_LABELS[statusKey]}`}
      className={cn(
        "group relative h-full flex flex-col bg-white rounded-xl",
        "border border-gray-200 shadow-sm",
        "hover:border-gray-300 hover:shadow-md",
        "transition-all duration-200 cursor-pointer",
        className
      )}
    >
      <div className="flex flex-col h-full p-5 gap-0">

        {/* ── Header row: status badge + edit icon ── */}
        <div className="flex items-center justify-between gap-3 mb-4">

          {/* Status badge — flat pill, no border */}
          <span
            className={cn(
              "inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full",
              "text-[10px] font-semibold uppercase tracking-wider",
              colors.bg,
              colors.text
            )}
          >
            {statusKey === "checked" && <CheckCircle className="w-2.5 h-2.5" />}
            {statusKey === "rejected" && <XCircle className="w-2.5 h-2.5" />}
            {STATUS_LABELS[statusKey]}
          </span>

          {/* Edit icon — always visible, muted but present */}
          {canEdit && (
            <button
              onClick={edit}
              aria-label="Editar proyecto"
              className={cn(
                "flex items-center justify-center w-7 h-7 rounded-md",
                "text-gray-400 hover:text-gray-700 hover:bg-gray-100",
                "transition-all duration-150"
              )}
            >
              <Pencil className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        {/* ── Title row + score ring ── */}
        <div className="flex items-start justify-between gap-3 mb-5">
          <h4
            className="text-[15px] font-bold text-gray-900 leading-snug line-clamp-2 flex-1 pr-2"
            title={project.title}
          >
            {project.title}
          </h4>

          {/* Score ring — always colored, status-matched */}
          {typeof project.score === "number" ? (
            <div className="relative w-11 h-11 flex-shrink-0 mt-0.5">
              <svg
                className="absolute inset-0 w-full h-full -rotate-90"
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
                    <stop offset="0%" stopColor={colors.scoreRing} />
                    <stop
                      offset="100%"
                      stopColor={colors.scoreRing.replace("500", "300")}
                    />
                  </linearGradient>
                </defs>
                <path
                  className={colors.scoreTrack}
                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                />
                <path
                  stroke={`url(#${gradientId})`}
                  strokeDasharray={`${(project.score / 20) * 100}, 100`}
                  d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                  fill="none"
                  strokeWidth="2"
                  strokeLinecap="round"
                />
              </svg>
              <div className="flex flex-col items-center justify-center absolute inset-0 leading-none">
                <span
                  className={cn("text-sm font-bold leading-none", colors.scoreText)}
                >
                  {project.score.toFixed(1)}
                </span>
                <span className="text-[7px] font-medium text-gray-300 leading-none mt-[2px]">
                  /20
                </span>
              </div>
            </div>
          ) : (
            /* Station icon chip — neutral gray */
            <div className="w-9 h-9 rounded-lg flex items-center justify-center bg-gray-50 flex-shrink-0 mt-0.5">
              {statusKey === "pending" && (
                <Clock className="w-4 h-4 text-gray-300" />
              )}
              {statusKey === "rejected" && (
                <XCircle className="w-4 h-4 text-gray-300" />
              )}
              {statusKey === "default" && (
                <Calendar className="w-4 h-4 text-gray-300" />
              )}
            </div>
          )}
        </div>

        {/* ── Metadata 2×2 grid — neutral icons, micro labels ── */}
        <div className="grid grid-cols-2 gap-x-4 gap-y-3 mb-5 flex-1">

          {/* Estudiante */}
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-md flex items-center justify-center bg-gray-50 flex-shrink-0">
              <GraduationCap className="w-3.5 h-3.5 text-gray-400" />
            </div>
            <div className="min-w-0">
              <p className="text-[9px] font-bold uppercase tracking-widest text-gray-400 leading-none mb-0.5">
                Estudiante
              </p>
              <p className="text-sm font-medium text-gray-800 leading-tight truncate">
                {project.student}
              </p>
            </div>
          </div>

          {/* Tutor */}
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-md flex items-center justify-center bg-gray-50 flex-shrink-0">
              <FileText className="w-3.5 h-3.5 text-gray-400" />
            </div>
            <div className="min-w-0">
              <p className="text-[9px] font-bold uppercase tracking-widest text-gray-400 leading-none mb-0.5">
                Tutor
              </p>
              <p className="text-sm font-medium text-gray-800 leading-tight truncate">
                {project.advisorNames?.[0] || "—"}
              </p>
            </div>
          </div>

          {/* Período */}
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-md flex items-center justify-center bg-gray-50 flex-shrink-0">
              <Clock className="w-3.5 h-3.5 text-gray-400" />
            </div>
            <div className="min-w-0">
              <p className="text-[9px] font-bold uppercase tracking-widest text-gray-400 leading-none mb-0.5">
                Período
              </p>
              <p className="text-sm font-medium text-gray-800 leading-tight">
                {project.period || "—"}
              </p>
            </div>
          </div>

          {/* Date */}
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-md flex items-center justify-center bg-gray-50 flex-shrink-0">
              <Calendar className="w-3.5 h-3.5 text-gray-400" />
            </div>
            <div className="min-w-0">
              <p className="text-[9px] font-bold uppercase tracking-widest text-gray-400 leading-none mb-0.5">
                {dateLabel}
              </p>
              <p className="text-sm font-medium text-gray-800 leading-tight">
                {dateValue}
              </p>
            </div>
          </div>
        </div>

        {/* ── Subtle CTA footer — card-level click target ── */}
        <div className={cn("mt-auto pt-4 border-t border-gray-100", colors.divider)}>
          <button
            onClick={navigate}
            aria-label={primaryLabel ?? "Ver detalles del proyecto"}
            className={cn(
              "flex items-center gap-1 text-[12px] font-semibold",
              "transition-all duration-150",
              colors.cta
            )}
          >
            <span>
              {primaryLabel ??
                (statusKey === "checked"
                  ? "Ver detalles"
                  : statusKey === "pending"
                  ? "Revisar ahora"
                  : "Ver detalles")}
            </span>
            <span
              className={cn(
                "transition-transform duration-150",
                colors.ctaArrow
              )}
            >
              <ArrowRight className="w-3.5 h-3.5" />
            </span>
          </button>
        </div>
      </div>
    </div>
  );
}
