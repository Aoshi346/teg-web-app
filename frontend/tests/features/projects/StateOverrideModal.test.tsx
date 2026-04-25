import { describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import StateOverrideModal from "@features/projects/components/StateOverrideModal";

const baseProps = {
  open: true,
  currentState: "pending_review_1" as const,
  projectType: "proyecto" as const,
  onClose: () => {},
  onSubmit: vi.fn(async () => {}),
};

describe("StateOverrideModal", () => {
  it("disables submit when no target state selected", () => {
    render(<StateOverrideModal {...baseProps} />);
    const submit = screen.getByRole("button", { name: /forzar/i });
    expect(submit).toBeDisabled();
  });

  it("disables submit when reason is <10 chars after trim", () => {
    render(<StateOverrideModal {...baseProps} />);
    fireEvent.change(screen.getByLabelText(/estado destino/i), {
      target: { value: "approved" },
    });
    fireEvent.change(screen.getByLabelText(/razón/i), {
      target: { value: "  short  " },
    });
    expect(screen.getByRole("button", { name: /forzar/i })).toBeDisabled();
  });

  it("calls onSubmit with trimmed reason when valid", async () => {
    const onSubmit = vi.fn(async () => {});
    render(<StateOverrideModal {...baseProps} onSubmit={onSubmit} />);
    fireEvent.change(screen.getByLabelText(/estado destino/i), {
      target: { value: "approved" },
    });
    fireEvent.change(screen.getByLabelText(/razón/i), {
      target: { value: "  dean office appeal #001  " },
    });
    fireEvent.click(screen.getByRole("button", { name: /forzar/i }));
    await new Promise((r) => setTimeout(r, 0));
    expect(onSubmit).toHaveBeenCalledWith({
      state: "approved",
      reason: "dean office appeal #001",
    });
  });

  it("does not include current state as an option", () => {
    render(<StateOverrideModal {...baseProps} />);
    const options = Array.from(
      screen.getByLabelText(/estado destino/i).querySelectorAll("option"),
    ).map((o) => o.getAttribute("value"));
    expect(options).not.toContain("pending_review_1");
  });
});
