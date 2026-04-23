"use client";

import * as React from "react";
import Link from "next/link";
import { ArrowRight, BookOpen, FileText } from "lucide-react";

import { cn } from "@shared/lib/utils";

type Status = "checked" | "pending" | "rejected" | "upcoming";

const STATUS_LABEL: Record<Status, string> = {
  checked: "Aprobado",
  pending: "Pendiente",
  rejected: "Rechazado",
  upcoming: "Próximo",
};

const STATUS_CLASS: Record<Status, string> = {
  checked: "bg-success-soft text-success border-success/20",
  pending: "bg-pending-soft text-pending border-pending/20",
  rejected: "bg-destructive-soft text-destructive border-destructive/20",
  upcoming: "bg-neutral-100 text-slate-700 border-slate-300/50",
};

export interface ListRowProps {
  title: string;
  subtitle?: string;
  type?: "proyecto" | "tesis";
  status?: Status;
  hint?: string;
  href?: string;
  onClick?: () => void;
  onHoverHref?: () => void;
}

export function ListRow({
  title,
  subtitle,
  type,
  status,
  hint,
  href,
  onClick,
  onHoverHref,
}: ListRowProps) {
  const isTeg = type === "tesis";
  const PillIcon = isTeg ? BookOpen : FileText;

  return (
    <div
      className="flex items-center gap-3 rounded-lg px-3 py-3 transition hover:bg-primary/5"
      onMouseEnter={onHoverHref}
    >
      {type && (
        <div
          data-slot="list-row-type"
          className={cn(
            "flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-lg border",
            isTeg
              ? "bg-[var(--accent-teg-soft-bg)] text-[var(--accent-teg-soft-fg)] border-[var(--accent-teg-soft-fg)]/15"
              : "bg-[var(--accent-pteg-soft-bg)] text-[var(--accent-pteg-soft-fg)] border-[var(--accent-pteg-soft-fg)]/15",
          )}
          aria-hidden
        >
          <PillIcon className="h-4 w-4" />
        </div>
      )}
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-semibold text-text-strong">{title}</p>
        {subtitle && <p className="truncate text-xs text-text-muted">{subtitle}</p>}
        {hint && <p className="truncate text-xs text-primary">{hint}</p>}
      </div>
      {status && (
        <span
          className={cn(
            "rounded-full border px-2.5 py-0.5 text-[11px] font-semibold",
            STATUS_CLASS[status],
          )}
        >
          {STATUS_LABEL[status]}
        </span>
      )}
      {href ? (
        <Link
          href={href}
          onClick={onClick}
          aria-label={`Abrir ${title}`}
          className="inline-flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-md text-text-muted transition hover:bg-primary/10 hover:text-primary"
        >
          <ArrowRight className="h-4 w-4" />
        </Link>
      ) : (
        <button
          type="button"
          onClick={onClick}
          aria-label={`Abrir ${title}`}
          className="inline-flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-md text-text-muted transition hover:bg-primary/10 hover:text-primary"
        >
          <ArrowRight className="h-4 w-4" />
        </button>
      )}
    </div>
  );
}
