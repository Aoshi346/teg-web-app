"use client";

import React from "react";

export interface RailSection {
  label: string;
  numeral: string;
  total: number;
  answered: number;
  isTeg?: boolean;
  subsections: { label: string; anchor: string; answered: number; total: number }[];
}

export interface RailProps {
  sections: RailSection[];
  activeAnchor?: string | null;
  onAnchorClick?: (anchor: string) => void;
  answeredCount: number;
  totalRequired: number;
  autosaving?: boolean;
}

export default function Rail({
  sections,
  activeAnchor,
  onAnchorClick,
  answeredCount,
  totalRequired,
  autosaving,
}: RailProps): React.ReactElement {
  const pct = totalRequired > 0 ? Math.round((answeredCount / totalRequired) * 100) : 0;

  return (
    <aside className="rail">
      {sections.map((sec) => (
        <div
          key={sec.numeral}
          className={`rail-grp${sec.isTeg ? " is-teg" : ""}`}
        >
          <div className="rail-grp-header">
            <span className="rail-grp-num font-display">{sec.numeral}</span>
            <span className="rail-grp-label">{sec.label}</span>
            <span className="rail-grp-chip">{sec.answered}/{sec.total}</span>
          </div>
          <div className="rail-anchors">
            {sec.subsections.map((sub) => {
              const isActive = activeAnchor === sub.anchor;
              return (
                <button
                  key={sub.anchor}
                  type="button"
                  className={`rail-anchor${isActive ? " active" : ""}`}
                  onClick={() => onAnchorClick?.(sub.anchor)}
                >
                  <span className="rail-dot" />
                  <span className="rail-anchor-label">{sub.label}</span>
                  <span className="rail-anchor-frac">{sub.answered}/{sub.total}</span>
                </button>
              );
            })}
          </div>
        </div>
      ))}

      <div className="rail-summary">
        <span className="font-display rail-summary-frac">{answeredCount}/{totalRequired}</span>
        <div className="rail-summary-bar" style={{ width: `${pct}%` }} />
      </div>

      <div className="rail-draft">
        <span className={`rail-draft-dot${autosaving ? " saving" : " saved"}`} />
        <span className="rail-draft-label">
          {autosaving ? "Guardando..." : "Guardado"}
        </span>
      </div>
    </aside>
  );
}
