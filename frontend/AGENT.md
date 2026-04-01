# Frontend Agent Guide - TesisFar (TEG Web App)

## Project Overview

This is the **Next.js frontend** for **TesisFar**, a university academic project management system. It provides a polished, animated UI for submitting, evaluating, and tracking "Trabajos Especiales de Grado" (TEG/Special Degree Projects).

## Tech Stack

- **Framework:** Next.js 15.5.0 (App Router)
- **Language:** TypeScript 5
- **React:** 19.1.0
- **Styling:** Tailwind CSS 4 + shadcn/ui components
- **Animations:** GSAP 3.13
- **Icons:** Lucide React
- **Forms:** React Hook Form + Zod (validation schemas)
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
│       ├── agregar/              # Add new project/thesis (modular)
│       │   ├── page.tsx          # Thin layout wrapper
│       │   ├── schema.ts         # Zod validation schema
│       │   ├── hooks/            # useDocumentData (data fetching)
│       │   └── components/       # DocumentFormNew, DocumentTypeSelector,
│       │                         # AdvisorsFieldArray, Combobox, FormSkeleton, AccessDenied
│       ├── scan/                 # QR/barcode scanning
│       └── settings/             # User & admin settings (3-column layout)
├── components/
│   ├── layout/                   # Header, Sidebar, DashboardHeader, Footer
│   ├── landing/                  # Hero, FeaturesSection, FeatureCard
│   ├── auth/                     # LoginModal
│   ├── dashboard/                # Dashboard, ProjectCard, DocumentForm, CommentsSection
│   ├── evaluation/               # Modular evaluation system
│   │   ├── EvaluationForm.tsx    # Main orchestrator (RHF + sidebar layout)
│   │   ├── EvaluationSidebar.tsx # Sticky sidebar with section/subsection progress
│   │   ├── QuestionCard.tsx      # Single question wrapper
│   │   ├── StickyActionBar.tsx   # Sticky bottom nav/submit bar
│   │   ├── ResultsSummary.tsx    # Post-submission results view
│   │   ├── hooks/                # useEvaluationDraft, useScrollSpy, useEvaluationSubmit
│   │   └── inputs/               # YesNoInput, FrequencyInput, TernaryInput,
│   │                             # StarRatingInput, FreeTextInput
│   └── ui/                       # shadcn/ui primitives + custom UI components
├── features/
│   ├── auth/                     # clientAuth.ts (CRUD users, auth), credentials.ts
│   └── projects/                 # projectService.ts (projects, evaluations, comments)
├── lib/
│   ├── api.ts                    # HTTP client with CSRF handling
│   ├── semesters.ts              # Semester CRUD + utilities + month names
│   ├── utils.ts                  # General utilities (cn helper)
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
| `/dashboard/proyectos/[id]` | View project details + evaluation history + evaluator comments | Authenticated |
| `/dashboard/proyectos/[id]/editar` | Edit project | Authenticated |
| `/dashboard/proyectos/[id]/evaluar` | Evaluate project | Jurado/Tutor/Admin |
| `/dashboard/tesis` | List theses (TEG) | Authenticated |
| `/dashboard/tesis/[id]` | View thesis details + evaluation history + evaluator comments | Authenticated |
| `/dashboard/tesis/[id]/editar` | Edit thesis | Authenticated |
| `/dashboard/tesis/[id]/evaluar/fase1` | Phase 1 thesis evaluation | Jurado/Tutor/Admin |
| `/dashboard/tesis/[id]/evaluar/fase2` | Phase 2 thesis evaluation | Jurado/Tutor/Admin |
| `/dashboard/tracking` | Project tracking table | Authenticated |
| `/dashboard/agregar` | Add new project/thesis | Estudiante/Admin |
| `/dashboard/scan` | QR/barcode scanning | Jurado/Tutor |
| `/dashboard/settings` | Settings & user management | Authenticated (admin features restricted) |

## User Roles & UI Behavior

1. **Administrador** - Sees all projects/theses, user management in settings, semester management
2. **Estudiante** - Sees own projects, semester-based document type (9no = proyecto, 10mo = tesis)
3. **Jurado** - Sees all projects, can evaluate, has scan access
4. **Tutor** - Sees assigned projects, can evaluate, has scan access

Sidebar menu items are dynamically filtered by role in `Sidebar.tsx`.

