import { useEffect, useCallback, useMemo } from "react";
import type { Question } from "@/lib/questions/questions";

type Ratings = Record<string, number | string>;

interface DraftPayload {
  ratings: Ratings;
  comments: string;
  page: number;
}

export function useEvaluationDraft(
  typeParam: string,
  projectId: string | null | undefined,
  questions: Question[],
) {
  const key = useMemo(
    () => `teg_eval_draft:${typeParam}:${projectId ?? "new"}`,
    [typeParam, projectId],
  );

  const loadDraft = useCallback((): Partial<DraftPayload> => {
    try {
      const raw = localStorage.getItem(key);
      if (!raw) return {};
      return JSON.parse(raw) as Partial<DraftPayload>;
    } catch {
      return {};
    }
  }, [key]);

  const buildDefaults = useCallback((): Ratings => {
    const draft = loadDraft();
    const draftRatings = draft.ratings || {};
    const defaults: Ratings = {};
    for (const q of questions) {
      const existing = draftRatings[q.id];
      defaults[q.id] =
        existing !== undefined ? existing : q.answerType === "text" ? "" : 0;
    }
    return defaults;
  }, [questions, loadDraft]);

  const saveDraft = useCallback(
    (ratings: Ratings, comments: string, page: number) => {
      try {
        localStorage.setItem(key, JSON.stringify({ ratings, comments, page }));
      } catch {}
    },
    [key],
  );

  const clearDraft = useCallback(() => {
    try {
      localStorage.removeItem(key);
    } catch {}
  }, [key]);

  return { loadDraft, buildDefaults, saveDraft, clearDraft };
}
