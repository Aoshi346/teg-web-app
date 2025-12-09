"use client";

import React, { useEffect } from "react";
import { CheckCircle, AlertTriangle, XCircle, Info } from "lucide-react";

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
    bg: "bg-emerald-50",
    border: "border-emerald-200",
    text: "text-emerald-700",
    icon: <CheckCircle className="w-5 h-5 text-emerald-600" />,
  },
  error: {
    bg: "bg-red-50",
    border: "border-red-200",
    text: "text-red-700",
    icon: <XCircle className="w-5 h-5 text-red-600" />,
  },
  warning: {
    bg: "bg-yellow-50",
    border: "border-yellow-200",
    text: "text-yellow-700",
    icon: <AlertTriangle className="w-5 h-5 text-yellow-600" />,
  },
  info: {
    bg: "bg-blue-50",
    border: "border-blue-200",
    text: "text-blue-700",
    icon: <Info className="w-5 h-5 text-blue-600" />,
  },
} as const;

export default function Banner({
  visible,
  message,
  type = "info",
  onClose,
  autoHide,
}: BannerProps) {
  useEffect(() => {
    if (!visible || !autoHide) return;
    const t = setTimeout(() => onClose && onClose(), autoHide);
    return () => clearTimeout(t);
  }, [visible, autoHide, onClose]);

  if (!visible) return null;

  const style = typeMap[type] ?? typeMap["info"];

  return (
    <div
      className={`w-full rounded-lg border ${style.border} ${style.bg} p-3 text-sm ${style.text} shadow-sm flex items-start gap-3`}
      role="status"
      aria-live="polite"
    >
      <div className="flex-shrink-0">{style.icon}</div>
      <div className="flex-1">
        <div className="leading-tight">{message}</div>
      </div>
      {onClose && (
        <div className="flex-shrink-0">
          <button
            onClick={onClose}
            className={`p-1 rounded-md text-gray-500 hover:text-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500`}
            aria-label="Cerrar aviso"
          >
            <svg
              className="w-4 h-4"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      )}
    </div>
  );
}
