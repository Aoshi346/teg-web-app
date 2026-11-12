# BM V2.1 — Plan de Paralelización
**Fecha:** 27 Feb 2026
**Basado en:** specs.md
**Prioridad:** Portal Clientes > Vista Mes > Sprints > Workouts > Email Marketing > Recurrentes

---

## 🗺️ MAPA DE DEPENDENCIAS

```
Wave 1 (Paralelo — sin conflictos)
├── Track A: Portal Clientes [M3]       ← PRIORITY 1
├── Track B: Sprints Mejoras [M4]       ← independiente
└── Track C: Vista Mes + KPIs [M1]      ← independiente

Wave 2 (Después de Wave 1)
├── Track D: Email Marketing [M2]       ← toca HoyPanel (Wait: Wave 1)
└── Track E: Workouts + Recurrentes     ← SettingsPage compartido [M5+M6]
```

---

## ⚡ WAVE 1 — Paralelo (3 Worktrees)

### TRACK A: Portal Clientes [PRIORIDAD 1]

**Objetivo:** Completar Portal con estados, prioridades Eisenhower, fechas duales

**Archivos afectados:**
```
backend/
  apps/clients/models.py          ← añadir task_status choices, review_date, deadline_date
  apps/clients/serializers.py     ← nuevos campos
  apps/clients/views.py           ← endpoint PATCH para estado/prioridad/fechas
  apps/clients/migrations/        ← migración nueva

frontend/
  src/pages/ClientPortal.tsx      ← dropdown prioridad Eisenhower, nuevos estados, fechas
  src/pages/ClientsPage.tsx       ← panel admin con mismas funcionalidades
  src/services/clientsService.ts  ← nuevos métodos (si existe) o actualizar
  src/types/models.ts             ← nuevos tipos ClientTask
```

**Orden interno (secuencial):**
1. Backend: modelos → serializers → views → migración
2. Frontend: tipos → service → ClientPortal → ClientsPage

**NO toca:** HoyPanel, NegocioPanel, SettingsPage, MonthlyPanel

**Riesgo de conflicto:** BAJO — archivos aislados

---

### TRACK B: Sprints Mejoras [M4]

**Objetivo:** Editar fechas, crear sprint con naming correcto, mover tareas entre sprints

**Archivos afectados:**
```
backend/
  apps/sprints/models.py          ← verificar campos start_date/end_date editables
  apps/sprints/views.py           ← endpoint PATCH para fechas, endpoint move-tasks
  apps/sprints/serializers.py     ← serializer para move tasks

frontend/
  src/pages/NegocioPanel.tsx      ← edit dates modal, create sprint naming, move tasks UI
  src/services/sprintsService.ts  ← moveTasks(), updateDates()
  src/types/models.ts             ← Sprint type update (compartido con Track A — VER NOTA)
```

**Orden interno (secuencial):**
1. Backend: verificar modelo → añadir views → serializer move-tasks
2. Frontend: sprintsService → NegocioPanel (modales + UI)

**NOTA CONFLICTO:** `src/types/models.ts` puede tocarse en Track A y B.
**Resolución:** Añadir tipos en secciones distintas del archivo; hacer merge manual al final.

**NO toca:** ClientPortal, SettingsPage, MonthlyPanel, HoyPanel

**Riesgo de conflicto:** BAJO (excepto models.ts — ver nota)

---

### TRACK C: Vista Mes + KPIs [M1]

**Objetivo:** Añadir KPIs faltantes (Energía, Llamadas, Workouts, Score), gráficos de progreso

**Archivos afectados:**
```
backend/
  apps/core/models.py             ← añadir campos KPI a WeeklyEntry/MonthlyEntry
  apps/core/serializers.py        ← nuevos campos
  apps/core/views.py              ← aggregation para KPIs
  apps/core/migrations/           ← migración nueva

frontend/
  src/pages/MonthlyPanel.tsx      ← nuevos KPIs, sección gráficos
  src/pages/WeeklyPanel.tsx       ← nuevos KPIs (energía, llamadas)
  src/services/monthlyService.ts  ← getCurrent() actualizado
  src/services/weeklyService.ts   ← getCurrent() actualizado
  src/types/models.ts             ← WeeklyEntry/MonthlyEntry types (compartido)
```

**Decisión charts:** Usar recharts (ya en deps) o Chart.js. Verificar package.json primero.
Si no están instalados → usar SVG/CSS puro para evitar npm install en producción.

**Orden interno (secuencial):**
1. Backend: modelos → migración → serializers → views aggregate
2. Frontend: types → services → WeeklyPanel → MonthlyPanel

**NOTA CONFLICTO:** `models.ts` compartido con Track A y B.
**Resolución:** Merge al final por secciones.

**NO toca:** ClientPortal, NegocioPanel, SettingsPage, HoyPanel

**Riesgo de conflicto:** BAJO (backend aislado; frontend solo MonthlyPanel/WeeklyPanel)

---

## ⚡ WAVE 2 — Post Wave 1

### TRACK D: Email Marketing [M2]

