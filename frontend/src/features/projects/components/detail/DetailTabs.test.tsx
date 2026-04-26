import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { DetailTabs, type DetailTabKey } from "./DetailTabs";

describe("DetailTabs", () => {
  it("renders all 5 tab labels", () => {
    render(
      <DetailTabs
        active="informacion"
        counts={{ evaluaciones: 2, comentarios: 5, archivos: 2 }}
        onChange={() => {}}
      />,
    );
    expect(screen.getByText("Información")).toBeTruthy();
    expect(screen.getByText("Evaluaciones")).toBeTruthy();
    expect(screen.getByText("Comentarios")).toBeTruthy();
    expect(screen.getByText("Archivos")).toBeTruthy();
    expect(screen.getByText("Historial")).toBeTruthy();
  });

  it("marks the active tab with data-active=true", () => {
    const { container } = render(
      <DetailTabs active="evaluaciones" counts={{}} onChange={() => {}} />,
    );
    const evals = container.querySelector("[data-tab='evaluaciones']") as HTMLElement;
    expect(evals.getAttribute("data-active")).toBe("true");
  });

  it("calls onChange with the new key when a tab is clicked", () => {
    let received: DetailTabKey | null = null;
    render(
      <DetailTabs active="informacion" counts={{}} onChange={(k) => (received = k)} />,
    );
    fireEvent.click(screen.getByText("Comentarios"));
    expect(received).toBe("comentarios");
  });

  it("renders count badges next to labels when counts are provided", () => {
    render(
      <DetailTabs active="informacion" counts={{ evaluaciones: 2, comentarios: 5 }} onChange={() => {}} />,
    );
    const evals = screen.getByText("Evaluaciones").parentElement!;
    expect(evals.textContent).toContain("2");
  });
});
