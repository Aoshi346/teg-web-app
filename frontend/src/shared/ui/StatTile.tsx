"use client";

import * as React from "react";
import Link from "next/link";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@shared/lib/utils";

const tileVariants = cva(
  "group relative flex min-h-[140px] flex-col justify-between rounded-xl p-5 text-white transition hover:brightness-[1.05] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-offset-background focus-visible:ring-white/80",
  {
    variants: {
      tone: {
        primary: "bg-primary",
        accent: "bg-[var(--brand-orange)]",
      },
    },
    defaultVariants: { tone: "primary" },
  },
);

export interface StatTileProps extends VariantProps<typeof tileVariants> {
  label: string;
  value: string;
  breakdown?: string;
  href?: string;
  className?: string;
}

export function StatTile({ tone, label, value, breakdown, href, className }: StatTileProps) {
  const content = (
    <>
      <p className="text-sm font-semibold uppercase tracking-wide text-white/80">{label}</p>
      <p className="text-4xl font-extrabold leading-none tracking-tight">{value}</p>
      {breakdown && <p className="text-sm text-white/80">{breakdown}</p>}
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
