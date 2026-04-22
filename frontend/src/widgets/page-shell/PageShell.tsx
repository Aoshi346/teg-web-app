import React from "react";

interface PageShellProps {
  children: React.ReactNode;
  className?: string;
}

export function PageShell({ children, className }: PageShellProps) {
  return (
    <div className={`flex flex-col h-full min-h-0${className ? ` ${className}` : ""}`}>
      {children}
    </div>
  );
}
