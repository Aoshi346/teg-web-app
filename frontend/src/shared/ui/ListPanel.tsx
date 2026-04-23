"use client";

import * as React from "react";

import { cn } from "@shared/lib/utils";

export interface ListPanelProps extends React.HTMLAttributes<HTMLDivElement> {
  title: string;
  count?: number;
  emptyText?: string;
  emptyHint?: string;
  isEmpty?: boolean;
}

export function ListPanel({
  title,
  count,
  emptyText,
  emptyHint,
  isEmpty,
  className,
  children,
  ...rest
}: ListPanelProps) {
  return (
    <section
      className={cn(
        "flex h-full min-h-0 flex-col rounded-xl border border-border-subtle bg-surface p-4 shadow-[0_1px_3px_0_rgba(15,23,42,0.04)]",
        className,
      )}
      {...rest}
    >
      <header className="sticky top-0 z-10 flex items-center justify-between border-b border-border-subtle/50 bg-surface pb-3">
        <h3 className="text-sm font-bold text-text-strong">{title}</h3>
        {typeof count === "number" && (
          <span className="rounded-md border border-border-subtle bg-surface-muted px-2 py-0.5 text-xs font-semibold text-text-muted">
            {count} {count === 1 ? "item" : "items"}
          </span>
        )}
      </header>
      {isEmpty ? (
        <div className="flex flex-1 flex-col items-center justify-center py-6 text-center">
          <p className="text-sm font-semibold text-text-strong">{emptyText ?? "Sin resultados"}</p>
          {emptyHint && <p className="mt-1 text-xs text-text-muted">{emptyHint}</p>}
        </div>
      ) : (
        <div className="flex flex-1 min-h-0 flex-col gap-1 overflow-y-auto pt-2">{children}</div>
      )}
    </section>
  );
}
