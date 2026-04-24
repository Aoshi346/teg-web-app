/**
 * Prefetch hygiene tests — Phase 2A (RED)
 *
 * These tests pin down the correct behavior: components must NOT call
 * router.prefetch() on mount. Prefetch is only permitted on explicit user
 * intent (mouseEnter / hover), never eagerly on every render.
 *
 * Tests 1-4 are expected to FAIL (RED) because the current code DOES call
 * router.prefetch() on mount. Test 5 is expected to PASS (the hover handler
 * already exists and is correct).
 */

import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, fireEvent } from "@testing-library/react";
import { Project } from "@/features/projects/types/project";

// ── next/navigation mock ───────────────────────────────────────────────────
// Must be hoisted before any import that consumes next/navigation.
// All three components under test use useRouter from next/navigation.

const mockPrefetch = vi.fn();
const mockPush = vi.fn();
const mockReplace = vi.fn();
const mockRedirect = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    prefetch: mockPrefetch,
    push: mockPush,
    replace: mockReplace,
    back: vi.fn(),
    forward: vi.fn(),
    refresh: vi.fn(),
  }),
  usePathname: () => "/dashboard",
  useSearchParams: () => new URLSearchParams(),
  redirect: mockRedirect,
}));

// ── next/image mock ────────────────────────────────────────────────────────
// Next Image uses an internal loader that doesn't work in jsdom.
vi.mock("next/image", () => ({
  default: ({ src, alt }: { src: string; alt: string }) => (
    // eslint-disable-next-line @next/next/no-img-element
    <img src={src} alt={alt} />
  ),
}));

// ── next/link mock ─────────────────────────────────────────────────────────
// next/link in jsdom produces an <a> but the prefetch prop triggers internal
// Next.js prefetch machinery that may not work in vitest. We mock it to a
// plain anchor that still forwards onClick and onMouseEnter so we can test
// the hover behavior properly.
vi.mock("next/link", () => ({
  default: ({
    href,
    children,
    onClick,
    onMouseEnter,
    className,
    prefetch: _prefetch, // drop the prop — we don't want Next.js auto-prefetch in tests
    ...rest
  }: React.AnchorHTMLAttributes<HTMLAnchorElement> & {
    href: string;
    prefetch?: boolean;
    children?: React.ReactNode;
  }) => (
    <a
      href={href}
      onClick={onClick}
      onMouseEnter={onMouseEnter}
      className={className}
      {...rest}
    >
      {children}
    </a>
  ),
}));

// ── @/features/auth/clientAuth mock ───────────────────────────────────────
// DashboardLayout and Sidebar both read from clientAuth. We return a valid
// active admin user so the auth guard doesn't redirect and the sidebar
// renders its full menu.
vi.mock("@/features/auth/api/clientAuth", () => ({
  isAuthenticated: () => true,
  getUser: () => ({
    email: "admin@test.com",
    status: "active",
    role: "Administrador",
    fullName: "Admin Test",
    firstName: "Admin",
    lastName: "Test",
  }),
  getUserRole: () => "Administrador",
  logout: vi.fn(),
}));

// ── gsap mock ─────────────────────────────────────────────────────────────
// Sidebar lazy-imports gsap for mobile drawer animation. Mock it so the
// dynamic import resolves without errors in jsdom.
vi.mock("gsap", () => ({
  gsap: {
    to: vi.fn(),
    fromTo: vi.fn(),
  },
}));

beforeEach(() => {
  mockPrefetch.mockClear();
  mockPush.mockClear();
  mockReplace.mockClear();
  mockRedirect.mockClear();
});

// ── Minimal mock Project ───────────────────────────────────────────────────
const mockProject: Project = {
  id: 1,
  title: "Test Project",
  student: "Student Name",
  submittedDate: "2026-04-01",
  status: "pending",
  state: "pending_review_1",
  period: "2026-01",
  advisorNames: [],
  type: "proyecto",
  failedAttempts: 0,
  stage1Passed: false,
  score: undefined,
  diagramacionScore: undefined,
  contenidoScore: undefined,
};

