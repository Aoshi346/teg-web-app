import { describe, expect, it } from "vitest";
import { profileSchema, semesterSchema } from "@features/settings/lib/schemas";

describe("profileSchema", () => {
  it("accepts a valid Estudiante profile with semester", () => {
    const result = profileSchema.safeParse({
      role: "Estudiante",
      fullName: "María Rodríguez",
      email: "maria@example.com",
      nationality: "V",
      cedula: "30243721",
      phone: "+58 412 1234567",
      semester: "9no",
    });
    expect(result.success).toBe(true);
  });

  it("rejects an Estudiante profile missing the semester field", () => {
    const result = profileSchema.safeParse({
      role: "Estudiante",
      fullName: "María Rodríguez",
      email: "maria@example.com",
      nationality: "V",
      cedula: "30243721",
    });
    expect(result.success).toBe(false);
  });

  it("accepts a Tutor profile without a semester field", () => {
    const result = profileSchema.safeParse({
      role: "Tutor",
      fullName: "Juan Pérez",
      email: "juan@example.com",
      nationality: "V",
      cedula: "15874213",
    });
    expect(result.success).toBe(true);
  });

  it("rejects a cedula with non-digits", () => {
    const result = profileSchema.safeParse({
      role: "Tutor",
      fullName: "Juan Pérez",
      email: "juan@example.com",
      nationality: "V",
      cedula: "V-15874213",
    });
    expect(result.success).toBe(false);
  });

  it("rejects a cedula shorter than 6 digits", () => {
    const result = profileSchema.safeParse({
      role: "Tutor",
      fullName: "Juan Pérez",
      email: "juan@example.com",
      nationality: "V",
      cedula: "12345",
    });
    expect(result.success).toBe(false);
  });

  it("rejects an invalid email", () => {
    const result = profileSchema.safeParse({
      role: "Tutor",
      fullName: "Juan Pérez",
      email: "not-an-email",
      nationality: "V",
      cedula: "15874213",
    });
    expect(result.success).toBe(false);
  });
});

describe("semesterSchema", () => {
  it("accepts 2026-01 with Enero–Junio", () => {
    const result = semesterSchema.safeParse({
      year: 2026,
      period: "01",
      startMonth: 1,
      endMonth: 6,
    });
    expect(result.success).toBe(true);
  });

  it("accepts a cross-year range (September to January)", () => {
    const result = semesterSchema.safeParse({
      year: 2026,
      period: "02",
      startMonth: 9,
      endMonth: 1,
    });
    expect(result.success).toBe(true);
  });

  it("rejects a year below 2020", () => {
    const result = semesterSchema.safeParse({
      year: 2019,
      period: "01",
      startMonth: 1,
      endMonth: 6,
    });
    expect(result.success).toBe(false);
  });

  it("rejects a month outside 1–12", () => {
    const result = semesterSchema.safeParse({
      year: 2026,
      period: "01",
      startMonth: 13,
      endMonth: 6,
    });
    expect(result.success).toBe(false);
  });
});
