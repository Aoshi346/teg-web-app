"use client";

import React from "react";
import type { Question } from "@features/evaluations/lib/questions/questions";
import { ImageTooltip } from "@shared/ui/ImageTooltip";
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
  numeral: string;
}

export default function QuestionCard({
  question,
  value,
  onChange,
  onAdvance,
  hasError,
  numeral,
}: QuestionCardProps) {
  const numVal = typeof value === "number" ? value : Number(value) || 0;
  const strVal = typeof value === "string" ? value : "";

  const isDone = question.answerType === "text"
    ? strVal.trim().length > 0
    : numVal > 0;

  const statusPill = hasError ? "Falta" : isDone ? "Respondida" : "Pendiente";

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
      className={`qcard${isDone ? " done" : ""}${hasError ? " error" : ""}`}
    >
      <div className="qcard-header">
        <span className="qcard-num font-display">{numeral}</span>
        <div className="qcard-body">
          <div className="qcard-label-row">
            <h5 className="qcard-label">{question.label}</h5>
            {question.relatedImage && (
              <span className="qcard-img-badge">
                <ImageTooltip imageUrl={question.relatedImage} title={question.label}>
                  <span>IMG</span>
                </ImageTooltip>
              </span>
            )}
          </div>
          {question.helper && (
            <p className="qcard-helper">{question.helper}</p>
          )}
        </div>
        <span className="qcard-status">{statusPill}</span>
      </div>
      <div className="qcard-input">{renderInput()}</div>
    </div>
  );
}
