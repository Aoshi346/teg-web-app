import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";

// ── next/image mock ───────────────────────────────────────────────────────────
vi.mock("next/image", () => ({
  default: ({ src, alt }: { src: string; alt: string }) => (
    // eslint-disable-next-line @next/next/no-img-element
    <img src={src} alt={alt} />
  ),
}));

// ── next/link mock ────────────────────────────────────────────────────────────
vi.mock("next/link", () => ({
  default: ({
    href,
    children,
    onClick,
    onMouseEnter,
    className,
    ...rest
  }: React.AnchorHTMLAttributes<HTMLAnchorElement> & {
    href: string;
    children?: React.ReactNode;
  }) => (
    <a href={href} onClick={onClick} onMouseEnter={onMouseEnter} className={className} {...rest}>
      {children}
    </a>
  ),
}));

// ── gsap mock — the sidebar lazy-imports gsap for drawer animation ────────────
vi.mock("gsap", () => ({
  gsap: { to: vi.fn(), fromTo: vi.fn() },
}));

// ── clientAuth mock ───────────────────────────────────────────────────────────
const mockGetUserRole = vi.fn<() => string | null>();
const mockGetUser = vi.fn();

vi.mock("@features/auth/api/clientAuth", () => ({
  getUser: () => mockGetUser(),
  getUserRole: () => mockGetUserRole(),
}));

// ── component under test ──────────────────────────────────────────────────────
import Sidebar from "./Sidebar";

// ─────────────────────────────────────────────────────────────────────────────

const defaultProps = {
  isCollapsed: false,
  setIsCollapsed: vi.fn(),
  mobileOpen: false,
  setMobileOpen: vi.fn(),
};

// ── Shared admin mock setup ───────────────────────────────────────────────────
function setupAdmin() {
  mockGetUserRole.mockReturnValue("Administrador");
  mockGetUser.mockReturnValue({ email: "salazar@unimet.edu.ve", semester: "8" });
}

// ─────────────────────────────────────────────────────────────────────────────
// LEGACY TESTS — Agregar role gating (must not regress)
// ─────────────────────────────────────────────────────────────────────────────
describe("Sidebar — Agregar item role gating", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("Administrador sees the Agregar item in the sidebar", async () => {
    mockGetUserRole.mockReturnValue("Administrador");
    mockGetUser.mockReturnValue({ email: "admin@test.com", role: "Administrador", status: "active" });

    render(<Sidebar {...defaultProps} />);

    await waitFor(() => {
      expect(screen.queryAllByText(/^Agregar$/i).length).toBeGreaterThan(0);
    });
  });

  it("Tutor does NOT see the Agregar item in the sidebar", async () => {
    mockGetUserRole.mockReturnValue("Tutor");
    mockGetUser.mockReturnValue({ email: "tutor@test.com", role: "Tutor", status: "active" });

    render(<Sidebar {...defaultProps} />);

    await waitFor(() => {
      expect(screen.queryAllByText(/^Agregar$/i)).toHaveLength(0);
    });
  });

  it("Jurado does NOT see the Agregar item in the sidebar", async () => {
    mockGetUserRole.mockReturnValue("Jurado");
    mockGetUser.mockReturnValue({ email: "jurado@test.com", role: "Jurado", status: "active" });

    render(<Sidebar {...defaultProps} />);

    await waitFor(() => {
      expect(screen.queryAllByText(/^Agregar$/i)).toHaveLength(0);
    });
  });

  it("Estudiante (semester 9no) does NOT see the Agregar item in the sidebar", async () => {
    mockGetUserRole.mockReturnValue("Estudiante");
    mockGetUser.mockReturnValue({
      email: "student@test.com",
      role: "Estudiante",
      status: "active",
      semester: "9no",
    });

    render(<Sidebar {...defaultProps} />);

    await waitFor(() => {
      expect(screen.queryAllByText(/^Agregar$/i)).toHaveLength(0);
    });
  });

  it("Administrador sees all expected base navigation items", async () => {
    mockGetUserRole.mockReturnValue("Administrador");
    mockGetUser.mockReturnValue({ email: "admin@test.com", role: "Administrador", status: "active" });

    render(<Sidebar {...defaultProps} />);

    await waitFor(() => {
      expect(screen.queryAllByText(/^Dashboard$/i).length).toBeGreaterThan(0);
    });

    expect(screen.queryAllByText(/^PTEG$/i).length).toBeGreaterThan(0);
    expect(screen.queryAllByText(/^TEG$/i).length).toBeGreaterThan(0);
    expect(screen.queryAllByText(/^Seguimiento$/i).length).toBeGreaterThan(0);
    expect(screen.queryAllByText(/^Configuración$/i).length).toBeGreaterThan(0);
  });
});

