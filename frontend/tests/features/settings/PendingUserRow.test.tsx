import { describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { PendingUserRow } from "@features/settings/components/admin/pending/PendingUserRow";

const base = {
  id: 1,
  fullName: "Carlos González",
  email: "carlos@example.com",
  role: "Estudiante" as const,
  nationality: "V" as const,
  cedula: "30243721",
  semester: "9no",
  phone: "+58 412 1234567",
  dateJoined: new Date(Date.now() - 2 * 24 * 3600 * 1000).toISOString(),
};

describe("PendingUserRow", () => {
  it("renders role, cedula, semester, and relative time", () => {
    render(<PendingUserRow user={base} onApprove={vi.fn()} onReject={vi.fn()} />);
    expect(screen.getByText(/estudiante/i)).toBeInTheDocument();
    expect(screen.getByText(/V-30243721/i)).toBeInTheDocument();
    expect(screen.getByText(/9no/i)).toBeInTheDocument();
    expect(screen.getByText(/hace 2 días/i)).toBeInTheDocument();
  });

  it("calls onApprove when Aprobar is clicked", () => {
    const onApprove = vi.fn();
    render(<PendingUserRow user={base} onApprove={onApprove} onReject={vi.fn()} />);
    fireEvent.click(screen.getByRole("button", { name: /aprobar/i }));
    expect(onApprove).toHaveBeenCalledWith(base);
  });

  it("calls onReject when Rechazar is clicked", () => {
    const onReject = vi.fn();
    render(<PendingUserRow user={base} onApprove={vi.fn()} onReject={onReject} />);
    fireEvent.click(screen.getByRole("button", { name: /rechazar/i }));
    expect(onReject).toHaveBeenCalledWith(base);
  });

  it("shows phone instead of semester for non-Estudiante", () => {
    const tutor = { ...base, role: "Tutor" as const, semester: undefined };
    render(<PendingUserRow user={tutor} onApprove={vi.fn()} onReject={vi.fn()} />);
    expect(screen.getByText(/\+58 412 1234567/i)).toBeInTheDocument();
    expect(screen.queryByText(/9no/i)).not.toBeInTheDocument();
  });
});
