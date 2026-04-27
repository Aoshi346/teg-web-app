import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { ProfileForm } from "./ProfileForm";
import type { ProfileInput } from "../../lib/schemas";

const STUDENT_VALUES: ProfileInput = {
  role: "Estudiante",
  fullName: "Ana Pérez",
  email: "ana@example.com",
  nationality: "V",
  cedula: "12345678",
  phone: "",
  semester: "10mo",
};

describe("ProfileForm — Estudiante self-view", () => {
  it("does not render an editable Semestre field for Estudiante", () => {
    render(
      <ProfileForm initialValues={STUDENT_VALUES} onSubmit={vi.fn()} />
    );

    // The semester label must not appear
    expect(screen.queryByLabelText(/Semestre/i)).toBeNull();

    // The semester select (id="semester-select") must not appear
    const semesterSelect = document.getElementById("semester-select");
    expect(semesterSelect).toBeNull();
  });

  it("still renders the Nombre completo, Email and Teléfono fields for Estudiante", () => {
    render(
      <ProfileForm initialValues={STUDENT_VALUES} onSubmit={vi.fn()} />
    );

    expect(screen.getByLabelText(/nombre completo/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/teléfono/i)).toBeInTheDocument();
  });

  it("still renders the CedulaField (Cédula label) for Estudiante", () => {
    render(
      <ProfileForm initialValues={STUDENT_VALUES} onSubmit={vi.fn()} />
    );

    // CedulaField renders a label with text "Cédula" linked to id="cedula-field-input"
    expect(screen.getByLabelText(/cédula/i)).toBeInTheDocument();
  });
});
