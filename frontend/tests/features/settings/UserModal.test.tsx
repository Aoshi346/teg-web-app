import { describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { UserModal } from "@features/settings/components/admin/directory/UserModal";

describe("UserModal", () => {
  it("shows semester field only when role=Estudiante", () => {
    render(<UserModal isOpen={true} onClose={vi.fn()} onSave={vi.fn()} initialData={null} />);
    const roleSelect = screen.getByLabelText(/rol/i);
    expect(screen.getByLabelText(/semestre/i)).toBeInTheDocument();
    fireEvent.change(roleSelect, { target: { value: "Tutor" } });
    expect(screen.queryByLabelText(/semestre/i)).not.toBeInTheDocument();
  });

  it("clears semester when role changes away from Estudiante", async () => {
    const onSave = vi.fn().mockResolvedValue(undefined);
    render(<UserModal isOpen={true} onClose={vi.fn()} onSave={onSave} initialData={null} />);
    fireEvent.change(screen.getByLabelText(/nombre completo/i), { target: { value: "Juan Pérez" } });
    fireEvent.change(screen.getByLabelText(/^email/i), { target: { value: "juan@example.com" } });
    fireEvent.change(screen.getByLabelText(/cédula/i), { target: { value: "15874213" } });
    fireEvent.change(screen.getByLabelText(/rol/i), { target: { value: "Tutor" } });
    fireEvent.click(screen.getByRole("button", { name: /crear usuario/i }));
    await waitFor(() => {
      expect(onSave).toHaveBeenCalledWith(expect.objectContaining({ role: "Tutor" }));
      expect(onSave).toHaveBeenCalledWith(expect.not.objectContaining({ semester: expect.anything() }));
    });
  });

  it("shows inline error for invalid email", async () => {
    render(<UserModal isOpen={true} onClose={vi.fn()} onSave={vi.fn()} initialData={null} />);
    const emailInput = screen.getByLabelText(/^email/i);
    fireEvent.change(emailInput, { target: { value: "not-an-email" } });
    fireEvent.blur(emailInput);
    await waitFor(() => expect(screen.getByText(/email inválido/i)).toBeInTheDocument());
  });

  it("shows 'Crear usuario' button in create mode", () => {
    render(<UserModal isOpen={true} onClose={vi.fn()} onSave={vi.fn()} initialData={null} />);
    expect(screen.getByRole("button", { name: /crear usuario/i })).toBeInTheDocument();
  });

  it("shows 'Guardar' button in edit mode", () => {
    render(<UserModal isOpen={true} onClose={vi.fn()} onSave={vi.fn()} initialData={{
      id: 1, role: "Estudiante", fullName: "María R.", email: "m@x.com",
      nationality: "V", cedula: "30243721", phone: "", semester: "9no",
    }} />);
    expect(screen.getByRole("button", { name: /^guardar$/i })).toBeInTheDocument();
  });
});
