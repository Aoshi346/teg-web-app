import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

// Mock before importing the component — the component will import changePassword from here.
// The api.ts client extracts the first array value from a field-error response and throws
// new Error(message), so we simulate that same shape here.
vi.mock("@features/auth/api/clientAuth", () => ({
  changePassword: vi.fn(),
}));

import { SecurityTab } from "./SecurityTab";
import { changePassword } from "@features/auth/api/clientAuth";

const mockChangePassword = vi.mocked(changePassword);

describe("SecurityTab", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders all 3 password inputs and the submit button", () => {
    render(<SecurityTab />);

    expect(screen.getByLabelText(/contraseña actual/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^nueva contraseña/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/confirmar nueva contraseña/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /cambiar contraseña/i })).toBeInTheDocument();

    const inputs = screen.getAllByDisplayValue("");
    // All three password inputs should be type="password"
    inputs.forEach((input) => {
      expect((input as HTMLInputElement).type).toBe("password");
    });
  });

  it("shows inline error and does NOT call changePassword when confirmPassword does not match", async () => {
    const user = userEvent.setup();
    render(<SecurityTab />);

    await user.type(screen.getByLabelText(/contraseña actual/i), "OldPass1!");
    await user.type(screen.getByLabelText(/^nueva contraseña/i), "NewPass123!");
    await user.type(screen.getByLabelText(/confirmar nueva contraseña/i), "DifferentPass!");
    await user.click(screen.getByRole("button", { name: /cambiar contraseña/i }));

    expect(await screen.findByText(/las contraseñas no coinciden/i)).toBeInTheDocument();
    expect(mockChangePassword).not.toHaveBeenCalled();
  });

  it("shows inline error and does NOT call changePassword when newPassword is shorter than 8 characters", async () => {
    const user = userEvent.setup();
    render(<SecurityTab />);

    await user.type(screen.getByLabelText(/contraseña actual/i), "OldPass1!");
    await user.type(screen.getByLabelText(/^nueva contraseña/i), "short");
    await user.type(screen.getByLabelText(/confirmar nueva contraseña/i), "short");
    await user.click(screen.getByRole("button", { name: /cambiar contraseña/i }));

    // The Zod schema enforces min length 8 on newPassword
    expect(await screen.findByText(/mínimo 8 caracteres/i)).toBeInTheDocument();
    expect(mockChangePassword).not.toHaveBeenCalled();
  });

  it("calls changePassword once with correct payload, shows success message, and clears the form", async () => {
    mockChangePassword.mockResolvedValueOnce(undefined);

    const user = userEvent.setup();
    render(<SecurityTab />);

    await user.type(screen.getByLabelText(/contraseña actual/i), "OldPass1!");
    await user.type(screen.getByLabelText(/^nueva contraseña/i), "NewPass123!");
    await user.type(screen.getByLabelText(/confirmar nueva contraseña/i), "NewPass123!");
    await user.click(screen.getByRole("button", { name: /cambiar contraseña/i }));

    expect(mockChangePassword).toHaveBeenCalledTimes(1);
    expect(mockChangePassword).toHaveBeenCalledWith({
      currentPassword: "OldPass1!",
      newPassword: "NewPass123!",
    });

    expect(await screen.findByText(/contraseña actualizada/i)).toBeInTheDocument();

    // All fields should be cleared after success
    const currentInput = screen.getByLabelText(/contraseña actual/i) as HTMLInputElement;
    const newInput = screen.getByLabelText(/^nueva contraseña/i) as HTMLInputElement;
    const confirmInput = screen.getByLabelText(/confirmar nueva contraseña/i) as HTMLInputElement;
    expect(currentInput.value).toBe("");
    expect(newInput.value).toBe("");
    expect(confirmInput.value).toBe("");
  });

  it("shows field error under current-password and does NOT clear the form when API rejects with wrong current password", async () => {
    // api.ts extracts the first string from the first field's array and throws new Error(message).
    // So { current_password: ["Contraseña actual incorrecta."] } becomes new Error("Contraseña actual incorrecta.")
    mockChangePassword.mockRejectedValueOnce(
      new Error("Contraseña actual incorrecta.")
    );

    const user = userEvent.setup();
    render(<SecurityTab />);

    await user.type(screen.getByLabelText(/contraseña actual/i), "WrongPass!");
    await user.type(screen.getByLabelText(/^nueva contraseña/i), "NewPass123!");
    await user.type(screen.getByLabelText(/confirmar nueva contraseña/i), "NewPass123!");
    await user.click(screen.getByRole("button", { name: /cambiar contraseña/i }));

    expect(await screen.findByText(/contraseña actual incorrecta/i)).toBeInTheDocument();

    // Form should NOT be cleared on API error
    const currentInput = screen.getByLabelText(/contraseña actual/i) as HTMLInputElement;
    expect(currentInput.value).toBe("WrongPass!");
  });
});
