"use client";

import React, { useEffect, useState } from "react";
import { X, CheckCircle, AlertCircle, Info } from "lucide-react";

export type ToastType = "success" | "error" | "info";

interface ToastProps {
  message: string;
  type?: ToastType;
  isVisible: boolean;
  onClose: () => void;
  duration?: number;
}

export default function Toast({
  message,
  type = "info",
  isVisible,
  onClose,
  duration = 3000
}: ToastProps) {
  const [isShowing, setIsShowing] = useState(false);

  useEffect(() => {
    if (isVisible) {
      setIsShowing(true);
      const timer = setTimeout(() => {
        setIsShowing(false);
        // Wait for animation to finish before calling onClose
        setTimeout(onClose, 300);
      }, duration);
      return () => clearTimeout(timer);
    } else {
      setIsShowing(false);
    }
  }, [isVisible, duration, onClose]);

  if (!isVisible && !isShowing) return null;

  const getIcon = () => {
    switch (type) {
      case "success": return <CheckCircle className="w-5 h-5 text-emerald-500" />;
      case "error": return <AlertCircle className="w-5 h-5 text-red-500" />;
      default: return <Info className="w-5 h-5 text-blue-500" />;
    }
  };

  const getStyles = () => {
    switch (type) {
      case "success": return "border-emerald-100 bg-white";
      case "error": return "border-red-100 bg-white";
      default: return "border-blue-100 bg-white";
    }
  };

  return (
    <div
      className={`fixed bottom-4 right-4 z-[110] flex items-center gap-3 px-4 py-3 rounded-xl border shadow-lg transition-all duration-300 transform ${isShowing ? "translate-y-0 opacity-100 scale-100" : "translate-y-2 opacity-0 scale-95"
        } ${getStyles()}`}
    >
      <div className="flex-shrink-0">
        {getIcon()}
      </div>
      <p className="text-sm font-medium text-gray-700">{message}</p>
      <button
        onClick={() => setIsShowing(false)}
        className="p-1 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100 transition-colors"
      >
        <X className="w-4 h-4" />
      </button>
    </div>
  );
}