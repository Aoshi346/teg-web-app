import { describe, it, expect } from "vitest";
import { TEG_ENTREGA_QUESTIONS } from "../questions";

// Dependency note for frontend-worker:
//   The `Question` interface in questions.ts must gain a `phase?: 'entrega' | 'articulo' | 'defensa'`
//   discriminator field. Tests below assert `phase === 'entrega'` on every entrega question.
//   The `kind?: 'review' | 'defense' | 'both'` field already exists (Sub-N).

describe("TEG_ENTREGA_QUESTIONS — total count", () => {
  it("exports exactly 49 questions (47 quintary + 2 yesno in Sec6)", () => {
    expect(TEG_ENTREGA_QUESTIONS).toHaveLength(49);
  });
});

describe("TEG_ENTREGA_QUESTIONS — section distribution", () => {
  it("has 4 questions in 'Diagramación'", () => {
    const count = TEG_ENTREGA_QUESTIONS.filter(
      (q) => q.section === "Diagramación"
    ).length;
    expect(count).toBe(4);
  });

  it("has 10 questions in 'Sección 1 (Capítulo 1)'", () => {
    const count = TEG_ENTREGA_QUESTIONS.filter(
      (q) => q.section === "Sección 1 (Capítulo 1)"
    ).length;
    expect(count).toBe(10);
  });

  it("has 3 questions in 'Sección 2 (Capítulo 2)'", () => {
    const count = TEG_ENTREGA_QUESTIONS.filter(
      (q) => q.section === "Sección 2 (Capítulo 2)"
    ).length;
    expect(count).toBe(3);
  });

  it("has 12 questions in 'Sección 3 (Capítulo 3)'", () => {
    const count = TEG_ENTREGA_QUESTIONS.filter(
      (q) => q.section === "Sección 3 (Capítulo 3)"
    ).length;
    expect(count).toBe(12);
  });

  it("has 9 questions in 'Sección 4 (Capítulo 4)'", () => {
    const count = TEG_ENTREGA_QUESTIONS.filter(
      (q) => q.section === "Sección 4 (Capítulo 4)"
    ).length;
    expect(count).toBe(9);
  });

  it("has 6 questions in 'Sección 5 (Capítulo 5)'", () => {
    const count = TEG_ENTREGA_QUESTIONS.filter(
      (q) => q.section === "Sección 5 (Capítulo 5)"
    ).length;
    expect(count).toBe(6);
  });

  it("has 2 questions in 'Sección 6 (Capítulo 6)'", () => {
    const count = TEG_ENTREGA_QUESTIONS.filter(
      (q) => q.section === "Sección 6 (Capítulo 6)"
    ).length;
    expect(count).toBe(2);
  });

  it("has 3 questions in 'Sección Final'", () => {
    const count = TEG_ENTREGA_QUESTIONS.filter(
      (q) => q.section === "Sección Final"
    ).length;
    expect(count).toBe(3);
  });
});

describe("TEG_ENTREGA_QUESTIONS — documentType and kind", () => {
  it("every question has documentType === 'Tesis'", () => {
    const nonTesis = TEG_ENTREGA_QUESTIONS.filter(
      (q) => q.documentType !== "Tesis"
    );
    expect(nonTesis).toHaveLength(0);
  });

  it("every question has kind === 'review'", () => {
    const nonReview = TEG_ENTREGA_QUESTIONS.filter((q) => q.kind !== "review");
    expect(nonReview).toHaveLength(0);
  });
});

describe("TEG_ENTREGA_QUESTIONS — phase discriminator", () => {
  it("every question has phase === 'entrega'", () => {
    // Requires Question interface to have phase?: 'entrega' | 'articulo' | 'defensa'
    const nonEntrega = TEG_ENTREGA_QUESTIONS.filter(
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (q) => (q as any).phase !== "entrega"
    );
    expect(nonEntrega).toHaveLength(0);
  });
});

