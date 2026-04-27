import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import Combobox from "./Combobox";

const OPTIONS = [
  { id: 1, label: "Option A" },
  { id: 2, label: "Option B" },
];

describe("Combobox — outer wrapper sizing", () => {
  it("wrapper element has flex-1 and min-w-0 classes so it grows inside a flex container", () => {
    const { container } = render(
      <div style={{ display: "flex", gap: 8 }}>
        <Combobox options={OPTIONS} value="" onChange={() => {}} />
        <button style={{ width: 80, flexShrink: 0 }}>+ Añadir</button>
      </div>,
    );

    // The Combobox outermost rendered element is the direct child of the flex wrapper.
    const wrapper = container.firstChild?.firstChild as HTMLElement | null;
    expect(wrapper).not.toBeNull();
    const cls = wrapper?.className ?? "";
    expect(cls).toContain("flex-1");
    expect(cls).toContain("min-w-0");
  });
});

describe("Sub-H token styling", () => {
  it("trigger uses agg-cb-trigger class and not legacy indigo/gray border classes", () => {
    render(
      <Combobox options={[{ id: 1, label: "Foo" }]} value="" onChange={() => {}} />,
    );
    const trigger = screen.getByRole("button");
    expect(trigger.className).toContain("agg-cb-trigger");
    expect(trigger.className).not.toContain("border-indigo-400");
    expect(trigger.className).not.toContain("border-gray-200");
  });

  it("open state adds is-open modifier to trigger", () => {
    render(
      <Combobox options={[{ id: 1, label: "Foo" }]} value="" onChange={() => {}} />,
    );
    const trigger = screen.getByRole("button");
    fireEvent.click(trigger);
    expect(trigger.className).toContain("is-open");
  });

  it("error state adds is-error modifier and does not use border-red-300", () => {
    render(
      <Combobox options={[{ id: 1, label: "Foo" }]} value="" onChange={() => {}} error={true} />,
    );
    const trigger = screen.getByRole("button");
    expect(trigger.className).toContain("is-error");
    expect(trigger.className).not.toContain("border-red-300");
  });

  it("selected option uses agg-cb-opt and is-selected classes without indigo highlight", () => {
    render(
      <Combobox options={[{ id: 1, label: "Foo" }]} value={1} onChange={() => {}} />,
    );
    const trigger = screen.getByRole("button");
    fireEvent.click(trigger);
    // The trigger itself also shows the selected label, so use getAllByRole and
    // pick the option button from the portaled list (it is not the trigger).
    const allButtons = screen.getAllByRole("button");
    // The option button is the one whose text content is "Foo" and is NOT the trigger.
    const optionButton = allButtons.find(
      (btn) => btn !== trigger && btn.textContent?.trim() === "Foo",
    ) as HTMLElement | undefined;
    expect(optionButton).toBeDefined();
    expect(optionButton!.className).toContain("agg-cb-opt");
    expect(optionButton!.className).toContain("is-selected");
    expect(optionButton!.className).not.toContain("bg-indigo-50");
    expect(optionButton!.className).not.toContain("text-indigo-700");
  });

  it("popover root uses agg-cb-pop class", () => {
    render(
      <Combobox options={[{ id: 1, label: "Foo" }]} value="" onChange={() => {}} />,
    );
    const trigger = screen.getByRole("button");
    fireEvent.click(trigger);
    const popover = document.querySelector(".agg-cb-pop");
    expect(popover).not.toBeNull();
  });
});
