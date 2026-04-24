import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { SettingsShell } from "@features/settings/components/SettingsShell";

vi.mock("@features/auth/api/clientAuth", () => ({
  getUserRole: vi.fn(),
  getUser: vi.fn(() => null),
  updateProfile: vi.fn(),
}));

vi.mock("@features/semesters/api/semesters", () => ({
  getSemesters: vi.fn().mockResolvedValue([]),
}));

import { getUserRole } from "@features/auth/api/clientAuth";

describe("SettingsShell", () => {
  it("shows the Administración tab for Administrador", () => {
    vi.mocked(getUserRole).mockReturnValue("Administrador");
    render(<SettingsShell />);
    expect(screen.getByRole("tab", { name: /Administración/i })).toBeInTheDocument();
  });

  it("hides the Administración tab for Estudiante", () => {
    vi.mocked(getUserRole).mockReturnValue("Estudiante");
    render(<SettingsShell />);
    expect(screen.queryByRole("tab", { name: /Administración/i })).not.toBeInTheDocument();
  });

  it("renders Perfil, Seguridad, Notificaciones for all roles", () => {
    vi.mocked(getUserRole).mockReturnValue("Tutor");
    render(<SettingsShell />);
    expect(screen.getByRole("tab", { name: /Perfil/i })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /Seguridad/i })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /Notificaciones/i })).toBeInTheDocument();
  });
});
