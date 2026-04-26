import * as React from "react";
import { cn } from "@shared/lib/utils";
import type { TimelineEvent, TimelineVariant } from "@features/projects/lib/buildStateTimeline";

const VARIANT_TO_DOT: Record<TimelineVariant, string> = {
  slate: "",
  amber: "is-warning",
  blue:  "is-primary",
  green: "is-success",
  red:   "is-danger",
};

function formatTimestamp(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleString("es-VE", {
    day: "2-digit", month: "short", year: "numeric",
    hour: "2-digit", minute: "2-digit",
  });
}

function PillFor({ event }: { event: TimelineEvent }) {
  if (event.kind === "evaluation" || event.kind === "state-transition") {
    return (
      <span className={cn("spill", `spill-${event.variant ?? "slate"}`)}>
        {event.label}
      </span>
    );
  }
  if (event.kind === "override") {
    return <span className="spill spill-amber">{event.label}</span>;
  }
  return (
    <span className="text-[10.5px] font-extrabold uppercase tracking-wider text-text-muted">
      {event.label}
    </span>
  );
}

export interface StateTimelineProps {
  events: TimelineEvent[];
  className?: string;
}

export function StateTimeline({ events, className }: StateTimelineProps) {
  if (events.length === 0) {
    return (
      <p className="text-[12.5px] text-text-muted font-medium">Sin actividad registrada todavía.</p>
    );
  }
  return (
    <ol className={cn("tline", className)}>
      {events.map((e) => (
        <li key={e.id} className="tline-item">
          <span
            className={cn(
              "tline-dot",
              e.variant && VARIANT_TO_DOT[e.variant],
              e.active && "is-active",
            )}
          >
            <span className="tline-dot-inner" />
          </span>
          <div className="flex items-center gap-2 flex-wrap">
            <PillFor event={e} />
            <span className="text-[11.5px] text-text-muted font-semibold ml-auto">
              {formatTimestamp(e.timestamp)}
            </span>
          </div>
          <p className="text-[12.5px] text-text-default font-medium mt-1.5 leading-relaxed">
            {e.body}
          </p>
        </li>
      ))}
    </ol>
  );
}
