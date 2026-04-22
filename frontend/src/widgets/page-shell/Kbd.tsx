import React from "react";

interface KbdProps {
  children: React.ReactNode;
  "aria-hidden"?: boolean | "true" | "false";
}

export function Kbd({ children, "aria-hidden": ariaHidden = true }: KbdProps) {
  return (
    <kbd
      aria-hidden={ariaHidden}
      className="font-mono text-[10px] px-1.5 py-0.5 rounded border border-slate-300 bg-slate-50 text-slate-600 leading-none"
    >
      {children}
    </kbd>
  );
}
