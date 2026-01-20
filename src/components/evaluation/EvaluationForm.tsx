"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import {
  FREQUENCY_OPTIONS,
  YESNO_OPTIONS,
  Question,
} from "@/lib/questions/questions";
import {
  calculateScore,
  getPassStatus,
  MAX_SCORE,
  PASSING_SCORE,
} from "@/lib/questions/scoring";
import Banner from "@/components/ui/Banner";
import { ImageTooltip } from "@/components/ui/ImageTooltip";

import { useValidation } from "@/hooks/useValidation";
import {
  Project,
  getProyectos,
  getTesis,
  updateProyecto,
  updateTesis,
} from "@/lib/data/mockData";

interface EvaluationFormProps {
  projectId?: string | null;
  typeParam?: string; // 'proyecto' | 'tesis'
  questions: Question[]; // required question set to evaluate
}

type SubmittedData = {
  ratings: Record<string, number | string>;
  comments: string;
  gradedAt: string;
  score: number;
  passStatus: "Pass" | "Fail";
} | null;

export default function EvaluationForm({
  projectId,
  typeParam = "proyecto",
  questions,
}: EvaluationFormProps) {
  const router = useRouter();
  const documentType =
    (typeParam || "proyecto").toLowerCase() === "tesis" ? "Tesis" : "Proyecto";

  // Fetch project data
  const [projectData, setProjectData] = useState<Project | null>(null);

  React.useEffect(() => {
    if (!projectId) return;

    const id = parseInt(projectId);
    const list = documentType === "Tesis" ? getTesis() : getProyectos();
    const found = list.find((p) => p.id === id);

    if (found) {
      setProjectData(found);
    }
  }, [projectId, documentType]);

  const sourceQuestions = questions;
  const filteredQuestions = sourceQuestions.filter(
    (q) =>
      !q.documentType ||
      q.documentType === "Both" ||
      q.documentType === documentType,
  );

  const [ratings, setRatings] = useState<Record<string, number | string>>(
    () => {
      const r: Record<string, number | string> = {};
      for (const q of filteredQuestions) {
        r[q.id] = q.answerType === "text" ? "" : 0;
      }
      return r;
    },
  );

  const sections = [
    ...new Set(filteredQuestions.map((q) => q.section || "Sección")),
  ];
  const totalPages = Math.max(1, sections.length);
  const [page, setPage] = useState<number>(1);
  const [, setActiveQuestion] = useState<Question | null>(null);
  const [comments, setComments] = useState<string>("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submittedData, setSubmittedData] = useState<SubmittedData>(null);
  const [, setActiveSubsection] = useState<string | null>(null);

  const { showBanner, bannerProps } = useValidation();

  const setRating = (qid: string, value: number | string) => {
    setRatings((prev) => ({ ...prev, [qid]: value }));
  };

  const slugify = (text: string) =>
    text
      .toString()
      .trim()
      .toLowerCase()
      .replace(/\s+/g, "-")
      .replace(/[^\w-]/g, "")
      .replace(/--+/g, "-")
      .replace(/^-+|-+$/g, "");

  const SCORE_COLOR_MAP = [
    "bg-red-50 text-red-700 border-red-200",
    "bg-orange-50 text-orange-700 border-orange-200",
    "bg-yellow-50 text-yellow-800 border-yellow-200",
    "bg-sky-50 text-sky-700 border-sky-200",
    "bg-green-50 text-green-700 border-green-200",
  ];

  const getAnswerLabel = (
    question: Question,
    value: number | string | undefined,
  ): string => {
    if (question.answerType === "text") {
      const textValue = typeof value === "string" ? value.trim() : "";
      return textValue.length > 0 ? textValue : "Sin respuesta";
    }

    const numericValue = typeof value === "number" ? value : 0;
    if (numericValue === 0) return "Sin respuesta";
    switch (question.answerType) {
      case "yesno":
        const yesNoOption = YESNO_OPTIONS.find(
          (opt) => opt.value === numericValue,
        );
        return yesNoOption?.label || "Sin respuesta";
      case "frequency":
        const freqOption = FREQUENCY_OPTIONS.find(
          (opt) => opt.value === numericValue,
        );
        return freqOption?.label || "Sin respuesta";
      case "stars":
        return `Puntuación ${numericValue} / 5`;
      default:
        return "Sin respuesta";
    }
  };

  const renderAnswerInput = (question: Question) => {
    const rawValue = ratings[question.id];
    const currentRating =
      typeof rawValue === "number" ? rawValue : Number(rawValue) || 0;
    const currentText = typeof rawValue === "string" ? rawValue : "";

    switch (question.answerType) {
      case "yesno":
        return (
          <div className="grid grid-cols-2 gap-3 w-full">
            {YESNO_OPTIONS.map((option) => {
              const isActive = currentRating === option.value;
              const isYes =
                option.label.toLowerCase() === "sí" ||
                option.label.toLowerCase() === "si";

              let activeClass = "";
              if (isActive) {
                // Determine color based on option (Yes usually Green/Blue, No usually Red/Gray)
                // Assuming option.color might already bring classes, but let's override for a cleaner look if needed
                // Or revert to using the provided option.color correctly but with better base styles
                activeClass = isYes
                  ? "bg-emerald-500 text-white border-emerald-500 shadow-md shadow-emerald-500/20"
                  : "bg-rose-500 text-white border-rose-500 shadow-md shadow-rose-500/20";
              } else {
                activeClass =
                  "bg-white text-gray-600 border-gray-200 hover:bg-gray-50 hover:border-gray-300";
              }

              return (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => setRating(question.id, option.value)}
                  className={`relative flex items-center justify-center py-3 px-6 rounded-xl text-sm font-bold border transition-all duration-300 transform active:scale-[0.98] ${activeClass} ${!isActive && "hover:shadow-md hover:-translate-y-0.5"}`}
                >
                  {/* Optional: Add icons if desired for friendly UI */}
                  {isActive && (
                    <span className="absolute left-3 animate-fade-in">
                      {isYes ? (
                        <svg
                          className="w-4 h-4"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                          strokeWidth="2.5"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            d="M5 13l4 4L19 7"
                          />
                        </svg>
                      ) : (
                        <svg
                          className="w-4 h-4"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                          strokeWidth="2.5"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            d="M6 18L18 6M6 6l12 12"
                          />
                        </svg>
                      )}
                    </span>
                  )}
                  {option.label}
                </button>
              );
            })}
          </div>
        );

      case "frequency":
        return (
          <div className="space-y-2 pt-2">
            {FREQUENCY_OPTIONS.map((option) => (
              <button
                key={option.value}
                type="button"
                onClick={() => setRating(question.id, option.value)}
                className={`w-full px-4 py-3 rounded-xl text-sm font-medium border transition-all text-left duration-200 ${
                  currentRating === option.value
                    ? `${option.color} shadow-md ring-2 ring-offset-1 ring-transparent`
                    : "bg-white text-gray-600 border-gray-200 hover:border-gray-300 hover:bg-gray-50 hover:shadow-sm"
                }`}
              >
                {option.label}
              </button>
            ))}
          </div>
        );

      case "stars":
        return (
          <div className="pt-2 space-y-2">
            <div className="grid grid-cols-5 gap-2">
              {Array.from({ length: 5 }).map((_, i) => {
                const val = i + 1;
                const isSelected = currentRating === val;
                const palette = SCORE_COLOR_MAP[i];
                return (
                  <button
                    key={val}
                    type="button"
                    onClick={() => setRating(question.id, val)}
                    aria-label={`Puntuación ${val}`}
                    className={`w-full px-3 py-2 rounded-lg text-sm font-semibold border-2 transition-all ${
                      isSelected
                        ? `${palette} shadow-md scale-[1.02]`
                        : "bg-white text-gray-700 border-gray-200 hover:border-blue-300 hover:bg-blue-50"
                    }`}
                  >
                    {val}
                  </button>
                );
              })}
            </div>
            {currentRating > 0 && (
              <p className="text-xs text-gray-600 text-center">
                Puntuación seleccionada: {currentRating} / 5
              </p>
            )}
          </div>
        );

      case "text":
        return (
          <div className="pt-2">
            <textarea
              value={currentText}
              onChange={(e) => setRating(question.id, e.target.value)}
              rows={4}
              className="w-full bg-white border border-gray-200 rounded-xl p-4 text-sm shadow-sm focus:border-blue-500 focus:ring-4 focus:ring-blue-500/10 transition-all resize-none placeholder:text-gray-400"
              placeholder="Escriba sus observaciones o recomendaciones..."
            />
            <p className="text-xs text-gray-500 mt-2">
              Este campo es de texto libre y no afecta el puntaje numérico.
            </p>
          </div>
        );

      default:
        return null;
    }
  };

  const isQuestionMissing = (question: Question) => {
    // Optional types or text don't count as missing
    if (
      question.answerType === "text" ||
      !["yesno", "frequency", "stars"].includes(question.answerType)
    )
      return false;

    const value = ratings[question.id];
    // Strict check for 0 or falsy values for required number types
    const numericValue = typeof value === "number" ? value : Number(value);
    return !numericValue || numericValue <= 0;
  };

  const findMissingIndexInSection = (section?: string) => {
    const sectionQuestions = filteredQuestions.filter(
      (q) => q.section === section,
    );
    return sectionQuestions.findIndex((q) => isQuestionMissing(q));
  };

  const scrollToQuestion = (questionId: string) => {
    setTimeout(() => {
      const el = document.getElementById(`qt-${questionId}`);
      if (el) {
        el.scrollIntoView({ behavior: "smooth", block: "center" });
        el.classList.add("ring-2", "ring-red-500", "ring-offset-2");
        setTimeout(
          () => el.classList.remove("ring-2", "ring-red-500", "ring-offset-2"),
          2000,
        );
      }
    }, 100); // Small delay to allow page render
  };

  const goToPage = (nextPage: number, onSuccess?: () => void) => {
    if (nextPage === page) {
      if (onSuccess) onSuccess();
      return;
    }

    // Allow going backward freely
    if (nextPage > page) {
      const missingIndex = findMissingIndexInSection(currentSection);
      if (missingIndex !== -1) {
        const sectionQuestions = filteredQuestions.filter(
          (q) => q.section === currentSection,
        );
        const missingQuestion = sectionQuestions[missingIndex];

        showBanner(
          "Por favor complete todas las preguntas de la sección actual antes de avanzar.",
          "error",
        );

        if (missingQuestion) {
          scrollToQuestion(missingQuestion.id);
        }
        return;
      }
    }

    const clamped = Math.max(1, Math.min(totalPages, nextPage));
    setPage(clamped);
    if (onSuccess) {
      setTimeout(onSuccess, 50);
    }
  };

  const handleNextSection = () => {
    const missingIndex = findMissingIndexInSection(currentSection);

    if (missingIndex !== -1) {
      const sectionQuestions = filteredQuestions.filter(
        (q) => q.section === currentSection,
      );
      const missingQuestion = sectionQuestions[missingIndex];

      showBanner(
        "Por favor califique todas las preguntas de esta sección antes de continuar.",
        "error",
      );

      if (missingQuestion) {
        scrollToQuestion(missingQuestion.id);
      }
      return;
    }
    setPage((p) => Math.min(totalPages, p + 1));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    // Global validation across sections
    let firstMissingQuestion: Question | undefined;
    const missingSectionIndex = sections.findIndex((section) => {
      const idx = findMissingIndexInSection(section);
      if (idx !== -1) {
        const sectionQuestions = filteredQuestions.filter(
          (q) => q.section === section,
        );
        firstMissingQuestion = sectionQuestions[idx];
        return true;
      }
      return false;
    });

    if (missingSectionIndex !== -1 && firstMissingQuestion) {
      const targetPage = missingSectionIndex + 1;
      setPage(targetPage);

      showBanner(
        "Por favor califique todas las preguntas obligatorias marcadas.",
        "error",
      );

      // improved scroll logic
      scrollToQuestion(firstMissingQuestion.id);
      setIsSubmitting(false);
      return;
    }

    const score = calculateScore(ratings, filteredQuestions);
    const passStatus = getPassStatus(score);

    const payload: SubmittedData = {
      ratings,
      comments,
      gradedAt: new Date().toISOString(),
      score,
      passStatus,
    };

    // Update Project/Tesis with Persistence
    if (projectData && projectId) {
      const updatedProject = {
        ...projectData,
        status: (passStatus === "Pass" ? "checked" : "rejected") as
          | "checked"
          | "rejected"
          | "pending",
        score: score,
        reviewDate: new Date().toISOString().split("T")[0],
      };

      if (documentType === "Tesis") {
        // Tesis specific logic
        // Check if it's stage 1 (based on question q57 passing)
        const isStage1 = filteredQuestions.some((q) => q.id === "q57");
        if (isStage1) {
          // If it's stage 1, preserve Stage 1 passed status if passed
          if (passStatus === "Pass") {
            updatedProject.stage1Passed = true;
          }
        }
        updateTesis(updatedProject);
      } else {
        // Project specific logic for failure attempts
        if (passStatus === "Fail") {
          const currentAttempts = (projectData.failedAttempts || 0) + 1;
          updatedProject.failedAttempts = currentAttempts;
          updatedProject.status = "rejected";

          // Alert logic handled below via banner, but here we set final status
          if (currentAttempts >= 2) {
            // Final failure
            updatedProject.status = "rejected";
          }
        } else {
          updatedProject.status = "checked";
        }
        updateProyecto(updatedProject);
      }
    }

    await new Promise((res) => setTimeout(res, 600));
    setSubmittedData(payload);

    if (documentType !== "Tesis" && passStatus === "Fail") {
      const attempts = (projectData?.failedAttempts || 0) + 1;
      if (attempts >= 2) {
        showBanner(
          "Proyecto rechazado definitivamente (2/2 intentos fallidos). Por favor contacte a su tutor.",
          "error",
        );
      } else {
        showBanner(
          `Proyecto rechazado. Intento ${attempts}/2 utilizado. Puede corregir y re-enviar.`,
          "warning",
        );
      }
    } else {
      showBanner("Evaluación enviada con éxito.", "success");
    }
    setIsSubmitting(false);

    // Redirect after delay
    setTimeout(() => {
      // Find the dashboard URL based on type
      const returnUrl =
        documentType === "Tesis" ? "/dashboard/tesis" : "/dashboard/proyectos";
      router.push(returnUrl);
    }, 2000);
  };

  const allSections = [
    ...new Set(filteredQuestions.map((q) => q.section).filter(Boolean)),
  ] as string[];
  const currentSection =
    sections[Math.max(0, Math.min(page - 1, sections.length - 1))];
  const pageQuestions = filteredQuestions.filter(
    (q) => q.section === currentSection,
  );
  const subsectionsOfCurrent = currentSection
    ? ([
        ...new Set(
          filteredQuestions
            .filter((q) => q.section === currentSection)
            .map((q) => q.subsection),
        ),
      ].filter(Boolean) as string[])
    : [];

  const getPageForSection = (section?: string) => {
    if (!section) return 1;
    const idx = sections.findIndex((s) => s === section);
    return idx === -1 ? 1 : idx + 1;
  };

  const getPageForSubsection = (sub?: string) => {
    if (!sub) return 1;
    const sectionForSub = filteredQuestions.find(
      (q) => q.subsection === sub,
    )?.section;
    return getPageForSection(sectionForSub);
  };

  const scrollToSubsection = (sub?: string) => {
    if (!sub) return;
    const targetId = `subsection-${slugify(sub)}`;
    const el = document.getElementById(targetId);
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  };

  // Observe subsection elements to detect which subsection is in view (for dynamic help sidebar)
  React.useEffect(() => {
    const handler = (entries: IntersectionObserverEntry[]) => {
      const visible = entries
        .filter((e) => e.isIntersecting)
        .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
      if (visible) {
        const id = visible.target.id || null;
        if (id && id.startsWith("subsection-")) {
          const name = id.replace("subsection-", "");
          setActiveSubsection(name);
        }
      }
    };
    const observer = new IntersectionObserver(handler, {
      root: null,
      rootMargin: "-20% 0px -40% 0px",
      threshold: [0.25, 0.5, 0.75],
    });

    const nodes = Array.from(
      document.querySelectorAll("[id^=subsection-]") as NodeListOf<Element>,
    );
    nodes.forEach((n) => observer.observe(n));
    return () => observer.disconnect();
  }, [page]);

  return (
    <>
      {bannerProps.visible && (
        <div className="fixed top-4 inset-x-0 z-[9999] flex justify-center px-4 pointer-events-none">
          <div className="pointer-events-auto w-full max-w-3xl">
            <Banner {...bannerProps} />
          </div>
        </div>
      )}

      <div className="mb-6">
        <h2 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-2">
          Evaluación del {documentType} {projectId ? `#${projectId}` : ""}
        </h2>
        {projectId && (
          <p className="text-sm text-gray-600 mb-2">
            Calificando {documentType.toLowerCase()} con id{" "}
            <strong className="text-blue-600">{projectId}</strong>
          </p>
        )}
        <p className="text-sm sm:text-base text-gray-600">
          Complete la evaluación respondiendo las{" "}
          <strong>{filteredQuestions.length} preguntas</strong> organizadas en{" "}
          <strong>
            {[...new Set(filteredQuestions.map((q) => q.section))].length}{" "}
            secciones
          </strong>
          . Las preguntas utilizan diferentes escalas: Sí/No, frecuencia,
          puntuación (1-5) y texto libre (opcional).
        </p>
      </div>

      {!submittedData ? (
        <div className="flex flex-col lg:flex-row gap-6 lg:gap-10">
          <form
            onSubmit={handleSubmit}
            className="bg-white p-4 sm:p-6 lg:p-8 rounded-xl shadow-lg flex-1 min-w-0"
          >
            <div className="space-y-6">
              <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl border border-blue-100 p-4 shadow-sm">
                <div className="mb-4">
                  <label className="text-xs font-semibold text-gray-700 uppercase tracking-wide mb-2 block">
                    Secciones
                  </label>
                  <div className="flex gap-2 overflow-x-auto pb-1">
                    {allSections.map((s) => {
                      const pageForSection = getPageForSection(s as string);
                      const count = filteredQuestions.filter(
                        (q) => q.section === s,
                      ).length;
                      const isActive = currentSection === s;
                      return (
                        <button
                          key={s}
                          type="button"
                          onClick={() => goToPage(pageForSection)}
                          className={`flex-shrink-0 px-5 py-2.5 rounded-full font-bold text-sm transition-all duration-300 ${
                            isActive
                              ? "bg-blue-600 text-white shadow-lg shadow-blue-500/25 scale-105"
                              : "bg-white text-gray-600 hover:bg-blue-50 hover:text-blue-600 border border-transparent hover:border-blue-100"
                          }`}
                        >
                          <div className="flex items-center gap-2">
                            <span>{s}</span>
                            <span
                              className={`text-[10px] px-2 py-0.5 rounded-full font-extrabold ${
                                isActive
                                  ? "bg-white/20 text-white"
                                  : "bg-gray-100 text-gray-500 group-hover:bg-blue-100 group-hover:text-blue-600"
                              }`}
                            >
                              {count}
                            </span>
                          </div>
                        </button>
                      );
                    })}
                  </div>
                </div>

                {subsectionsOfCurrent.length > 0 && (
                  <div>
                    <label className="text-xs font-semibold text-gray-700 uppercase tracking-wide mb-2 block">
                      Subsecciones de {currentSection}
                    </label>
                    <div className="flex flex-wrap gap-2">
                      {subsectionsOfCurrent.map((sub) => {
                        const subPage = getPageForSubsection(String(sub));
                        const isCurrentSubPage = subPage === page;
                        return (
                          <button
                            key={String(sub)}
                            type="button"
                            onClick={() => {
                              goToPage(subPage, () =>
                                scrollToSubsection(String(sub)),
                              );
                            }}
                            className={`group flex items-center gap-1.5 px-3 py-1.5 rounded-md text-[11px] font-semibold border transition-all shadow-sm ${
                              isCurrentSubPage
                                ? "bg-emerald-600 border-emerald-600 text-white shadow-md"
                                : "bg-white/80 border-gray-200 text-gray-700 hover:bg-emerald-50 hover:border-emerald-200 hover:shadow"
                            }`}
                          >
                            <span
                              className={`w-1.5 h-1.5 rounded-full ${
                                isCurrentSubPage ? "bg-white" : "bg-emerald-500"
                              }`}
                              aria-hidden
                            />
                            <span className="whitespace-nowrap">{sub}</span>
                          </button>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>

              <div className="bg-white rounded-xl border border-gray-200 p-4 shadow-sm">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-3">
                  <div className="text-sm font-medium text-gray-700">
                    <span className="text-blue-600 font-bold">
                      Sección {page}
                    </span>{" "}
                    de {totalPages}
                  </div>
                  <div className="text-xs text-gray-500">
                    {currentSection || "Sección"} · {pageQuestions.length}{" "}
                    pregunta
                    {pageQuestions.length !== 1 ? "s" : ""}
                  </div>
                </div>

                <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden mb-4">
                  <div
                    className="h-2 bg-gradient-to-r from-blue-500 to-indigo-600 rounded-full transition-all duration-300"
                    style={{
                      width: `${Math.round((page / totalPages) * 100)}%`,
                    }}
                  />
                </div>

                <div className="flex items-center justify-center gap-1.5 flex-wrap">
                  {Array.from({ length: totalPages }).map((_, idx) => {
                    const p = idx + 1;
                    return (
                      <button
                        key={p}
                        type="button"
                        onClick={() => goToPage(p)}
                        className={`min-w-[2.5rem] h-10 px-3 rounded-lg font-semibold text-sm transition-all ${
                          p === page
                            ? "bg-blue-600 text-white shadow-md scale-105"
                            : "bg-gray-50 text-gray-700 hover:bg-gray-100 border border-gray-200"
                        }`}
                      >
                        {p}
                      </button>
                    );
                  })}
                </div>
              </div>

              <div className="space-y-6">
                {currentSection && (
                  <div className="space-y-6">
                    <div className="bg-gradient-to-r from-blue-50 to-transparent border-l-4 border-blue-600 pl-4 pr-4 py-3 rounded-r-lg">
                      <h3 className="text-lg sm:text-xl font-bold text-gray-900">
                        {currentSection}
                      </h3>
                      <p className="text-sm text-gray-600 mt-1">
                        {pageQuestions.length} pregunta
                        {pageQuestions.length !== 1 ? "s" : ""} en esta sección
                      </p>
                    </div>

                    {[
                      ...new Set(
                        pageQuestions.map((q) => q.subsection || "General"),
                      ),
                    ].map((sub) => {
                      const subId = `subsection-${slugify(sub)}`;
                      const questionsInSub = pageQuestions.filter(
                        (q) => (q.subsection || "General") === sub,
                      );
                      return (
                        <div key={sub} id={subId} className="space-y-3">
                          <div className="flex items-center gap-2">
                            <div
                              className="w-2 h-2 rounded-full bg-blue-500"
                              aria-hidden
                            />
                            <h4 className="text-sm font-semibold text-gray-800">
                              {sub}
                            </h4>
                          </div>
                          <div className="grid gap-6 sm:grid-cols-1 lg:grid-cols-2 lg:auto-rows-fr">
                            {questionsInSub.map((q) => (
                              <div
                                key={q.id}
                                id={`qt-${q.id}`}
                                onMouseEnter={() => setActiveQuestion(q)}
                                // Optional: clear on leave or keep persistent? Keeping persistent usually feels better
                                // onMouseLeave={() => setActiveQuestion(null)}
                                className="group flex flex-col h-full bg-white rounded-2xl border border-gray-100 p-5 shadow-sm hover:shadow-md hover:border-blue-200 transition-all duration-300 scroll-mt-32 focus-within:ring-2 focus-within:ring-blue-100 ring-offset-2"
                              >
                                <div className="mb-4 flex-1">
                                  <h5 className="font-bold text-gray-900 leading-snug mb-2 flex items-start justify-between gap-2">
                                    {q.label}
                                    {q.relatedImage && (
                                      <ImageTooltip
                                        imageUrl={q.relatedImage}
                                        title={q.label}
                                      >
                                        <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-bold bg-blue-50 text-blue-600 border border-blue-100 hover:bg-blue-100 hover:border-blue-200 transition-colors cursor-help">
                                          📷 IMG
                                        </span>
                                      </ImageTooltip>
                                    )}
                                  </h5>
                                  {q.helper && (
                                    <p className="text-sm text-gray-500 leading-relaxed">
                                      {q.helper}
                                    </p>
                                  )}
                                </div>

                                <div className="mt-auto pt-4 border-t border-gray-50">
                                  {renderAnswerInput(q)}
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>

              {page === totalPages && (
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Comentarios adicionales (opcional)
                  </label>
                  <textarea
                    value={comments}
                    onChange={(e) => setComments(e.target.value)}
                    rows={4}
                    className="w-full border border-gray-300 rounded-lg p-3 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all resize-none"
                    placeholder={`Agregue observaciones generales sobre el ${documentType.toLowerCase()}...`}
                  />
                  <p className="text-xs text-gray-500 mt-2">
                    Este cuadro aparece solo en la última página para que sus
                    observaciones sean lo último que complete.
                  </p>
                </div>
              )}

              <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 pt-4 border-t border-gray-200">
                <div className="flex items-center gap-3 flex-1">
                  <button
                    type="button"
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page === 1}
                    className="flex items-center justify-center gap-2 px-5 py-3 rounded-lg bg-white border-2 border-gray-300 text-sm font-semibold text-gray-700 hover:bg-gray-50 hover:border-gray-400 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
                  >
                    <svg
                      className="w-4 h-4"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M15 19l-7-7 7-7"
                      />
                    </svg>
                    Anterior
                  </button>
                  {page < totalPages ? (
                    <button
                      type="button"
                      onClick={handleNextSection}
                      className="group flex items-center justify-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 text-white text-sm font-bold hover:shadow-lg hover:shadow-blue-500/30 transition-all duration-300 transform hover:-translate-y-0.5"
                    >
                      Siguiente
                      <svg
                        className="w-4 h-4 group-hover:translate-x-1 transition-transform"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M9 5l7 7-7 7"
                        />
                      </svg>
                    </button>
                  ) : (
                    <button
                      type="submit"
                      disabled={isSubmitting}
                      className="flex items-center justify-center gap-2 bg-green-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-green-700 disabled:opacity-60 disabled:cursor-not-allowed transition-all shadow-md hover:shadow-lg"
                    >
                      {isSubmitting ? (
                        <>
                          <svg
                            className="animate-spin h-5 w-5"
                            viewBox="0 0 24 24"
                          >
                            <circle
                              className="opacity-25"
                              cx="12"
                              cy="12"
                              r="10"
                              stroke="currentColor"
                              strokeWidth="4"
                              fill="none"
                            />
                            <path
                              className="opacity-75"
                              fill="currentColor"
                              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                            />
                          </svg>
                          Enviando...
                        </>
                      ) : (
                        <>
                          <svg
                            className="w-5 h-5"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M5 13l4 4L19 7"
                            />
                          </svg>
                          Enviar evaluación
                        </>
                      )}
                    </button>
                  )}
                </div>

                <button
                  type="button"
                  onClick={() => router.back()}
                  className="text-sm text-gray-600 hover:text-gray-900 font-medium transition-colors px-3 py-2"
                >
                  Cancelar
                </button>
              </div>
            </div>
          </form>
        </div>
      ) : (
        <div className="bg-white p-6 sm:p-8 rounded-xl shadow-lg space-y-6">
          <div className="flex items-center gap-3 pb-4 border-b border-gray-200">
            <div
              className={`w-12 h-12 rounded-full flex items-center justify-center ${
                submittedData.passStatus === "Pass"
                  ? "bg-green-100"
                  : "bg-red-100"
              }`}
            >
              {submittedData.passStatus === "Pass" ? (
                <svg
                  className="w-6 h-6 text-green-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M5 13l4 4L19 7"
                  />
                </svg>
              ) : (
                <svg
                  className="w-6 h-6 text-red-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              )}
            </div>
            <div>
              <h3 className="text-xl font-bold text-gray-900">
                Evaluación completada:{" "}
                {submittedData.passStatus === "Pass" ? "Aprobado" : "Reprobado"}
              </h3>
              <p className="text-sm text-gray-600 mt-1">
                Puntaje obtenido:{" "}
                <strong
                  className={
                    submittedData.passStatus === "Pass"
                      ? "text-green-600"
                      : "text-red-600"
                  }
                >
                  {submittedData.score} / {MAX_SCORE}
                </strong>{" "}
                (Mínimo requerido: {PASSING_SCORE})
              </p>
            </div>
          </div>

          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 space-y-4">
            <h4 className="font-semibold text-gray-700 mb-3 flex items-center gap-2">
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01"
                />
              </svg>
              Resumen de respuestas
            </h4>
            <div className="bg-white rounded-lg p-4 border border-gray-200 space-y-3 max-h-96 overflow-y-auto">
              {filteredQuestions.map((q) => (
                <div
                  key={q.id}
                  className="pb-3 border-b border-gray-100 last:border-0 last:pb-0"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900">
                        {q.label}
                      </p>
                      <p className="text-xs text-gray-500 mt-0.5">
                        {q.section}
                      </p>
                    </div>
                    <span className="text-sm font-semibold text-blue-600 whitespace-nowrap">
                      {getAnswerLabel(q, ratings[q.id])}
                    </span>
                  </div>
                </div>
              ))}
            </div>
            {comments && (
              <div className="bg-white rounded-lg p-4 border border-gray-200">
                <h5 className="text-sm font-semibold text-gray-700 mb-2">
                  Comentarios adicionales:
                </h5>
                <p className="text-sm text-gray-600 whitespace-pre-wrap">
                  {comments}
                </p>
              </div>
            )}
          </div>

          <div className="flex flex-col sm:flex-row gap-3 pt-4">
            <button
              onClick={() =>
                router.push(
                  typeParam === "tesis"
                    ? "/dashboard/tesis/evaluar"
                    : "/dashboard/proyectos",
                )
              }
              className="flex-1 sm:flex-initial bg-blue-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-700 transition-all shadow-sm hover:shadow-md"
            >
              ← Volver
            </button>
            <button
              onClick={() => setSubmittedData(null)}
              className="flex-1 sm:flex-initial border-2 border-gray-300 text-gray-700 px-6 py-3 rounded-lg font-medium hover:bg-gray-50 transition-all"
            >
              Nueva evaluación
            </button>
          </div>
        </div>
      )}
    </>
  );
}
