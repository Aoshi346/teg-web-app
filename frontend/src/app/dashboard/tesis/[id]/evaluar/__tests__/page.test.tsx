/**
 * Tests for EvaluarTesisPage — Phase C (page wiring).
 *
 * The page at /dashboard/tesis/[id]/evaluar currently shows a 3-phase gate picker.
 * After Phase C frontend-worker wiring:
 *   - When project.state === 'pending_entrega', an entrega evaluation form renders
 *     showing TEG_ENTREGA_QUESTIONS (or at least spot-checks from them).
 *   - When project.state === 'pending_articulo', entrega questions are NOT shown.
 *   - When project.state === 'approved' (terminal), no form is shown.
 *
 * NOTE: As of Phase C RED, the page does NOT yet render entrega questions —
 * it only shows a 3-card gate picker without any actual question text.
 * These tests are expected to FAIL (RED) until frontend-worker adds the wiring.
 */

import React, { Suspense } from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { act, render, screen, waitFor } from "@testing-library/react";

// ── navigation mock ────────────────────────────────────────────────────────────
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), back: vi.fn() }),
  useParams: () => ({ id: "42" }),
}));

// ── project service mock ───────────────────────────────────────────────────────
const mockGetProject = vi.fn();
vi.mock("@features/projects/api/projectService", () => ({
  getProject: (...args: unknown[]) => mockGetProject(...args),
  createEvaluation: vi.fn().mockResolvedValue({ id: 1 }),
}));

// ── widget stubs (avoid complex chrome rendering) ─────────────────────────────
vi.mock("@widgets/header/DashboardHeader", () => ({
  default: ({ pageTitle }: { pageTitle: string }) => (
    <header data-testid="dashboard-header">{pageTitle}</header>
  ),
}));

// ── evaluation sub-component stubs (keep the test focused on question rendering)
vi.mock("@features/evaluations/hooks/useEvaluationDraft", () => ({
  useEvaluationDraft: () => ({
    buildDefaults: () => ({}),
    saveDraft: vi.fn(),
    clearDraft: vi.fn(),
    loadDraft: () => ({}),
  }),
}));

vi.mock("@features/evaluations/hooks/useScrollSpy", () => ({
  useScrollSpy: () => ({ activeId: null, scrollTo: vi.fn() }),
}));

vi.mock("@features/evaluations/hooks/useEvaluationSubmit", () => ({
  useEvaluationSubmit: () => ({ submit: vi.fn() }),
}));

vi.mock("@shared/hooks/useValidation", () => ({
  useValidation: () => ({
    showBanner: vi.fn(),
    bannerProps: { visible: false },
  }),
}));

vi.mock("@shared/ui/Banner", () => ({
  default: () => null,
}));

vi.mock("@shared/ui/ImageTooltip", () => ({
  ImageTooltip: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

// ── component under test ───────────────────────────────────────────────────────
import EvaluarTesisPage from "../page";
import EvaluarTesisEntregaPage from "../entrega/page";

// ── helpers ────────────────────────────────────────────────────────────────────
function makeApiProject(state: string) {
  return {
    id: 42,
    title: "Mi Tesis",
    student: "Estudiante Uno",
    submittedDate: "2026-01-01",
    state,
    period: "2026-01",
    type: "tesis",
  };
}

// ── tests ──────────────────────────────────────────────────────────────────────

describe("EvaluarTesisEntregaPage — entrega evaluation form (phase picker links here)", () => {
  beforeEach(() => {
    mockGetProject.mockResolvedValue(makeApiProject("pending_entrega"));
  });

  // The phase picker (../page) only routes; the entrega questions live in ../entrega/page.
  async function renderEntrega() {
    const params = Promise.resolve({ id: "42" });
    await act(async () => {
      render(
        <Suspense fallback={null}>
          <EvaluarTesisEntregaPage params={params} />
        </Suspense>,
      );
    });
  }

  it("renders an entrega question text fragment (te-d1)", async () => {
    await renderEntrega();

    await waitFor(() => {
      const element = screen.queryByText(/acta de aprobación del tutor/i);
      expect(element).not.toBeNull();
    }, { timeout: 3000 });
  });

  it("renders the Sec6 factible yes/no UI (te-s6-1)", async () => {
    await renderEntrega();

    await waitFor(() => {
      const element = screen.queryByText(/factible/i);
      expect(element).not.toBeNull();
    }, { timeout: 3000 });
  });
});

describe("EvaluarTesisPage — pending_articulo state", () => {
  beforeEach(() => {
    mockGetProject.mockResolvedValue(makeApiProject("pending_articulo"));
  });

  it("does NOT show entrega question text (te-d1 fragment) when state is pending_articulo", async () => {
    render(<EvaluarTesisPage />);

    // Give time for any async render
    await waitFor(() => {
      // The page should have loaded (header present)
      expect(screen.queryByTestId("dashboard-header")).not.toBeNull();
    }, { timeout: 3000 });

    // Entrega questions must not appear
    expect(screen.queryByText(/acta de aprobación del tutor/i)).toBeNull();
  });
});

describe("EvaluarTesisPage — terminal state (approved)", () => {
  beforeEach(() => {
    mockGetProject.mockResolvedValue(makeApiProject("approved"));
  });

  it("hides the evaluation form / shows lifecycle message when project is approved", async () => {
    render(<EvaluarTesisPage />);

    await waitFor(() => {
      expect(screen.queryByTestId("dashboard-header")).not.toBeNull();
    }, { timeout: 3000 });

    // No active evaluation form — no submit button
    const submitBtn = screen.queryByRole("button", { name: /enviar evaluaci/i });
    expect(submitBtn).toBeNull();

    // Entrega question text must not appear
    expect(screen.queryByText(/acta de aprobación del tutor/i)).toBeNull();
  });
});
