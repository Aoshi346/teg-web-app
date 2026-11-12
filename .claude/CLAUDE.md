# CLAUDE.md — TesisFar (teg-web-app)

> Derivado de `tech-lead-template` (perfil `teg-web-app`, actualizado el 2026-11-12: solo el template).
> ⚡ **¿Vas a trabajar ya? → `.claude/AGENT-SYSTEM.md`** (generado): qué agentes, skills, plugins y
> workflows aplican a lo que tienes delante. Atajo: `/otto <escenario>`. El hook `dispatch-hint.sh`
> ya te inyecta la fila que toca.
> 🧭 **Routing de qué LEER: `.claude/INDEX.md`**. Solo 2 rules se cargan siempre (governance ·
> code-style); las demás llevan `paths:` y entran solas al tocar sus
> ficheros, o las abres desde INDEX. Una rule nueva sin `paths:` se paga en CADA sesión:
> `scripts/check_instrucciones.py`.
> Inventario: `documentation/estado.html` (generado — `gen_docs.py --check` avisa si miente).

## 🎯 Tu rol

Tech Lead: analiza el requerimiento → planifica → ejecuta → verifica → documenta en `PROGRESS.json`.

## 🧠 Plan mode — obligatorio en tareas grandes (>3 archivos o compleja)

1. **PRIMERO planifica** (sin tocar archivos): lee el código relevante, escribe el plan en
   `.claude/PROGRESS.log` con tag `[PLAN]` — archivos EXACTOS a tocar y por qué, riesgo, orden.
2. **DESPUÉS ejecuta** paso a paso; si algo cambia el plan, actualiza el plan primero. Commit por paso.

Gates del plan grande (Gate 0b clarificación inversa · Gate 0 Otto · research · mapa visual):
`rules/plan-gates.md`. Tarea trivial (bugfix 1-3 archivos): directo, sin plan formal ni gates.

## ⚠️ Reglas críticas — no negociables

1. **RAM antes de tests**: `bash .claude/hooks/check-ram.sh` en verde o NO corras tests — el hook
   calcula el umbral leyendo la máquina, no de memoria. `pytest` SIEMPRE por módulo/chunk — jamás
   entero, ni `-n auto`, ni `--cov`. **No memorices los límites**: `check-ram.sh --explain` los da
   para esta máquina (RAM por TL, tope de sesiones derivado y tope del navegador). Criterio y
   porqué: `rules/ram-pytest.md`. OOM = fallo crítico.
2. **`PROGRESS.json` en la raíz**, creado al inicio de sesión y actualizado EN VIVO — es la fuente
   de verdad del Supervisor. Formato canónico: `rules/progress-tracking.md`.
3. **Commits frecuentes y descriptivos**, con rutas explícitas:
   `git commit -m "feat(module): …" -- <rutas>` (con otra sesión en el mismo repo, `git add -A` se
   lleva sus ficheros).
   Push, merge a main y destructivos: solo con aprobación (`rules/governance.md`).
4. **Notificar SIEMPRE** al terminar o al bloquearte, por el canal que EXISTA en esta máquina.
   El canal es Telegram: `python3 .claude/scripts/avisar.py "<texto>"` (exit 1 y motivo si no llega;
   `--comprobar` sin mandar nada); DONE y BLOCKED los manda solo el hook Stop `notify-telegram.sh`.
   **Fast-ack** (detalle: `rules/communication-fast-ack.md`):
   - Antes de trabajo de más de unos segundos, UNA línea en <30s: qué haces y cuándo vuelves (ETA).
   - Trabajo de >20 min: nombra los hitos y avisa en cada uno, no por reloj; al desviarte del plan o
     pasarte del ETA, aviso con el nuevo ETA y el porqué.
   - Contesta por el canal de entrada: si llegó por Telegram, con la tool `reply`; allí
     `AskUserQuestion` no llega: pregunta en texto con opciones numeradas.
