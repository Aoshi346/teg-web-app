"use client";

import * as React from "react";
import Link from "next/link";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@shared/lib/utils";

const tileVariants = cva(
  "group relative flex flex-col gap-4 rounded-2xl border p-6 transition-shadow focus-visible:outline-none focus-visible:ring-2",
  {
    variants: {
      tone: {
        primary:
          "bg-gradient-to-br from-white via-primary/5 to-primary/10 border-primary/15 shadow-[0_2px_16px_-4px_rgba(0,102,255,0.12)] hover:shadow-[0_4px_24px_-4px_rgba(0,102,255,0.18)] focus-visible:ring-primary/40",
        accent:
          "bg-gradient-to-br from-white via-[var(--brand-orange)]/5 to-[var(--brand-orange)]/10 border-[var(--brand-orange)]/20 shadow-[0_2px_16px_-4px_rgba(255,107,53,0.14)] hover:shadow-[0_4px_24px_-4px_rgba(255,107,53,0.22)] focus-visible:ring-[var(--brand-orange)]/40",
      },
    },
    defaultVariants: { tone: "primary" },
  },
);

const labelClasses: Record<"primary" | "accent", string> = {
  primary: "text-primary/70",
  accent: "text-[var(--brand-orange)]/75",
};

const valueClasses: Record<"primary" | "accent", string> = {
  primary: "text-primary",
  accent: "text-[var(--brand-orange)]",
};

const BULLET_COLORS = ["bg-success", "bg-pending", "bg-destructive"] as const;

export interface StatTileProps extends VariantProps<typeof tileVariants> {
  label: string;
  value: string;
  breakdown?: string;
  href?: string;
  className?: string;
}

function renderBreakdown(breakdown?: string): React.ReactNode {
  if (!breakdown) return null;
  if (!breakdown.includes(" · ")) {
    return <p className="text-sm text-text-default">{breakdown}</p>;
  }
  const parts = breakdown.split(" · ");
  return (
    <ul className="flex flex-col gap-1.5">
      {parts.map((part, i) => (
        <li key={part + i} className="flex items-center gap-2 text-sm text-text-default">
          <span
            className={cn("h-1.5 w-1.5 flex-shrink-0 rounded-full", BULLET_COLORS[i] ?? "bg-text-muted")}
            aria-hidden
          />
          {part}
        </li>
      ))}
    </ul>
  );
}

export function StatTile({ tone, label, value, breakdown, href, className }: StatTileProps) {
  const toneKey: "primary" | "accent" = tone === "accent" ? "accent" : "primary";
  const content = (
    <>
      <p className={cn("text-xs font-semibold uppercase tracking-wide", labelClasses[toneKey])}>{label}</p>
      <p className={cn("text-5xl font-extrabold leading-none tracking-tight", valueClasses[toneKey])}>
        {value}
      </p>
      {renderBreakdown(breakdown)}
    </>
  );

  if (href) {
    return (
      <Link href={href} className={cn(tileVariants({ tone }), className)} aria-label={`${label}: ${value}`}>
        {content}
      </Link>
    );
  }

  return <div className={cn(tileVariants({ tone }), className)}>{content}</div>;
}
