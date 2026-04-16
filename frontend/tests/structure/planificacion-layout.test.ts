import { existsSync, readFileSync } from "node:fs";
import path from "node:path";
import { describe, it, expect } from "vitest";

const src = (...parts: string[]) =>
  path.resolve(__dirname, "../../src", ...parts);

describe("Planificacion module layout", () => {
  it("route files exist", () => {
    expect(existsSync(src("app/dashboard/planificacion/page.tsx")), "planificacion/page.tsx").toBe(true);
    expect(existsSync(src("app/dashboard/planificacion/loading.tsx")), "planificacion/loading.tsx").toBe(true);
  });

  it("scan route is removed", () => {
    expect(existsSync(src("app/dashboard/scan")), "scan/ directory should be gone").toBe(false);
  });

  it("feature files exist", () => {
    const files = [
      "features/planificacion/index.ts",
      "features/planificacion/api/planificacionService.ts",
      "features/planificacion/types/planificacion.ts",
      "features/planificacion/components/PlanificacionView.tsx",
      "features/planificacion/components/WeekCalendar.tsx",
      "features/planificacion/components/DayCard.tsx",
      "features/planificacion/components/PresentationCard.tsx",
      "features/planificacion/components/PresentationFormModal.tsx",
      "features/planificacion/components/EmptyDayState.tsx",
      "features/planificacion/hooks/usePlanificacion.ts",
      "features/planificacion/hooks/useDateSelection.ts",
    ];
    for (const f of files) {
      expect(existsSync(src(f)), f).toBe(true);
    }
  });

  it("sidebar contains planificacion href and not scan href", () => {
    const sidebarPath = src("widgets/sidebar/Sidebar.tsx");
    expect(existsSync(sidebarPath), "Sidebar.tsx must exist").toBe(true);
    const content = readFileSync(sidebarPath, "utf8");
    expect(content, "sidebar must link to /dashboard/planificacion").toContain("/dashboard/planificacion");
    expect(content, "sidebar must not link to /dashboard/scan").not.toContain("/dashboard/scan");
  });
});
