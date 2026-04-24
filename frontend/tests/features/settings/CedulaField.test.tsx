import { describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { CedulaField } from "@features/settings/components/profile/CedulaField";

describe("CedulaField", () => {
  it("renders nationality dropdown and cedula input", () => {
    render(<CedulaField nationality="V" cedula="30243721" onChange={vi.fn()} />);
    expect(screen.getByLabelText(/nacionalidad/i)).toBeInTheDocument();
    expect(screen.getByDisplayValue("30243721")).toBeInTheDocument();
  });

  it("calls onChange with updated nationality", () => {
    const onChange = vi.fn();
    render(<CedulaField nationality="V" cedula="30243721" onChange={onChange} />);
    fireEvent.change(screen.getByLabelText(/nacionalidad/i), { target: { value: "E" } });
    expect(onChange).toHaveBeenCalledWith({ nationality: "E", cedula: "30243721" });
  });

  it("calls onChange with updated cedula", () => {
    const onChange = vi.fn();
    render(<CedulaField nationality="V" cedula="30243721" onChange={onChange} />);
    const input = screen.getByDisplayValue("30243721");
    fireEvent.change(input, { target: { value: "12345678" } });
    expect(onChange).toHaveBeenCalledWith({ nationality: "V", cedula: "12345678" });
  });

  it("shows error message when provided", () => {
    render(<CedulaField nationality="V" cedula="" onChange={vi.fn()} error="La cédula debe tener 6–9 dígitos" />);
    expect(screen.getByText(/6–9 dígitos/i)).toBeInTheDocument();
  });
});
