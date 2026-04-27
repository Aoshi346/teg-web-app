import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { DetailHero } from "../DetailHero";
import type { Project } from "@features/projects/types/project";

vi.mock("@features/projects/api/projectService", () => ({
  deleteProject: vi.fn(),
}));

const mockPush = vi.fn();

vi.mock("next/navigation", async () => {
  const actual = await vi.importActual<typeof import("next/navigation")>("next/navigation");
  return {
    ...actual,
    useRouter: () => ({
      push: mockPush,
      replace: vi.fn(),
      back: vi.fn(),
      forward: vi.fn(),
      refresh: vi.fn(),
      prefetch: vi.fn(),
    }),
    useSearchParams: () => new URLSearchParams(),
    usePathname: () => "/",
  };
});

import { deleteProject } from "@features/projects/api/projectService";

const mockDeleteProject = vi.mocked(deleteProject);

function makeProject(overrides: Partial<Project> = {}): Project {
  return {
    id: 7,
    title: "Sistema de gestión académica",
    student: "Carlos López",
    advisorNames: ["Prof. Ramírez"],
    reviewerName: "Prof. Soto",
    submittedDate: "2026-01-15",
    state: "pending_review_1",
    period: "2026-01",
    type: "proyecto",
    ...overrides,
  } as Project;
}

beforeEach(() => {
  vi.clearAllMocks();
});

describe("DetailHero — admin delete button", () => {
  it("renders 'Eliminar proyecto' button in the right rail for admin viewing a PTEG project", () => {
    render(
      <DetailHero
        project={makeProject({ type: "proyecto" })}
        role="Administrador"
        onOverrideClick={() => {}}
        onDeleteClick={() => {}}
      />
    );
    expect(screen.getByRole("button", { name: /Eliminar proyecto/i })).toBeTruthy();
  });

  it("renders 'Eliminar proyecto' button in the right rail for admin viewing a TEG project", () => {
    render(
      <DetailHero
        project={makeProject({ type: "tesis", state: "pending_articulo" })}
        role="Administrador"
        onOverrideClick={() => {}}
        onDeleteClick={() => {}}
      />
    );
    expect(screen.getByRole("button", { name: /Eliminar proyecto/i })).toBeTruthy();
  });

  it("does not render 'Eliminar proyecto' button for Estudiante", () => {
    render(
      <DetailHero
        project={makeProject()}
        role="Estudiante"
      />
    );
    expect(screen.queryByRole("button", { name: /Eliminar proyecto/i })).toBeNull();
  });

  it("does not render 'Eliminar proyecto' button for Tutor", () => {
    render(
      <DetailHero
        project={makeProject()}
        role="Tutor"
      />
    );
    expect(screen.queryByRole("button", { name: /Eliminar proyecto/i })).toBeNull();
  });

  it("does not render 'Eliminar proyecto' button for Jurado", () => {
    render(
      <DetailHero
        project={makeProject()}
        role="Jurado"
        evaluarHref="/dashboard/proyectos/7/evaluar"
      />
    );
    expect(screen.queryByRole("button", { name: /Eliminar proyecto/i })).toBeNull();
  });

  it("clicking 'Eliminar proyecto' opens DeleteProjectModal (title input label visible)", async () => {
    const user = userEvent.setup();
    render(
      <DetailHero
        project={makeProject({ type: "proyecto" })}
        role="Administrador"
        onOverrideClick={() => {}}
        onDeleteClick={() => {}}
      />
    );
    const deleteBtn = screen.getByRole("button", { name: /Eliminar proyecto/i });
    await user.click(deleteBtn);
    expect(screen.getByRole("textbox")).toBeTruthy();
  });

  it("after modal onConfirmed, router.push goes to /dashboard/proyectos for PTEG", async () => {
    mockDeleteProject.mockResolvedValueOnce(undefined);
    const user = userEvent.setup();
    render(
      <DetailHero
        project={makeProject({ type: "proyecto", title: "Sistema de gestión académica" })}
        role="Administrador"
        onOverrideClick={() => {}}
        onDeleteClick={() => {}}
      />
    );

    const deleteBtn = screen.getByRole("button", { name: /Eliminar proyecto/i });
    await user.click(deleteBtn);

    const input = screen.getByRole("textbox");
    await user.type(input, "Sistema de gestión académica");

    const confirmBtn = screen.getByRole("button", { name: /Eliminar/i });
    await user.click(confirmBtn);

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith("/dashboard/proyectos");
    });
  });

  it("after modal onConfirmed, router.push goes to /dashboard/tesis for TEG", async () => {
    mockDeleteProject.mockResolvedValueOnce(undefined);
    const user = userEvent.setup();
    render(
      <DetailHero
        project={makeProject({ type: "tesis", state: "pending_articulo", title: "Sistema de gestión académica" })}
        role="Administrador"
        onOverrideClick={() => {}}
        onDeleteClick={() => {}}
      />
    );

    const deleteBtn = screen.getByRole("button", { name: /Eliminar proyecto/i });
    await user.click(deleteBtn);

    const input = screen.getByRole("textbox");
    await user.type(input, "Sistema de gestión académica");

    const confirmBtn = screen.getByRole("button", { name: /Eliminar/i });
    await user.click(confirmBtn);

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith("/dashboard/tesis");
    });
  });
});
