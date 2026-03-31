z# Frontend Development Guide - TesisFar

## Quick Reference

- **Entry point:** `src/app/layout.tsx` (root layout) / `src/app/page.tsx` (landing)
- **Run dev server:** `npm run dev` (port 3000, Turbopack)
- **Backend API:** http://localhost:8000/api
- **Install deps:** `npm install`

## Architecture

Next.js 15 App Router with file-based routing. All dashboard routes are protected by the auth guard in `src/app/dashboard/layout.tsx`.

```
User Action → Component → Service Layer (features/) → HTTP Client (lib/api.ts) → Django API
```

## Code Conventions

- All pages under `dashboard/` use `"use client"` directive
- Components are organized by feature: layout/, landing/, auth/, dashboard/, evaluation/, ui/
- API services split into `clientAuth.ts` (auth/users) and `projectService.ts` (projects/evaluations)
- Spanish naming in UI text and some variable names (proyectos, tesis, evaluar, agregar)
- Tailwind classes applied inline, no CSS modules
- shadcn/ui components in `src/components/ui/` follow the CVA pattern

## When Adding a New Page

1. Create directory under `src/app/dashboard/` (e.g., `dashboard/new-page/page.tsx`)
2. Add `"use client"` at the top
3. Add sidebar link in `src/components/layout/Sidebar.tsx` (filter by role if needed)
4. Use `DashboardHeader` component for page title
5. Wrap content in `PageTransition` for entry animation

## When Adding a New Component

1. Place in the appropriate `src/components/` subdirectory
2. Use Tailwind for styling, Lucide for icons
3. For reusable UI primitives, follow the shadcn/ui pattern in `src/components/ui/`
4. Use TypeScript interfaces for props

## When Adding API Calls

1. Add the function to the appropriate service file:
   - Auth/users: `src/features/auth/clientAuth.ts`
   - Projects/evaluations: `src/features/projects/projectService.ts`
2. Use the `api` client from `src/lib/api.ts` (handles CSRF + session cookies automatically)
3. Define TypeScript types in `src/types/project.ts`

## Authentication Pattern

```typescript
// Check auth in components:
import { isAuthenticated, getUser, getUserRole } from "@/features/auth/credentials";

const user = getUser();           // From sessionStorage
const role = getUserRole();       // "Administrador" | "Estudiante" | "Jurado" | "Tutor"
const authed = isAuthenticated(); // boolean
```

Session is stored in `sessionStorage` under key `tf_session_user`. The dashboard layout auto-redirects if not authenticated.

## Role-Based UI Pattern

```typescript
// In Sidebar.tsx, menu items are filtered:
const menuItems = allItems.filter(item => {
  if (item.roles && !item.roles.includes(userRole)) return false;
  return true;
});
```

Roles: `Administrador`, `Estudiante`, `Jurado`, `Tutor`

## Evaluation Questions

- Defined in `src/lib/questions/questions.ts`
- Scoring logic in `src/lib/questions/scoring.ts`
- Question types: `yes_no`, `frequency`, `ternary`, `text`
- Two evaluation categories: Diagramacion (formatting) and Contenido (content)
- Thesis has two phases; proyecto has one

## Styling Patterns

- Use Tailwind utilities inline
- For class composition: `clsx()` + `tailwind-merge` (via `cn()` from `lib/utils.ts`)
- Custom theme colors defined as CSS variables in `globals.css`
- Primary palette: Navy (#011638), Blue (#0066ff), Orange (#ff6b35), Yellow (#ffd23f)
- Animation: GSAP for complex sequences, CSS keyframes for simple loops

## Key Files to Know

| File | Purpose |
|------|---------|
| `src/lib/api.ts` | HTTP client, CSRF handling |
| `src/features/auth/clientAuth.ts` | Auth + user management API calls |
| `src/features/auth/credentials.ts` | Session storage helpers |
| `src/features/projects/projectService.ts` | Project/evaluation/semester API calls |
| `src/components/layout/Sidebar.tsx` | Navigation with role filtering |
| `src/components/evaluation/EvaluationForm.tsx` | Multi-page evaluation form |
| `src/lib/questions/questions.ts` | Evaluation question definitions |
| `src/lib/questions/scoring.ts` | Score calculation |
| `src/types/project.ts` | TypeScript interfaces |
| `src/app/globals.css` | Theme variables + custom animations |

## Known Limitations

- No test suite (no Jest, Vitest, or Cypress configured)
- `@supabase/supabase-js` is in dependencies but not used for auth (Django handles it)
- No error boundaries for React error handling
- No i18n setup (UI text is hardcoded in Spanish)
