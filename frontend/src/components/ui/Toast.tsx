"use client";

/**
 * Toast — legacy floating notification API. Internally delegates to the
 * unified Notice primitive so every surface in the app shares the same
 * aesthetic. Prefer `useNotify()` from NotificationProvider for new code.
 */

import React, { useEffect, useState } from "react";
import Notice, { NoticeVariant } from "./Notice";

export type ToastType = NoticeVariant;

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
  duration = 3500,
}: ToastProps) {
  const [mounted, setMounted] = useState(false);
  const [leaving, setLeaving] = useState(false);
  const [progress, setProgress] = useState(1);

  useEffect(() => {
    if (!isVisible) return;

    setMounted(true);
    setLeaving(false);
    setProgress(1);

    const start = Date.now();
    const tick = window.setInterval(() => {
      const p = Math.max(0, 1 - (Date.now() - start) / duration);
      setProgress(p);
    }, 60);

    const hide = window.setTimeout(() => {
      setLeaving(true);
      window.setTimeout(() => {
        setMounted(false);
        onClose();
      }, 260);
    }, duration);

    return () => {
      window.clearInterval(tick);
      window.clearTimeout(hide);
    };
  }, [isVisible, duration, onClose]);

  const handleClose = () => {
    setLeaving(true);
    window.setTimeout(() => {
      setMounted(false);
      onClose();
    }, 260);
  };

  if (!isVisible && !mounted) return null;

  return (
    <div
      className={[
        "fixed z-[200] top-3 right-3 left-3 sm:left-auto sm:top-6 sm:right-6",
        "sm:w-[400px] will-change-transform",
        leaving ? "notice-exit" : "notice-enter",
      ].join(" ")}
      style={{
        top: "max(0.75rem, env(safe-area-inset-top))",
        right: "max(0.75rem, env(safe-area-inset-right))",
      }}
    >
      <Notice
        variant={type}
        message={message}
        onClose={handleClose}
        progress={progress}
      />
    </div>
  );
}
