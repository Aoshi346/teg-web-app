import { describe, it, expect } from "vitest";
import { render } from "@testing-library/react";
import { StateTimeline } from "./StateTimeline";
import type { TimelineEvent } from "@features/projects/lib/buildStateTimeline";

describe("StateTimeline", () => {
  it("renders one row per event", () => {
    const events: TimelineEvent[] = [
      { id: "a", kind: "evaluation", label: "Rev 1 → Pass", variant: "green", timestamp: "2026-03-28T00:00:00Z", body: "Body A" },
      { id: "b", kind: "creation",   label: "Creado",      variant: "slate", timestamp: "2026-03-14T00:00:00Z", body: "Body B" },
    ];
    const { container } = render(<StateTimeline events={events} />);
    expect(container.querySelectorAll(".tline-item")).toHaveLength(2);
  });

  it("attaches the active class when active=true", () => {
    const events: TimelineEvent[] = [
      { id: "a", kind: "evaluation", label: "Now", variant: "blue", timestamp: "2026-04-14T00:00:00Z", body: "Live", active: true },
    ];
    const { container } = render(<StateTimeline events={events} />);
    expect(container.querySelector(".tline-dot.is-active")).not.toBeNull();
  });

  it("renders empty state when events is empty", () => {
    const { container } = render(<StateTimeline events={[]} />);
    expect(container.textContent).toContain("Sin actividad");
  });
});
