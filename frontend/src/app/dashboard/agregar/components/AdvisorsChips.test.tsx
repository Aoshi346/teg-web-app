import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, act } from "@testing-library/react";
import { useForm, FormProvider, useWatch } from "react-hook-form";
import type { DocumentFormData } from "../schema";
import type { UserOption } from "../hooks/useDocumentData";

// Mocking strategy: the real Combobox is portal-based (createPortal to document.body) which
// makes unit testing unreliable — the dropdown renders outside the component tree and
// getBoundingClientRect() returns zeros in jsdom. We replace it with a controlled <select>
// that exposes the same onChange(number | "") contract. The "placeholder" prop is used as the
// aria-label for the select so tests can query it.
vi.mock("./Combobox", () => ({
  default: function MockCombobox({
    value,
    onChange,
    options,
    placeholder,
    disabled,
  }: {
    value: number | "" | null | undefined;
    onChange: (v: number | "") => void;
    options: Array<{ id: number; label: string }>;
    placeholder?: string;
    disabled?: boolean;
  }) {
    return (
      <select
        aria-label={placeholder ?? "combobox"}
        data-testid="advisors-combobox"
        value={value === "" || value == null ? "" : String(value)}
        disabled={disabled}
        onChange={(e) =>
          onChange(e.target.value === "" ? "" : Number(e.target.value))
        }
      >
        <option value="">—</option>
        {options.map((o) => (
          <option key={o.id} value={o.id}>
            {o.label}
          </option>
        ))}
      </select>
    );
  },
}));

// ---------------------------------------------------------------------------
// Test fixture data
// ---------------------------------------------------------------------------

const TUTORS: UserOption[] = [
  { id: 12, label: "Prof. Alpha", email: "alpha@test.com" },
  { id: 34, label: "Prof. Beta", email: "beta@test.com" },
  { id: 56, label: "Prof. Gamma", email: "gamma@test.com" },
];

// ---------------------------------------------------------------------------
// Helper: renderWithForm
//
// Wraps the given UI in a FormProvider using react-hook-form with the supplied
// defaultValues. An optional FormSpy renders the current advisors array as JSON
// into a <span data-testid="advisors-state"> so tests can read form state
// without triggering a submit.
// ---------------------------------------------------------------------------

type FormDefaults = Partial<Pick<DocumentFormData, "advisors">> &
  Partial<Omit<DocumentFormData, "advisors">>;

function renderWithForm(
  defaultValues: FormDefaults,
  ui: React.ReactElement,
) {
  const merged: DocumentFormData = {
    advisors: [],
    title: "",
    documentType: "proyecto",
    studentId: "",
    semesterPeriod: "",
    userRole: "",
    reviewer: null,
    files: [],
    ...defaultValues,
  };

  function Wrapper({ children }: { children: React.ReactNode }) {
    const methods = useForm<DocumentFormData>({ defaultValues: merged });
    return (
      <FormProvider {...methods}>
        {children}
        <FormSpy />
      </FormProvider>
    );
  }

  function FormSpy() {
    const advisors = useWatch<DocumentFormData, "advisors">({ name: "advisors" });
    return (
      <span data-testid="advisors-state">{JSON.stringify(advisors ?? [])}</span>
    );
  }

  return render(ui, { wrapper: Wrapper });
}

// ---------------------------------------------------------------------------
// The component under test
// ---------------------------------------------------------------------------

