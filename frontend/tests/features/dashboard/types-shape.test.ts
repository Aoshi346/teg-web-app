import { describe, it, expectTypeOf } from "vitest";
import type { StatTileData, ChipSegment } from "@features/dashboard/lib/types";

describe("StatTileData shape", () => {
  it("supports hero tone with chips and urgent flag", () => {
    expectTypeOf<StatTileData>().toMatchTypeOf<{
      tone: "primary" | "accent" | "hero" | "blue" | "orange" | "green" | "amber";
    }>();
    const t: StatTileData = {
      tone: "hero",
      label: "X",
      value: "1",
      chips: [{ label: "a", count: 1, href: "/x" }],
      urgent: true,
    };
    expectTypeOf<typeof t.chips>().toEqualTypeOf<ChipSegment[] | undefined>();
  });
});
