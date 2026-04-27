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
      // Sub-I new components (replace legacy WeekCalendar, PresentationCard, EmptyDayState)
      "features/planificacion/components/UnifiedCalendar.tsx",
      "features/planificacion/components/DayCard.tsx",
      "features/planificacion/components/DayDetailModal.tsx",
      "features/planificacion/components/PresentationRow.tsx",
      "features/planificacion/components/PlanAdminView.tsx",
      "features/planificacion/components/PlanReviewerView.tsx",
      "features/planificacion/components/PlanStudentView.tsx",
      // PresentationFormModal is unchanged — deferred to Sub-J
      "features/planificacion/components/PresentationFormModal.tsx",
      "features/planificacion/hooks/usePlanificacion.ts",
      "features/planificacion/hooks/useDateSelection.ts",
    ];
    for (const f of files) {
      expect(existsSync(src(f)), f).toBe(true);
    }
  });

  it("legacy components removed in Sub-I", () => {
    const deleted = [
      "features/planificacion/components/WeekCalendar.tsx",
      "features/planificacion/components/PresentationCard.tsx",
      "features/planificacion/components/CompactDayCard.tsx",
      "features/planificacion/components/ScheduleOverviewCalendar.tsx",
      "features/planificacion/components/DateSelectionCalendar.tsx",
      "features/planificacion/components/EmptyDayState.tsx",
    ];
    for (const f of deleted) {
      expect(existsSync(src(f)), `${f} should be deleted`).toBe(false);
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
