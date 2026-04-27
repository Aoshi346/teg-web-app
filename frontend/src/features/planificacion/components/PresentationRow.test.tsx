import { describe, it, expect, vi } from "vitest";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import PresentationRow from "./PresentationRow";
import type { Presentation } from "../types/planificacion";

const BASE: Presentation = {
  id: 1,
  day: 10,
  project: 42,
  project_title: "Análisis predictivo del rendimiento académico",
  project_type: "tesis",
  student_name: "Diego Torres",
  student_email: "diego@example.com",
  tutor: 5,
  tutor_name: "P. Linares",
  jurado: [9, 10, 11],
  jurado_names: ["R. Linares", "A. Pérez", "M. Núñez"],
  start_time: "14:00",
  duration_minutes: 60,
  order: 1,
};

describe("PresentationRow", () => {
  // 1 — Time block
  it("shows start time and duration inside .ptime", () => {
    render(<PresentationRow presentation={BASE} role="admin" />);
    const ptime = document.querySelector(".ptime");
    expect(ptime).not.toBeNull();
    expect(ptime!.textContent).toContain("14:00");
    expect(ptime!.textContent).toContain("60 min");
  });

  // 2a — Title block with TEG modality dot + spill
  it("renders .ptitle with project title, .tdot.teg, and .spill.teg chip for tesis", () => {
    render(<PresentationRow presentation={BASE} role="admin" />);
    const ptitle = document.querySelector(".ptitle");
    expect(ptitle).not.toBeNull();
    expect(ptitle!.textContent).toContain("Análisis predictivo del rendimiento académico");
    expect(ptitle!.querySelector(".tdot.teg")).not.toBeNull();
    const spillTeg = ptitle!.querySelector(".spill.teg");
    expect(spillTeg).not.toBeNull();
    expect(spillTeg!.textContent).toMatch(/^TEG$/i);
  });

  // 2b — Title block with PTEG modality dot + spill
  it("renders .tdot.pteg and .spill.pteg chip for proyecto type", () => {
    const ptegPresentation: Presentation = { ...BASE, project_type: "proyecto" };
    render(<PresentationRow presentation={ptegPresentation} role="admin" />);
    const ptitle = document.querySelector(".ptitle");
    expect(ptitle).not.toBeNull();
    expect(ptitle!.querySelector(".tdot.pteg")).not.toBeNull();
    const spillPteg = ptitle!.querySelector(".spill.pteg");
    expect(spillPteg).not.toBeNull();
    expect(spillPteg!.textContent).toMatch(/^PTEG$/i);
  });

  // 3a — Person meta line: admin sees student + tutor + "Jur. N"
  it("shows student name, tutor name, and Jur. 3 count in .pmeta for admin role", () => {
    render(<PresentationRow presentation={BASE} role="admin" />);
    const pmeta = document.querySelector(".pmeta");
    expect(pmeta).not.toBeNull();
    expect(pmeta!.textContent).toContain("Diego Torres");
    expect(pmeta!.textContent).toContain("P. Linares");
    expect(pmeta!.textContent).toContain("Jur. 3");
  });

  // 3b — Non-admin reviewer sees jurado names joined
  it("shows jurado names listed in .pmeta for tutor role", () => {
    render(<PresentationRow presentation={BASE} role="tutor" viewerId={5} />);
    const pmeta = document.querySelector(".pmeta");
    expect(pmeta).not.toBeNull();
    expect(pmeta!.textContent).toContain("R. Linares");
    expect(pmeta!.textContent).toContain("A. Pérez");
    expect(pmeta!.textContent).toContain("M. Núñez");
  });

  // 4a — Admin actions: edit and delete buttons present
  it("renders Editar and Eliminar icon buttons for admin role", () => {
    const onEdit = vi.fn();
    const onDelete = vi.fn();
    render(
      <PresentationRow
        presentation={BASE}
        role="admin"
        onEdit={onEdit}
        onDelete={onDelete}
      />
    );
    expect(screen.getByRole("button", { name: /editar/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /eliminar/i })).toBeInTheDocument();
  });

  // 4b — Clicking Editar calls onEdit with the presentation
  it("calls onEdit with presentation when Editar is clicked", async () => {
    const user = userEvent.setup();
    const onEdit = vi.fn();
    const onDelete = vi.fn();
    const onClick = vi.fn();
    render(
      <PresentationRow
        presentation={BASE}
        role="admin"
        onClick={onClick}
        onEdit={onEdit}
        onDelete={onDelete}
      />
    );
    await user.click(screen.getByRole("button", { name: /editar/i }));
    expect(onEdit).toHaveBeenCalledWith(BASE);
    expect(onClick).not.toHaveBeenCalled();
  });

  // 4c — Clicking Eliminar calls onDelete with the presentation and does not bubble onClick
  it("calls onDelete with presentation when Eliminar is clicked and does not bubble", async () => {
    const user = userEvent.setup();
    const onEdit = vi.fn();
    const onDelete = vi.fn();
    const onClick = vi.fn();
    render(
      <PresentationRow
        presentation={BASE}
        role="admin"
        onClick={onClick}
        onEdit={onEdit}
        onDelete={onDelete}
      />
    );
    await user.click(screen.getByRole("button", { name: /eliminar/i }));
    expect(onDelete).toHaveBeenCalledWith(BASE);
    expect(onClick).not.toHaveBeenCalled();
  });

  // 5 — Tutor row variant: mine class, spill.you Tutoreas chip, arrow button, no edit/delete
  it("renders mine class, Tutoreas chip, and Ver detalle arrow for tutor viewer", () => {
    render(
      <PresentationRow presentation={BASE} role="tutor" viewerId={5} />
    );
    const row = document.querySelector(".mine");
    expect(row).not.toBeNull();
    const spillYou = document.querySelector(".spill.you");
    expect(spillYou).not.toBeNull();
    expect(spillYou!.textContent).toMatch(/tutoreas/i);
    expect(screen.getByRole("button", { name: /ver detalle/i })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /editar/i })).toBeNull();
    expect(screen.queryByRole("button", { name: /eliminar/i })).toBeNull();
  });

  // 6 — Jurado row variant: mine class, spill.you Jurado chip, arrow button, no edit/delete
  it("renders mine class, Jurado chip, and Ver detalle arrow for jurado viewer", () => {
    render(
      <PresentationRow presentation={BASE} role="jurado" viewerId={9} />
    );
    const row = document.querySelector(".mine");
    expect(row).not.toBeNull();
    const spillYou = document.querySelector(".spill.you");
    expect(spillYou).not.toBeNull();
    expect(spillYou!.textContent).toMatch(/^jurado$/i);
    expect(screen.getByRole("button", { name: /ver detalle/i })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /editar/i })).toBeNull();
    expect(screen.queryByRole("button", { name: /eliminar/i })).toBeNull();
  });

  // 7 — Estudiante row variant: mine class, Tu defensa chip, no buttons at all
  it("renders mine class and Tu defensa chip for estudiante role; no action buttons", () => {
    render(
      <PresentationRow presentation={BASE} role="estudiante" />
    );
    const row = document.querySelector(".mine");
    expect(row).not.toBeNull();
    const spillYou = document.querySelector(".spill.you");
    expect(spillYou).not.toBeNull();
    expect(spillYou!.textContent).toMatch(/tu defensa/i);
    expect(screen.queryByRole("button", { name: /editar/i })).toBeNull();
    expect(screen.queryByRole("button", { name: /eliminar/i })).toBeNull();
    expect(screen.queryByRole("button", { name: /ver detalle/i })).toBeNull();
  });

  // 8 — Clicking the row (outside buttons) fires onClick
  it("calls onClick with presentation when the row is clicked outside buttons", async () => {
    const user = userEvent.setup();
    const onClick = vi.fn();
    render(
      <PresentationRow presentation={BASE} role="admin" onClick={onClick} />
    );
    const row = document.querySelector(".ptime")!.closest("[class]") as HTMLElement;
    await user.click(row);
    expect(onClick).toHaveBeenCalledWith(BASE);
  });

  // 9 — Admin with no onEdit/onDelete: buttons are absent
  it("does not render Editar or Eliminar buttons when callbacks are not provided for admin", () => {
    render(<PresentationRow presentation={BASE} role="admin" />);
    expect(screen.queryByRole("button", { name: /editar/i })).toBeNull();
    expect(screen.queryByRole("button", { name: /eliminar/i })).toBeNull();
  });
});
