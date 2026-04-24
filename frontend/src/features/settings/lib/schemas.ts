import { z } from "zod";

export const nationalitySchema = z.enum(["V", "E", "P"]);
export const cedulaSchema = z.string().regex(/^\d{6,9}$/, "La cédula debe tener 6–9 dígitos");
export const roleSchema = z.enum(["Administrador", "Tutor", "Jurado", "Estudiante"]);
export const semesterValueSchema = z.enum(["9no", "10mo", "N/A"]);

const baseFields = {
  fullName: z.string().min(2, "Nombre muy corto").max(120, "Nombre muy largo"),
  email: z.string().email("Email inválido"),
  nationality: nationalitySchema,
  cedula: cedulaSchema,
  phone: z.string().max(20).optional().or(z.literal("")),
};

export const profileSchema = z.discriminatedUnion("role", [
  z.object({
    role: z.literal("Estudiante"),
    ...baseFields,
    semester: semesterValueSchema,
  }),
  z.object({
    role: z.enum(["Administrador", "Tutor", "Jurado"]),
    ...baseFields,
  }),
]);

export const userCreateSchema = profileSchema;
export const userUpdateSchema = profileSchema;

export const semesterSchema = z.object({
  year: z.number().int().min(2020, "Año mínimo 2020").max(2050, "Año máximo 2050"),
  period: z.enum(["01", "02"]),
  startMonth: z.number().int().min(1).max(12),
  endMonth: z.number().int().min(1).max(12),
});

export type ProfileInput = z.infer<typeof profileSchema>;
export type UserInput = z.infer<typeof userCreateSchema>;
export type SemesterInput = z.infer<typeof semesterSchema>;
