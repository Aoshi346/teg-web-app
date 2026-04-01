"use client";

import React, { useState, useEffect, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";
import { useForm, FormProvider } from "react-hook-form";
import type { Question } from "@/lib/questions/questions";
import { getProject } from "@/features/projects/projectService";
import type { Project } from "@/types/project";
import Banner from "@/components/ui/Banner";
import { useValidation } from "@/hooks/useValidation";
import { useEvaluationDraft } from "./hooks/useEvaluationDraft";
import { useScrollSpy } from "./hooks/useScrollSpy";
import { useEvaluationSubmit } from "./hooks/useEvaluationSubmit";
import EvaluationSidebar from "./EvaluationSidebar";
import QuestionCard from "./QuestionCard";
import StickyActionBar from "./StickyActionBar";
import ResultsSummary from "./ResultsSummary";

interface EvaluationFormProps {
  projectId?: string | null;
  typeParam?: string;
  questions: Question[];
}

type Ratings = Record<string, number | string>;

interface SubmittedData {
  score: number;
  passStatus: "Pass" | "Fail";
  ratings: Ratings;
  comments: string;
}

function slugify(t: string) {
  return t.trim().toLowerCase().replace(/\s+/g, "-").replace(/[^\w-]/g, "").replace(/--+/g, "-");
}

export default function EvaluationForm({
  projectId,
  typeParam = "proyecto",
  questions,
}: EvaluationFormProps) {
  const router = useRouter();
  const documentType = typeParam.toLowerCase() === "tesis" ? "Tesis" : "Proyecto";

  // Filter questions for this document type
  const filteredQuestions = questions.filter(
    (q) => !q.documentType || q.documentType === "Both" || q.documentType === documentType,
  );

  const sections = [...new Set(filteredQuestions.map((q) => q.section || "Sección"))];
  const totalPages = Math.max(1, sections.length);

  // Project data
  const [projectData, setProjectData] = useState<Project | null>(null);
  useEffect(() => {
    if (!projectId) return;
    const id = parseInt(projectId);
    if (!Number.isNaN(id)) getProject(id).then((p) => p && setProjectData(p));
  }, [projectId]);

  // Hooks
  const { buildDefaults, saveDraft, clearDraft, loadDraft } = useEvaluationDraft(
    typeParam,
    projectId,
    filteredQuestions,
  );
  const { activeId: activeSubsection, scrollTo: scrollToSub } = useScrollSpy("subsection-");
  const { submit } = useEvaluationSubmit(
    projectId,
    documentType,
    typeParam,
    filteredQuestions,
    projectData,
  );
  const { showBanner, bannerProps } = useValidation();

  // State
  const [page, setPage] = useState(1);
  const [comments, setComments] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submittedData, setSubmittedData] = useState<SubmittedData | null>(null);
  const [focusedQId, setFocusedQId] = useState<string | null>(null);

  // RHF for ratings
  const defaults = buildDefaults();
  const methods = useForm<{ ratings: Ratings }>({
    defaultValues: { ratings: defaults },
  });
  const { watch, setValue, getValues } = methods;
  const ratings = watch("ratings");

  // Load draft on mount
  useEffect(() => {
    const draft = loadDraft();
    if (draft.ratings) {
      const merged: Ratings = {};
      for (const q of filteredQuestions) {
        merged[q.id] = draft.ratings[q.id] ?? (q.answerType === "text" ? "" : 0);
      }
      setValue("ratings", merged);
    }
    if (typeof draft.comments === "string") setComments(draft.comments);
    if (typeof draft.page === "number") setPage(draft.page);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Auto-save draft (debounced)
  useEffect(() => {
    const t = setTimeout(() => saveDraft(ratings, comments, page), 300);
    return () => clearTimeout(t);
  }, [ratings, comments, page, saveDraft]);

  // Derived
  const currentSection = sections[Math.max(0, Math.min(page - 1, sections.length - 1))];
  const pageQuestions = filteredQuestions.filter((q) => q.section === currentSection);
  const subsections = [...new Set(pageQuestions.map((q) => q.subsection || "General"))];

  const isDiagramacion = currentSection?.toLowerCase().includes("diagramaci");

  // Helpers
  const isQuestionMissing = useCallback(
    (q: Question) => {
      if (q.answerType === "text") return false;
      const v = ratings[q.id];
      const n = typeof v === "number" ? v : Number(v) || 0;
      return n <= 0;
    },
    [ratings],
  );

  const totalRequired = filteredQuestions.filter((q) => q.answerType !== "text").length;
  const answeredCount = filteredQuestions.filter(
    (q) => q.answerType !== "text" && !isQuestionMissing(q),
  ).length;

  const scrollToQuestion = useCallback((qid: string) => {
    setTimeout(() => {
      const el = document.getElementById(`qt-${qid}`);
      if (el) {
        el.scrollIntoView({ behavior: "smooth", block: "center" });
        setFocusedQId(qid);
        setTimeout(() => setFocusedQId(null), 2500);
      }
    }, 100);
  }, []);

  const findMissing = useCallback(
    (section: string) => {
      const qs = filteredQuestions.filter((q) => q.section === section);
      return qs.find((q) => isQuestionMissing(q));
    },
    [filteredQuestions, isQuestionMissing],
  );

  // Navigation
  const goToSection = useCallback(
    (section: string) => {
      const idx = sections.indexOf(section);
      if (idx === -1) return;
      setPage(idx + 1);
    },
    [sections],
  );

  const handleNext = useCallback(() => {
    const missing = findMissing(currentSection);
    if (missing) {
      showBanner("Complete todas las preguntas de esta sección antes de continuar.", "error");
      scrollToQuestion(missing.id);
      return;
    }
    setPage((p) => Math.min(totalPages, p + 1));
  }, [currentSection, findMissing, showBanner, scrollToQuestion, totalPages]);

  const handlePrev = useCallback(() => {
    setPage((p) => Math.max(1, p - 1));
  }, []);

  // Auto-advance: focus next unanswered question after answering
  const advanceToNext = useCallback(
    (currentQId: string) => {
      const idx = pageQuestions.findIndex((q) => q.id === currentQId);
      if (idx === -1) return;
      for (let i = idx + 1; i < pageQuestions.length; i++) {
        if (isQuestionMissing(pageQuestions[i])) {
          scrollToQuestion(pageQuestions[i].id);
          return;
        }
      }
    },
    [pageQuestions, isQuestionMissing, scrollToQuestion],
  );

  // Submit
  const handleFormSubmit = useCallback(async () => {
    // Global validation
    for (const section of sections) {
      const missing = findMissing(section);
      if (missing) {
        const targetPage = sections.indexOf(section) + 1;
        setPage(targetPage);
        showBanner("Complete todas las preguntas obligatorias.", "error");
        scrollToQuestion(missing.id);
        return;
      }
    }

    setIsSubmitting(true);
    try {
      await submit(
        ratings,
        comments,
        (result) => {
          setSubmittedData(result);
          clearDraft();
          showBanner("Evaluación enviada con éxito.", "success");
        },
        (msg) => showBanner(msg, "error"),
      );
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Error al enviar.";
      showBanner(msg, "error");
    } finally {
      setIsSubmitting(false);
    }
  }, [sections, findMissing, ratings, comments, submit, clearDraft, showBanner, scrollToQuestion]);

  const handleClearDraft = useCallback(() => {
    clearDraft();
    const fresh: Ratings = {};
    for (const q of filteredQuestions) {
      fresh[q.id] = q.answerType === "text" ? "" : 0;
    }
    setValue("ratings", fresh);
    setComments("");
    setPage(1);
    showBanner("Borrador limpiado.", "success");
  }, [clearDraft, filteredQuestions, setValue, showBanner]);

  // Sidebar section click with validation
  const handleSidebarSection = useCallback(
    (section: string) => {
      const targetIdx = sections.indexOf(section);
      const currentIdx = page - 1;

      // Allow backward navigation freely
      if (targetIdx <= currentIdx) {
        goToSection(section);
        return;
      }

      // Forward: validate current section
      const missing = findMissing(currentSection);
      if (missing) {
        showBanner("Complete la sección actual antes de avanzar.", "error");
        scrollToQuestion(missing.id);
        return;
      }
      goToSection(section);
    },
    [sections, page, currentSection, goToSection, findMissing, showBanner, scrollToQuestion],
  );

  if (submittedData) {
    return (
      <>
        {bannerProps.visible && (
          <div className="fixed top-4 inset-x-0 z-[9999] flex justify-center px-4 pointer-events-none">
            <div className="pointer-events-auto w-full max-w-3xl">
              <Banner {...bannerProps} />
            </div>
          </div>
        )}
        <ResultsSummary
          score={submittedData.score}
          passStatus={submittedData.passStatus}
          ratings={submittedData.ratings}
          comments={submittedData.comments}
          questions={filteredQuestions}
          typeParam={typeParam}
          onReset={() => {
            setSubmittedData(null);
            handleClearDraft();
          }}
        />
      </>
    );
  }

  return (
    <>
      {bannerProps.visible && (
        <div className="fixed top-4 inset-x-0 z-[9999] flex justify-center px-4 pointer-events-none">
          <div className="pointer-events-auto w-full max-w-3xl">
            <Banner {...bannerProps} />
          </div>
        </div>
      )}

      {/* Header */}
      <div className="mb-5">
        <h2 className="text-2xl font-bold text-gray-900">
          Evaluación del {documentType} {projectId ? `#${projectId}` : ""}
        </h2>
        <p className="text-sm text-gray-500 mt-1">
          {filteredQuestions.length} preguntas en {sections.length} secciones
        </p>
      </div>

      <FormProvider {...methods}>
        <div className="flex gap-6">
          {/* Sidebar — desktop only */}
          <aside className="hidden lg:block w-56 flex-shrink-0">
            <div className="sticky top-4 space-y-4">
              <EvaluationSidebar
                questions={filteredQuestions}
                ratings={ratings}
                sections={sections}
                currentSection={currentSection}
                onSectionClick={handleSidebarSection}
                onSubsectionClick={scrollToSub}
                activeSubsection={activeSubsection}
              />

              {/* Global progress */}
              <div className="bg-white rounded-lg border border-gray-100 p-3 shadow-sm">
                <p className="text-[11px] font-bold text-gray-400 uppercase tracking-wider mb-2">
                  Progreso total
                </p>
                <div className="h-2 bg-gray-100 rounded-full overflow-hidden mb-1.5">
                  <div
                    className="h-full bg-gradient-to-r from-blue-500 to-indigo-600 rounded-full transition-all duration-500"
                    style={{ width: `${totalRequired ? Math.round((answeredCount / totalRequired) * 100) : 0}%` }}
                  />
                </div>
                <p className="text-xs text-gray-500 font-semibold">
                  {answeredCount}/{totalRequired} respondidas
                </p>
              </div>
            </div>
          </aside>

          {/* Main content */}
          <div className="flex-1 min-w-0 pb-20">
            {/* Section header with color shift */}
            <div
              className={`rounded-xl border-l-4 pl-4 pr-4 py-3 mb-5 ${
                isDiagramacion
                  ? "bg-blue-50/60 border-blue-600"
                  : "bg-emerald-50/60 border-emerald-600"
              }`}
            >
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-bold text-gray-900">
                    {currentSection}
                  </h3>
                  <p className="text-xs text-gray-500 mt-0.5">
                    Sección {page} de {totalPages} · {pageQuestions.length} pregunta
                    {pageQuestions.length !== 1 ? "s" : ""}
                  </p>
                </div>

                {/* Mobile section pills */}
                <div className="flex lg:hidden gap-1.5">
                  {sections.map((s, i) => (
                    <button
                      key={s}
                      type="button"
                      onClick={() => handleSidebarSection(s)}
                      className={`w-8 h-8 rounded-lg text-xs font-bold transition-all ${
                        i + 1 === page
                          ? "bg-blue-600 text-white shadow-md"
                          : "bg-white text-gray-500 border border-gray-200 hover:bg-gray-50"
                      }`}
                    >
                      {i + 1}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Questions by subsection */}
            {subsections.map((sub) => {
              const subId = `subsection-${slugify(sub)}`;
              const qs = pageQuestions.filter((q) => (q.subsection || "General") === sub);
              return (
                <div key={sub} id={subId} className="mb-6">
                  <div className="flex items-center gap-2 mb-3">
                    <div
                      className={`w-2 h-2 rounded-full ${isDiagramacion ? "bg-blue-500" : "bg-emerald-500"}`}
                    />
                    <h4 className="text-sm font-semibold text-gray-700">
                      {sub}
                    </h4>
                  </div>
                  <div className="grid gap-4 sm:grid-cols-1 lg:grid-cols-2">
                    {qs.map((q) => (
                      <QuestionCard
                        key={q.id}
                        question={q}
                        value={ratings[q.id]}
                        onChange={(v) => {
                          setValue(`ratings.${q.id}`, v, { shouldDirty: true });
                        }}
                        onAdvance={() => advanceToNext(q.id)}
                        hasError={false}
                        isFocused={focusedQId === q.id}
                      />
                    ))}
                  </div>
                </div>
              );
            })}

            {/* Comments on last page */}
            {page === totalPages && (
              <div className="mt-6">
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Comentarios adicionales (opcional)
                </label>
                <textarea
                  value={comments}
                  onChange={(e) => setComments(e.target.value)}
                  rows={3}
                  className="w-full border border-gray-200 rounded-lg p-3 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all resize-none"
                  placeholder={`Observaciones generales sobre el ${documentType.toLowerCase()}...`}
                />
              </div>
            )}
          </div>
        </div>
      </FormProvider>

      {/* Sticky footer */}
      <StickyActionBar
        page={page}
        totalPages={totalPages}
        answeredCount={answeredCount}
        totalRequired={totalRequired}
        isSubmitting={isSubmitting}
        onPrev={handlePrev}
        onNext={handleNext}
        onSubmit={handleFormSubmit}
        onCancel={() => router.back()}
        onClearDraft={handleClearDraft}
      />
    </>
  );
}
