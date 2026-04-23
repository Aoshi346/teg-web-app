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

const KIND_CIRCLE: Record<Kind, string> = {
  submitted: "bg-primary/10 text-primary",
  reviewed: "bg-success-soft text-success",
  rejected: "bg-destructive-soft text-destructive",
  commented: "bg-pending-soft text-pending",
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
        "flex h-full min-h-0 flex-col rounded-xl border border-border-subtle bg-surface p-4 shadow-[0_1px_3px_0_rgba(15,23,42,0.04)]",
        className,
      )}
      {...rest}
    >
      <h3 className="sticky top-0 z-10 border-b border-border-subtle/50 bg-surface pb-3 text-sm font-bold text-text-strong">
        {title}
      </h3>
      {items.length === 0 ? (
        <p className="flex flex-1 items-center justify-center py-6 text-center text-xs text-text-muted">
          Sin actividad reciente.
        </p>
      ) : (
        <ol className="flex flex-1 min-h-0 flex-col gap-3 overflow-y-auto pr-1 pt-2">
          {items.map((item) => {
            const Icon = KIND_ICON[item.kind];
            return (
              <li key={item.id} className="flex items-start gap-3">
                <span
                  className={cn(
                    "flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full",
                    KIND_CIRCLE[item.kind],
                  )}
                  aria-hidden
                >
                  <Icon className="h-3.5 w-3.5" />
                </span>
                <div className="min-w-0 flex-1">
                  <p className="text-sm leading-tight text-text-default">{item.text}</p>
                  <p className="text-xs text-text-muted">{item.time}</p>
                </div>
              </li>
            );
          })}
        </ol>
      )}
    </aside>
  );
}
