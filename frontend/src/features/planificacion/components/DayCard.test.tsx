import { describe, it, expect, vi } from "vitest";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import DayCard from "./DayCard";
import type { PresentationDay, Presentation } from "../types/planificacion";
import { formatWeekday, formatMonthYear } from "../lib/formatDate";

function makePresentation(
  id: number,
  start_time: string,
  student_name: string
): Presentation {
  return {
    id,
    day: 20,
    project: id + 100,
    project_title: `Project ${id}`,
    project_type: "tesis",
    student_name,
    student_email: `student${id}@example.com`,
    tutor: null,
    tutor_name: null,
    jurado: [],
    jurado_names: [],
    start_time,
    duration_minutes: 60,
    order: id,
  };
}

const DAY_WITH_PRESENTATIONS: PresentationDay = {
  id: 20,
  date: "2026-03-12",
  notes: "",
  presentations: [
    makePresentation(1, "14:00", "Diego Torres"),
    makePresentation(2, "15:30", "N. Gutiérrez"),
    makePresentation(3, "17:00", "F. Roa"),
  ],
};

const DAY_EMPTY: PresentationDay = {
  id: 21,
  date: "2026-03-12",
  notes: "",
  presentations: [],
};

describe("DayCard", () => {
  // 1 — Fraunces day numeral
  it("renders day number 12 inside .daycard-numblk .n", () => {
    render(<DayCard day={DAY_WITH_PRESENTATIONS} />);
    const numblk = document.querySelector(".daycard-numblk");
    expect(numblk).not.toBeNull();
    const n = numblk!.querySelector(".n");
    expect(n).not.toBeNull();
    expect(n!.textContent).toBe("12");
  });

  // 2 — Weekday and month/year labels
  it("renders weekday in .dow and month+year in .my", () => {
    render(<DayCard day={DAY_WITH_PRESENTATIONS} />);
    const numblk = document.querySelector(".daycard-numblk");
    expect(numblk).not.toBeNull();
    const dow = numblk!.querySelector(".dow");
    expect(dow).not.toBeNull();
    const expectedWeekday = formatWeekday("2026-03-12");
    expect(dow!.textContent!.toLowerCase()).toContain(expectedWeekday.toLowerCase());
    const my = numblk!.querySelector(".my");
    expect(my).not.toBeNull();
    const expectedMonthYear = formatMonthYear("2026-03-12");
    expect(my!.textContent!.toLowerCase()).toContain(expectedMonthYear.toLowerCase());
  });

  // 3a — Count chip shows "3 pres" for 3 presentations
  it("renders 3 pres in .daycard-cnt for three presentations", () => {
    render(<DayCard day={DAY_WITH_PRESENTATIONS} />);
    const cnt = document.querySelector(".daycard-cnt");
    expect(cnt).not.toBeNull();
    expect(cnt!.textContent).toContain("3 pres");
  });

  // 3b — Count chip uses singular form for 1 presentation
  it("renders 1 pres in .daycard-cnt for a single presentation", () => {
    const singleDay: PresentationDay = {
      ...DAY_WITH_PRESENTATIONS,
      presentations: [makePresentation(1, "14:00", "Diego Torres")],
    };
    render(<DayCard day={singleDay} />);
    const cnt = document.querySelector(".daycard-cnt");
    expect(cnt).not.toBeNull();
    expect(cnt!.textContent).toContain("1 pres");
  });

  // 4 — List items: time and student last name
  it("renders three .daycard-item elements each with a time in .t and student last name", () => {
    render(<DayCard day={DAY_WITH_PRESENTATIONS} />);
    const items = document.querySelectorAll(".daycard-item");
    expect(items).toHaveLength(3);

    const [item1, item2, item3] = Array.from(items);

    const t1 = item1.querySelector(".t");
    expect(t1).not.toBeNull();
    expect(t1!.textContent).toContain("14:00");
    expect(item1.textContent).toContain("Torres");

    const t2 = item2.querySelector(".t");
    expect(t2).not.toBeNull();
    expect(t2!.textContent).toContain("15:30");
    expect(item2.textContent).toContain("Gutiérrez");

    const t3 = item3.querySelector(".t");
    expect(t3).not.toBeNull();
    expect(t3!.textContent).toContain("17:00");
    expect(item3.textContent).toContain("Roa");
  });

  // 5a — Empty state: 0 pres count
  it("renders 0 pres in .daycard-cnt for empty presentations", () => {
    render(<DayCard day={DAY_EMPTY} />);
    const cnt = document.querySelector(".daycard-cnt");
    expect(cnt).not.toBeNull();
    expect(cnt!.textContent).toContain("0 pres");
  });

  // 5b — Empty state: .empty element with sin presentaciones text
  it("renders .empty element with sin presentaciones text when no presentations", () => {
    render(<DayCard day={DAY_EMPTY} />);
    const empty = document.querySelector(".empty");
    expect(empty).not.toBeNull();
    expect(empty!.textContent).toMatch(/sin presentaciones/i);
  });

  // 6 — Click on card calls onClick with the day
  it("calls onClick with the day object when the card is clicked", async () => {
    const user = userEvent.setup();
    const onClick = vi.fn();
    render(<DayCard day={DAY_WITH_PRESENTATIONS} onClick={onClick} />);
    const card = document.querySelector(".daycard") as HTMLElement;
    expect(card).not.toBeNull();
    await user.click(card);
    expect(onClick).toHaveBeenCalledWith(DAY_WITH_PRESENTATIONS);
  });

  // 7 — Root element has class daycard
  it("root element has class daycard", () => {
    render(<DayCard day={DAY_WITH_PRESENTATIONS} />);
    const card = document.querySelector(".daycard");
    expect(card).not.toBeNull();
  });

  // 8 — Delete button absent when onDelete not provided
  it("does not render a delete button when onDelete is not provided", () => {
    render(<DayCard day={DAY_WITH_PRESENTATIONS} />);
    expect(screen.queryByRole("button", { name: /eliminar día/i })).toBeNull();
  });

  // 9 — Delete button present when onDelete provided
  it("renders delete button with aria-label 'Eliminar día' when onDelete is provided", () => {
    const onDelete = vi.fn();
    render(<DayCard day={DAY_WITH_PRESENTATIONS} onDelete={onDelete} />);
    expect(screen.getByRole("button", { name: /eliminar día/i })).not.toBeNull();
  });

  // 10 — Clicking delete calls onDelete and does NOT call onClick
  it("clicking the delete button calls onDelete(day) and does not propagate to onClick", async () => {
    const user = userEvent.setup();
    const onClick = vi.fn();
    const onDelete = vi.fn();
    render(<DayCard day={DAY_WITH_PRESENTATIONS} onClick={onClick} onDelete={onDelete} />);
    const delBtn = screen.getByRole("button", { name: /eliminar día/i });
    await user.click(delBtn);
    expect(onDelete).toHaveBeenCalledWith(DAY_WITH_PRESENTATIONS);
    expect(onClick).not.toHaveBeenCalled();
  });

  // 11 — selectable mode: checkbox unchecked when selected=false
  it("shows unchecked .daycard-check when selectable=true and selected=false", () => {
    render(<DayCard day={DAY_WITH_PRESENTATIONS} selectable={true} selected={false} />);
    const check = document.querySelector(".daycard-check");
    expect(check).not.toBeNull();
    expect(check!.classList.contains("checked")).toBe(false);
  });

  // 12 — selectable mode: checkbox checked when selected=true
  it("shows checked .daycard-check when selectable=true and selected=true", () => {
    render(<DayCard day={DAY_WITH_PRESENTATIONS} selectable={true} selected={true} />);
    const check = document.querySelector(".daycard-check");
    expect(check).not.toBeNull();
    expect(check!.classList.contains("checked")).toBe(true);
  });

  // 13 — selectable mode: clicking card calls onSelect(day, true) when not yet selected
  it("calls onSelect(day, true) when card is clicked in selectable mode with selected=false", async () => {
    const user = userEvent.setup();
    const onClick = vi.fn();
    const onSelect = vi.fn();
    render(
      <DayCard
        day={DAY_WITH_PRESENTATIONS}
        selectable={true}
        selected={false}
        onClick={onClick}
        onSelect={onSelect}
      />
    );
    const card = document.querySelector(".daycard") as HTMLElement;
    await user.click(card);
    expect(onSelect).toHaveBeenCalledWith(DAY_WITH_PRESENTATIONS, true);
    expect(onClick).not.toHaveBeenCalled();
  });

  // 14 — selectable mode: clicking card calls onSelect(day, false) when already selected
  it("calls onSelect(day, false) when card is clicked in selectable mode with selected=true", async () => {
    const user = userEvent.setup();
    const onSelect = vi.fn();
    render(
      <DayCard
        day={DAY_WITH_PRESENTATIONS}
        selectable={true}
        selected={true}
        onSelect={onSelect}
      />
    );
    const card = document.querySelector(".daycard") as HTMLElement;
    await user.click(card);
    expect(onSelect).toHaveBeenCalledWith(DAY_WITH_PRESENTATIONS, false);
  });

  // 15 — selectable mode: delete button is hidden
  it("hides the delete button when selectable=true even if onDelete is provided", () => {
    render(
      <DayCard
        day={DAY_WITH_PRESENTATIONS}
        selectable={true}
        onDelete={vi.fn()}
      />
    );
    expect(screen.queryByRole("button", { name: /eliminar día/i })).toBeNull();
  });

  // 16 — selectable mode: card root has selected class when selected=true
  it("root element has selected class when selectable=true and selected=true", () => {
    render(<DayCard day={DAY_WITH_PRESENTATIONS} selectable={true} selected={true} />);
    const card = document.querySelector(".daycard");
    expect(card).not.toBeNull();
    expect(card!.classList.contains("selected")).toBe(true);
  });
});
