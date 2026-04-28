import { describe, it, expect } from "vitest";
import { TEG_DEFENSA_QUESTIONS } from "../questions";

describe("TEG_DEFENSA_QUESTIONS — total count", () => {
  it("exports exactly 15 questions", () => {
    expect(TEG_DEFENSA_QUESTIONS).toHaveLength(15);
  });
});

describe("TEG_DEFENSA_QUESTIONS — section distribution", () => {
  it("has 10 questions in 'Criterios de Evaluación Técnica'", () => {
    const count = TEG_DEFENSA_QUESTIONS.filter(
      (q) => q.section === "Criterios de Evaluación Técnica"
    ).length;
    expect(count).toBe(10);
  });

  it("has 5 questions in 'Criterios de Evaluación Divulgativa'", () => {
    const count = TEG_DEFENSA_QUESTIONS.filter(
      (q) => q.section === "Criterios de Evaluación Divulgativa"
    ).length;
    expect(count).toBe(5);
  });
});

describe("TEG_DEFENSA_QUESTIONS — shared field values", () => {
  it("every question has documentType === 'Tesis'", () => {
    const nonTesis = TEG_DEFENSA_QUESTIONS.filter(
      (q) => q.documentType !== "Tesis"
    );
    expect(nonTesis).toHaveLength(0);
  });

  it("every question has kind === 'defense'", () => {
    const nonDefense = TEG_DEFENSA_QUESTIONS.filter(
      (q) => q.kind !== "defense"
    );
    expect(nonDefense).toHaveLength(0);
  });

  it("every question has phase === 'defensa'", () => {
    const nonDefensa = TEG_DEFENSA_QUESTIONS.filter(
      (q) => q.phase !== "defensa"
    );
    expect(nonDefensa).toHaveLength(0);
  });

  it("every question has answerType === 'quaternary_defense'", () => {
    const nonQuaternary = TEG_DEFENSA_QUESTIONS.filter(
      (q) => q.answerType !== "quaternary_defense"
    );
    expect(nonQuaternary).toHaveLength(0);
  });
});

describe("TEG_DEFENSA_QUESTIONS — ID patterns", () => {
  it("all IDs are unique", () => {
    const ids = TEG_DEFENSA_QUESTIONS.map((q) => q.id);
    const unique = new Set(ids);
    expect(unique.size).toBe(ids.length);
  });

  it("contains the exact set of expected IDs", () => {
    const expectedIds = new Set([
      "td-tech1", "td-tech2", "td-tech3", "td-tech4", "td-tech5",
      "td-tech6", "td-tech7", "td-tech8", "td-tech9", "td-tech10",
      "td-div1", "td-div2", "td-div3", "td-div4", "td-div5",
    ]);
    const actualIds = new Set(TEG_DEFENSA_QUESTIONS.map((q) => q.id));
    expect(actualIds).toEqual(expectedIds);
  });

  it("Técnica questions have IDs td-tech1 through td-tech10 in order", () => {
    const tecnica = TEG_DEFENSA_QUESTIONS.filter(
      (q) => q.section === "Criterios de Evaluación Técnica"
    );
    const expectedIds = Array.from({ length: 10 }, (_, i) => `td-tech${i + 1}`);
    expect(tecnica.map((q) => q.id)).toEqual(expectedIds);
  });

  it("Divulgativa questions have IDs td-div1 through td-div5 in order", () => {
    const divulgativa = TEG_DEFENSA_QUESTIONS.filter(
      (q) => q.section === "Criterios de Evaluación Divulgativa"
    );
    const expectedIds = Array.from({ length: 5 }, (_, i) => `td-div${i + 1}`);
    expect(divulgativa.map((q) => q.id)).toEqual(expectedIds);
  });
});

describe("TEG_DEFENSA_QUESTIONS — question text", () => {
  it("every question has a non-empty label", () => {
    const emptyLabel = TEG_DEFENSA_QUESTIONS.filter(
      (q) => !q.label || q.label.trim() === ""
    );
    expect(emptyLabel).toHaveLength(0);
  });

  it("td-tech1 has the correct verbatim text", () => {
    const q = TEG_DEFENSA_QUESTIONS.find((q) => q.id === "td-tech1");
    expect(q).toBeDefined();
    expect(q!.label).toBe(
      "Planteamiento y delimitación del problema / Justificación."
    );
  });

  it("td-tech8 has the correct verbatim text", () => {
    const q = TEG_DEFENSA_QUESTIONS.find((q) => q.id === "td-tech8");
    expect(q).toBeDefined();
    expect(q!.label).toBe(
      "Organización o tabulación de los datos obtenidos. Análisis e interpretación de resultados: Coherencia."
    );
  });

  it("td-div1 has the correct verbatim text", () => {
    const q = TEG_DEFENSA_QUESTIONS.find((q) => q.id === "td-div1");
    expect(q).toBeDefined();
    expect(q!.label).toBe(
      "Adecuada dicción, vocabulario, tono de voz, postura y lenguaje corporal, contacto visual"
    );
  });
});
