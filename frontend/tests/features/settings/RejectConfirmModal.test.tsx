import { describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { RejectConfirmModal } from "@features/settings/components/admin/pending/RejectConfirmModal";

describe("RejectConfirmModal", () => {
  it("shows the user's name in the title", () => {
    render(<RejectConfirmModal isOpen={true} userName="Carlos González" onConfirm={vi.fn()} onCancel={vi.fn()} />);
    expect(screen.getByText(/carlos gonzález/i)).toBeInTheDocument();
  });

  it("calls onConfirm when Rechazar is clicked (reason is UX-only, not passed)", () => {
    const onConfirm = vi.fn();
    render(<RejectConfirmModal isOpen={true} userName="Carlos González" onConfirm={onConfirm} onCancel={vi.fn()} />);
    fireEvent.change(screen.getByPlaceholderText(/motivo/i), { target: { value: "Datos incompletos" } });
    fireEvent.click(screen.getByRole("button", { name: /^rechazar$/i }));
    expect(onConfirm).toHaveBeenCalledWith();
  });

  it("calls onCancel when Cancelar is clicked", () => {
    const onCancel = vi.fn();
    render(<RejectConfirmModal isOpen={true} userName="Carlos González" onConfirm={vi.fn()} onCancel={onCancel} />);
    fireEvent.click(screen.getByRole("button", { name: /cancelar/i }));
    expect(onCancel).toHaveBeenCalled();
  });

  it("does not render when isOpen=false", () => {
    render(<RejectConfirmModal isOpen={false} userName="Carlos González" onConfirm={vi.fn()} onCancel={vi.fn()} />);
    expect(screen.queryByText(/carlos gonzález/i)).not.toBeInTheDocument();
  });
});
