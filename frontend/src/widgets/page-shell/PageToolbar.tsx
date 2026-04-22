import React from "react";
import { cn } from "@shared/lib/utils";

interface PageToolbarProps {
  children: React.ReactNode;
  className?: string;
}

function PageToolbar({ children, className }: PageToolbarProps) {
  return (
    <div
      className={cn(
        "h-14 px-6 border-b border-slate-200 bg-white flex items-center justify-between gap-3 sticky top-0 z-10",
        className
      )}
    >
      <div className="flex items-center gap-2 min-w-0 flex-1">{children}</div>
    </div>
  );
}

function Title({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <h1 className={cn("font-display text-sm font-semibold text-slate-900 truncate", className)}>
      {children}
    </h1>
  );
}

function Subtitle({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <p className={cn("font-mono text-xs text-slate-500 truncate", className)}>
      {children}
    </p>
  );
}

function Actions({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={cn("flex items-center gap-2 flex-shrink-0 ml-auto", className)}>
      {children}
    </div>
  );
}

PageToolbar.Title = Title;
PageToolbar.Subtitle = Subtitle;
PageToolbar.Actions = Actions;

export { PageToolbar };