describe("TEG_ENTREGA_QUESTIONS — answerTypes", () => {
  it("all non-Sección-6 questions have answerType === 'quintary'", () => {
    const nonSec6 = TEG_ENTREGA_QUESTIONS.filter(
      (q) => q.section !== "Sección 6 (Capítulo 6)"
    );
    const nonQuintary = nonSec6.filter((q) => q.answerType !== "quintary");
    expect(nonQuintary).toHaveLength(0);
  });

  it("both Sección 6 questions have answerType === 'yesno'", () => {
    const sec6 = TEG_ENTREGA_QUESTIONS.filter(
      (q) => q.section === "Sección 6 (Capítulo 6)"
    );
    expect(sec6).toHaveLength(2);
    const nonYesno = sec6.filter((q) => q.answerType !== "yesno");
    expect(nonYesno).toHaveLength(0);
  });
});

describe("TEG_ENTREGA_QUESTIONS — ID patterns", () => {
  it("all IDs are unique", () => {
    const ids = TEG_ENTREGA_QUESTIONS.map((q) => q.id);
    const unique = new Set(ids);
    expect(unique.size).toBe(ids.length);
  });

  it("contains the exact set of expected IDs", () => {
    const expectedIds = new Set([
      "te-d1", "te-d2", "te-d3", "te-d4",
      "te-s1-1", "te-s1-2", "te-s1-3", "te-s1-4", "te-s1-5",
      "te-s1-6", "te-s1-7", "te-s1-8", "te-s1-9", "te-s1-10",
      "te-s2-1", "te-s2-2", "te-s2-3",
      "te-s3-1", "te-s3-2", "te-s3-3", "te-s3-4", "te-s3-5",
      "te-s3-6", "te-s3-7", "te-s3-8", "te-s3-9", "te-s3-10",
      "te-s3-11", "te-s3-12",
      "te-s4-1", "te-s4-2", "te-s4-3", "te-s4-4", "te-s4-5",
      "te-s4-6", "te-s4-7", "te-s4-8", "te-s4-9",
      "te-s5-1", "te-s5-2", "te-s5-3", "te-s5-4", "te-s5-5", "te-s5-6",
      "te-s6-1", "te-s6-2",
      "te-f1", "te-f2", "te-f3",
    ]);
    const actualIds = new Set(TEG_ENTREGA_QUESTIONS.map((q) => q.id));
    expect(actualIds).toEqual(expectedIds);
  });
});

describe("TEG_ENTREGA_QUESTIONS — question text", () => {
  it("every question has a non-empty text/label", () => {
    const emptyLabel = TEG_ENTREGA_QUESTIONS.filter(
      (q) => !q.label || q.label.trim() === ""
    );
    expect(emptyLabel).toHaveLength(0);
  });

  // Spot-check D.1 — first Diagramación question (section 6.1 text confirmed in brief)
  it("te-s6-1 text is '¿El estudio constituye un proyecto factible?'", () => {
    const q = TEG_ENTREGA_QUESTIONS.find((q) => q.id === "te-s6-1");
    expect(q).toBeDefined();
    expect(q!.label).toBe("¿El estudio constituye un proyecto factible?");
  });

  // Spot-check 6.2 — confirmed in brief Confirmed Decisions §2
  it("te-s6-2 text is '¿Se adjunta el modelo operativo en el Capítulo 6?'", () => {
    const q = TEG_ENTREGA_QUESTIONS.find((q) => q.id === "te-s6-2");
    expect(q).toBeDefined();
    expect(q!.label).toBe("¿Se adjunta el modelo operativo en el Capítulo 6?");
  });

  // Spot-check F.3 — last question in Sección Final (te-f3)
  it("te-f3 is the third question in Sección Final", () => {
    const finalQs = TEG_ENTREGA_QUESTIONS.filter(
      (q) => q.section === "Sección Final"
    );
    expect(finalQs).toHaveLength(3);
    expect(finalQs[2].id).toBe("te-f3");
    expect(finalQs[2].label.trim().length).toBeGreaterThan(0);
  });
});
