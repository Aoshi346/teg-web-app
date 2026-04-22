import React from "react";
import { cn } from "@shared/lib/utils";

interface SectionHeaderProps {
  title: string;
  children?: React.ReactNode;
  className?: string;
}

interface ActionProps {
  children: React.ReactNode;
  href?: string;
  onClick?: () => void;
  className?: string;
}

function Action({ children, href, onClick, className }: ActionProps) {
  const cls = cn("text-xs font-medium text-primary hover:underline cursor-pointer", className);
  if (href) {
    return (
      <a href={href} className={cls} onClick={onClick}>
        {children}
      </a>
    );
  }
  return (
    <button type="button" className={cls} onClick={onClick}>
      {children}
    </button>
  );
}

function SectionHeader({ title, children, className }: SectionHeaderProps) {
  return (
    <div className={cn("flex items-end justify-between mb-2 px-0.5", className)}>
      <span className="font-mono text-[11px] tracking-wider text-slate-500 uppercase">
        {title}
      </span>
      {children && <div>{children}</div>}
    </div>
  );
}

SectionHeader.Action = Action;

export { SectionHeader };
