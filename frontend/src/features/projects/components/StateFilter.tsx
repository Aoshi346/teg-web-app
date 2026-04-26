"use client";

import * as React from "react";
import { ChevronDown, Check } from "lucide-react";

import { cn } from "@shared/lib/utils";
import type { ProjectState } from "@features/projects/types/project";

export interface StateFilterOption {
  state: ProjectState;
  label: string;
  count: number;
  dotColor: string;
}

export interface StateFilterProps {
  value: ProjectState | null;
  onChange: (next: ProjectState | null) => void;
  options: StateFilterOption[];
  totalCount: number;
  allLabel?: string;
  className?: string;
}

export function StateFilter({
  value,
  onChange,
  options,
  totalCount,
  allLabel = "Todos",
  className,
}: StateFilterProps) {
  const [open, setOpen] = React.useState(false);
  const wrapperRef = React.useRef<HTMLDivElement | null>(null);

  React.useEffect(() => {
    if (!open) return;
    function onDocClick(e: MouseEvent) {
      if (!wrapperRef.current?.contains(e.target as Node)) setOpen(false);
    }
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") setOpen(false);
    }
    document.addEventListener("mousedown", onDocClick);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDocClick);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  const current = value == null ? null : options.find((o) => o.state === value) ?? null;
  const triggerLabel = current?.label ?? allLabel;
  const triggerCount = current?.count ?? totalCount;
  const triggerDot = current?.dotColor ?? null;

  const select = (next: ProjectState | null) => {
    onChange(next);
    setOpen(false);
  };

  return (
    <div ref={wrapperRef} className={cn("relative", className)}>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-haspopup="listbox"
        aria-expanded={open}
        className="inline-flex items-center gap-2 h-11 px-4 rounded-xl border border-border-subtle bg-surface text-[13px] font-bold text-text-strong hover:border-border-default focus:outline-none focus:border-primary transition-colors min-w-[180px]"
      >
        {triggerDot && (
          <span
            aria-hidden
            className="inline-block w-1.5 h-1.5 rounded-full"
            style={{ background: triggerDot }}
          />
        )}
        <span className="flex-1 text-left truncate">{triggerLabel}</span>
        <span className="text-[11px] font-bold text-text-muted bg-surface-sunken rounded-full px-1.5 py-0.5 min-w-[22px] text-center tabular-nums">
          {triggerCount}
        </span>
        <ChevronDown className={cn("w-4 h-4 text-text-muted transition-transform", open && "rotate-180")} strokeWidth={2.4} />
      </button>

      {open && (
        <div
          role="listbox"
          className="absolute z-30 mt-1.5 w-full min-w-[220px] rounded-xl border border-border-subtle bg-surface shadow-lg overflow-hidden"
        >
          <button
            type="button"
            role="option"
            aria-selected={value == null}
            onClick={() => select(null)}
            className={cn(
              "w-full flex items-center gap-2 px-4 py-2.5 text-[13px] font-semibold text-left hover:bg-surface-sunken transition-colors",
              value == null && "text-text-strong",
            )}
          >
            <span className="w-1.5 h-1.5" aria-hidden />
            <span className="flex-1">{allLabel}</span>
            <span className="text-[11px] font-bold text-text-muted tabular-nums">{totalCount}</span>
            {value == null && <Check className="w-3.5 h-3.5 text-primary" strokeWidth={3} />}
          </button>
          <div className="h-px bg-border-subtle" />
          {options.map((o) => {
            const selected = value === o.state;
            return (
              <button
                key={o.state}
                type="button"
                role="option"
                aria-selected={selected}
                onClick={() => select(o.state)}
                className={cn(
                  "w-full flex items-center gap-2 px-4 py-2.5 text-[13px] font-semibold text-left hover:bg-surface-sunken transition-colors",
                  selected ? "text-text-strong" : "text-text-muted",
                )}
              >
                <span
                  aria-hidden
                  className="inline-block w-1.5 h-1.5 rounded-full"
                  style={{ background: o.dotColor }}
                />
                <span className="flex-1">{o.label}</span>
                <span className="text-[11px] font-bold text-text-muted tabular-nums">{o.count}</span>
                {selected && <Check className="w-3.5 h-3.5 text-primary" strokeWidth={3} />}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
