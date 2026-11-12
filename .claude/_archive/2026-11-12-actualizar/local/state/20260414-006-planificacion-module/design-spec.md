# Planificación — Visual Design Spec

> Output of Phase 0 of task 006. This document is the contract that
> `frontend-worker` will follow when building `features/planificacion/`.

## Conceptual Direction — "Editorial Almanac"

The Planificación page is a calendar, but conceptually it's an **almanac
spread**: a thoughtfully laid-out agenda that treats dates and times as
typographic anchors rather than UI controls. Where the rest of the
dashboard is utilitarian, this page leans editorial — weighted serif
numerals, a generous header, and time pills that feel like printed
indexes. The vibe is *"the hand-bound thesis defense schedule on the
director's desk"*, not *"another SaaS calendar"*.

This is a conscious step up from the rest of the dashboard, but it
**inherits the existing palette and tooling** (Tailwind 4, USM Navy /
Blue / Orange / Yellow, shadcn primitives). The lift comes from
typography, spatial composition, and motion — not from a competing
visual language.

## Type System

The dashboard already loads **Geist Sans** as the body face and
**Geist Mono** as mono. We introduce **one** new face — a variable
serif — scoped to this module via `next/font`:

```ts
// frontend/src/app/dashboard/planificacion/fonts.ts
import { Fraunces } from "next/font/google";
export const fraunces = Fraunces({
  subsets: ["latin"],
  variable: "--font-display",
  axes: ["opsz", "SOFT"],
});
```

The page wrapper applies `fraunces.variable` so `font-display` only
exists inside Planificación.

| Token             | Family                             | Use                                                              |
|-------------------|-----------------------------------|------------------------------------------------------------------|
| `font-display`    | Fraunces (var serif, opsz 144)    | Big day numerals, "Planificación" wordmark, day-card headers    |
| `font-sans`       | Geist Sans (existing)             | All body text, labels, buttons                                   |
| `font-mono`       | Geist Mono (existing)             | Time pills (HH:MM), duration badges                              |

**Type scale** (the only sizes used):

| Token       | Size         | Weight | Use                                       |
|-------------|--------------|--------|-------------------------------------------|
| `display-xl`| 88px / 0.95  | 300    | Day numeral inside a day card             |
| `display-l` | 56px / 1.0   | 400    | "Planificación" wordmark in header        |
| `display-m` | 28px / 1.15  | 500    | Day-card header (weekday + month)         |
| `body-l`    | 16px / 1.4   | 500    | Project titles                            |
| `body-m`    | 14px / 1.5   | 400    | Names, labels                             |
| `body-s`    | 12px / 1.4   | 500    | Role chips, helper text (uppercase)       |
| `mono-m`    | 14px         | 600    | Time pills, duration                      |

## Color System

Reuse the four USM brand tokens already in `globals.css`. We add **one**
gradient and **one** soft surface as new tokens — both scoped via the
component, not added globally so they don't leak.

```css
/* defined inline in PlanificacionView.tsx as Tailwind arbitrary values */
--planif-gradient: linear-gradient(135deg, #011638 0%, #0a2461 45%, #0066ff 100%);
--planif-paper:   #fbfaf6;          /* warm off-white "agenda paper" */
--planif-grain:   url(noise.svg);   /* 4% opacity SVG noise overlay */
```

**Semantic mapping inside the module:**

