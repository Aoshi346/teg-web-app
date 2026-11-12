# Plan — actualizar el harness de teg-web-app al template actual

> Fecha: 2026-11-12 · Origen: T-237 (sesión del template, rama `aoshi-develop`, CORE `8edf90a8a06e`)
> Estado: **APROBADO el 2026-11-12** (D1 «solo el template», D2 frontend + Aitor, D3 Lidia + persona Daniela).
> Pendiente de ejecutar. No se ha tocado nada del harness.

## 1. Dónde estamos (medido hoy)

| Dato | Valor |
|---|---|
| Harness actual | Instalado a mano el 2026-09-21: núcleo TL mínimo (gate de RAM, PROGRESS, registro de peticiones, Vera/Lidia-«Daniela»/Ignacio + `/qa-loop`, `django-orm-optimization`) **encima** del orquestador de abril (`backend-worker`, `frontend-worker`, `test-worker`, briefs en `.claude/state/`) |
| `template_diff.py` | CORE **INCOMPLETO/STALE** · `CORE_VERSION` ausente · 592 MISSING · 8 STALE · 11 DIVERGENTE · 4 LOCAL · 1 RETIRADO · `state/` sin inventariar |
| Simulacro `propagar.py` (perfil prestado de aquila-erp) | 694 ficheros en `.claude/` (39 skills, 11 agentes) + 128 de smoke + 11 de `.specify/` + 70 del corpus de diseño. 11 que no se pisan. CORE_VERSION no se escribiría hasta resolver 3 piezas CORE divergentes (`capture-task.sh`, `tasks_registry.py`, `verdict-contract.md`) |
| Perfil en `packs/CONFIGURACION.yaml` del template | **No existe** → `propagar.py` se niega sin él |
| Uso medido (transcripciones de esta máquina) | 14 sesiones (09-14 → 09-28), **0 subagentes, 0 skills** lanzados. El trabajo de abril (orquestador) se hizo con otra identidad git y sus transcripciones no están aquí: «0» es «0 observado» |
| Otros `.claude/` | `backend/.claude/` y `frontend/.claude/` (deny-lists, `state/`, y 4 skills de frontend: `add-page`, `add-component`, `add-api-call`, `add-evaluation`). `propagar.py` no los toca |
| Ramas | Reorganizadas el 11-12 (T-236): `master` = `development` = `6808d56`. El trabajo se hará en una rama `chore/actualizar-template` desde `development` |

## 2. Perfil propuesto (va al template, `packs/CONFIGURACION.yaml`)

```yaml
  teg-web-app:
    ruta: /home/aoshi/proyectos/teg-web-app
    stack: django-react          # Django 6 + DRF · Next.js 15 + React 19 + Tailwind 4
    bot: "no"
    packs: [nucleo]
    extra: [agents/desarrollador-frontend, agents/aitor-a11y-auditor]   # D2
    medido: >-
      TesisFar (gestión de TEG de la USM): estudiantes, tutores y jurados → datos personales
      (cédula), UI pública para usuarios no técnicos. Sin bot, sin RAG, sin multi-tenant.
      Uso (-home-aoshi-proyectos-teg-web-app*): 14 sesiones, 0 subagentes; el orquestador de abril
      usaba backend/frontend/test-worker (otra identidad git, sin transcripciones aquí).
      desarrollador-frontend sustituye a frontend-worker (era el worker principal); aitor por la UI
      pública. Prod retirada el 2026-09-28 (T-003).
```

`.claude/CONFIGURACION.yaml` del proyecto (nuevo):
`stack: django-react` · `agente_ia: no` · `rag: no` · `multi_tenant: no` ·
`datos_sensibles: datos-personales` · `ui: si-publica` · `observabilidad: ninguna` ·
`autonomia: semi-autonomous` · `git_commit: agente` · `git_merge: usuario` ·
`git_branching: develop` (la rama se llama `development`; se dice en la sección PROYECTO) ·
`auto_format: lineas-tocadas` · `nocturno: no` · **`capture_task: si`** (sin ella el registro de
peticiones se apaga en silencio).

## 3. Decisiones (Aoshi, 2026-11-12)

- **D1 — Solo el template.** «Quita todo lo demás y mantén solamente el template». El orquestador
  de abril y todo lo propio del harness se retira: `backend-worker`, `frontend-worker`, `test-worker`,
  `.claude/state/`, `hooks/post-edit-lint.sh`, lo propio de las 6 rules divergentes (NO se crean
  `*-teg-web-app.md`), y los `.claude/`, `CLAUDE.md` y `AGENT.md` de `backend/` y `frontend/`
  (deny-lists, `state/` y las skills `add-page`, `add-component`, `add-api-call`, `add-evaluation`).
  **Retirar = mover a `.claude/_archive/2026-11-12-actualizar/`** conservando la estructura, no borrar:
  queda la historia y `template_diff` lo ve como PODADO. Lo único propio que sobrevive es la sección
  PROYECTO del `CLAUDE.md` (stack, rama, comandos y convenciones de código condensadas).
