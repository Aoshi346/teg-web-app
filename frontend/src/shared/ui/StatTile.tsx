"use client";

import * as React from "react";
import Link from "next/link";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@shared/lib/utils";
import type { BreakdownSegment, ChipSegment } from "@features/dashboard/lib/types";

const tileVariants = cva(
  "group relative flex flex-col gap-3 overflow-hidden rounded-2xl border p-6 transition-[transform,box-shadow,border-color] focus-visible:outline-none focus-visible:ring-2 hover:-translate-y-0.5",
  {
    variants: {
      tone: {
        primary:
          "bg-gradient-to-br from-white via-primary/5 to-primary/10 border-primary/15 shadow-[0_2px_16px_-4px_rgba(0,102,255,0.12)] hover:shadow-[0_4px_24px_-4px_rgba(0,102,255,0.18)] focus-visible:ring-primary/40",
        accent:
          "bg-gradient-to-br from-white via-[var(--brand-orange)]/5 to-[var(--brand-orange)]/10 border-[var(--brand-orange)]/20 shadow-[0_2px_16px_-4px_rgba(255,107,53,0.14)] hover:shadow-[0_4px_24px_-4px_rgba(255,107,53,0.22)] focus-visible:ring-[var(--brand-orange)]/40",
        hero:
          "text-white border-transparent shadow-[0_4px_16px_-4px_rgba(1,22,56,0.4),inset_0_1px_0_rgba(255,255,255,0.06)] hover:shadow-[0_12px_28px_-8px_rgba(1,22,56,0.55)]",
        blue:
          "bg-surface border-border-subtle shadow-[0_1px_2px_rgba(12,21,48,0.03)] hover:shadow-[0_10px_30px_-8px_rgba(12,21,48,0.10)] hover:border-primary/20 focus-visible:ring-primary/40",
        orange:
          "bg-surface border-border-subtle shadow-[0_1px_2px_rgba(12,21,48,0.03)] hover:shadow-[0_10px_30px_-8px_rgba(12,21,48,0.10)] hover:border-[var(--brand-orange)]/22 focus-visible:ring-[var(--brand-orange)]/40",
        green:
          "bg-surface border-border-subtle shadow-[0_1px_2px_rgba(12,21,48,0.03)] hover:shadow-[0_10px_30px_-8px_rgba(12,21,48,0.10)] hover:border-success/20 focus-visible:ring-success/40",
        amber:
          "bg-surface border-border-subtle shadow-[0_1px_2px_rgba(12,21,48,0.03)] hover:shadow-[0_10px_30px_-8px_rgba(12,21,48,0.10)] hover:border-pending/22 focus-visible:ring-pending/40",
      },
    },
    defaultVariants: { tone: "primary" },
  },
);

const SECONDARY_TONES = ["blue", "orange", "green", "amber"] as const;
type SecondaryTone = (typeof SECONDARY_TONES)[number];

const ACCENT_FG: Record<SecondaryTone, string> = {
  blue: "text-primary",
  orange: "text-[var(--brand-orange)]",
  green: "text-success",
  amber: "text-pending",
};

const ACCENT_DOT_BG: Record<SecondaryTone, string> = {
  blue: "bg-primary",
  orange: "bg-[var(--brand-orange)]",
  green: "bg-success",
  amber: "bg-pending",
};

const ACCENT_DOT_RING: Record<SecondaryTone, string> = {
  blue: "ring-primary/20",
  orange: "ring-[var(--brand-orange)]/22",
  green: "ring-success/20",
  amber: "ring-pending/22",
};

const HERO_BG = "linear-gradient(135deg,#011638 0%,#03204a 50%,#053070 100%)";

const BULLET_COLORS = ["bg-success", "bg-pending", "bg-destructive"] as const;

