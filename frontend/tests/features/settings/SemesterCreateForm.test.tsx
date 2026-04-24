import { describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { SemesterCreateForm } from "@features/settings/components/admin/semesters/SemesterCreateForm";

const existingSemesters = [
  { id: 1, period: "2025-01", start_month: 1, end_month: 6, is_active: false, label: "", project_count: 5, created_at: "2025-01-01" },
];

describe("SemesterCreateForm", () => {
  it("auto-fills Jan-Jun when period 01 is selected", () => {
    render(<SemesterCreateForm existing={existingSemesters} onCreate={vi.fn()} />);
    const period = screen.getByLabelText(/período/i) as HTMLSelectElement;
    fireEvent.change(period, { target: { value: "01" } });
    const startMonth = screen.getByLabelText(/mes inicial/i) as HTMLSelectElement;
    const endMonth = screen.getByLabelText(/mes final/i) as HTMLSelectElement;
    expect(startMonth.value).toBe("1");
    expect(endMonth.value).toBe("6");
  });

  it("auto-fills Sep-Jan when period 02 is selected", () => {
    render(<SemesterCreateForm existing={existingSemesters} onCreate={vi.fn()} />);
    fireEvent.change(screen.getByLabelText(/período/i), { target: { value: "02" } });
    const startMonth = screen.getByLabelText(/mes inicial/i) as HTMLSelectElement;
    const endMonth = screen.getByLabelText(/mes final/i) as HTMLSelectElement;
    expect(startMonth.value).toBe("9");
    expect(endMonth.value).toBe("1");
  });

  it("blocks create when period already exists", async () => {
    const onCreate = vi.fn();
    render(<SemesterCreateForm existing={existingSemesters} onCreate={onCreate} />);
    fireEvent.change(screen.getByLabelText(/año/i), { target: { value: "2025" } });
    fireEvent.change(screen.getByLabelText(/período/i), { target: { value: "01" } });
    fireEvent.click(screen.getByRole("button", { name: /crear/i }));
    await waitFor(() => {
      expect(screen.getByText(/ya existe un semestre/i)).toBeInTheDocument();
    });
    expect(onCreate).not.toHaveBeenCalled();
  });

  it("calls onCreate with valid payload", async () => {
    const onCreate = vi.fn().mockResolvedValue(undefined);
    render(<SemesterCreateForm existing={existingSemesters} onCreate={onCreate} />);
    fireEvent.change(screen.getByLabelText(/año/i), { target: { value: "2026" } });
    fireEvent.change(screen.getByLabelText(/período/i), { target: { value: "01" } });
    fireEvent.click(screen.getByRole("button", { name: /crear/i }));
    await waitFor(() => {
      expect(onCreate).toHaveBeenCalledWith({ period: "2026-01", start_month: 1, end_month: 6 });
    });
  });

  it("renders preview label including month range", () => {
    render(<SemesterCreateForm existing={existingSemesters} onCreate={vi.fn()} />);
    fireEvent.change(screen.getByLabelText(/año/i), { target: { value: "2026" } });
    fireEvent.change(screen.getByLabelText(/período/i), { target: { value: "02" } });
    expect(screen.getByText(/septiembre 2026 a enero 2027/i)).toBeInTheDocument();
  });
});
