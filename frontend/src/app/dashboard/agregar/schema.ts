import { z } from "zod";

export const documentFormSchema = z
  .object({
    title: z.string().min(1, "El título es obligatorio.").max(255),
    documentType: z.enum(["proyecto", "tesis"]),
    studentId: z.union([z.number().int().positive(), z.literal("")]),
    partnerId: z.union([z.number().int().positive(), z.literal(""), z.null()]).optional(),
    advisors: z
      .array(z.union([z.number().int().positive(), z.literal("")]))
      .min(1, "Debe asignar al menos un tutor."),
    semesterPeriod: z.string().min(1, "Seleccione un período académico."),
    files: z.array(z.instanceof(File)).optional(),
    userRole: z.string(),
  })
  .superRefine((data, ctx) => {
    // studentId is required
    if (data.studentId === "" || data.studentId === undefined) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "Debe seleccionar un estudiante.",
        path: ["studentId"],
      });
    }

    // At least one valid advisor
    const validAdvisors = data.advisors.filter((a): a is number => a !== "");
    if (validAdvisors.length === 0) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "Debe asignar al menos un tutor.",
        path: ["advisors"],
      });
    }

    // No duplicate advisors
    const uniqueAdvisors = new Set(validAdvisors);
    if (uniqueAdvisors.size !== validAdvisors.length) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "No se permiten tutores duplicados.",
        path: ["advisors"],
      });
    }

    // Students must upload at least one file
    if (data.userRole === "Estudiante") {
      if (!data.files || data.files.length === 0) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: "Debe adjuntar al menos un archivo.",
          path: ["files"],
        });
      }
    }

    // File size limit: 10MB per file
    if (data.files) {
      const MAX_SIZE = 10 * 1024 * 1024;
      for (let i = 0; i < data.files.length; i++) {
        if (data.files[i].size > MAX_SIZE) {
          ctx.addIssue({
            code: z.ZodIssueCode.custom,
            message: `"${data.files[i].name}" excede el límite de 10 MB.`,
            path: ["files"],
          });
        }
      }
    }
  });

export type DocumentFormData = z.infer<typeof documentFormSchema>;
