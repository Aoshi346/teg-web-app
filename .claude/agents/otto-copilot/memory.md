# Memoria de Otto — copiloto · teg-web-app

> Última actualización: 2026-11-12 · v0 (escrita a mano al actualizar al template; sin sesiones de
> Otto todavía en este repo). Plan: `.docs/plans/2026-11-12-actualizar-template/plan.md`.

## Mapa de configuración del proyecto

| Clave | Valor |
|---|---|
| Naturaleza | Producto: TesisFar, gestión de PTEG/TEG de la USM (estudiantes, tutores, jurados, coordinación). Funcionalmente completo (informe de avance al 100 %, 2026-09-28). Sin producción desde el 2026-09-28 |
| Stack | Django 6 + DRF (una app `api/`, SQLite) · Next.js 15 + React 19 + TS + Tailwind 4 (FSD) |
| Arranque | `./start.sh` (Django :8000 + Next :3000) · `--clean` si `.next` se corrompe |
| Tests | `cd backend && pytest tests/<modulo> -q` (por módulo, gate de RAM) · `cd frontend && npx vitest run <ruta>` |
| Límites del servidor | no los memorices: `bash .claude/hooks/check-ram.sh --explain` |
| Ramas | `development` integración · `master` estable · `feat/…`/`chore/…` cortas · push y merge: Aoshi |
| Agentes | núcleo del template + `desarrollador-frontend` y `aitor-a11y-auditor` (perfil `teg-web-app`). Lidia se lanza con la persona Daniela (estudiante) |
| QA visual | `/qa-loop` (Lidia+Vera+Ignacio) · Aitor por la UI pública |
| Documentación del dominio | `docs/backend.md` (modelos, máquina de estados del TEG, roles) · `docs/frontend.md` (rutas, marca) · `docs/customer-journeys.md` |
| Histórico | el orquestador de abril (workers + briefs en `state/`) está en `.claude/_archive/2026-11-12-actualizar/`; no se usa |

## Lo que he aprendido de este proyecto

*(vacío: se rellena con lo que salga de las sesiones, no de leer el código)*
