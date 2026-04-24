import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { DateCell } from "@shared/ui/DateCell";

describe("DateCell", () => {
  it("renders month abbreviation and day", () => {
    render(<DateCell date={new Date(2026, 3, 26)} />);
    expect(screen.getByText("26")).toBeInTheDocument();
    expect(screen.getByText(/Abr/i)).toBeInTheDocument();
  });

  it("accepts ISO string", () => {
    render(<DateCell date="2026-05-02T10:00:00" />);
    expect(screen.getByText("02")).toBeInTheDocument();
    expect(screen.getByText(/May/i)).toBeInTheDocument();
  });
});
