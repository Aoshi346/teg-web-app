"use client";

import React from "react";
import { GraduationCap, Briefcase, Scale, Check } from "lucide-react";

export type RoleName = "Estudiante" | "Tutor" | "Jurado";

const ROLE_META: Record<RoleName, { num: string; testid: string; Icon: React.ComponentType<{ className?: string; size?: number }> }> = {
  Estudiante: { num: "i", testid: "role-icon-estudiante", Icon: GraduationCap },
  Tutor: { num: "ii", testid: "role-icon-tutor", Icon: Briefcase },
  Jurado: { num: "iii", testid: "role-icon-jurado", Icon: Scale },
};

interface RoleChipProps {
  role: RoleName;
  active: boolean;
  onChange: (role: RoleName) => void;
  onArrowKey?: (direction: -1 | 1) => void;
}

export default function RoleChip({ role, active, onChange, onArrowKey }: RoleChipProps) {
  const meta = ROLE_META[role];
  const Icon = meta.Icon;

  return (
    <button
      type="button"
      role="radio"
      aria-checked={active}
      tabIndex={active ? 0 : -1}
      onClick={() => onChange(role)}
      onKeyDown={(e) => {
        if (e.key === "ArrowRight" || e.key === "ArrowDown") {
          e.preventDefault();
          onArrowKey?.(1);
        } else if (e.key === "ArrowLeft" || e.key === "ArrowUp") {
          e.preventDefault();
          onArrowKey?.(-1);
        } else if (e.key === " " || e.key === "Enter") {
          e.preventDefault();
          onChange(role);
        }
      }}
      className={`lm-role-chip${active ? " lm-role-chip-active" : ""}`}
    >
      <Icon className="role-icon" data-testid={meta.testid} />
      <span className="role-name">{role}</span>
      <span className="role-num">{meta.num}</span>
      {active && (
        <span className="lm-role-check" aria-hidden="true">
          <Check size={12} strokeWidth={3} />
        </span>
      )}
    </button>
  );
}
