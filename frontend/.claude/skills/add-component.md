---
name: add-component
description: Create a new React component following TesisFar project conventions
user_invocable: true
arguments:
  - name: name
    description: The component name in PascalCase (e.g., "StatusBadge", "ProjectFilter")
    required: true
  - name: category
    description: "Component category: ui, layout, dashboard, evaluation, landing, or auth"
    required: true
---

# Add Component

Create a new React component for TesisFar following project conventions.

## Steps

1. **Create the component file** at `src/components/{{ category }}/{{ name }}.tsx`:
   - Add `"use client"` directive at the top (all components in this project are client-side)
   - Use TypeScript with an explicit props interface named `{{ name }}Props`
   - Export as a named `React.FC<{{ name }}Props>` or default function component
   - Use Tailwind CSS classes inline for all styling (no CSS modules, no styled-components)
   - Use `clsx` or the `cn()` utility from `@/lib/utils` for conditional classes
   - Use Lucide React (`lucide-react`) for icons — never install other icon libraries
   - All user-facing text must be in **Spanish**

2. **Follow the project's component patterns**:
   - For **ui/** components: Follow the shadcn/ui pattern with `class-variance-authority` (CVA) for variants. See `src/components/ui/button.tsx` as reference.
   - For **dashboard/** components: These are feature components that may call API services. Import from `@/features/` for data fetching.
   - For **layout/** components: These handle page structure. May use `SidebarContext` from `@/components/layout/SidebarContext`.
   - For **evaluation/** components: These handle scoring/evaluation UI. Reference `@/lib/questions/` for question types and scoring.
   - For **landing/** components: These are public-facing. May use GSAP (`gsap`) for animations.
   - For **auth/** components: These handle login/register. Use `@/features/auth/clientAuth` for auth calls.

3. **Styling guidelines**:
   - Primary colors: Navy (`#011638`), Blue (`#0066ff`), Orange (`#ff6b35`), Yellow (`#ffd23f`)
   - Use existing custom CSS classes from `globals.css` when applicable: `glassmorphism`, `dot-grid`, `gradient-border-top`, `floating`, `pulse-glow`
   - Font is Montserrat (already configured globally)
   - Use responsive prefixes: `sm:`, `md:`, `lg:`

4. **Do NOT**:
   - Create separate CSS files or CSS modules
   - Install new dependencies without asking
   - Add testing files (no test framework is configured)
   - Create index barrel files