// ═══════════════════════════════════════════════════════════════════════════
// describe: ProjectCard prefetch hygiene
// ═══════════════════════════════════════════════════════════════════════════

describe("ProjectCard prefetch hygiene", () => {
  // Lazy import inside describe to ensure mocks are registered before the
  // module is evaluated by vitest (top-level vi.mock is hoisted, which is
  // sufficient, but we co-locate the import for clarity).
  let ProjectCard: typeof import("@/features/projects/components/ProjectCard").default;

  beforeEach(async () => {
    // Re-import each time to pick up fresh mock state
    const mod = await import("@/features/projects/components/ProjectCard");
    ProjectCard = mod.default;
  });

  it("does not prefetch on mount when given a primaryHref", () => {
    render(
      <ProjectCard
        project={mockProject}
        primaryHref="/dashboard/proyectos/1"
      />
    );

    expect(mockPrefetch).not.toHaveBeenCalled();
  });

  it("does not prefetch when a grid of 10 cards is rendered", () => {
    const projects: Project[] = Array.from({ length: 10 }, (_, i) => ({
      ...mockProject,
      id: i + 1,
      title: `Project ${i + 1}`,
    }));

    render(
      <div>
        {projects.map((p) => (
          <ProjectCard
            key={p.id}
            project={p}
            primaryHref={`/dashboard/proyectos/${p.id}`}
          />
        ))}
      </div>
    );

    // Even with 10 cards, router.prefetch must have been called zero times
    // on mount. This is the regression guard for the main offender.
    expect(mockPrefetch).not.toHaveBeenCalled();
  });
});

// ═══════════════════════════════════════════════════════════════════════════
// describe: DashboardLayout prefetch hygiene
// ═══════════════════════════════════════════════════════════════════════════

describe("DashboardLayout prefetch hygiene", () => {
  let DashboardLayout: typeof import("@/app/dashboard/layout").default;

  beforeEach(async () => {
    const mod = await import("@/app/dashboard/layout");
    DashboardLayout = mod.default;
  });

  it("does not prefetch on mount when user is authenticated and active", () => {
    render(
      <DashboardLayout>
        <div>children</div>
      </DashboardLayout>
    );

    expect(mockPrefetch).not.toHaveBeenCalled();
  });
});

// ═══════════════════════════════════════════════════════════════════════════
// describe: Sidebar prefetch hygiene
// ═══════════════════════════════════════════════════════════════════════════

describe("Sidebar prefetch hygiene", () => {
  let Sidebar: typeof import("@/widgets/sidebar/Sidebar").default;

  beforeEach(async () => {
    const mod = await import("@/widgets/sidebar/Sidebar");
    Sidebar = mod.default;
  });

  function renderSidebar() {
    return render(
      <Sidebar
        isCollapsed={false}
        setIsCollapsed={() => {}}
        mobileOpen={false}
        setMobileOpen={() => {}}
      />
    );
  }

  it("does not prefetch on mount", () => {
    renderSidebar();

    // No useEffect prefetch, no <Link prefetch={true}> auto-prefetch should
    // fire during initial render.
    expect(mockPrefetch).not.toHaveBeenCalled();
  });

  it("prefetches on link hover (the good pattern — must stay)", () => {
    const { container } = renderSidebar();

    // The desktop sidebar renders nav links. Find the first anchor in the
    // desktop aside element and hover over it to trigger handleLinkHover.
    const desktopAside = container.querySelector("aside");
    expect(desktopAside).toBeTruthy();

    const firstLink = desktopAside!.querySelector("a");
    expect(firstLink).toBeTruthy();

    fireEvent.mouseEnter(firstLink!);

    // handleLinkHover calls router.prefetch(href) — it must have been called
    // at least once with the href of the first nav item.
    expect(mockPrefetch).toHaveBeenCalledTimes(1);
    expect(mockPrefetch).toHaveBeenCalledWith(
      expect.stringMatching(/^\/dashboard/)
    );
  });
});