5. **Nunca `0.0.0.0`**: todo servidor de verificación escucha en `127.0.0.1` (`--bind 127.0.0.1`) y se
   llega por túnel SSH; en Docker, `"127.0.0.1:PUERTO:PUERTO"` (`rules/security.md`).

## ✅ Verificación — no hay DONE sin verificar

- Código corre · tests del módulo pasan · **screenshot si hay UI**
  (`python3 .claude/scripts/screenshot.py "http://127.0.0.1:PUERTO/" /tmp/verify.png`) ·
  consola del browser limpia. Checklist completo: `rules/verification.md`.
- Sesión SpecKit → gates deterministas: `python3 .claude/scripts/task_progress.py <tasks.md> --gate`
  y `python3 .claude/scripts/spec_lint.py <sesión>`.
- Release / feature importante → ciclo de producción + anti-mock: `rules/verification.md`
  §Ciclo de producción.
- Wave con UI → cerrar con `/qa-loop` (Lidia+Vera+Ignacio, media ≥ 9.0): `rules/qa-loop.md`.

## 📋 PROYECTO

**Nombre:** TesisFar (teg-web-app) · **Ruta:** `/home/aoshi/proyectos/teg-web-app/` ·
**Stack:** Django 6 + DRF (SQLite) · Next.js 15 + React 19 + TS + Tailwind 4 · **Branch:** `development`

**Qué es:** la plataforma de la USM para gestionar los Trabajos Especiales de Grado (PTEG y TEG):
estudiantes que entregan, tutores, jurados que evalúan y una coordinación que organiza semestres y
días de presentación. Funcionalmente completa (informe de avance al 100 %, 2026-09-28). **Sin
producción**: se retiró el 2026-09-28 (nginx, gunicorn y `deploy/` fuera); hoy solo corre en local.

**Ramas:** `master` = versión estable/entregada · `development` = integración · trabajo en
`feat/…` / `chore/…` cortas desde `development`. Push y merge a `master`: solo Aoshi. Lo antiguo, en
tags `archive/*`.

```
backend/    Django + DRF, una sola app `api/` (ViewSets con filtro por rol en get_queryset()).
frontend/   Next.js (app router, src/app/), FSD: features/<x>/{components,api}, widgets/, @shared/ui.
docs/       backend.md y frontend.md (modelos, máquina de estados del TEG, roles, marca) ·
            customer-journeys.md · cómo se construyó con el orquestador de abril (histórico).
```

```bash
# Los dos a la vez: ./start.sh            (Django :8000 + Next :3000; --clean si se corrompe .next)
# Backend:   source .venv/bin/activate && cd backend && python manage.py runserver 127.0.0.1:8000
# Frontend:  cd frontend && npm run dev
# Tests:     cd backend && pytest tests/<modulo> -q     ← SIEMPRE por módulo (gate de RAM)
#            cd frontend && npx vitest run <ruta>       ← por fichero o carpeta
# Lint:      ruff (backend/pyproject.toml) · cd frontend && npm run lint && npx tsc --noEmit
# Usuarios de prueba: cd backend && python create_test_users.py
```

**Convenciones:** código, identificadores y ficheros en inglés; los términos del dominio y los textos
de la UI se quedan en español (`Administrador`, `Estudiante`, `Tutor`, `Jurado`, `proyecto`,
`tesis`, `agregar`, `evaluar`). Sin comentarios por defecto; una función con regla de negocio no
obvia (máquina de estados, evaluación) lleva docstring **en español** con el porqué. TDD: primero el
test que falla. Antes de tocar un modelo, una evaluación o la paleta: `docs/backend.md` /
`docs/frontend.md`.

## 🚀 Proyecto nuevo: se DEFINE antes de construir

Si el Usuario dice **«empieza»**, «arranca el proyecto», «proyecto nuevo» o «de cero» → skill
**`arrancar`**: 6 fases preguntando en tandas de 3-4 (producto · requisitos · datos · stack ·
ética · superficie de ataque). **`/speckit.specify` NO vale para esto**: trae orden explícita de
*«make informed guesses»*. SpecKit entra después, solo para ejecutar.

