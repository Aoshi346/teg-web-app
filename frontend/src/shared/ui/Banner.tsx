"use client";

/**
 * Banner — inline form notice. Delegates to the unified Notice primitive
 * so inline form validation messages share the exact look of global toasts.
 */

import React, { useEffect, useState } from "react";
import Notice, { NoticeVariant } from "./Notice";

export type BannerProps = {
  visible: boolean;
  message: string;
  type?: NoticeVariant;
  onClose?: () => void;
  autoHide?: number; // ms
};

export default function Banner({
  visible,
  message,
  type = "info",
  onClose,
  autoHide,
}: BannerProps) {
  const [leaving, setLeaving] = useState(false);
  const [progress, setProgress] = useState(1);

  useEffect(() => {
    if (!visible) {
      setLeaving(false);
      setProgress(1);
      return;
    }
    if (!autoHide) return;

    const start = Date.now();
    const tick = window.setInterval(() => {
      const p = Math.max(0, 1 - (Date.now() - start) / autoHide);
      setProgress(p);
    }, 60);
    const hide = window.setTimeout(() => {
      setLeaving(true);
      window.setTimeout(() => onClose?.(), 260);
    }, autoHide);

    return () => {
      window.clearInterval(tick);
      window.clearTimeout(hide);
    };
  }, [visible, autoHide, onClose]);

  const handleClose = () => {
    setLeaving(true);
    window.setTimeout(() => onClose?.(), 260);
  };

  if (!visible && !leaving) return null;

  return (
    <div
      className={[
        "w-full will-change-transform",
        leaving ? "notice-exit" : "notice-enter",
      ].join(" ")}
    >
      <Notice
        variant={type}
        message={message}
        onClose={onClose ? handleClose : undefined}
        progress={autoHide ? progress : undefined}
      />
    </div>
  );
}
