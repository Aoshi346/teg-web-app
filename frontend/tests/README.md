# Frontend Tests — TesisFar

## Running

```bash
cd frontend
npx vitest                                # watch mode
npx vitest run                            # single run
npx vitest run src/features/auth          # one directory
npx vitest run path/to/file.test.tsx      # one file
npx vitest run --reporter=verbose         # verbose
```

Add these scripts to `package.json` if you want shortcuts:

```json
"test": "vitest",
"test:run": "vitest run",
"test:ui": "vitest --ui"
```

## Conventions

- **Location:** Co-locate component tests next to the component (`Button.tsx` + `Button.test.tsx`), or put higher-level integration tests under `frontend/tests/<feature>/`.
- **Framework:** `vitest` + `@testing-library/react` + `jsdom`.
- **Queries:** Prefer `getByRole` > `getByLabelText` > `getByText`. Avoid `getByTestId` unless nothing else works.
- **Mocks:** Mock the `api` client at the module level: `vi.mock('@/lib/api')`.
- **Language:** Test code and test names in **English**. Complex helpers may have a **Spanish** docstring.

## Test Naming

Describe behavior, not implementation:

- ✅ `it("redirects unauthenticated users to /login")`
- ✅ `it("shows an error when the evaluation form is submitted with no rating")`
- ❌ `it("calls useEffect")`
- ❌ `it("renders correctly")`

## TDD Workflow

This repo enforces strict TDD via the orchestration system in `.claude/`:

1. **RED** — `test-worker` writes a failing test.
2. **GREEN** — `frontend-worker` implements the smallest change to make it pass.
3. **REFACTOR** — only if the test is green and the refactor is in the brief's scope.

## Example: Mocking the API client

```tsx
import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { ProjectList } from "@/components/dashboard/ProjectList";

vi.mock("@/lib/api", () => ({
  api: {
    get: vi.fn(),
  },
}));

import { api } from "@/lib/api";

describe("ProjectList", () => {
  beforeEach(() => {
    vi.mocked(api.get).mockResolvedValue({ data: [] });
  });

  it("renders an empty state when there are no projects", async () => {
    render(<ProjectList />);
    expect(await screen.findByText(/no projects yet/i)).toBeInTheDocument();
  });
});
```
