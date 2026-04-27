"use client";

import React from "react";

export interface MobileCategoryJumperProps {
  sections: { label: string; shortLabel?: string; answered: number; total: number; isTeg?: boolean }[];
  onJump?: (index: number) => void;
}

export default function MobileCategoryJumper({ sections, onJump }: MobileCategoryJumperProps): React.ReactElement {
  return (
    <div className="m-jumper">
      {sections.map((sec, idx) => (
        <button
          key={sec.label}
          type="button"
          aria-label={sec.label}
          className={`m-jumper-pill${sec.isTeg ? " is-teg" : ""}`}
          onClick={() => onJump?.(idx)}
        >
          <span className="m-jumper-label" aria-hidden="true">{sec.shortLabel ?? sec.label}</span>
          <span className="m-jumper-count">{sec.answered}/{sec.total}</span>
        </button>
      ))}
    </div>
  );
}
