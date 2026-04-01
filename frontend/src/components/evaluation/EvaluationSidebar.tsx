"use client";

import React from "react";
import { CheckCircle, Circle } from "lucide-react";
import type { Question } from "@/lib/questions/questions";

interface SidebarProps {
  questions: Question[];
  ratings: Record<string, number | string>;
  sections: string[];
  currentSection: string;
  onSectionClick: (section: string) => void;
  onSubsectionClick: (sub: string) => void;
  activeSubsection: string | null;
}

function slugify(text: string) {
  return text.trim().toLowerCase().replace(/\s+/g, "-").replace(/[^\w-]/g, "").replace(/--+/g, "-");
}

function isAnswered(q: Question, ratings: Record<string, number | string>): boolean {
  if (q.answerType === "text") return true;
  const v = ratings[q.id];
  const num = typeof v === "number" ? v : Number(v) || 0;
  return num > 0;
}

export default function EvaluationSidebar({
  questions,
  ratings,
  sections,
  currentSection,
  onSectionClick,
  onSubsectionClick,
  activeSubsection,
}: SidebarProps) {
  return (
    <nav className="space-y-1">
      {sections.map((section) => {
        const sectionQs = questions.filter((q) => q.section === section);
        const answered = sectionQs.filter((q) => isAnswered(q, ratings)).length;
        const total = sectionQs.length;
        const complete = answered === total;
        const isActive = section === currentSection;

        const subsections = [
          ...new Set(sectionQs.map((q) => q.subsection).filter(Boolean)),
        ] as string[];

        const isDiagramacion = section.toLowerCase().includes("diagramaci");

        return (
          <div key={section}>
            <button
              type="button"
              onClick={() => onSectionClick(section)}
              className={`w-full flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-left text-sm font-semibold transition-all ${
                isActive
                  ? isDiagramacion
                    ? "bg-blue-50 text-blue-800 border-l-[3px] border-blue-600"
                    : "bg-emerald-50 text-emerald-800 border-l-[3px] border-emerald-600"
                  : "text-gray-600 hover:bg-gray-50 border-l-[3px] border-transparent"
              }`}
            >
              {complete ? (
                <CheckCircle className="w-4 h-4 text-emerald-500 flex-shrink-0" />
              ) : (
                <Circle className="w-4 h-4 text-gray-300 flex-shrink-0" />
              )}
              <span className="flex-1 truncate">{section}</span>
              <span
                className={`text-[10px] font-bold px-1.5 py-0.5 rounded-full ${
                  complete
                    ? "bg-emerald-100 text-emerald-700"
                    : "bg-gray-100 text-gray-500"
                }`}
              >
                {answered}/{total}
              </span>
            </button>

            {/* Subsections visible when active */}
            {isActive && subsections.length > 0 && (
              <div className="ml-7 mt-1 space-y-0.5">
                {subsections.map((sub) => {
                  const subQs = sectionQs.filter(
                    (q) => q.subsection === sub,
                  );
                  const subAnswered = subQs.filter((q) =>
                    isAnswered(q, ratings),
                  ).length;
                  const subComplete = subAnswered === subQs.length;
                  const subActive = activeSubsection === slugify(sub);

                  return (
                    <button
                      key={sub}
                      type="button"
                      onClick={() => onSubsectionClick(slugify(sub))}
                      className={`w-full flex items-center gap-2 px-2.5 py-1.5 rounded-md text-xs transition-all ${
                        subActive
                          ? "bg-white shadow-sm text-gray-900 font-semibold"
                          : "text-gray-500 hover:text-gray-700 hover:bg-gray-50"
                      }`}
                    >
                      <span
                        className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${
                          subComplete ? "bg-emerald-500" : "bg-gray-300"
                        }`}
                      />
                      <span className="flex-1 truncate text-left">{sub}</span>
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        );
      })}
    </nav>
  );
}
