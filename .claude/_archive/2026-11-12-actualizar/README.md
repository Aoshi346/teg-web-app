# Archivo — actualización al template (2026-11-12)

Plan: `.docs/plans/2026-11-12-actualizar-template/plan.md`. Decisión de Aoshi (D1): «quita todo lo
demás y mantén solamente el template». Nada se borró: todo está aquí con su estructura.

| Carpeta | Qué es |
|---|---|
| `divergente/` | Las 11 piezas del template que el proyecto tenía en versión del 21-09 con ajustes propios (rules, Vera/Ignacio/Lidia-«Daniela», capture-task, tasks_registry). Sustituidas por la versión del template |
| `retirado/skills/django-orm-optimization` | Skill que el template jubiló; la sustituye `skills/django-orm` |
| `local/agents/` | El orquestador de abril: `backend-worker`, `frontend-worker`, `test-worker`. Sustituidos por `desarrollador-backend`, `desarrollador-frontend` y la skill `escribir-tests` |
| `local/hooks/post-edit-lint.sh` | Lint tras cada edición del orquestador. Lo cubren `auto-format` y `pattern-check` del template |
| `local/state/` | Briefs y resultados de las tareas del orquestador (abril). Histórico |
| `subdirs/{backend,frontend}/` | Sus `.claude/` (deny-lists y las skills `add-page`, `add-component`, `add-api-call`, `add-evaluation`) y los `AGENT.md` de los workers |

Los antiguos `backend/CLAUDE.md` y `frontend/CLAUDE.md` NO están aquí: son documentación del dominio
(modelos, máquina de estados, roles, sistema de marca) y viven en `docs/backend.md` y `docs/frontend.md`.
