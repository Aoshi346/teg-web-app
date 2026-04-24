import { describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { PasswordRevealModal } from "@features/settings/components/admin/directory/PasswordRevealModal";

describe("PasswordRevealModal", () => {
  it("displays the password", () => {
    render(<PasswordRevealModal isOpen={true} password="X7k9-mP2q-W8nR" onClose={vi.fn()} />);
    expect(screen.getByText("X7k9-mP2q-W8nR")).toBeInTheDocument();
  });

  it("calls onClose when Entendido is clicked", () => {
    const onClose = vi.fn();
    render(<PasswordRevealModal isOpen={true} password="X7k9-mP2q-W8nR" onClose={onClose} />);
    fireEvent.click(screen.getByRole("button", { name: /entendido/i }));
    expect(onClose).toHaveBeenCalled();
  });

  it("calls clipboard.writeText when Copiar is clicked", () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, { clipboard: { writeText } });
    render(<PasswordRevealModal isOpen={true} password="X7k9-mP2q-W8nR" onClose={vi.fn()} />);
    fireEvent.click(screen.getByRole("button", { name: /copiar/i }));
    expect(writeText).toHaveBeenCalledWith("X7k9-mP2q-W8nR");
  });

  it("does not render when isOpen=false", () => {
    render(<PasswordRevealModal isOpen={false} password="X7k9-mP2q-W8nR" onClose={vi.fn()} />);
    expect(screen.queryByText("X7k9-mP2q-W8nR")).not.toBeInTheDocument();
  });
});
