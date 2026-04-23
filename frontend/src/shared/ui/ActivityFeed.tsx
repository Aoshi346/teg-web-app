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

const KIND_COLOR: Record<Kind, string> = {
  submitted: "text-primary",
  reviewed: "text-success",
  rejected: "text-destructive",
  commented: "text-pending",
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
        "flex h-full flex-col rounded-xl border border-border-subtle bg-surface p-4",
        "lg:sticky lg:top-[calc(var(--header-height,72px)+1rem)]",
        className,
      )}
      {...rest}
    >
      <h3 className="mb-3 text-sm font-bold text-text-strong">{title}</h3>
      {items.length === 0 ? (
        <p className="py-6 text-center text-xs text-text-muted">Sin actividad reciente.</p>
      ) : (
        <ol className="flex max-h-[480px] flex-col gap-2 overflow-y-auto pr-1">
          {items.map((item) => {
            const Icon = KIND_ICON[item.kind];
            return (
              <li key={item.id} className="flex items-start gap-2">
                <Icon className={cn("mt-0.5 h-4 w-4 flex-shrink-0", KIND_COLOR[item.kind])} aria-hidden />
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