// Note: AdvisorsChips.tsx does not yet exist — all tests must fail at import.
import AdvisorsChips from "./AdvisorsChips";

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("AdvisorsChips — Sub-H", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // Test 1: Renders one chip per advisor already in form state.
  // Selector strategy: chips are queried by their label text via getAllByText
  // scoped to elements with the class ".a-chip" using container.querySelectorAll.
  it("renders one chip per advisor in form state", () => {
    const { container } = renderWithForm(
      { advisors: [12, 34] },
      <AdvisorsChips tutors={TUTORS} />,
    );
    const chips = container.querySelectorAll(".a-chip");
    expect(chips).toHaveLength(2);
    expect(screen.getByText("Prof. Alpha")).toBeTruthy();
    expect(screen.getByText("Prof. Beta")).toBeTruthy();
  });

  // Test 2: Adding a tutor via combobox + "Añadir" appends to advisors.
  // We select the option in the mock <select>, then click the "Añadir" button.
  // Form state is read from the <span data-testid="advisors-state">.
  it("appends a new advisor when a tutor is selected and Añadir is clicked", async () => {
    renderWithForm(
      { advisors: [12] },
      <AdvisorsChips tutors={TUTORS} />,
    );

    const combobox = screen.getByTestId("advisors-combobox");
    await act(async () => {
      fireEvent.change(combobox, { target: { value: "34" } });
    });

    const addButton = screen.getByRole("button", { name: /añadir/i });
    await act(async () => {
      fireEvent.click(addButton);
    });

    const stateEl = screen.getByTestId("advisors-state");
    const advisors = JSON.parse(stateEl.textContent ?? "[]");
    expect(advisors).toContain(12);
    expect(advisors).toContain(34);
    expect(advisors.filter((a: number | "") => a !== "")).toHaveLength(2);
  });

  // Test 3: Clicking the × button on a chip removes that advisor.
  it("removes an advisor when its × button is clicked", async () => {
    renderWithForm(
      { advisors: [12, 34] },
      <AdvisorsChips tutors={TUTORS} />,
    );

    // The × button must have an accessible name or be a child of the chip for
    // "Prof. Alpha". We use getByRole scoped to the chip; if that's not possible,
    // we fall back to querying all × buttons and clicking the first one.
    // The implementer should give each × button aria-label="Eliminar tutor" or similar,
    // or use title="Eliminar". We use getAllByRole("button") and filter by the chip
    // text proximity — here we simply grab all remove buttons in order.
    const removeButtons = screen
      .getAllByRole("button")
      .filter(
        (b) =>
          b.getAttribute("aria-label")?.includes("Eliminar") ||
          b.textContent?.trim() === "×" ||
          b.getAttribute("title")?.includes("Eliminar"),
      );

    // The first remove button belongs to Prof. Alpha (id=12).
    await act(async () => {
      fireEvent.click(removeButtons[0]);
    });

    const stateEl = screen.getByTestId("advisors-state");
    const advisors = JSON.parse(stateEl.textContent ?? "[]");
    const cleaned = advisors.filter((a: number | "") => a !== "");
    expect(cleaned).not.toContain(12);
    expect(cleaned).toContain(34);
  });

  // Test 4: Dedup — adding an already-present advisor is a no-op.
  // The Añadir handler must silently ignore duplicates; form state stays [12].
  it("does not add a duplicate advisor (dedup is silent)", async () => {
    renderWithForm(
      { advisors: [12] },
      <AdvisorsChips tutors={TUTORS} />,
    );

    const combobox = screen.getByTestId("advisors-combobox");
    await act(async () => {
      fireEvent.change(combobox, { target: { value: "12" } });
    });

    const addButton = screen.getByRole("button", { name: /añadir/i });
    await act(async () => {
      fireEvent.click(addButton);
    });

    const stateEl = screen.getByTestId("advisors-state");
    const advisors = JSON.parse(stateEl.textContent ?? "[]");
    const cleaned = advisors.filter((a: number | "") => a !== "");
    expect(cleaned).toEqual([12]);
  });

  // Test 5: 2-tutor cap — "+ Añadir" button is disabled when 2 advisors are present.
  // Decision: assert toBeDisabled() on the button (not hidden). The implementer should
  // render the button with the `disabled` attribute when advisors.length >= 2. This is
  // simpler than hiding and keeps the affordance visible to screen readers.
  it("disables the Añadir button when 2 tutors are already added", () => {
    renderWithForm(
      { advisors: [12, 34] },
      <AdvisorsChips tutors={TUTORS} />,
    );

    const addButton = screen.getByRole("button", { name: /añadir/i });
    expect(addButton).toBeDisabled();
  });

  // Test 6: No empty "" entries — starting from advisors: [] renders no chips
  // and the form state does not contain "".
  it("renders no chips and no empty entries when advisors is []", () => {
    const { container } = renderWithForm(
      { advisors: [] },
      <AdvisorsChips tutors={TUTORS} />,
    );

    const chips = container.querySelectorAll(".a-chip");
    expect(chips).toHaveLength(0);

    const stateEl = screen.getByTestId("advisors-state");
    const advisors = JSON.parse(stateEl.textContent ?? "[]");
    expect(advisors.filter((a: number | "") => a === "")).toHaveLength(0);
  });
});