- **D2 — Lentes:** `desarrollador-frontend` + `aitor-a11y-auditor`.
- **D3 — Daniela:** Lidia del template; Daniela (estudiante de la USM) como persona que se le pasa
  al lanzarla, anotada en `agents/lidia-naive-tester/memory.md` del proyecto.

## 4. Pasos

Se ejecuta desde la sesión del template, en un worktree de teg-web-app
(`git worktree add ../teg-web-app-wt/actualizar-template -b chore/actualizar-template development`).
Un commit por paso, con rutas explícitas.

1. **Perfil.** Añadir `teg-web-app` a `packs/CONFIGURACION.yaml` del template;
   `gen_packs.py --check` en verde. Commit en el template.
2. **Simulacro** `propagar.py <worktree>` con su perfil; revisar la lista contra §1 (no debe tocar
   LOCAL, `state/` ni `settings.json`).
3. **Aplicar** `propagar.py <worktree> --aplica`. Commit `chore(harness): propaga el núcleo del template`.
4. **Divergentes (11): todas a la versión del template.** Antes de pisar, `diff` contra la
   versión del template del 09-21 y copia de lo propio al archivo (`_archive/.../divergente/`), por si
   algo resulta ser un arreglo. Daniela según D3.
5. **Retirar lo que no es template** (D1), todo a `_archive/2026-11-12-actualizar/` con estructura:
   - `retirado/skills/django-orm-optimization` (la sustituye `skills/django-orm`, del núcleo).
   - `local/agents/{backend,frontend,test}-worker.md`, `local/hooks/post-edit-lint.sh`
     (y su registro en `settings.json`), `local/state/`.
   - `subdirs/backend/` y `subdirs/frontend/`: sus `.claude/`, `CLAUDE.md` y `AGENT.md`, con `git mv`.
     Antes, extraer las convenciones de stack que sigan valiendo (estructura de carpetas, cómo
     correr los tests, librerías) para la sección PROYECTO del paso 6.
6. **`CLAUDE.md`.** El del template + sección PROYECTO (nombre, ruta, stack, rama `development`,
   comandos: `./start.sh`, `pytest backend/<app>/`, `npm run test` en frontend). Lo que vale de
   «Repository Layout», «Coding Conventions» y de los `CLAUDE.md` de `backend/` y `frontend/` se
   condensa en PROYECTO; el resto del `CLAUDE.md` actual (orquestador) se archiva.
7. **Configuración.** `.claude/CONFIGURACION.yaml` (§2) · `settings.json`: `ensure_hooks.py` +
   lo que no cubre (checklist del sync 3: hooks nuevos, SessionEnd, `agent-registry-log` en
   PostToolUse sin duplicar en SubagentStop, timeouts en segundos, `AGENT_TEAMS=0`, sin
   `defaultMode`), conservando su deny-list y el arreglo `Write()` de `78a4265` (permisos: van en el
   `settings.json` de la raíz, que es el único que queda), sin `post-edit-lint.sh` · `.gitignore`:
   `.claude/PROGRESS.auto.log`, `.claude/.incoming-config*`, `__pycache__/` · `INDEX.md`,
   `gen_agent_system.py`, `gen_skill_index.py`, `gen_agent_index.py` · memorias con
   `sembrar_v0.py <worktree> --template <tpl> --app teg-web-app` (la de otto-copilot, a mano).
8. **Verificar** (sin DONE sin esto):
   - `template_diff.py` → CORE completo; entonces `echo 8edf90a8a06e > .claude/CORE_VERSION`.
   - `check_mechanisms.py` y `scripts/check_instrucciones.py` del proyecto en verde.
   - Después del commit, nunca antes (checklist punto 7): `claude -p "/context"` en el worktree →
     contexto al arrancar del orden del template (~30k), solo las rules ambientales cargadas.
   - Arranque sin errores de hooks (`SessionStart`, `UserPromptSubmit` registra en `pending-tasks.md`).
   - No se toca código de la app: `git diff development --stat -- backend/ frontend/` solo muestra
     los `.claude/`, `CLAUDE.md` y `AGENT.md` movidos al archivo.
   - `template_diff.py` sin LOCAL ni DIVERGENTE (salvo lo que el propio template marque).
9. **Cierre.** `READY_MERGE` → con tu OK, merge de `chore/actualizar-template` en `development`;
   el push lo lanzas tú. Borrar el worktree solo con tu OK.

## 5. Riesgos

| Riesgo | Mitigación |
|---|---|
| Se pierde lo propio de una rule o un agente al tomar la versión del template | Todo lo propio se archiva, no se borra; `diff` antes de pisar cada divergente |
| Se pierde una convención de stack útil al retirar los `CLAUDE.md` de `backend/` y `frontend/` | Se condensa en PROYECTO antes de moverlos |
| Contexto al arrancar inflado | Verificación de `/context` del paso 8 |
| Ficheros de hooks colados en el commit (`.incoming-config*`) | `.gitignore` antes del primer `claude -p` |

## 6. Fuera de este plan

Retomar el desarrollo de la app y la vuelta a producción.
