"use client";

import React, { useEffect, useState } from "react";
import { CheckCircle, AlertTriangle, XCircle, Info, X } from "lucide-react";

type BannerType = "success" | "error" | "warning" | "info";

export type BannerProps = {
  visible: boolean;
  message: string;
  type?: BannerType;
  onClose?: () => void;
  autoHide?: number; // ms
};

const typeMap = {
  success: {
    bg: "bg-gradient-to-r from-emerald-50 to-green-50",
    border: "border-emerald-300",
    text: "text-emerald-800",
    icon: <CheckCircle className="w-5 h-5 text-emerald-600" />,
    progressBg: "bg-emerald-500",
  },
  error: {
    bg: "bg-gradient-to-r from-red-50 to-rose-50",
    border: "border-red-300",
    text: "text-red-800",
    icon: <XCircle className="w-5 h-5 text-red-600" />,
    progressBg: "bg-red-500",
  },
  warning: {
    bg: "bg-gradient-to-r from-yellow-50 to-amber-50",
    border: "border-yellow-300",
    text: "text-yellow-800",
    icon: <AlertTriangle className="w-5 h-5 text-yellow-600" />,
    progressBg: "bg-yellow-500",
  },
  info: {
    bg: "bg-gradient-to-r from-blue-50 to-indigo-50",
    border: "border-blue-300",
    text: "text-blue-800",
    icon: <Info className="w-5 h-5 text-blue-600" />,
    progressBg: "bg-blue-500",
  },
} as const;

export default function Banner({
  visible,
  message,
  type = "info",
  onClose,
  autoHide,
}: BannerProps) {
  const [isAnimatingOut, setIsAnimatingOut] = useState(false);
  const [progress, setProgress] = useState(100);

  useEffect(() => {
    if (!visible) {
      setProgress(100);
      setIsAnimatingOut(false);
      return;
    }

    if (!autoHide) return;

    // Progress bar animation
    const startTime = Date.now();
    const progressInterval = setInterval(() => {
      const elapsed = Date.now() - startTime;
      const remaining = Math.max(0, 100 - (elapsed / autoHide) * 100);
      setProgress(remaining);
    }, 16); // ~60fps

    // Auto-hide timer
    const hideTimer = setTimeout(() => {
      setIsAnimatingOut(true);
      setTimeout(() => {
        onClose?.();
      }, 300); // Wait for slide-out animation
    }, autoHide);

    return () => {
      clearInterval(progressInterval);
      clearTimeout(hideTimer);
    };
  }, [visible, autoHide, onClose]);

  const handleClose = () => {
    setIsAnimatingOut(true);
    setTimeout(() => {
      onClose?.();
    }, 300);
  };

  if (!visible && !isAnimatingOut) return null;

  const style = typeMap[type] ?? typeMap["info"];

  return (
    <div
      className={`w-full rounded-xl border-2 ${style.border} ${style.bg} shadow-lg overflow-hidden transition-all duration-300 ${
        isAnimatingOut
          ? "opacity-0 -translate-y-2 scale-95"
          : "opacity-100 translate-y-0 scale-100"
      }`}
      role="alert"
      aria-live="assertive"
      aria-atomic="true"
    >
      <div className="relative">
        {/* Progress bar */}
        {autoHide && (
          <div className="absolute bottom-0 left-0 right-0 h-1 bg-gray-200/30">
            <div
              className={`h-full ${style.progressBg} transition-all duration-75 ease-linear`}
              style={{ width: `${progress}%` }}
            />
          </div>
        )}

        {/* Content */}
        <div className="flex items-start gap-3 p-4">
          <div className="flex-shrink-0 mt-0.5">{style.icon}</div>
          <div className="flex-1 min-w-0">
            <div
              className={`text-sm font-semibold leading-relaxed ${style.text}`}
            >
              {message}
            </div>
          </div>
          {onClose && (
            <button
              onClick={handleClose}
              className="flex-shrink-0 p-1.5 rounded-lg hover:bg-black/5 transition-colors group"
              aria-label="Cerrar notificación"
            >
              <X className="w-4 h-4 text-gray-500 group-hover:text-gray-700" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