**Esperar a:** Wave 1 completa (HoyPanel se tocará aquí)

**Archivos afectados:**
```
backend/
  apps/email_marketing/           ← NUEVA app Django
    __init__.py, apps.py
    models.py                     ← EmailCampaign, EmailMetrics
    serializers.py
    views.py
    urls.py
  config/urls.py                  ← registrar nueva app
  config/settings/base.py         ← INSTALLED_APPS

frontend/
  src/pages/EmailMarketingPage.tsx  ← NUEVA página
  src/services/emailMarketingService.ts  ← NUEVO service
  src/App.tsx                         ← nueva ruta /email-marketing
  src/components/Sidebar.tsx          ← nuevo ítem nav
  src/pages/HoyPanel.tsx              ← tab Email (nuevos KPIs del día)
  src/types/models.ts                 ← nuevos tipos EmailMetrics
```

**Orden interno (secuencial):**
1. Backend: nueva app → models → serializers → views → urls → settings
2. Frontend: tipos → service → página → App.tsx ruta → Sidebar → HoyPanel tab

**NOTA:** GHL API investigation primero. Si no hay API → input manual (más simple).

**Riesgo de conflicto:** MEDIO — HoyPanel, App.tsx, Sidebar tocados. Hacer después de Wave 1.

---

### TRACK E: Workouts + Recurrentes [M5 + M6]

**Esperar a:** Wave 1 completa (SettingsPage compartido)

**Archivos afectados:**
```
backend/
  apps/workouts/models.py         ← ExerciseCatalog, WorkoutTemplate, WorkoutPlan
  apps/workouts/serializers.py    ← CRUDs
  apps/workouts/views.py          ← endpoints catálogo + plantillas + activa
  apps/workouts/migrations/       ← migración
  apps/objectives/models.py       ← SystematicTask clarifications (M6)

frontend/
  src/pages/SettingsPage.tsx      ← tab Workouts rediseñado + tab Recurrentes clarificado
  src/pages/WorkoutsPage.tsx      ← usar plantilla activa
  src/services/workoutsService.ts ← nuevos endpoints
  src/types/models.ts             ← Exercise, WorkoutTemplate types
```

**Orden M5 vs M6 (secuencial dentro del track):**
1. M5 Workouts backend → M5 frontend
2. M6 UX decision (fusionar/mantener) → ajustar SettingsPage

**Riesgo de conflicto:** BAJO — SettingsPage compartido pero no con otros tracks activos

---

## 📋 TABLA DE ARCHIVOS CRÍTICOS

| Archivo | Track | Wave | Conflicto |
|---------|-------|------|-----------|
| `apps/clients/models.py` | A | 1 | ❌ |
| `apps/clients/views.py` | A | 1 | ❌ |
| `pages/ClientPortal.tsx` | A | 1 | ❌ |
| `apps/sprints/views.py` | B | 1 | ❌ |
| `pages/NegocioPanel.tsx` | B | 1 | ❌ |
| `apps/core/models.py` | C | 1 | ❌ |
| `pages/MonthlyPanel.tsx` | C | 1 | ❌ |
| `pages/WeeklyPanel.tsx` | C | 1 | ❌ |
| `types/models.ts` | A+B+C | 1 | ⚠️ MERGE |
| `pages/HoyPanel.tsx` | D | 2 | ⚠️ POST W1 |
| `App.tsx` | D | 2 | ⚠️ POST W1 |
| `Sidebar.tsx` | D | 2 | ⚠️ POST W1 |
| `pages/SettingsPage.tsx` | E | 2 | ⚠️ POST W1 |

---

## 🔄 PROTOCOLO DE MERGE (models.ts)

Al terminar Wave 1, hacer merge de `types/models.ts` en este orden:
1. Aplicar cambios Track A (ClientTask nuevos campos)
2. Aplicar cambios Track B (Sprint nuevos campos)
3. Aplicar cambios Track C (WeeklyEntry/MonthlyEntry KPIs)
4. Verificar no hay duplicados ni conflictos de tipos
5. Compilar TypeScript para validar

---

## 🚫 RESTRICCIONES

- ❌ NO correr `pytest` ni tests masivos (riesgo OOM: los límites de la máquina, en `bash .claude/hooks/check-ram.sh --explain`)
- ❌ NO `npm install` sin verificar que el paquete no existe
- ✅ Verificar `npm run build` al terminar cada track
- ✅ Migraciones Django: aplicar con `python manage.py migrate` (bajo riesgo)
- ✅ Reload Gunicorn al terminar: `kill -HUP $(pgrep -f "gunicorn.*8001" | head -1)`

---

## ⏱️ ESTIMACIÓN DE TRACKS

| Track | Módulo | Complejidad | Archivos |
|-------|--------|-------------|----------|
| A | Portal Clientes | Alta | 8 |
| B | Sprints | Media | 6 |
| C | Vista Mes | Media | 8 |
| D | Email Marketing | Alta | 9 |
| E | Workouts + Recurrentes | Media | 8 |

---

_Generado por Tech Lead — 27 Feb 2026_
