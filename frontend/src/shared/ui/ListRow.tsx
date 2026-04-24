"use client";

import * as React from "react";
import Link from "next/link";
import { ArrowRight } from "lucide-react";

import { cn } from "@shared/lib/utils";

type Status = "checked" | "pending" | "rejected" | "upcoming";

const STATUS_LABEL: Record<Status, string> = {
  checked: "Aprobado",
  pending: "Pendiente",
  rejected: "Rechazado",
  upcoming: "Próximo",
};

const STATUS_BADGE: Record<Status, string> = {
  checked: "bg-success/10 text-success border-success/22",
  pending: "bg-pending/10 text-pending border-pending/22",
  rejected: "bg-destructive/10 text-destructive border-destructive/22",
  upcoming: "bg-primary/10 text-primary border-primary/22",
};

const INDICATOR_BG: Record<Status, string> = {
  checked: "bg-success ring-success/22",
  pending: "bg-pending ring-pending/22",
  rejected: "bg-destructive ring-destructive/22",
  upcoming: "bg-primary ring-primary/22",
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

const SUBTITLE_SEP = " · ";

function renderSubtitle(subtitle: string): React.ReactNode {
  if (!subtitle.includes(SUBTITLE_SEP)) {
    return <span>{subtitle}</span>;
  }
  const parts = subtitle.split(SUBTITLE_SEP);
  return parts.map((part, i) => (
    <React.Fragment key={`${part}-${i}`}>
      {i > 0 && (
        <span
          aria-hidden
          className="mx-1 inline-block h-[3px] w-[3px] rounded-full bg-border-default align-middle"
        />
      )}
      <span>{part}</span>
    </React.Fragment>
  ));
}

export function ListRow({
  title,
  subtitle,
  status,
  hint,
  href,
  onClick,
  onHoverHref,
}: ListRowProps) {
  const inner = (
    <div className="flex flex-1 items-center gap-3 min-w-0">
      {status && (
        <span
          data-slot="list-row-indicator"
          aria-hidden
          className={cn(
            "h-2 w-2 flex-shrink-0 rounded-full ring-[3px]",
            INDICATOR_BG[status],
          )}
        />
      )}
      <div className="min-w-0 flex-1">
        <p className="truncate text-[13px] font-bold text-text-strong">{title}</p>
        {subtitle && (
          <p className="mt-0.5 truncate text-[11px] font-medium text-text-muted">
            {renderSubtitle(subtitle)}
          </p>
        )}
        {hint && <p className="mt-0.5 truncate text-[11px] text-primary">{hint}</p>}
      </div>
      {status && (
        <span
          className={cn(
            "rounded-full border px-2.5 py-0.5 text-[10px] font-extrabold tracking-wide",
            STATUS_BADGE[status],
          )}
        >
          {STATUS_LABEL[status]}
        </span>
      )}
      <ArrowRight
        aria-hidden
        className="h-4 w-4 flex-shrink-0 text-text-muted opacity-0 transition group-hover:translate-x-0.5 group-hover:opacity-100"
      />
    </div>
  );

  const className =
    "group flex items-center justify-between gap-3 rounded-xl border border-transparent px-3 py-2.5 transition hover:border-border-subtle hover:bg-surface-muted";

  if (href) {
    return (
      <Link
        href={href}
        onClick={onClick}
        onMouseEnter={onHoverHref}
        aria-label={`Abrir ${title}`}
        className={className}
      >
        {inner}
      </Link>
    );
  }
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label={`Abrir ${title}`}
      className={cn(className, "w-full text-left")}
    >
      {inner}
    </button>
  );
}
