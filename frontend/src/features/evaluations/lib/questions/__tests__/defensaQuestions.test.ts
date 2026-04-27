import { describe, it, expect } from "vitest";
import { PTEG_DEFENSA_QUESTIONS } from "../questions";

describe("PTEG_DEFENSA_QUESTIONS — existence and length", () => {
  it("exports exactly 20 questions", () => {
    expect(PTEG_DEFENSA_QUESTIONS).toHaveLength(20);
  });
});

describe("PTEG_DEFENSA_QUESTIONS — section distribution", () => {
  it("has 15 questions in Criterios de Evaluación Técnica", () => {
    const tecnica = PTEG_DEFENSA_QUESTIONS.filter(
      (q) => q.section === "Criterios de Evaluación Técnica"
    );
    expect(tecnica).toHaveLength(15);
  });

  it("has 5 questions in Criterios de Evaluación Divulgativa", () => {
    const divulgativa = PTEG_DEFENSA_QUESTIONS.filter(
      (q) => q.section === "Criterios de Evaluación Divulgativa"
    );
    expect(divulgativa).toHaveLength(5);
  });
});

describe("PTEG_DEFENSA_QUESTIONS — shared field values", () => {
  it("every question has answerType === 'ternary_defense'", () => {
    for (const q of PTEG_DEFENSA_QUESTIONS) {
      expect(q.answerType).toBe("ternary_defense");
    }
  });

  it("every question has documentType === 'Proyecto'", () => {
    for (const q of PTEG_DEFENSA_QUESTIONS) {
      expect(q.documentType).toBe("Proyecto");
    }
  });

  it("every question has kind === 'defense'", () => {
    for (const q of PTEG_DEFENSA_QUESTIONS) {
      expect((q as { kind?: string }).kind).toBe("defense");
    }
  });
});

describe("PTEG_DEFENSA_QUESTIONS — ID patterns", () => {
  it("Técnica questions have IDs pd-tech1 through pd-tech15", () => {
    const tecnica = PTEG_DEFENSA_QUESTIONS.filter(
      (q) => q.section === "Criterios de Evaluación Técnica"
    );
    const expectedIds = Array.from({ length: 15 }, (_, i) => `pd-tech${i + 1}`);
    expect(tecnica.map((q) => q.id)).toEqual(expectedIds);
  });

  it("Divulgativa questions have IDs pd-div1 through pd-div5", () => {
    const divulgativa = PTEG_DEFENSA_QUESTIONS.filter(
      (q) => q.section === "Criterios de Evaluación Divulgativa"
    );
    const expectedIds = Array.from({ length: 5 }, (_, i) => `pd-div${i + 1}`);
    expect(divulgativa.map((q) => q.id)).toEqual(expectedIds);
  });
});

describe("PTEG_DEFENSA_QUESTIONS — verbatim labels (Técnica)", () => {
  const tecnica = () =>
    PTEG_DEFENSA_QUESTIONS.filter(
      (q) => q.section === "Criterios de Evaluación Técnica"
    );

  const EXPECTED_TECNICA_LABELS = [
    "Planteamiento y delimitación del problema",
    "Justificación",
    "Objetivo General",
    "Objetivos Específicos",
    "Definición y Operacionalización de variables",
    "Antecedentes",
    "Tipo, diseño, nivel y modo de la investigación",
    "Población, muestra y muestreo",
    "Técnica, métodos y procedimientos experimentales",
    "Técnica e instrumentos de recolección de datos. Validez y Confiabilidad. Técnicas y Herramientas de Procesamiento de datos",
    "Viabilidad Organizacional, Legal, de Mercado, Ambiental, Económica",
    "Viabilidad Técnica",
    "Viabilidad Temporal",
    "Referencias Bibliográficas",
    "Aporte a las Ciencias Farmacéuticas / Pertinencia",
  ];

  it("labels match the verbatim user list in order", () => {
    expect(tecnica().map((q) => q.label)).toEqual(EXPECTED_TECNICA_LABELS);
  });
});

describe("PTEG_DEFENSA_QUESTIONS — verbatim labels (Divulgativa)", () => {
  const divulgativa = () =>
    PTEG_DEFENSA_QUESTIONS.filter(
      (q) => q.section === "Criterios de Evaluación Divulgativa"
    );

  const EXPECTED_DIVULGATIVA_LABELS = [
    "Adecuada dicción, vocabulario, tono de voz, postura y lenguaje corporal, contacto visual",
    "Seguridad y dominio del tema",
    "Material de apoyo: Legibilidad del texto, Diseños no sobrecargados, Imágenes acordes al apartado",
    "Gestión del tiempo",
    "Precisión y claridad al responder al jurado",
  ];

  it("labels match the verbatim user list in order", () => {
    expect(divulgativa().map((q) => q.label)).toEqual(EXPECTED_DIVULGATIVA_LABELS);
  });
});
