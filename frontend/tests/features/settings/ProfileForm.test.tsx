import { describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { ProfileForm } from "@features/settings/components/profile/ProfileForm";

const estudianteUser = {
  role: "Estudiante" as const,
  fullName: "María Rodríguez",
  email: "maria@example.com",
  nationality: "V" as const,
  cedula: "30243721",
  phone: "+58 412 1234567",
  semester: "9no" as const,
};

const tutorUser = {
  role: "Tutor" as const,
  fullName: "Juan Pérez",
  email: "juan@example.com",
  nationality: "V" as const,
  cedula: "15874213",
  phone: "",
};

describe("ProfileForm", () => {
  it("renders semester field for Estudiante", () => {
    render(<ProfileForm initialValues={estudianteUser} onSubmit={vi.fn()} />);
    expect(screen.getByLabelText(/semestre/i)).toBeInTheDocument();
  });

  it("does NOT render semester field for Tutor", () => {
    render(<ProfileForm initialValues={tutorUser} onSubmit={vi.fn()} />);
    expect(screen.queryByLabelText(/semestre/i)).not.toBeInTheDocument();
  });

  it("disables Save button until the form is dirty", () => {
    render(<ProfileForm initialValues={estudianteUser} onSubmit={vi.fn()} />);
    const save = screen.getByRole("button", { name: /guardar cambios/i });
    expect(save).toBeDisabled();
  });

  it("enables Save button after edit", async () => {
    render(<ProfileForm initialValues={estudianteUser} onSubmit={vi.fn()} />);
    const nameInput = screen.getByDisplayValue("María Rodríguez");
    fireEvent.change(nameInput, { target: { value: "María Rodríguez García" } });
    await waitFor(() => {
      expect(screen.getByRole("button", { name: /guardar cambios/i })).not.toBeDisabled();
    });
  });

  it("shows inline error for invalid cedula", async () => {
    render(<ProfileForm initialValues={estudianteUser} onSubmit={vi.fn()} />);
    const cedulaInput = screen.getByDisplayValue("30243721");
    fireEvent.change(cedulaInput, { target: { value: "abc" } });
    fireEvent.blur(cedulaInput);
    await waitFor(() => {
      expect(screen.getByText(/6–9 dígitos/i)).toBeInTheDocument();
    });
  });

  it("calls onSubmit with sanitized payload when valid", async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    render(<ProfileForm initialValues={estudianteUser} onSubmit={onSubmit} />);
    const nameInput = screen.getByDisplayValue("María Rodríguez");
    fireEvent.change(nameInput, { target: { value: "María R. García" } });
    fireEvent.click(screen.getByRole("button", { name: /guardar cambios/i }));
    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith(expect.objectContaining({
        fullName: "María R. García",
        role: "Estudiante",
        semester: "9no",
      }));
    });
  });
});