// ─────────────────────────────────────────────────────────────────────────────
// NEW TESTS — Sub-M chrome redesign
// ─────────────────────────────────────────────────────────────────────────────
describe("Sidebar — Sub-M redesign: logo block", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setupAdmin();
  });

  it("renders the Fraunces wordmark 'Tesisfar'", async () => {
    render(<Sidebar {...defaultProps} />);
    await waitFor(() => {
      expect(screen.queryAllByText(/^Tesisfar$/i).length).toBeGreaterThan(0);
    });
  });

  it("renders the 'Gestión TEG' tag text", async () => {
    render(<Sidebar {...defaultProps} />);
    await waitFor(() => {
      expect(screen.queryAllByText(/gestión teg/i).length).toBeGreaterThan(0);
    });
  });

  it("logo mark element carries class sb-logo-mark", async () => {
    const { container } = render(<Sidebar {...defaultProps} />);
    await waitFor(() => {
      expect(container.querySelector(".sb-logo-mark")).not.toBeNull();
    });
  });
});

describe("Sidebar — Sub-M redesign: group titles", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setupAdmin();
  });

  it("renders the 'Workspace' group title in expanded view", async () => {
    render(<Sidebar {...defaultProps} />);
    await waitFor(() => {
      expect(screen.queryAllByText(/^Workspace$/i).length).toBeGreaterThan(0);
    });
  });

  it("renders the 'Operación' group title in expanded view", async () => {
    render(<Sidebar {...defaultProps} />);
    await waitFor(() => {
      expect(screen.queryAllByText(/^Operación$/i).length).toBeGreaterThan(0);
    });
  });
});

describe("Sidebar — Sub-M redesign: group composition", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setupAdmin();
  });

  it("Workspace group contains Dashboard, PTEG, TEG, Planificación", async () => {
    const { container } = render(<Sidebar {...defaultProps} />);
    await waitFor(() => {
      const group = container.querySelector("[data-testid='sb-group-Workspace']");
      expect(group).not.toBeNull();
      expect(group!.textContent).toMatch(/Dashboard/i);
      expect(group!.textContent).toMatch(/PTEG/i);
      expect(group!.textContent).toMatch(/TEG/i);
      expect(group!.textContent).toMatch(/Planificación/i);
    });
  });

  it("Operación group contains Seguimiento, Agregar, Configuración", async () => {
    const { container } = render(<Sidebar {...defaultProps} />);
    await waitFor(() => {
      const group = container.querySelector("[data-testid='sb-group-Operación']");
      expect(group).not.toBeNull();
      expect(group!.textContent).toMatch(/Seguimiento/i);
      expect(group!.textContent).toMatch(/Agregar/i);
      expect(group!.textContent).toMatch(/Configuración/i);
    });
  });
});

describe("Sidebar — Sub-M redesign: item active state", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setupAdmin();
  });

  it("active item has aria-current='page' and carries both 'active' and 'sb-item' classes", async () => {
    const { container } = render(<Sidebar {...defaultProps} />);
    await waitFor(() => {
      const activeEl = container.querySelector("[aria-current='page']");
      expect(activeEl).not.toBeNull();
      expect(activeEl!.classList.contains("active")).toBe(true);
      expect(activeEl!.classList.contains("sb-item")).toBe(true);
    });
  });
});

describe("Sidebar — Sub-M redesign: keyboard shortcut chips", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setupAdmin();
  });

  it("does not render Alt+N keyboard shortcut chips on items (visual noise)", async () => {
    const { container } = render(<Sidebar {...defaultProps} />);
    await waitFor(() => {
      expect(container.querySelectorAll(".sb-item").length).toBeGreaterThan(0);
      expect(container.querySelectorAll(".sb-item-kbd").length).toBe(0);
    });
  });
});

