import { describe, it, expect } from "vitest";
import {
  applyStateFilter,
  readStateFromSearchParams,
} from "@features/projects/lib/applyStateFilter";
import type { Project, ProjectState } from "@features/projects/types/project";

const proj = (id: number, state: ProjectState, type: Project["type"] = "proyecto"): Project => ({
  id,
  title: `P${id}`,
  student: "S",
  submittedDate: "2026-01-01",
  state,
  period: "2026-01",
  type,
});

describe("readStateFromSearchParams", () => {
  it("returns a valid ProjectState when set", () => {
    const sp = new URLSearchParams("state=pending_defense");
    expect(readStateFromSearchParams(sp)).toBe("pending_defense");
  });

  it("returns null when missing", () => {
    expect(readStateFromSearchParams(new URLSearchParams(""))).toBeNull();
  });

  it("returns null for unknown values", () => {
    const sp = new URLSearchParams("state=gibberish");
    expect(readStateFromSearchParams(sp)).toBeNull();
  });
});

describe("applyStateFilter", () => {
  const projects = [
    proj(1, "pending_review_1"),
    proj(2, "pending_defense"),
    proj(3, "pending_defense"),
    proj(4, "approved", "tesis"),
  ];

  it("returns the original list when no filter", () => {
    expect(applyStateFilter(projects, null)).toEqual(projects);
  });

  it("filters PTEG projects by state", () => {
    const filtered = applyStateFilter(projects, "pending_defense");
    expect(filtered.map((p) => p.id)).toEqual([2, 3]);
  });

  it("excludes tesis projects even if state matches", () => {
    const filtered = applyStateFilter(projects, "approved");
    expect(filtered).toEqual([]);
  });
});
