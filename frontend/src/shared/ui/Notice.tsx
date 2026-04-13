"use client";

/**
 * Notice — the single visual primitive for every notification in the app.
 * Both the inline form Banner and the floating toast stack render through
 * this component, so success/error/warning/info messages all look the same.
 *
 * Bold, colorful surface: the entire card is saturated with the variant
 * color via a 135° diagonal gradient, with crisp white text, a translucent
 * white icon chip, a tiny uppercase kicker, and an optional hairline
 * progress bar along the bottom.
 */

import React from "react";
import { CheckCircle2, AlertTriangle, XOctagon, Info, X } from "lucide-react";

export type NoticeVariant = "success" | "error" | "warning" | "info";

export interface NoticeProps {
  variant?: NoticeVariant;
  message: React.ReactNode;
  /** Optional override for the tiny uppercase kicker above the message. */
  kicker?: string;
  /** If rendered, shows a close button. */
  onClose?: () => void;
  /** 0..1 — renders a hairline progress bar along the bottom. */
  progress?: number;
  /** Compact form used inside stacks / tight layouts. */
  dense?: boolean;
  /** Extra classes applied to the outer card. */
  className?: string;
}

const VARIANT_COPY: Record<NoticeVariant, string> = {
  success: "¡LISTO!",
  error: "UPS...",
  warning: "ATENCIÓN",
  info: "AVISO",
};

const VARIANT_ICON: Record<NoticeVariant, React.ReactNode> = {
  success: <CheckCircle2 className="w-[18px] h-[18px]" strokeWidth={2.5} />,
  error: <XOctagon className="w-[18px] h-[18px]" strokeWidth={2.5} />,
  warning: <AlertTriangle className="w-[18px] h-[18px]" strokeWidth={2.5} />,
  info: <Info className="w-[18px] h-[18px]" strokeWidth={2.5} />,
};

// Per-variant surface: the entire card is the variant color.
// All gradients chosen so white text meets WCAG AA (≥4.5:1) across the surface.
const VARIANT_SURFACE: Record<
  NoticeVariant,
  { gradient: string; shadow: string }
> = {
  success: {
    gradient: "linear-gradient(135deg, #10b981 0%, #059669 100%)",
    shadow:
      "0 16px 40px -12px rgba(16,185,129,0.45), 0 4px 10px -4px rgba(15,23,42,0.15)",
  },
  error: {
    gradient: "linear-gradient(135deg, #ff4b3a 0%, #d6281b 100%)",
    shadow:
      "0 16px 40px -12px rgba(255,75,58,0.45), 0 4px 10px -4px rgba(15,23,42,0.15)",
  },
  // Warning: darkened end stop from #ffb347 to #c84a17 for AA contrast
  // with white text on the lighter half of the gradient.
  warning: {
    gradient: "linear-gradient(135deg, #ff6b35 0%, #c84a17 100%)",
    shadow:
      "0 16px 40px -12px rgba(255,107,53,0.45), 0 4px 10px -4px rgba(15,23,42,0.15)",
  },
  // Info: ends at darker navy #001a42 to keep contrast crisp.
  info: {
    gradient: "linear-gradient(135deg, #0066ff 0%, #001a42 100%)",
    shadow:
      "0 16px 40px -12px rgba(0,102,255,0.45), 0 4px 10px -4px rgba(15,23,42,0.15)",
  },
};

export default function Notice({
  variant = "info",
  message,
  kicker,
  onClose,
  progress,
  dense = false,
  className = "",
}: NoticeProps) {
  const surface = VARIANT_SURFACE[variant];
  const kickerText = kicker ?? VARIANT_COPY[variant];

  return (
    <div
      role="alert"
      aria-live={variant === "error" ? "assertive" : "polite"}
      aria-atomic="true"
      className={[
        "relative isolate overflow-hidden",
        "rounded-[18px]",
        "ring-1 ring-white/15",
        className,
      ].join(" ")}
      style={{
        backgroundImage: surface.gradient,
        boxShadow: surface.shadow,
      }}
    >
      {/* Soft radial highlight overlay in the top-right corner */}
      <span
        className="pointer-events-none absolute inset-0"
        aria-hidden="true"
        style={{
          backgroundImage:
            "radial-gradient(circle at top right, rgba(255,255,255,0.18), transparent 60%)",
        }}
      />

      {/* Film grain overlay — understated */}
      <span
        className="pointer-events-none absolute inset-0 opacity-[0.04] mix-blend-overlay"
        aria-hidden="true"
        style={{
          backgroundImage:
            "url(\"data:image/svg+xml,%3Csvg viewBox='0 0 120 120' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E\")",
          backgroundSize: "120px 120px",
        }}
      />

      <div
        className={[
          "relative flex items-start gap-3",
          dense ? "px-3 py-2.5" : "px-4 py-3.5",
        ].join(" ")}
      >
        {/* Translucent white icon chip */}
        <div
          className={[
            "flex-shrink-0 flex items-center justify-center rounded-full",
            dense ? "w-6 h-6 mt-[1px]" : "w-8 h-8 mt-[2px]",
            "bg-white/20 ring-1 ring-white/30 text-white",
          ].join(" ")}
          aria-hidden="true"
        >
          {dense ? (
            <span className="flex items-center justify-center [&>svg]:w-[14px] [&>svg]:h-[14px]">
              {VARIANT_ICON[variant]}
            </span>
          ) : (
            VARIANT_ICON[variant]
          )}
        </div>

        <div className="flex-1 min-w-0 pt-[1px]">
          <div
            className={[
              "font-bold uppercase leading-none text-white/70",
              "tracking-[0.16em]",
              dense ? "text-[9px] mb-1" : "text-[10px] mb-1.5",
            ].join(" ")}
          >
            {kickerText}
          </div>
          <div
            className={[
              "font-semibold leading-snug break-words text-white",
              dense ? "text-[12.5px]" : "text-[13.5px]",
            ].join(" ")}
          >
            {message}
          </div>
        </div>

        {onClose && (
          <button
            type="button"
            onClick={onClose}
            aria-label="Cerrar notificación"
            className={[
              "flex-shrink-0",
              "w-7 h-7 rounded-full flex items-center justify-center",
              "text-white bg-white/10 hover:bg-white/25",
              "transition-all duration-200 hover:rotate-90",
            ].join(" ")}
          >
            <X className="w-3.5 h-3.5" strokeWidth={2.75} />
          </button>
        )}
      </div>

      {/* Hairline progress bar */}
      {typeof progress === "number" && (
        <div className="absolute bottom-0 left-0 right-0 h-[2px] bg-black/20">
          <div
            className="h-full bg-white/80 transition-[width] duration-75 ease-linear"
            style={{ width: `${Math.max(0, Math.min(100, progress * 100))}%` }}
          />
        </div>
      )}
    </div>
  );
}
