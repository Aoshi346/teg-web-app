import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

// ── next/navigation mock ──────────────────────────────────────────────────────
vi.mock("next/navigation", async () => {
  const actual = await vi.importActual<typeof import("next/navigation")>("next/navigation");
  return {
    ...actual,
    useRouter: () => ({
      push: vi.fn(),
      replace: vi.fn(),
      back: vi.fn(),
      forward: vi.fn(),
      refresh: vi.fn(),
      prefetch: vi.fn(),
    }),
    usePathname: () => "/dashboard/settings",
    useSearchParams: () => new URLSearchParams(),
  };
});

// ── component under test ──────────────────────────────────────────────────────
import ProfileMenu, { ProfileMenuProps } from "./ProfileMenu";

// ─────────────────────────────────────────────────────────────────────────────

const defaultProps: ProfileMenuProps = {
  isOpen: true,
  email: "salazar@unimet.edu.ve",
  role: "Administrador",
  onClose: vi.fn(),
  onLogout: vi.fn(),
};

function setup(overrides: Partial<ProfileMenuProps> = {}) {
  const props = { ...defaultProps, ...overrides, onClose: vi.fn(), onLogout: vi.fn() };
  const result = render(<ProfileMenu {...props} />);
  return { ...result, props };
}

describe("ProfileMenu — visibility", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("returns null or hidden element when isOpen=false", () => {
    const { container } = setup({ isOpen: false });
    // The menu should not be in the DOM when closed
    const menu = container.querySelector("[role='menu']");
    const isHidden = menu === null || menu.getAttribute("aria-hidden") === "true";
    expect(isHidden).toBe(true);
  });

  it("renders [role='menu'] with class prof-pop when isOpen=true", () => {
    const { container } = setup({ isOpen: true });
    const menu = container.querySelector("[role='menu']");
    expect(menu).not.toBeNull();
    expect(menu!.classList.contains("prof-pop")).toBe(true);
  });
});

describe("ProfileMenu — band header", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("header band has class prof-band with pteg-soft styling class", () => {
    const { container } = setup();
    expect(container.querySelector(".prof-band")).not.toBeNull();
  });

  it("avatar block has class prof-band-ava", () => {
    const { container } = setup();
    expect(container.querySelector(".prof-band-ava")).not.toBeNull();
  });

  it("avatar shows first letter of email uppercased (Fraunces)", () => {
    const { container } = setup({ email: "salazar@unimet.edu.ve" });
    const ava = container.querySelector(".prof-band-ava");
    expect(ava).not.toBeNull();
    // "salazar@..." → "S"
    expect(ava!.textContent?.trim().toUpperCase()).toBe("S");
  });

  it("eyebrow text 'Identificado como' is present", () => {
    setup();
    expect(screen.getByText(/identificado como/i)).toBeInTheDocument();
  });

  it("name element (prof-band-name) shows first-letter-uppercased local part of email", () => {
    const { container } = setup({ email: "salazar@unimet.edu.ve" });
    const nameEl = container.querySelector(".prof-band-name");
    expect(nameEl).not.toBeNull();
    // "salazar@unimet.edu.ve" → local part "salazar" → "Salazar"
    expect(nameEl!.textContent?.toLowerCase()).toContain("salazar");
  });

  it("email is rendered verbatim in prof-band-email", () => {
    const { container } = setup({ email: "salazar@unimet.edu.ve" });
    const emailEl = container.querySelector(".prof-band-email");
    expect(emailEl).not.toBeNull();
    expect(emailEl!.textContent).toContain("salazar@unimet.edu.ve");
  });

  it("role chip (prof-band-role) contains the role prop text", () => {
    const { container } = setup({ role: "Administrador" });
    const roleEl = container.querySelector(".prof-band-role");
    expect(roleEl).not.toBeNull();
    expect(roleEl!.textContent?.toUpperCase()).toContain("ADMINISTRADOR");
  });
});

describe("ProfileMenu — sections", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders 'Cuenta' section title", () => {
    setup();
    expect(screen.getByText(/^Cuenta$/i)).toBeInTheDocument();
  });

  it("renders 'Mi perfil' item in Cuenta section", () => {
    setup();
    expect(screen.getByText(/^Mi perfil$/i)).toBeInTheDocument();
  });

  it("renders 'Configuración' item with ⌘, shortcut chip", () => {
    const { container } = setup();
    expect(screen.getByText(/^Configuración$/i)).toBeInTheDocument();
    const chips = container.querySelectorAll(".prof-shortcut");
    const chipTexts = Array.from(chips).map(el => el.textContent ?? "");
    expect(chipTexts.some(t => t.includes("⌘") && t.includes(","))).toBe(true);
  });

  it("renders 'Privacidad' item in Cuenta section", () => {
    setup();
    expect(screen.getByText(/^Privacidad$/i)).toBeInTheDocument();
  });

  it("renders 'Soporte' section title", () => {
    setup();
    expect(screen.getByText(/^Soporte$/i)).toBeInTheDocument();
  });

  it("renders 'Centro de ayuda' item in Soporte section", () => {
    setup();
    expect(screen.getByText(/^Centro de ayuda$/i)).toBeInTheDocument();
  });

  it("renders 'Reportar problema' item in Soporte section", () => {
    setup();
    expect(screen.getByText(/^Reportar problema$/i)).toBeInTheDocument();
  });

  it("renders 'Cerrar sesión' item with class danger and ⇧⌘ Q shortcut chip", () => {
    const { container } = setup();
    expect(screen.getByText(/cerrar sesión/i)).toBeInTheDocument();
    const dangerItem = container.querySelector(".prof-item.danger");
    expect(dangerItem).not.toBeNull();
    const chips = container.querySelectorAll(".prof-shortcut");
    const chipTexts = Array.from(chips).map(el => el.textContent ?? "");
    expect(chipTexts.some(t => t.includes("⇧") && t.includes("Q"))).toBe(true);
  });
});

describe("ProfileMenu — logout action", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("clicking 'Cerrar sesión' calls onLogout exactly once", () => {
    const onLogout = vi.fn();
    render(<ProfileMenu {...defaultProps} onLogout={onLogout} />);
    const logoutBtn = screen.getByText(/cerrar sesión/i).closest("button, [role='menuitem']") as HTMLElement;
    fireEvent.click(logoutBtn);
    expect(onLogout).toHaveBeenCalledTimes(1);
  });
});

describe("ProfileMenu — keyboard and outside-click closing", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("pressing ESC calls onClose", () => {
    const onClose = vi.fn();
    render(<ProfileMenu {...defaultProps} onClose={onClose} />);
    fireEvent.keyDown(document, { key: "Escape" });
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("clicking outside the menu calls onClose", () => {
    const onClose = vi.fn();
    render(
      <div>
        <ProfileMenu {...defaultProps} onClose={onClose} />
        <button data-testid="outside">Outside</button>
      </div>
    );
    fireEvent.mouseDown(screen.getByTestId("outside"));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("clicking inside the menu does NOT call onClose", () => {
    const onClose = vi.fn();
    const { container } = render(<ProfileMenu {...defaultProps} onClose={onClose} />);
    const menu = container.querySelector("[role='menu']") as HTMLElement;
    fireEvent.mouseDown(menu);
    expect(onClose).not.toHaveBeenCalled();
  });
});
