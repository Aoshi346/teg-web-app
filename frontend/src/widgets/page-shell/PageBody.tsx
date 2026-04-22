import React from "react";
import { cn } from "@shared/lib/utils";

interface PageBodyProps {
  children: React.ReactNode;
  className?: string;
}

export function PageBody({ children, className }: PageBodyProps) {
  return (
    <div className={cn("flex-1 min-h-0 overflow-y-auto px-6 py-5 bg-slate-50/50 space-y-5", className)}>
      {children}
    </div>
  );
}
