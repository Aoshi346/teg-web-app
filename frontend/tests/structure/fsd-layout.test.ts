import { existsSync } from "node:fs";
import path from "node:path";
import { describe, it, expect } from "vitest";

const src = (...parts: string[]) =>
  path.resolve(__dirname, "../../src", ...parts);

describe("FSD layout", () => {
  it("new target paths exist after reshuffle", () => {
    // shared/api
    expect(existsSync(src("shared/api/api.ts")), "shared/api/api.ts").toBe(true);
    expect(existsSync(src("shared/api/normalizeError.ts")), "shared/api/normalizeError.ts").toBe(true);

    // shared/lib
    expect(existsSync(src("shared/lib/utils.ts")), "shared/lib/utils.ts").toBe(true);

    // shared/ui
    expect(existsSync(src("shared/ui/button.tsx")), "shared/ui/button.tsx").toBe(true);
    expect(existsSync(src("shared/ui/card.tsx")), "shared/ui/card.tsx").toBe(true);

    // features/auth
    expect(existsSync(src("features/auth/api/clientAuth.ts")), "features/auth/api/clientAuth.ts").toBe(true);
    expect(existsSync(src("features/auth/api/credentials.ts")), "features/auth/api/credentials.ts").toBe(true);
    expect(existsSync(src("features/auth/components/LoginModal.tsx")), "features/auth/components/LoginModal.tsx").toBe(true);

    // features/projects
    expect(existsSync(src("features/projects/api/projectService.ts")), "features/projects/api/projectService.ts").toBe(true);
    expect(existsSync(src("features/projects/components/ProjectCard.tsx")), "features/projects/components/ProjectCard.tsx").toBe(true);
    expect(existsSync(src("features/projects/types/project.ts")), "features/projects/types/project.ts").toBe(true);

    // features/evaluations
    expect(existsSync(src("features/evaluations/components/EvaluationForm.tsx")), "features/evaluations/components/EvaluationForm.tsx").toBe(true);
    expect(existsSync(src("features/evaluations/lib/questions/questions.ts")), "features/evaluations/lib/questions/questions.ts").toBe(true);

    // features/semesters
    expect(existsSync(src("features/semesters/api/semesters.ts")), "features/semesters/api/semesters.ts").toBe(true);

    // features/dashboard
    expect(existsSync(src("features/dashboard/components/Dashboard.tsx")), "features/dashboard/components/Dashboard.tsx").toBe(true);

    // features/landing
    expect(existsSync(src("features/landing/components/Hero.tsx")), "features/landing/components/Hero.tsx").toBe(true);

    // widgets
    expect(existsSync(src("widgets/sidebar/Sidebar.tsx")), "widgets/sidebar/Sidebar.tsx").toBe(true);
    expect(existsSync(src("widgets/header/DashboardHeader.tsx")), "widgets/header/DashboardHeader.tsx").toBe(true);
  });

  it("old paths no longer exist after reshuffle", () => {
    expect(existsSync(src("lib/api.ts")), "src/lib/api.ts should be gone").toBe(false);
    expect(existsSync(src("components/layout/Sidebar.tsx")), "src/components/layout/Sidebar.tsx should be gone").toBe(false);
    expect(existsSync(src("types/project.ts")), "src/types/project.ts should be gone").toBe(false);
    expect(existsSync(src("lib/utils.ts")), "src/lib/utils.ts should be gone").toBe(false);
    expect(existsSync(src("components/dashboard/ProjectCard.tsx")), "src/components/dashboard/ProjectCard.tsx should be gone").toBe(false);
    expect(existsSync(src("lib/semesters.ts")), "src/lib/semesters.ts should be gone").toBe(false);
  });
});
