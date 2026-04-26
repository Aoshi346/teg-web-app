import * as React from "react";
import { cn } from "@shared/lib/utils";

export interface ScoreGaugeProps {
  score: number;
  max?: number;
  size?: "sm" | "md" | "lg";
  tone?: "primary" | "success";
  className?: string;
}

const SIZE_CLASS = {
  sm: "gauge-sm",
  md: "",
  lg: "gauge-lg",
} as const;

function formatScore(n: number): string {
  return Number.isInteger(n) ? String(n) : n.toFixed(1);
}

export function ScoreGauge({
  score,
  max = 20,
  size = "md",
  tone = "primary",
  className,
}: ScoreGaugeProps) {
  const raw = max === 0 ? 0 : (score / max) * 100;
  const pct = Math.max(0, Math.min(100, raw));

  return (
    <div
      className={cn(
        "gauge",
        SIZE_CLASS[size],
        tone === "success" && "gauge-green",
        className,
      )}
      style={{ ["--pct" as string]: String(Math.round(pct)) } as React.CSSProperties}
      aria-label={`Puntaje ${formatScore(score)} de ${max}`}
    >
      <span>{formatScore(score)}</span>
    </div>
  );
}