describe("Sidebar — Sub-M redesign: foot card", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setupAdmin();
  });

  it("foot card element with class sb-foot is rendered", async () => {
    const { container } = render(<Sidebar {...defaultProps} />);
    await waitFor(() => {
      expect(container.querySelector(".sb-foot")).not.toBeNull();
    });
  });

  it("foot card avatar (sb-foot-ava) shows the first letter of the user email", async () => {
    const { container } = render(<Sidebar {...defaultProps} />);
    await waitFor(() => {
      const ava = container.querySelector(".sb-foot-ava");
      expect(ava).not.toBeNull();
      // "salazar@unimet.edu.ve" → first letter "S"
      expect(ava!.textContent?.trim().toUpperCase()).toBe("S");
    });
  });

  it("foot card renders user name in sb-foot-name element", async () => {
    const { container } = render(<Sidebar {...defaultProps} />);
    await waitFor(() => {
      const nameEl = container.querySelector(".sb-foot-name");
      expect(nameEl).not.toBeNull();
      expect(nameEl!.textContent?.trim().length).toBeGreaterThan(0);
    });
  });

  it("foot card renders uppercase role in sb-foot-role element", async () => {
    const { container } = render(<Sidebar {...defaultProps} />);
    await waitFor(() => {
      const roleEl = container.querySelector(".sb-foot-role");
      expect(roleEl).not.toBeNull();
      // The element should contain the role text (CSS uppercases, but text is present)
      expect(roleEl!.textContent?.trim().length).toBeGreaterThan(0);
    });
  });
});

describe("Sidebar — Sub-M redesign: collapsed state", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setupAdmin();
  });

  it("root aside has class is-collapsed when isCollapsed=true", async () => {
    const { container } = render(
      <Sidebar {...defaultProps} isCollapsed={true} />
    );
    await waitFor(() => {
      // The sidebar root element (aside or div with sb class) carries is-collapsed
      expect(container.querySelector(".is-collapsed")).not.toBeNull();
    });
  });

  it("logo word ('Tesisfar' text) is NOT rendered when collapsed", async () => {
    render(<Sidebar {...defaultProps} isCollapsed={true} />);
    await waitFor(() => {
      // sb-logo-word container is hidden/absent; Tesisfar wordmark not visible
      expect(screen.queryAllByText(/^Tesisfar$/i)).toHaveLength(0);
    });
  });

  it("item labels are NOT rendered when collapsed", async () => {
    render(<Sidebar {...defaultProps} isCollapsed={true} />);
    await waitFor(() => {
      expect(screen.queryAllByText(/^Dashboard$/i)).toHaveLength(0);
    });
  });

  it("kbd shortcut chips are NOT rendered when collapsed", async () => {
    const { container } = render(<Sidebar {...defaultProps} isCollapsed={true} />);
    await waitFor(() => {
      // .sb-item-kbd elements are absent in collapsed state
      expect(container.querySelectorAll(".sb-item-kbd").length).toBe(0);
    });
  });

  it("foot card shows only avatar (no name/role text) when collapsed", async () => {
    render(<Sidebar {...defaultProps} isCollapsed={true} />);
    await waitFor(() => {
      expect(screen.queryAllByText(/salazar/i)).toHaveLength(0);
      expect(screen.queryAllByText(/administrador/i)).toHaveLength(0);
    });
  });
});

describe("Sidebar — Sub-M redesign: collapsed tooltip via data-label", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setupAdmin();
  });

  it("each nav item has a data-label attribute matching its label", async () => {
    const { container } = render(<Sidebar {...defaultProps} />);
    await waitFor(() => {
      const dashboardItem = container.querySelector(".sb-item[data-label='Dashboard']");
      expect(dashboardItem).not.toBeNull();
    });
  });

  it("Planificación item carries data-label='Planificación'", async () => {
    const { container } = render(<Sidebar {...defaultProps} />);
    await waitFor(() => {
      const el = container.querySelector(".sb-item[data-label='Planificación']");
      expect(el).not.toBeNull();
    });
  });
});

describe("Sidebar — Sub-M redesign: mobile drawer markup", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setupAdmin();
  });

  it("drawer with role='dialog' is rendered when mobileOpen=true", async () => {
    render(<Sidebar {...defaultProps} mobileOpen={true} />);
    await waitFor(() => {
      expect(screen.queryAllByRole("dialog").length).toBeGreaterThan(0);
    });
  });
});

describe("Sidebar — Sub-M redesign: no legacy color classes", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setupAdmin();
  });

  const BANNED_CLASSES = [
    "text-slate-",
    "bg-slate-",
    "border-slate-",
    "bg-primary/10",
    "bg-primary/5",
    "bg-blue-100",
    "bg-purple-100",
    "bg-emerald-100",
    "bg-amber-100",
  ];

  it("rendered HTML does not contain legacy Tailwind color classes", async () => {
    const { container } = render(<Sidebar {...defaultProps} />);
    await waitFor(() => {
      // Confirm component mounted (logo mark present)
      expect(container.querySelector(".sb-logo-mark")).not.toBeNull();
    });
    const html = container.innerHTML;
    for (const cls of BANNED_CLASSES) {
      expect(html, `should not contain '${cls}'`).not.toContain(cls);
    }
  });
});