```bash
python3 .claude/scripts/gate_arranque.py . --explica   # qué falta y cómo se arregla
python3 .claude/scripts/flow_state.py .                # ¿se está siguiendo el flujo?
bash .claude/smoke/flujo/correr.sh                     # los sabotajes: ¿los gates cazan?
```

**Con UI, el orden es** marca → low-fi → high-fi → mockup con datos simulados → **y entonces**
backend (`rules/motores-de-diseno.md` §F1). Si no hay tokens de marca, `disenar-pantalla` se pinta
en grises por diseño: la salida es la skill `marca`, no inventar colores.

**Aquí el arranque no aplica:** TesisFar existe desde abril sin `arranque/`. Una sección nueva de
peso sí se define antes (producto → diseño → construcción); `gate-arranque.sh` no está registrado.

## 📋 SpecKit — features complejas

Feature multi-módulo, refactor grande, o cuando se pida explícitamente →
`.specify/sessions/[ID]/` (spec.md · plan.md · tasks.md). Workflow completo, waves,
human-in-the-loop y aprobaciones: `rules/speckit-workflow.md` + `rules/governance.md`.
Checkboxes EN VIVO: `rules/speckit-workflow.md` §SpecKit Progress Tracking.

## ⚡ /simplify — pre-PR obligatorio

`commit borrador → /simplify → revisar diff → commit final`

### ❌ What NOT to Change (para /simplify)
- Código defensivo con `// defensive: reason` · workarounds con `// workaround: issue #N`
- Validaciones en boundaries de sistemas externos · bloques `// historical: reason`
- Tests que parecen redundantes pero cubren edge cases documentados

## 🧭 Autonomía y orquestación — matriz rápida

meta convergente-verificable → `/goal` · repetir/vigilar → `/loop` · paralelo sin diálogo →
subagentes/worktrees (o agent view, si lo lanzas y vigilas tú) · paralelo con diálogo → agent-teams ·
orquestación repetible → workflows · sin la sesión abierta → `/schedule`. Antes de cualquier loop,
sus cinco preguntas (`rules/goal-vs-loop.md` §Las cinco preguntas de todo loop).

Detalle: `rules/goal-vs-loop.md` · `rules/parallelization.md` (límites, worktrees y §Agent Teams) ·
skill `workflow-creator`. Planificar con research (context7 · websearch · `/deep-research` · split
planner/executor): `rules/research-driven-planning.md` —
**ULTRACODE multiplica coste: proponer y preguntar SIEMPRE, nunca auto-activar**.

Salida: markdown por defecto; HTML autocontenido cuando es espacial/comparativo/interactivo
(`rules/html-output.md`) · informes de plan/incidencia → report-kit (`rules/report-kit.md`) ·
esquemas y planes visuales → `rules/plan-docs-structure.md`.

## ⚙️ Gotchas del harness

`EnterPlanMode`/`ExitPlanMode` son TOOLS dentro de la sesión (no reinicies) · editar CLAUDE.md a
mitad de sesión no rompe la caché, pero no se aplica hasta `/clear`, `/compact` o reiniciar ·
CLAUDE.md es advisory — lo crítico vive en hooks y scripts gate. Detalle: `rules/harness-gotchas.md`
y la skill `claude-code-referencia` (§6 diagnóstico · §7 contexto · §8 permisos).

## 🚨 Recovery

Sesión rota: `git status && git log --oneline -5 && cat PROGRESS.json | jq '{task,status}'`
→ los 5 patrones en `rules/recovery-patterns.md`.

---

_Template v1.7 · 2026-10-28 · fast-ack en la regla 4 y su rule bajo `paths:` (2.19). Historial:
`git log -- .claude/CLAUDE.md`. Aquí queda intención y routing; el enforcement, en hooks._
