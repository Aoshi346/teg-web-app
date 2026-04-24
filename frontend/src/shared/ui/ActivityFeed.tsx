"use client";

import * as React from "react";
import { CheckCircle, FileText, MessageSquare, XCircle } from "lucide-react";

import { cn } from "@shared/lib/utils";

type Kind = "submitted" | "reviewed" | "rejected" | "commented";

const KIND_ICON: Record<Kind, React.ComponentType<{ className?: string }>> = {
  submitted: FileText,
  reviewed: CheckCircle,
  rejected: XCircle,
  commented: MessageSquare,
};

const KIND_BG: Record<Kind, string> = {
  submitted: "bg-primary/10 text-primary",
  reviewed: "bg-success/10 text-success",
  rejected: "bg-destructive/10 text-destructive",
  commented: "bg-pending/15 text-pending",
};

export interface ActivityFeedItem {
  id: string | number;
  kind: Kind;
  text: string;
  time: string;
}

export interface ActivityFeedProps extends React.HTMLAttributes<HTMLDivElement> {
  title?: string;
  items: ActivityFeedItem[];
}

export function ActivityFeed({
  title = "Actividad reciente",
  items,
  className,
  ...rest
}: ActivityFeedProps) {
  return (
    <aside
      className={cn(
        "flex h-full min-h-0 flex-col rounded-2xl border border-border-subtle bg-surface p-5 shadow-[0_1px_3px_0_rgba(15,23,48,0.04)]",
        className,
      )}
      {...rest}
    >
      <h3 className="mb-3 border-b border-border-subtle pb-3 text-[11px] font-extrabold uppercase tracking-[0.1em] text-text-strong">
        {title}
      </h3>
      {items.length === 0 ? (
        <p className="flex flex-1 items-center justify-center py-6 text-center text-xs text-text-muted">
          Sin actividad reciente.
        </p>
      ) : (
        <ol className="flex flex-1 min-h-0 flex-col overflow-y-auto pr-1">
          {items.map((item, i) => {
            const Icon = KIND_ICON[item.kind];
            return (
              <li
                key={item.id}
                className={cn(
                  "flex items-start gap-3 py-2.5",
                  i < items.length - 1 && "border-b border-dashed border-border-subtle",
                )}
              >
                <span
                  data-slot="activity-icon"
                  className={cn(
                    "flex h-[30px] w-[30px] flex-shrink-0 items-center justify-center rounded-[10px]",
                    KIND_BG[item.kind],
                  )}
                  aria-hidden
                >
                  <Icon className="h-3.5 w-3.5" />
                </span>
                <div className="min-w-0 flex-1">
                  <p className="text-xs font-medium leading-snug text-text-default">
                    {item.text}
                  </p>
                  <p className="mt-0.5 text-[10px] font-medium tabular-nums text-text-muted">
                    {item.time}
                  </p>
                </div>
              </li>
            );
          })}
        </ol>
      )}
    </aside>
  );
}
