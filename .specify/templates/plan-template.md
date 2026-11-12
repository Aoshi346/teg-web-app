# Plan Técnico: [NOMBRE DE LA SESIÓN]

**Fecha:** YYYY-MM-DD
**Estado:** READY_TO_IMPLEMENT
**Sesión:** [ID]

---

## Análisis

### [Problema/Feature 1]

**Causa raíz / Contexto:**
[Análisis técnico del problema o contexto de la feature]

**Solución propuesta:**
[Descripción de la solución técnica]

---

## Arquitectura de Implementación

### Principios
1. Paralelizar al máximo posible
2. Testing obligatorio antes de merge
3. Human-in-the-loop para commits críticos

---

## Estrategia de Paralelización

### Tech Leads Necesarios

| Tech Lead | Responsabilidad | Worktree | Branch |
|-----------|-----------------|----------|--------|
| TL-1 (Principal) | Coordinación + Wave 1 | - | develop |
| TL-2 | Wave 2 backend | worktrees/wave2-backend | feature/wave2-backend |
| TL-3 | Wave 2 frontend | worktrees/wave2-frontend | feature/wave2-frontend |

### Subagentes por Tech Lead

| Tech Lead | Subagentes | Propósito |
|-----------|------------|-----------|
| TL-1 | Architect, Tester | Diseño + validación |
| TL-2 | Backend Dev, DB Expert | Implementación + queries |
| TL-3 | Frontend Dev, UX Review | Componentes + accesibilidad |

### Herramientas por Tarea

| Tarea | Skills | MCPs | Plugins |
|-------|--------|------|---------|
| Backend API | django-orm | postgresql, context7 | - |
| Frontend UI | - | context7 | frontend-design |
| Tests E2E | deployment-testing | - | playwright |
| DB Migrations | django-orm | postgresql | - |

---

## Fases de Implementación

### Wave 1 — [Nombre] (Prioridad MÁXIMA)
**Objetivo:** [Objetivo de esta wave]
**Ejecuta:** TL-1 (sin worktree, en develop)
**Paralelizable internamente:** Sí/No

| ID | Qué | Archivos | Paralelizable | Subagente |
|----|-----|----------|---------------|-----------|
| XXX-01 | Descripción | `archivo1.py` | No | - |
| XXX-02 | Descripción | `archivo2.tsx` | Sí | Frontend Dev |

### Wave 2 — [Nombre]
**Objetivo:** [Objetivo]
**Ejecuta:** TL-2 + TL-3 en paralelo
**Worktrees:** 
- `worktrees/wave2-backend` → TL-2
- `worktrees/wave2-frontend` → TL-3

| ID | Qué | Archivos | Tech Lead | Worktree |
|----|-----|----------|-----------|----------|
| XXX-03 | Backend API | `views.py` | TL-2 | wave2-backend |
| XXX-04 | Frontend UI | `Component.tsx` | TL-3 | wave2-frontend |

---

## Testing Strategy

### Por Wave

| Wave | Tests Unitarios | Tests E2E | Playwright |
|------|-----------------|-----------|------------|
| Wave 1 | `pytest apps/module/ -v` | - | - |
| Wave 2 | `pytest apps/api/ -v` | `pytest tests/e2e/ -v` | `playwright test` |
| Final | Full suite | Full E2E | Full Playwright |

### Criterios de Merge

- [ ] Tests unitarios del módulo pasan
- [ ] Sin errores de TypeScript
- [ ] Build pasa (`npm run build`)
- [ ] Tests E2E pasan (si aplica)
- [ ] Playwright tests pasan (si frontend)

---

## Merge Protocol

### Pre-Merge Checklist (por worktree)

```
1. ✅ Todos los tests del worktree pasan
2. ✅ Build sin errores
3. ⏳ PEDIR CONFIRMACIÓN AL SUPERVISOR antes de merge
4. 🔄 Merge a develop
5. ✅ Tests completos en develop
6. ⏳ PEDIR CONFIRMACIÓN para borrar worktree
```

### Flujo de Aprobación

```
Tech Lead detecta: "Tests pasan, listo para merge"
        ↓
Tech Lead → Supervisor: "¿Puedo hacer merge de [worktree]?"
        ↓
Supervisor → Usuario: "Tech Lead quiere merge de [worktree]. ¿Apruebas?"
        ↓
Usuario: "Sí" / "No, primero revisar X"
        ↓
Supervisor → Tech Lead: "Aprobado, procede" / "Espera, revisar X"
```

---

## Riesgos

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Conflictos en merge | Media | Medio | Merges frecuentes, comunicación |
| Tests flaky | Baja | Alto | Retry, fix inmediato |
| OOM en tests | Media | Alto | Chunks pequeños, verificar RAM |

---

## Estimación

| Wave | Tech Leads | Tiempo estimado | Paralelo |
|------|------------|-----------------|----------|
| Wave 1 | 1 | ~2h | No |
| Wave 2 | 2 | ~3h | Sí (1.5h real) |
| Testing + Merge | 1 | ~1h | No |
| **Total** | - | **~4.5h** | - |
