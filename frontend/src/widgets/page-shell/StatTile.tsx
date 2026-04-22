import React from "react";
import { cn } from "@shared/lib/utils";
import { Surface } from "@shared/ui/Surface";

type AccentVariant = "teg" | "pteg" | "success" | "pending" | "destructive";

interface StatTileProps {
  label: string;
  value: React.ReactNode;
  delta?: React.ReactNode;
  subtext?: React.ReactNode;
  accent?: AccentVariant;
  icon?: React.ReactNode;
  variant?: "default" | "hero";
  className?: string;
}

const ACCENT_RULE: Record<AccentVariant, string> = {
  teg: "bg-[color:var(--color-accent-teg)]",
  pteg: "bg-[color:var(--color-accent-pteg)]",
  success: "bg-success",
  pending: "bg-pending",
  destructive: "bg-destructive",
};

const ACCENT_ICON_BG: Record<AccentVariant, string> = {
  teg: "bg-[color:var(--color-accent-teg-soft)] text-[color:var(--color-accent-teg)]",
  pteg: "bg-[color:var(--color-accent-pteg-soft)] text-[color:var(--color-accent-pteg)]",
  success: "bg-success/10 text-success",
  pending: "bg-pending/10 text-pending",
  destructive: "bg-destructive/10 text-destructive",
};

export function StatTile({ label, value, delta, subtext, accent, icon, variant = "default", className }: StatTileProps) {
  if (variant === "hero") {
    return (
      <div
        className={cn(
          "relative h-24 p-4 rounded-xl border border-slate-900/10 overflow-hidden",
          "bg-gradient-to-br from-[#01102C] via-[#011638] to-[#0066ff] text-white",
          "shadow-[0_8px_24px_-8px_rgb(1_22_56_/_0.5)]",
          className
        )}
      >
        <div
          aria-hidden="true"
          className="absolute -top-8 -right-8 w-24 h-24 rounded-full bg-blue-400/20 blur-2xl pointer-events-none"
        />
        <p className="font-mono text-[11px] uppercase tracking-widest text-white/60 font-semibold leading-none">
          {label}
        </p>
        <div className="mt-2">
          <p className="font-display text-4xl text-white tabular-nums leading-none">
            {value}
          </p>
          {(delta || subtext) && (
            <p className="text-xs text-white/70 mt-1 truncate">
              {delta ?? subtext}
            </p>
          )}
        </div>
      </div>
    );
  }

  return (
    <Surface className={cn("relative h-24 p-4 overflow-hidden transition-shadow duration-150 hover:shadow-md", className)}>
      {accent && (
        <span
          className={cn("absolute left-0 top-0 bottom-0 w-[3px]", ACCENT_RULE[accent])}
          aria-hidden="true"
        />
      )}
      {icon && (
        <div
          className={cn(
            "absolute top-3 right-3 w-7 h-7 rounded-lg flex items-center justify-center",
            accent ? ACCENT_ICON_BG[accent] : "bg-slate-100 text-slate-500"
          )}
        >
          {icon}
        </div>
      )}
      <p className="font-mono text-[11px] uppercase tracking-wider text-slate-500 leading-none">
        {label}
      </p>
      <div className="mt-2">
        <p className="font-display tabular-nums text-2xl font-semibold text-slate-900 leading-none">
          {value}
        </p>
        {(delta || subtext) && (
          <p className="text-xs text-slate-500 mt-1 truncate">
            {delta ?? subtext}
          </p>
        )}
      </div>
    </Surface>
  );
}
