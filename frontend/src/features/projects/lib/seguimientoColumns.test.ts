import { describe, it, expect } from "vitest";
import {
  seguimientoColumnsFor,
  type Role,
  type SeguimientoColumnKey,
} from "./seguimientoColumns";

describe("seguimientoColumnsFor", () => {
  const cases: Array<{ role: Role; expected: SeguimientoColumnKey[] }> = [
    {
      role: "Administrador",
      expected: [
        "title",
        "estudiante",
        "tutorJurado",
        "estado",
        "fase",
        "recibido",
        "action",
      ],
    },
    {
      role: "Jurado",
      // Mockup shows "Tutor" column (not combined), drops "Fase".
      // tutorJurado key is reused — the component renders only the tutor for jurado.
      expected: [
        "title",
        "estudiante",
        "tutorJurado",
        "estado",
        "recibido",
        "action",
      ],
    },
    {
      role: "Tutor",
      // Mockup shows "Jurado" column, "Última actividad" instead of "Recibido", no "Fase".
      expected: [
        "title",
        "estudiante",
        "jurado",
        "estado",
        "ultimaActividad",
        "action",
      ],
    },
    {
      role: "Estudiante",
      // No table — page renders MyProjectCard instead.
      expected: [],
    },
  ];

  it.each(cases)(
    "$role returns the correct column set",
    ({ role, expected }) => {
      expect(seguimientoColumnsFor(role)).toEqual(expected);
    }
  );

  it.each(cases.filter((c) => c.expected.length > 0))(
    "$role column set starts with 'title'",
    ({ role }) => {
      const cols = seguimientoColumnsFor(role);
      expect(cols[0]).toBe("title");
    }
  );

  it.each(cases.filter((c) => c.expected.length > 0))(
    "$role column set ends with 'action'",
    ({ role }) => {
      const cols = seguimientoColumnsFor(role);
      expect(cols[cols.length - 1]).toBe("action");
    }
  );

  it("Estudiante returns an empty array (signals card view, no table)", () => {
    expect(seguimientoColumnsFor("Estudiante")).toHaveLength(0);
  });
});
