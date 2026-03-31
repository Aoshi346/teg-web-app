# Frontend Agent Guide - TesisFar (TEG Web App)

## Project Overview

This is the **Next.js frontend** for **TesisFar**, a university academic project management system. It provides a polished, animated UI for submitting, evaluating, and tracking "Trabajos Especiales de Grado" (TEG/Special Degree Projects).

## Tech Stack

- **Framework:** Next.js 15.5.0 (App Router)
- **Language:** TypeScript 5
- **React:** 19.1.0
- **Styling:** Tailwind CSS 4 + shadcn/ui components
- **Animations:** GSAP 3.13 + Framer Motion 12
- **Icons:** Lucide React
- **Build:** Turbopack (Next.js built-in)
- **Backend API:** Django at http://localhost:8000/api

## Project Structure

```
frontend/src/
├── app/                          # Next.js App Router pages
│   ├── layout.tsx                # Root layout (Montserrat font)
│   ├── page.tsx                  # Landing page
│   ├── globals.css               # Global styles + Tailwind theme
│   └── dashboard/                # Protected dashboard routes
│       ├── layout.tsx            # Auth guard + sidebar layout
│       ├── page.tsx              # Dashboard home (stats cards)
│       ├── proyectos/            # Project (PTEG) management
│       │   ├── page.tsx          # List projects
│       │   └── [id]/             # View, edit, evaluate project
│       ├── tesis/                # Thesis (TEG) management
│       │   ├── page.tsx          # List theses
│       │   └── [id]/             # View, edit, evaluate (fase1/fase2)
│       ├── tracking/             # Project tracking table
│       ├── agregar/              # Add new project/thesis
│       ├── scan/                 # QR/barcode scanning
│       └── settings/             # User & admin settings
├── components/
│   ├── layout/                   # Header, Sidebar, DashboardHeader, Footer
│   ├── landing/                  # Hero, FeaturesSection, FeatureCard
│   ├── auth/                     # LoginModal
│   ├── dashboard/                # Dashboard, ProjectCard, DocumentForm, CommentsSection
│   ├── evaluation/               # EvaluationForm (multi-page scoring)
│   └── ui/                       # shadcn/ui primitives + custom UI components
├── features/
│   ├── auth/                     # clientAuth.ts, credentials.ts
│   └── projects/                 # projectService.ts
├── lib/
│   ├── api.ts                    # HTTP client with CSRF handling
│   ├── semesters.ts              # Semester utilities
│   ├── dashboardState.ts         # Dashboard initialization state
│   ├── utils.ts                  # General utilities
│   └── questions/                # Evaluation questions & scoring logic
├── hooks/
│   └── useValidation.ts          # Validation banner hook
└── types/
    └── project.ts                # Project/thesis TypeScript interfaces
```

## Routing

| Route | Page | Access |
|-------|------|--------|
| `/` | Landing page with hero + features + login modal | Public |
| `/dashboard` | Stats dashboard with animated counters | Authenticated |
| `/dashboard/proyectos` | List projects (PTEG) | Authenticated |
| `/dashboard/proyectos/[id]` | View project details | Authenticated |
| `/dashboard/proyectos/[id]/editar` | Edit project | Authenticated |
| `/dashboard/proyectos/[id]/evaluar` | Evaluate project | Jurado/Tutor/Admin |
| `/dashboard/tesis` | List theses (TEG) | Authenticated |
| `/dashboard/tesis/[id]` | View thesis details | Authenticated |
| `/dashboard/tesis/[id]/editar` | Edit thesis | Authenticated |
| `/dashboard/tesis/[id]/evaluar/fase1` | Phase 1 thesis evaluation | Jurado/Tutor/Admin |
| `/dashboard/tesis/[id]/evaluar/fase2` | Phase 2 thesis evaluation (after fase1 passes) | Jurado/Tutor/Admin |
| `/dashboard/tracking` | Project tracking table | Authenticated |
| `/dashboard/agregar` | Add new project/thesis | Estudiante |
| `/dashboard/scan` | QR/barcode scanning | Jurado/Tutor |
| `/dashboard/settings` | Settings & user management | Authenticated (admin features restricted) |

## User Roles & UI Behavior

1. **Administrador** - Sees all projects/theses, user management in settings, semester management
2. **Estudiante** - Sees own projects, semester-based menu (semester 10 = PTEG, otherwise TEG)
3. **Jurado** - Sees all projects, can evaluate, has scan access
4. **Tutor** - Sees assigned projects, has scan access

Sidebar menu items are dynamically filtered by role in `Sidebar.tsx`.

## Authentication

- Session-based auth with Django backend
- User stored in `sessionStorage` (key: `tf_session_user`)
- Auth guard in `dashboard/layout.tsx` redirects unauthenticated users
- CSRF token fetched from `/api/csrf/` and sent with every request
- Login/register via `LoginModal` component

## API Integration

All API calls go through `src/lib/api.ts`:
- Custom HTTP client with `get()`, `post()`, `patch()`, `put()`, `delete()`
- Automatic CSRF token extraction from cookies
- `credentials: "include"` for session cookies
- Service layers: `clientAuth.ts` (auth/users), `projectService.ts` (projects/evaluations/semesters/comments)

## Evaluation System

- Multi-page form with 28+ questions per document type
- Question types: Yes/No, Frequency, Ternary, Text
- Scoring: Diagramacion (5pts) + Contenido (15pts) = 20pts total, passing = 10pts
- Thesis has two sequential phases (fase1 must pass before fase2)
- Draft persistence via localStorage (`teg_eval_draft:{type}:{projectId}`)
- Questions/scoring defined in `src/lib/questions/`

## State Management

- **No global state library** (no Redux/Zustand)
- React Context: `SidebarContext` for sidebar collapse state
- `sessionStorage`: User session data
- `localStorage`: Selected semester, evaluation drafts
- Component-level: `useState`, `useCallback`, `useMemo`, `useRef`

## Styling

- Tailwind CSS 4 with custom theme variables (oklch color space)
- shadcn/ui for base components (button, card, input)
- Custom CSS animations: gradient, float, pulse-glow, shine
- Glassmorphism, dot-grid, mesh-gradient utility classes
- Font: Montserrat via Google Fonts
- Responsive breakpoints: sm, md, lg

## Key Dependencies

- `next@15.5.0`, `react@19.1.0`, `typescript@^5`
- `tailwindcss@^4`, `lucide-react@^0.541.0`
- `gsap@^3.13.0`, `framer-motion@^12.23.12`, `split-type@^0.3.4`
- `class-variance-authority`, `clsx`, `tailwind-merge`
- `@supabase/supabase-js@^2.56.1` (imported but not actively used)

## Development Commands

```bash
npm install          # Install dependencies
npm run dev          # Start dev server with Turbopack (port 3000)
npm run build        # Production build
npm run lint         # ESLint
npm run lint:fix     # ESLint auto-fix
npm run type-check   # TypeScript validation
```

## Known Limitations

- No testing framework configured (no Jest/Vitest/Cypress)
- Supabase dependency installed but unused
- No error boundary components
- Auth is frontend-guarded only (backend enforces actual permissions)
