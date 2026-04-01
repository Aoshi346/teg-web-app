"use client";

import React from "react";
import type { Question } from "@/lib/questions/questions";
import { ImageTooltip } from "@/components/ui/ImageTooltip";
import {
  YesNoInput,
  FrequencyInput,
  TernaryInput,
  StarRatingInput,
  FreeTextInput,
} from "./inputs";

interface QuestionCardProps {
  question: Question;
  value: number | string;
  onChange: (value: number | string) => void;
  onAdvance?: () => void;
  hasError?: boolean;
  isFocused?: boolean;
}

export default function QuestionCard({
  question,
  value,
  onChange,
  onAdvance,
  hasError,
  isFocused,
}: QuestionCardProps) {
  const numVal = typeof value === "number" ? value : Number(value) || 0;
  const strVal = typeof value === "string" ? value : "";

  const renderInput = () => {
    switch (question.answerType) {
      case "yesno":
        return <YesNoInput value={numVal} onChange={onChange} onAdvance={onAdvance} />;
      case "frequency":
        return <FrequencyInput value={numVal} onChange={onChange} onAdvance={onAdvance} />;
      case "ternary":
        return <TernaryInput value={numVal} onChange={onChange} variant="ternary" onAdvance={onAdvance} />;
      case "ternary_na":
        return <TernaryInput value={numVal} onChange={onChange} variant="ternary_na" onAdvance={onAdvance} />;
      case "ternary_info":
        return <TernaryInput value={numVal} onChange={onChange} variant="ternary_info" onAdvance={onAdvance} />;
      case "stars":
        return <StarRatingInput value={numVal} onChange={onChange} onAdvance={onAdvance} />;
      case "text":
        return <FreeTextInput value={strVal} onChange={onChange} />;
      default:
        return null;
    }
  };

  return (
    <div
      id={`qt-${question.id}`}
      className={`flex flex-col h-full bg-white rounded-xl border p-4 transition-all duration-300 scroll-mt-32 ${
        hasError
          ? "border-red-300 ring-2 ring-red-100 ring-offset-1 shadow-sm"
          : isFocused
            ? "border-blue-400 ring-2 ring-blue-100 ring-offset-1 shadow-md"
            : "border-gray-200 shadow-sm hover:border-gray-300 hover:shadow-md"
      }`}
    >
      <div className="mb-3 flex-1">
        <h5 className="font-bold text-gray-900 text-sm leading-snug mb-1 flex items-start justify-between gap-2">
          <span>{question.label}</span>
          {question.relatedImage && (
            <ImageTooltip imageUrl={question.relatedImage} title={question.label}>
              <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-bold bg-blue-50 text-blue-600 border border-blue-100 hover:bg-blue-100 cursor-help flex-shrink-0">
                IMG
              </span>
            </ImageTooltip>
          )}
        </h5>
        {question.helper && (
          <p className="text-xs text-gray-500 leading-relaxed">
            {question.helper}
          </p>
        )}
      </div>
      <div className="mt-auto pt-3 border-t border-gray-100">{renderInput()}</div>
    </div>
  );
}
