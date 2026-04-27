"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { useForm, FormProvider } from "react-hook-form";
import type { Question } from "@features/evaluations/lib/questions/questions";
import { getProject } from "@features/projects/api/projectService";
import type { Project } from "@features/projects/types/project";
import Banner from "@shared/ui/Banner";
import { useValidation } from "@shared/hooks/useValidation";
import { useEvaluationDraft } from "../hooks/useEvaluationDraft";
import { useScrollSpy } from "../hooks/useScrollSpy";
import { useEvaluationSubmit } from "../hooks/useEvaluationSubmit";
import Rail from "./Rail";
import type { RailSection } from "./Rail";
import MobileCategoryJumper from "./MobileCategoryJumper";
import QuestionCard from "./QuestionCard";
import StickyActionBar from "./StickyActionBar";
import ResultsSummary from "./ResultsSummary";

interface EvaluationFormProps {
  projectId?: string | null;
  typeParam?: string;
  questions: Question[];
  kind?: "review" | "defense";
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
  kind = "review",
}: EvaluationFormProps) {
  const router = useRouter();
  const documentType = typeParam.toLowerCase() === "tesis" ? "Tesis" : "Proyecto";

  const filteredQuestions = questions.filter(
    (q) => !q.documentType || q.documentType === "Both" || q.documentType === documentType,
  );

  const sections = [...new Set(filteredQuestions.map((q) => q.section || "Sección"))];

  const [projectData, setProjectData] = useState<Project | null>(null);
  useEffect(() => {
    if (!projectId) return;
    const id = parseInt(projectId);
    if (!Number.isNaN(id)) getProject(id).then((p) => p && setProjectData(p));
  }, [projectId]);

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
    kind,
  );
  const { showBanner, bannerProps } = useValidation();

  const [comments, setComments] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submittedData, setSubmittedData] = useState<SubmittedData | null>(null);
  const [focusedQId, setFocusedQId] = useState<string | null>(null);
  const [errorQId, setErrorQId] = useState<string | null>(null);

  const defaults = buildDefaults();
  const methods = useForm<{ ratings: Ratings }>({
    defaultValues: { ratings: defaults },
  });
  const { watch, setValue } = methods;
  const ratings = watch("ratings");

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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const t = setTimeout(() => saveDraft(ratings, comments, 1), 300);
    return () => clearTimeout(t);
  }, [ratings, comments, saveDraft]);

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
        if (typeof el.scrollIntoView === "function") {
          el.scrollIntoView({ behavior: "smooth", block: "center" });
        }
        setFocusedQId(qid);
        setTimeout(() => setFocusedQId(null), 2500);
      }
    }, 100);
  }, []);

  const findMissingGlobal = useCallback(() => {
    return filteredQuestions.find((q) => isQuestionMissing(q));
  }, [filteredQuestions, isQuestionMissing]);

  const advanceToNext = useCallback(
    (currentQId: string) => {
      const idx = filteredQuestions.findIndex((q) => q.id === currentQId);
      if (idx === -1) return;
      for (let i = idx + 1; i < filteredQuestions.length; i++) {
        if (isQuestionMissing(filteredQuestions[i])) {
          scrollToQuestion(filteredQuestions[i].id);
          return;
        }
      }
    },
    [filteredQuestions, isQuestionMissing, scrollToQuestion],
  );

  const handleFormSubmit = useCallback(async () => {
    const missing = findMissingGlobal();
    if (missing) {
      setErrorQId(missing.id);
      scrollToQuestion(missing.id);
      return;
    }

    setIsSubmitting(true);
    setErrorQId(null);
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
  }, [findMissingGlobal, ratings, comments, submit, clearDraft, showBanner, scrollToQuestion]);

  const handleClearDraft = useCallback(() => {
    clearDraft();
    const fresh: Ratings = {};
    for (const q of filteredQuestions) {
      fresh[q.id] = q.answerType === "text" ? "" : 0;
    }
    setValue("ratings", fresh);
    setComments("");
    setErrorQId(null);
    showBanner("Borrador limpiado.", "success");
  }, [clearDraft, filteredQuestions, setValue, showBanner]);

  const handleJumpToMissing = useCallback(() => {
    if (errorQId) scrollToQuestion(errorQId);
  }, [errorQId, scrollToQuestion]);

  // Build rail sections
  const railSections: RailSection[] = sections.map((section, idx) => {
    const sectionQs = filteredQuestions.filter((q) => q.section === section);
    const subsectionNames = [...new Set(sectionQs.map((q) => q.subsection || "General"))];
    const answered = sectionQs.filter((q) => q.answerType !== "text" && !isQuestionMissing(q)).length;
    const total = sectionQs.filter((q) => q.answerType !== "text").length;
    const isTeg = !section.toLowerCase().includes("diagramaci");

    return {
      label: section,
      numeral: String(idx + 1).padStart(2, "0"),
      total,
      answered,
      isTeg,
      subsections: subsectionNames.map((sub) => {
        const subQs = sectionQs.filter((q) => (q.subsection || "General") === sub);
        const subAnswered = subQs.filter((q) => q.answerType !== "text" && !isQuestionMissing(q)).length;
        const subTotal = subQs.filter((q) => q.answerType !== "text").length;
        return {
          label: sub,
          anchor: slugify(sub),
          answered: subAnswered,
          total: subTotal,
        };
      }),
    };
  });

  // Build project title
  const projectTitle = projectData
    ? (projectData as { studentName?: string; authorName?: string }).studentName ||
      (projectData as { authorName?: string }).authorName ||
      `${documentType} #${projectId}`
    : `${documentType} ${projectId ? `#${projectId}` : ""}`;

  // Compute global question numerals (01–20)
  const questionNumerals: Record<string, string> = {};
  let numeralIdx = 0;
  for (const section of sections) {
    const sectionQs = filteredQuestions.filter((q) => q.section === section);
    for (const q of sectionQs) {
      numeralIdx++;
      questionNumerals[q.id] = String(numeralIdx).padStart(2, "0");
    }
  }

  const diagramacionCount = filteredQuestions.filter(
    (q) => q.section?.toLowerCase().includes("diagramaci")
  ).length;
  const contenidoCount = filteredQuestions.filter(
    (q) => !q.section?.toLowerCase().includes("diagramaci") && q.section?.toLowerCase().includes("contenido")
  ).length;

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

      {/* Hero */}
      <div className="ev-hero">
        <div className="ev-hero-eyebrow">
          <span className="ev-hero-pill">
            Evaluación · {documentType} {projectId ? `#${projectId.padStart(3, "0")}` : ""} · Revisión
          </span>
        </div>
        <h2 className="ev-hero-title font-display">{projectTitle}</h2>
        <p className="ev-hero-lede">
          Evalúe cada criterio respondiendo las preguntas en orden.
        </p>
        <div className="ev-hero-strip">
          <div className="ev-hero-stat">
            <span className="ev-hero-stat-n">{diagramacionCount}</span>
            <span className="ev-hero-stat-l">Diagramación</span>
          </div>
          <div className="ev-hero-stat">
            <span className="ev-hero-stat-n">{contenidoCount}</span>
            <span className="ev-hero-stat-l">Contenido</span>
          </div>
          <div className="ev-hero-stat">
            <span className="ev-hero-stat-n">{answeredCount}</span>
            <span className="ev-hero-stat-l">Respondidas</span>
          </div>
        </div>
      </div>

      {/* Mobile category jumper */}
      <MobileCategoryJumper
        sections={railSections.map((s) => ({
          label: s.label,
          answered: s.answered,
          total: s.total,
          isTeg: s.isTeg,
        }))}
        onJump={(idx) => {
          const section = sections[idx];
          if (!section) return;
          const firstQ = filteredQuestions.find((q) => q.section === section);
          if (firstQ) scrollToQuestion(firstQ.id);
        }}
      />

      {/* Validation error banner */}
      {errorQId && (
        <div className="err-banner">
          <span className="err-banner-msg">Falta responder 1 pregunta obligatoria</span>
          <button
            type="button"
            className="err-banner-jump"
            onClick={handleJumpToMissing}
          >
            Saltar a falta
          </button>
        </div>
      )}

      <FormProvider {...methods}>
        <div className="ev-layout">
          {/* Feed */}
          <div className="ev-feed">
            {sections.map((section) => {
              const isTeg = !section.toLowerCase().includes("diagramaci");
              const sectionQs = filteredQuestions.filter((q) => q.section === section);
              const subsectionNames = [...new Set(sectionQs.map((q) => q.subsection || "General"))];
              const sectionAnswered = sectionQs.filter(
                (q) => q.answerType !== "text" && !isQuestionMissing(q)
              ).length;
              const sectionTotal = sectionQs.filter((q) => q.answerType !== "text").length;

              return (
                <div key={section}>
                  {/* Sticky ribbon */}
                  <div className={`ribbon${isTeg ? " is-teg" : ""}`} aria-label={section} data-section={section}>
                    <div className="ribbon-info">
                      <span className="ribbon-label">{section}</span>
                      <span className="ribbon-desc">
                        {sectionQs.length} preguntas
                      </span>
                    </div>
                    <div className="ribbon-progress">
                      <span className="ribbon-frac font-display">
                        <em>{sectionAnswered}</em>/{sectionTotal}
                      </span>
                    </div>
                  </div>

                  {/* Questions by subsection */}
                  {subsectionNames.map((sub) => {
                    const subId = `subsection-${slugify(sub)}`;
                    const qs = sectionQs.filter((q) => (q.subsection || "General") === sub);
                    return (
                      <div key={sub} id={subId} className="ev-subsection">
                        <h4 className="ev-sub-title">{sub}</h4>
                        <div className="ev-questions">
                          {qs.map((q) => (
                            <QuestionCard
                              key={q.id}
                              question={q}
                              value={ratings[q.id]}
                              onChange={(v) => {
                                setValue(`ratings.${q.id}`, v, { shouldDirty: true });
                              }}
                              onAdvance={() => advanceToNext(q.id)}
                              hasError={errorQId === q.id}
                              isFocused={focusedQId === q.id}
                              numeral={questionNumerals[q.id] || "01"}
                            />
                          ))}
                        </div>
                      </div>
                    );
                  })}
                </div>
              );
            })}

            {/* Comments — always rendered at end of feed */}
            <div className="ev-comments">
              <label className="ev-comments-label">
                Comentarios adicionales (opcional)
              </label>
              <textarea
                value={comments}
                onChange={(e) => setComments(e.target.value)}
                rows={3}
                className="ev-comments-textarea"
                placeholder={`Observaciones generales sobre el ${documentType.toLowerCase()}...`}
              />
            </div>
          </div>

          {/* Right rail */}
          <Rail
            sections={railSections}
            activeAnchor={activeSubsection}
            onAnchorClick={scrollToSub}
            answeredCount={answeredCount}
            totalRequired={totalRequired}
            autosaving={false}
          />
        </div>
      </FormProvider>

      <StickyActionBar
        answeredCount={answeredCount}
        totalRequired={totalRequired}
        isSubmitting={isSubmitting}
        onSubmit={handleFormSubmit}
        onCancel={() => router.back()}
        onClearDraft={handleClearDraft}
        errorMode={false}
        onJumpToMissing={handleJumpToMissing}
      />
    </>
  );
}
