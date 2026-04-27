import { describe, it, expect } from "vitest";
import { buildStateTimeline, type ProjectEvaluation } from "./buildStateTimeline";
import type { Project } from "@features/projects/types/project";

function mkProject(overrides: Partial<Project> & { evaluations?: ProjectEvaluation[] } = {}): Project {
  return {
    id: 1,
    title: "T",
    student: "S",
    submittedDate: "2026-03-14T16:22:00Z",
    state: "pending_defense",
    period: "2026-01",
    type: "proyecto",
    ...overrides,
  } as Project;
}

describe("buildStateTimeline", () => {
  it("emits a 'creation' event for the submittedDate", () => {
    const events = buildStateTimeline(mkProject());
    expect(events.some((e) => e.kind === "creation")).toBe(true);
  });

  it("emits one 'evaluation' event per Evaluation, newest first", () => {
    const project = mkProject({
      evaluations: [
        { id: 1, kind: "review", pass_status: "Pass", score: 17.2, graded_at: "2026-03-28T11:02:00Z", reviewer_name: "L" },
        { id: 2, kind: "review", pass_status: "Pass", score: 18.0, graded_at: "2026-04-10T14:18:00Z", reviewer_name: "L" },
      ],
    });
    const events = buildStateTimeline(project);
    const evals = events.filter((e) => e.kind === "evaluation");
    expect(evals).toHaveLength(2);
    expect(evals[0].timestamp).toBe("2026-04-10T14:18:00Z");
    expect(evals[1].timestamp).toBe("2026-03-28T11:02:00Z");
  });

  it("emits one 'override' event per StateOverride", () => {
    const project = mkProject({
      stateOverrides: [
        { id: 1, fromState: "pending_review_2", toState: "pending_defense", reason: "skip", adminName: "M", createdAt: "2026-04-02T14:18:00Z" },
      ],
    });
    const events = buildStateTimeline(project);
    expect(events.some((e) => e.kind === "override")).toBe(true);
  });

  it("orders events newest first across all kinds", () => {
    const project = mkProject({
      evaluations: [
        { id: 1, kind: "review", pass_status: "Pass", score: 15, graded_at: "2026-03-20T00:00:00Z", reviewer_name: "L" },
      ],
      stateOverrides: [
        { id: 9, fromState: "pending_review_1", toState: "pending_review_2", reason: "x", adminName: "M", createdAt: "2026-03-25T00:00:00Z" },
      ],
    });
    const events = buildStateTimeline(project);
    const stamps = events.map((e) => e.timestamp);
    const sorted = [...stamps].sort().reverse();
    expect(stamps).toEqual(sorted);
  });

  it("flags the most recent event with active=true when project is in a non-terminal state", () => {
    const project = mkProject({
      state: "pending_defense",
      evaluations: [
        { id: 1, kind: "review", pass_status: "Pass", score: 18, graded_at: "2026-04-10T00:00:00Z", reviewer_name: "L" },
      ],
    });
    const events = buildStateTimeline(project);
    expect(events[0].active).toBe(true);
  });

  it("does not flag any event as active in terminal states", () => {
    const project = mkProject({
      state: "approved",
      evaluations: [
        { id: 1, kind: "defense", pass_status: "Pass", score: 18, graded_at: "2026-04-10T00:00:00Z", reviewer_name: "L" },
      ],
    });
    const events = buildStateTimeline(project);
    expect(events.every((e) => !e.active)).toBe(true);
  });
});