| Element                       | Color                                                  |
|-------------------------------|--------------------------------------------------------|
| Header background             | `--planif-gradient` + grain overlay                    |
| Page background               | `--planif-paper` (warm, not stark white)              |
| Day card surface              | `white` with 1px `slate-200/60` border                 |
| Day card left border (proyecto)| 4px `usm-blue` (#0066ff)                              |
| Day card left border (tesis)  | 4px `usm-orange` (#ff6b35)                             |
| Time pill background          | `usm-navy/8` with `usm-navy` text                      |
| Selected date (calendar)      | `usm-navy` solid + white text                          |
| Range fill (calendar)         | `usm-blue/15` with `usm-blue` text                     |
| Today marker                  | 2px ring `usm-yellow`                                  |
| Empty-state illustration      | Two-tone `usm-blue` + `usm-yellow`                     |
| Admin action buttons          | `usm-navy` solid (primary), `usm-orange` (destructive) |

We deliberately do **not** introduce purple, teal, or any color outside
the existing palette.

## Layout — Page Composition

```
┌─────────────────────────────────────────────────────────────────┐
│  ▓▓▓ HEADER STRIP (gradient + grain, 280px tall) ▓▓▓             │
│   "Planificación"                                  [Sem. 2026-01]│
│   subtitle: "Agenda de presentaciones"                            │
│                                       [● Rango  ○ Individual]    │
└─────────────────────────────────────────────────────────────────┘
   ↓ overlap −48px ↓
┌─────────────────────────────────────────────────────────────────┐
│  ┌────────────────────┐  ┌─────────────────────────────────┐    │
│  │   MONTH CALENDAR   │  │   DAY CARDS (vertical stack)    │    │
│  │   (sticky on lg+)  │  │                                 │    │
│  │                    │  │   ┌─ day card ─────────────┐    │    │
│  │   <  Abril 2026  > │  │   │ 88   Lunes              │    │    │
│  │   L M M J V S D    │  │   │      14 Abril           │    │    │
│  │   . . . . . 1 2    │  │   │ ──────────────────────  │    │    │
│  │   3 4 5 6 7 8 9    │  │   │ 09:00 ▎ Project A       │    │    │
│  │   10 11 12 [13][14]│  │   │ 10:00 ▎ Project B       │    │    │
│  │   ...              │  │   └─────────────────────────┘    │    │
│  │                    │  │                                 │    │
│  │   [Crear días]     │  │   ┌─ day card ─────────────┐    │    │
│  └────────────────────┘  │   ...                            │    │
│                          │                                 │    │
└─────────────────────────────────────────────────────────────────┘
```

### Header Strip (`PlanificacionHeader.tsx`)

- Full-bleed within the dashboard content area, **280px** tall on `lg+`,
  **200px** on mobile.
- Background: `--planif-gradient` with the grain SVG layered at 6% opacity
  via `mix-blend-overlay`. **No** plain navy fill; the gradient is the
  whole point.
- Wordmark: `font-display`, `display-l`, color `usm-yellow`, letter-spacing
  `-0.02em`. Subtitle below in `body-m` Geist, `white/70`.
- Top-right cluster: semester pill (`white/12` background, white text,
  rounded-full, padding `8px 16px`) + mode toggle.
- Mode toggle: pill-shaped 2-segment switch (`Rango` ⇄ `Individual`),
  `white/12` track, white indicator, 200ms cubic-bezier slide.
- Decorative serif comma in `--planif-paper/15` set behind the wordmark
  at 240px, slightly clipped — borrows the editorial feel.

### Month Calendar (`WeekCalendar.tsx`)

Hand-built, **no new dependencies**. ~150 LoC of state + render.

- Card surface: white, `rounded-2xl`, `shadow-[0_1px_0_0_rgba(2,18,56,.06),0_24px_48px_-24px_rgba(2,18,56,.18)]`.
  No flat shadows — the soft drop is part of the editorial feel.
- Header row: `<` `Abril 2026` `>`. Month name in `font-display`,
  `display-m`, weight 400. Arrows are 32px hit targets.
- Weekday strip: `body-s` uppercase, color `slate-400`, `tracking-[0.18em]`.
- Day cells: 40×40 with 6px gap. Hover: `bg-slate-100`, 120ms.
- **Range mode**: clicking start, then end fills inclusive range. Hover
  during range selection shows a "preview" range in `usm-blue/8`.
- **Individual mode**: each click toggles a single day in/out of a Set.
- **Existing `PresentationDay` from API** → small `usm-blue` dot under
  the numeral.
- **Today** → 2px `usm-yellow` ring.
- **Selected** → solid `usm-navy` + white text + scale 1.05 on selection.
- Sticky on `lg+` (top: 96px), scrolls with content on mobile.
- CTA button below calendar: `Crear / actualizar días` — admin only.
  Hidden for non-admins. Solid `usm-navy`, white text, `font-sans`,
  500 weight, `rounded-xl`, 48px tall.

### Day Card (`DayCard.tsx`)

- Surface: white, `rounded-2xl`, 1px `slate-200/60` border, **4px left
  border** colored by the *first* presentation's project_type. If a day
  mixes proyecto + tesis, the border is split 50/50 (CSS gradient on the
  border-image, not two cards).
- Header layout: a 2-column flex.
  - Left: the day numeral in `font-display`, `display-xl`, weight 300,
    color `usm-navy`. Optical kerning matters here — that's what
    Fraunces gives us.
  - Right: weekday in `font-display` `display-m`, then month + year in
    `body-m` slate-500, then a small admin actions row (✎ edit, 🗑 delete)
    only visible to Administrador.
- Divider: 1px `slate-200`.
- Presentations list: vertical stack with `divide-y divide-slate-100`.
- "+ Agregar presentación" affordance at the bottom — admin only,
  ghost button, dashed `usm-navy/30` border, `usm-navy/70` text.
- Empty day: friendly tagline "Día sin presentaciones programadas",
  centered, 96px tall.

### Presentation Row (`PresentationCard.tsx`)

A single row inside the day card. Layout:

```
[09:00]  Project Title                                      ✎ 🗑
 30 min  Estudiante · email                                  (admin only)
         Tutor: Nombre  ·  Jurado: Nombre, Nombre, Nombre
```

- Time pill: 64×64 square-ish, `usm-navy/8` background, `font-mono`
  `mono-m` (HH:MM). Below the time, in 11px slate-500: duration ("30 min").
  This is the row's typographic anchor.
- Project title: `body-l` Geist, 500 weight, slate-900.
- Student line: `body-m` slate-500.
- Tutor + jurado line: `body-s` uppercase tracking-wide, slate-500 with
  `slate-700` for the actual names.
- Hover: row background `usm-paper` (warm tint), `transition-colors 120ms`.
- Admin icons appear on row hover only (opacity 0 → 1).

### Empty State (`EmptyDayState.tsx`)

For the case where no `PresentationDay` exists for the chosen semester.

- Two-tone SVG illustration: a stylized open agenda book, `usm-blue`
  cover + `usm-yellow` page accent, ~200px tall. **Hand-crafted SVG**
  inline (no external asset).
- Headline `font-display` `display-m`: "Aún no hay días planificados".
- Subline `body-m` slate-500.
- Admin sees CTA "Selecciona días en el calendario para empezar"; non-
  admin sees "Pídele al administrador que planifique la semana".

### Add / Edit Modal (`PresentationFormModal.tsx`)

Built on the existing `Dialog` shadcn primitive with custom inner styling.

- Width 560px, `rounded-2xl`, `--planif-paper` background.
- Title in `font-display` `display-m`: "Programar presentación".
- Form fields, top to bottom:
  1. **Proyecto / Tesis** — existing `Combobox`, scoped to projects in
     active semester. Selecting a project auto-fills tutor + project_type
     readout.
  2. **Tutor** — read-only chip showing the project's first advisor,
     with an "override" toggle that swaps it for a tutor `Combobox`.
  3. **Jurado(s)** — multi-select chip input (existing `Combobox`
     pattern, but multi). Pulls users with `role == 'Jurado'`. Shows
     selected jurados as removable pills below the input.
  4. **Hora de inicio** + **Duración** — side-by-side. Hora is a native
     `<input type="time">` styled to match. Duración is a number input
     with stepper (default 30, step 5, min 5, max 240).
- Footer: secondary "Cancelar" + primary "Guardar". Primary is solid
  `usm-navy`, hover `usm-blue`.
- Validation messages render inline in `usm-orange`, `body-s`.

## Motion

Use Tailwind transitions and CSS keyframes — **no new motion lib**.
The existing `tw-animate-css` package is already loaded.

| Trigger                   | Effect                                                                 |
|---------------------------|------------------------------------------------------------------------|
| Page mount                | Header strip slides down 12px + fades in (400ms cubic-bezier(.2,.8,.2,1)). |
| Day cards entrance        | Stagger fade-in/up, 60ms per card, max 6 cards animated.              |
| Calendar mode toggle      | Slide indicator 200ms, ease-out.                                       |
| Day cell selection        | Scale 1.0 → 1.05 → 1.0 over 220ms, color crossfade.                    |
| Modal open                | Fade + scale 0.96 → 1.0 (180ms), backdrop blur 0 → 8px.                |
| Hover on presentation row | Background crossfade 120ms; admin icons opacity 0 → 1.                 |
| "Crear días" success      | Toast slides in from top-right, sticks 3s.                             |

No parallax, no scroll-triggered reveals after the initial mount, no
infinite loops. Motion is for delight at moments of action, not ambient
noise.

## Atmosphere & Detail

- **Grain overlay** on the header (and only the header) — an inline SVG
  `<feTurbulence>` filter, 4–6% opacity. Gives the gradient texture and
  hides banding.
- **Decorative serif glyph** behind the header wordmark (the comma trick
  from above), `font-display`, `--planif-paper/12`, sized 240px,
  positioned `-bottom-12 left-8`, `pointer-events-none`.
- **Soft "agenda paper" page background** `#fbfaf6` instead of pure
  white — a 2% warmth shift makes the white day cards feel like cards,
  not the same surface as the page.
- **Calendar drop shadow** is the soft 24px blur described above —
  never the default Tailwind `shadow-lg`.
- **Day-card border** uses `border-image` for the split 50/50 navy
  variant (mixed proyecto/tesis day) — small detail that pays off.

## Responsive

- `< 768px`: header collapses to 200px, mode toggle stacks below
  wordmark, calendar and day cards stack vertically (calendar first,
  then day list). Day numeral shrinks from `display-xl` to 64px.
- `768px–1023px`: same single-column flow but with more breathing room.
- `≥ 1024px`: 2-column layout, calendar sticky in the left column at
  `top: 96px`.

## Accessibility

- All custom day cells have `role="button"`, `aria-pressed`, and visible
  focus ring (`ring-2 ring-usm-yellow ring-offset-2`).
- The mode toggle is a `role="radiogroup"` with two `role="radio"`.
- Time pill renders the time via `<time dateTime="HH:MM">`.
- Color contrast: navy on yellow checked (≥ AAA); white on the gradient
  uses the darker stops, contrast ≥ 7:1.
- Modal uses the existing shadcn `Dialog` which already handles focus
  trap + ESC dismiss + ARIA roles.
- All admin-only controls are gated by role *before* render — never
  rendered with `disabled` to non-admins (avoids leaking the affordance).

## Component Inventory & File Map

```
features/planificacion/
  api/planificacionService.ts        # CRUD against /api/planificacion/*
  components/
    PlanificacionView.tsx            # top-level orchestrator
    PlanificacionHeader.tsx          # gradient header + mode toggle
    WeekCalendar.tsx                 # custom month grid
    DayCard.tsx                      # one day's card
    PresentationCard.tsx             # one presentation row
    PresentationFormModal.tsx        # admin add/edit
    EmptyDayState.tsx                # zero-data state
    icons/AgendaIllustration.tsx     # inline 2-tone SVG
  hooks/
    usePlanificacion.ts              # fetch + cache
    useDateSelection.ts              # range/individual selection state
  lib/
    formatDate.ts                    # locale-aware Spanish formatters
  types/planificacion.ts             # TS interfaces
  index.ts                           # public barrel
```

## Out of Scope (do NOT build now)

- ICS export
- Drag-to-reorder presentations within a day
- Conflict warnings on overlapping HH:MM slots
- Room / location field
- Multi-month calendar view
- Print stylesheet (could be a nice follow-up given the editorial vibe)

## Open detail to confirm

- **Time format:** the spec assumes 24-hour `HH:MM` (matches the rest of
  the app's Spanish locale convention). If you'd rather have 12-hour AM/PM,
  say so before Phase 1.
- **Fraunces import** adds ~28 KB woff2 over the wire (variable font,
  subsetted to latin). Acceptable? If you want zero new fonts, the spec
  degrades gracefully to `font-sans` for the display tokens — it'll be
  less editorial but still distinctive.