export interface StatTileProps extends VariantProps<typeof tileVariants> {
  label: string;
  value: string;
  breakdown?: string;
  segments?: BreakdownSegment[];
  chips?: ChipSegment[];
  urgent?: boolean;
  href?: string;
  className?: string;
  spanCols?: 1 | 2;
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

function renderSegments(segments?: BreakdownSegment[]): React.ReactNode {
  if (!segments || segments.length === 0) return null;
  return (
    <div className="flex flex-wrap gap-1.5">
      {segments.map((s) => (
        <Link
          key={s.label}
          href={s.href}
          className="rounded-full bg-primary/10 px-2 py-0.5 text-xs text-primary transition hover:bg-primary/20"
        >
          {s.count} {s.label}
        </Link>
      ))}
    </div>
  );
}

function renderChips(chips: ChipSegment[]): React.ReactNode {
  return (
    <div className="relative z-10 mt-1 flex flex-wrap gap-1">
      {chips.map((c) =>
        c.href ? (
          <Link
            key={c.label}
            href={c.href}
            className="inline-flex items-center gap-1 rounded-full border border-white/15 bg-white/10 px-2 py-0.5 text-xs font-semibold text-white transition hover:border-[var(--brand-yellow)]/40 hover:bg-white/20"
          >
            <span className="text-[var(--brand-yellow)]">{c.count}</span>
            <span>{c.label}</span>
          </Link>
        ) : (
          <span
            key={c.label}
            className="inline-flex items-center gap-1 rounded-full border border-white/15 bg-white/10 px-2 py-0.5 text-xs font-semibold text-white"
          >
            <span className="text-[var(--brand-yellow)]">{c.count}</span>
            <span>{c.label}</span>
          </span>
        ),
      )}
    </div>
  );
}

function HeroDecorations() {
  return (
    <>
      <span
        aria-hidden
        className="pointer-events-none absolute inset-0"
        style={{
          backgroundImage:
            "radial-gradient(circle, rgba(255,255,255,0.06) 1px, transparent 1px)",
          backgroundSize: "22px 22px",
        }}
      />
      <span
        aria-hidden
        className="pointer-events-none absolute -right-8 -top-8 h-40 w-40 rounded-full transition-all duration-500 group-hover:-right-12 group-hover:-top-12 group-hover:h-60 group-hover:w-60"
        style={{
          background:
            "radial-gradient(circle, rgba(255,210,63,0.18) 0%, transparent 65%)",
        }}
      />
      <span
        aria-hidden
        className="pointer-events-none absolute inset-x-0 bottom-0 h-0.5 opacity-60"
        style={{
          background:
            "linear-gradient(90deg, transparent, var(--brand-yellow), var(--brand-orange), transparent)",
        }}
      />
    </>
  );
}

export function StatTile({
  tone,
  label,
  value,
  breakdown,
  segments,
  chips,
  urgent,
  href,
  className,
  spanCols,
}: StatTileProps) {
  const isHero = tone === "hero";
  const secondaryTone = (SECONDARY_TONES as readonly string[]).includes(tone ?? "")
    ? (tone as SecondaryTone)
    : null;

  const labelEl = (
    <p
      className={cn(
        "relative z-10 flex items-center gap-2 text-[10px] font-extrabold uppercase tracking-[0.12em]",
        isHero
          ? "text-[var(--brand-yellow)] before:block before:h-[1.5px] before:w-3.5 before:rounded-full before:bg-[var(--brand-yellow)]"
          : secondaryTone
            ? ACCENT_FG[secondaryTone]
            : "text-primary/70",
      )}
    >
      {!isHero && secondaryTone && (
        <span
          className={cn(
            "h-1.5 w-1.5 rounded-full ring-[3px]",
            ACCENT_DOT_BG[secondaryTone],
            ACCENT_DOT_RING[secondaryTone],
          )}
          aria-hidden
        />
      )}
      <span>{label}</span>
      {urgent && (
        <span
          className="ml-1 inline-block h-2 w-2 rounded-full bg-pending pulse-soft"
          aria-hidden
        />
      )}
    </p>
  );

  const valueEl = (
    <p
      className={cn(
        "relative z-10 leading-none tracking-[-0.035em]",
        isHero
          ? "text-[60px] font-black tracking-[-0.045em]"
          : secondaryTone
            ? "text-[46px] font-black text-text-strong"
            : "text-5xl font-extrabold",
        !isHero && !secondaryTone && tone === "primary" && "text-primary",
        !isHero && !secondaryTone && tone === "accent" && "text-[var(--brand-orange)]",
      )}
    >
      {value}
    </p>
  );

  const subEl = chips && chips.length > 0
    ? renderChips(chips)
    : segments
      ? renderSegments(segments)
      : renderBreakdown(breakdown);

  const inner = (
    <>
      {isHero && <HeroDecorations />}
      {labelEl}
      {valueEl}
      {subEl}
    </>
  );

  const heroStyle = isHero ? { background: HERO_BG } : undefined;
  const colSpan = spanCols === 2 ? "lg:col-span-2" : "";

  if (href && !chips) {
    return (
      <Link
        href={href}
        aria-label={`${label}: ${value}`}
        className={cn(tileVariants({ tone }), colSpan, className)}
        style={heroStyle}
      >
        {inner}
      </Link>
    );
  }

  return (
    <div className={cn(tileVariants({ tone }), colSpan, className)} style={heroStyle}>
      {inner}
    </div>
  );
}
