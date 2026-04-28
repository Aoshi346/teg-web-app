"use client";

import React, { useRef } from "react";
import RoleChip, { RoleName } from "./RoleChip";

const ROLES: RoleName[] = ["Estudiante", "Tutor", "Jurado"];

interface RoleGridProps {
  value: RoleName;
  onChange: (role: RoleName) => void;
}

export default function RoleGrid({ value, onChange }: RoleGridProps) {
  const gridRef = useRef<HTMLDivElement>(null);

  const handleArrow = (direction: -1 | 1) => {
    const currentIdx = ROLES.indexOf(value);
    const nextIdx = (currentIdx + direction + ROLES.length) % ROLES.length;
    const nextRole = ROLES[nextIdx];
    onChange(nextRole);
    requestAnimationFrame(() => {
      const buttons = gridRef.current?.querySelectorAll<HTMLButtonElement>("button[role='radio']");
      buttons?.[nextIdx]?.focus();
    });
  };

  return (
    <div className="lm-field">
      <span className="lm-role-grid-h">— Tu rol</span>
      <div ref={gridRef} className="lm-role-grid" role="radiogroup" aria-label="Rol de usuario">
        {ROLES.map((role) => (
          <RoleChip
            key={role}
            role={role}
            active={value === role}
            onChange={onChange}
            onArrowKey={handleArrow}
          />
        ))}
      </div>
    </div>
  );
}
