import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { DeleteProjectModal } from "../DeleteProjectModal";

vi.mock("@features/projects/api/projectService", () => ({
  deleteProject: vi.fn(),
}));

import { deleteProject } from "@features/projects/api/projectService";

const mockDeleteProject = vi.mocked(deleteProject);

const DEFAULT_PROPS = {
  isOpen: true,
  projectTitle: "Plataforma de tutorías online",
  projectId: 42,
  projectType: "proyecto" as const,
  onClose: vi.fn(),
  onConfirmed: vi.fn(),
};

beforeEach(() => {
  vi.clearAllMocks();
});

describe("DeleteProjectModal", () => {
  it("returns nothing when isOpen is false", () => {
    const { container } = render(
      <DeleteProjectModal {...DEFAULT_PROPS} isOpen={false} />
    );
    expect(container.firstChild).toBeNull();
  });

  it("renders the project title when open", () => {
    render(<DeleteProjectModal {...DEFAULT_PROPS} />);
    expect(screen.getByText("Plataforma de tutorías online")).toBeTruthy();
  });

  it("renders a text input asking the admin to type the project title", () => {
    render(<DeleteProjectModal {...DEFAULT_PROPS} />);
    const input = screen.getByRole("textbox");
    expect(input).toBeTruthy();
  });

  it("destructive button is disabled while the input is empty", () => {
    render(<DeleteProjectModal {...DEFAULT_PROPS} />);
    const deleteBtn = screen.getByRole("button", { name: /Eliminar/i });
    expect((deleteBtn as HTMLButtonElement).disabled).toBe(true);
  });

  it("destructive button is disabled while the input does not match the title", async () => {
    const user = userEvent.setup();
    render(<DeleteProjectModal {...DEFAULT_PROPS} />);
    const input = screen.getByRole("textbox");
    await user.type(input, "plataforma de tutorias online");
    const deleteBtn = screen.getByRole("button", { name: /Eliminar/i });
    expect((deleteBtn as HTMLButtonElement).disabled).toBe(true);
  });

  it("destructive button is enabled when input matches the title exactly", async () => {
    const user = userEvent.setup();
    render(<DeleteProjectModal {...DEFAULT_PROPS} />);
    const input = screen.getByRole("textbox");
    await user.type(input, "Plataforma de tutorías online");
    const deleteBtn = screen.getByRole("button", { name: /Eliminar/i });
    expect((deleteBtn as HTMLButtonElement).disabled).toBe(false);
  });

  it("calls deleteProject and then onConfirmed on successful submit", async () => {
    mockDeleteProject.mockResolvedValueOnce(undefined);
    const onConfirmed = vi.fn();
    const user = userEvent.setup();
    render(<DeleteProjectModal {...DEFAULT_PROPS} onConfirmed={onConfirmed} />);
    const input = screen.getByRole("textbox");
    await user.type(input, "Plataforma de tutorías online");
    const deleteBtn = screen.getByRole("button", { name: /Eliminar/i });
    await user.click(deleteBtn);
    await waitFor(() => {
      expect(mockDeleteProject).toHaveBeenCalledWith(42);
      expect(onConfirmed).toHaveBeenCalledTimes(1);
    });
  });

  it("shows an error message and does not call onConfirmed when deleteProject rejects", async () => {
    mockDeleteProject.mockRejectedValueOnce(new Error("Error del servidor"));
    const onConfirmed = vi.fn();
    const user = userEvent.setup();
    render(<DeleteProjectModal {...DEFAULT_PROPS} onConfirmed={onConfirmed} />);
    const input = screen.getByRole("textbox");
    await user.type(input, "Plataforma de tutorías online");
    const deleteBtn = screen.getByRole("button", { name: /Eliminar/i });
    await user.click(deleteBtn);
    await waitFor(() => {
      expect(screen.getByText(/Error del servidor/i)).toBeTruthy();
    });
    expect(onConfirmed).not.toHaveBeenCalled();
  });

  it("calls onClose when the Cancel button is clicked and never calls deleteProject", async () => {
    const onClose = vi.fn();
    const user = userEvent.setup();
    render(<DeleteProjectModal {...DEFAULT_PROPS} onClose={onClose} />);
    const cancelBtn = screen.getByRole("button", { name: /Cancelar/i });
    await user.click(cancelBtn);
    expect(onClose).toHaveBeenCalledTimes(1);
    expect(mockDeleteProject).not.toHaveBeenCalled();
  });

  it("calls onClose when clicking the overlay backdrop", async () => {
    const onClose = vi.fn();
    const user = userEvent.setup();
    render(<DeleteProjectModal {...DEFAULT_PROPS} onClose={onClose} />);
    const overlay = screen.getByRole("dialog").parentElement!;
    await user.click(overlay);
    expect(onClose).toHaveBeenCalled();
  });

  it("calls onClose when the ESC key is pressed", async () => {
    const onClose = vi.fn();
    const user = userEvent.setup();
    render(<DeleteProjectModal {...DEFAULT_PROPS} onClose={onClose} />);
    await user.keyboard("{Escape}");
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("disables both buttons while the delete request is in-flight", async () => {
    let resolve!: () => void;
    mockDeleteProject.mockImplementationOnce(
      () => new Promise<void>((res) => { resolve = res; })
    );
    const user = userEvent.setup();
    render(<DeleteProjectModal {...DEFAULT_PROPS} />);
    const input = screen.getByRole("textbox");
    await user.type(input, "Plataforma de tutorías online");
    const deleteBtn = screen.getByRole("button", { name: /Eliminar/i });
    await user.click(deleteBtn);
    const cancelBtn = screen.getByRole("button", { name: /Cancelar/i });
    expect((deleteBtn as HTMLButtonElement).disabled).toBe(true);
    expect((cancelBtn as HTMLButtonElement).disabled).toBe(true);
    resolve();
  });
});