## Authentication

- Session-based auth with Django backend
- User stored in `sessionStorage` (key: `tf_session_user`)
- Auth guard in `dashboard/layout.tsx` redirects unauthenticated users
- CSRF token fetched from `/api/csrf/` and sent with every request
- Login/register via `LoginModal` component
- User fields: id, email, firstName, lastName, fullName, cedula, role, status, semester, phone, dateJoined

## API Integration

All API calls go through `src/lib/api.ts`:
- Custom HTTP client with `get()`, `post()`, `patch()`, `put()`, `delete()`
- Automatic CSRF token extraction from cookies
- `credentials: "include"` for session cookies
- Service layers: `clientAuth.ts` (auth/users), `projectService.ts` (projects/evaluations/comments), `semesters.ts` (semester CRUD)

## Evaluation System

- Modular architecture: orchestrator + sidebar + inputs + hooks + action bar + results
- Two-column layout: sticky sidebar (section progress) + scrollable question grid
- Input components: YesNoInput, FrequencyInput, TernaryInput (3 variants), StarRatingInput, FreeTextInput
- Custom hooks: useEvaluationDraft (localStorage), useScrollSpy (IntersectionObserver), useEvaluationSubmit (scoring + API)
- Scoring: Diagramacion (5pts) + Contenido (15pts) = 20pts total, passing = 10pts
- Thesis has two sequential phases (fase1 must pass before fase2)
- Draft persistence via localStorage (`teg_eval_draft:{type}:{projectId}`)
- Auto-advance: after answering, focus scrolls to next unanswered question
- Evaluator comments stored as `{ general: "..." }` in Evaluation.comments and displayed to students on project/thesis detail pages
- Keyboard accessible: all input buttons support Tab + Space/Enter

## Document Creation (Agregar Page)

- Modular: page.tsx (wrapper) → DocumentFormNew (RHF orchestrator) + sub-components
- Zod schema validates: required title, required student, min 1 non-duplicate advisor, file size limits, conditional file requirement for students
- Combobox with portal-based dropdown (never clipped by overflow)
- Semester period is read-only (set by active semester from admin)
- Tutor/Jurado see AccessDenied instead of the form
- Skeleton loader while data fetches

## Semester System

- Semesters: `{ id, period, is_active, start_month, end_month, label, created_at }`
- Format: `YYYY-01` or `YYYY-02`, with configurable month ranges
- Can span years (e.g., September 2026 – January 2027)
- Admin manages in Settings > Administración > Semestres
- Active semester auto-assigned to new projects

## Settings Page

- 3-column layout: left nav | main content | context panel
- Tabs: Perfil (profile edit), Seguridad (password), Notificaciones, Administración
- Admin sub-tabs: Pendientes (approve users), Directorio (user CRUD), Semestres (period management)
- Searchable user list with role/status badges, pagination
- Semester creator with year, period, start/end month pickers

## State Management

- **No global state library** (no Redux/Zustand)
- React Context: `SidebarContext` for sidebar collapse state
- React Hook Form: document creation and evaluation forms
- `sessionStorage`: User session data
- `localStorage`: Selected semester, evaluation drafts
- Component-level: `useState`, `useCallback`, `useMemo`, `useRef`

## Styling

- Tailwind CSS 4 with custom theme variables (oklch color space)
- shadcn/ui for base components (button, card, input)
- Custom CSS animations: gradient, float, pulse-glow, shine
- Font: Montserrat via Google Fonts
- Responsive breakpoints: sm, md, lg, xl

## Key Dependencies

- `next@15.5.0`, `react@19.1.0`, `typescript@^5`
- `tailwindcss@^4`, `lucide-react@^0.541.0`
- `gsap@^3.13.0`
- `react-hook-form@^7`, `zod@^3`, `@hookform/resolvers`
- `class-variance-authority`, `clsx`, `tailwind-merge`

## Development Commands

```bash
npm install          # Install dependencies
npm run dev          # Start dev server with Turbopack (port 3000)
npm run build        # Production build
npm run lint         # ESLint
npm run type-check   # TypeScript validation
```

## Known Limitations

- No testing framework configured (no Jest/Vitest/Cypress)
- Supabase dependency installed but unused
- No error boundary components
- Auth is frontend-guarded only (backend enforces actual permissions)
- No i18n setup (UI text is hardcoded in Spanish)
