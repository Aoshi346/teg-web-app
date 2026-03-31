---
name: add-page
description: Scaffold a new dashboard page with routing, auth guard, and sidebar entry
user_invocable: true
arguments:
  - name: page_name
    description: The route name for the new page (e.g., "reportes", "estadisticas")
    required: true
  - name: label
    description: The sidebar label displayed to users (e.g., "Reportes", "Estadísticas")
    required: true
  - name: roles
    description: Comma-separated roles that can see this page (Administrador,Estudiante,Jurado,Tutor). Omit for all roles.
    required: false
---

# Add Dashboard Page

Create a new page under the TesisFar dashboard following project conventions.

## Steps

1. **Create the page file** at `src/app/dashboard/{{ page_name }}/page.tsx`:
   - Add `"use client"` directive at the top
   - Import `DashboardHeader` from `@/components/layout/DashboardHeader`
   - Import `PageTransition` from `@/components/ui/PageTransition`
   - Import `useSidebar` from `@/components/layout/SidebarContext` if the page needs sidebar state
   - Wrap the page content in `<PageTransition>` for entry animation
   - Use Tailwind CSS for all styling (no CSS modules)
   - Use Lucide React for any icons
   - All UI text should be in **Spanish**

2. **Add sidebar entry** in `src/components/layout/Sidebar.tsx`:
   - Add the new menu item to the `baseItems` array (around line 102-127)
   - Use a Lucide icon import that fits the page purpose
   - Set `label: "{{ label }}"` and `href: "/dashboard/{{ page_name }}"`
   - If roles are specified, add `requiredRole: [{{ roles }}]`
   - Keep the item positioned logically (before Settings, which should always be last)

3. **Follow these conventions**:
   - Use the `api` client from `@/lib/api.ts` for any backend calls
   - Use `getUser()` / `getUserRole()` from `@/features/auth/clientAuth` for auth checks
   - Store any service functions in `src/features/` following the existing pattern
   - TypeScript interfaces go in `src/types/`
   - Use shadcn/ui components (`button`, `card`, `input`) from `src/components/ui/` for UI primitives

4. **If the page needs dynamic routes** (e.g., detail pages):
   - Create `src/app/dashboard/{{ page_name }}/[id]/page.tsx`
   - Use `useParams()` from `next/navigation` to get the ID
   - Follow the pattern in `src/app/dashboard/proyectos/[id]/page.tsx`
