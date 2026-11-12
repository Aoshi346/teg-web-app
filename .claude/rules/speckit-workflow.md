---
paths:
  - ".specify/**"
  - ".claude/commands/speckit.*"
  - ".specify/sessions/*/tasks.md"
  - ".claude/scripts/task_progress.py"
  - ".docs/plans/*/dashboard.md"
  - ".docs/plans/*/tasks.md"
---
# SpecKit Workflow Rule

> **Cuándo aplicar:** 
> - Features complejas, refactors grandes, múltiples módulos afectados
> - **Cuando se especifique explícitamente usar SpecKit**
> - Mientras trabajas en una sesión SpecKit: los checkboxes de `tasks.md` se marcan **en vivo**
>   (§SpecKit Progress Tracking)
> - Una vez por trabajo grande, al decidir **qué se crea**: ¿sesión SpecKit, informe report-kit, los
>   dos o ninguno? (§SpecKit e informe)
>
> **NO aplicar:** Fixes pequeños, cambios triviales (salvo que se indique lo contrario).
>
> **Relacionado:** [`governance.md`](./governance.md) define **cuándo** usar SpecKit vs cambio directo, los **approval gates** (qué requiere aprobación del Supervisor/Usuario) y los **3 niveles de autonomía** (Supervised / Semi-autonomous / Autonomous). `report-kit.md` (el CÓMO del informe) · `plan-gates.md` · `plan-docs-structure.md`.
>
> **Fusionada el 2026-10-20 (LI-29, sub-ola 1.06).** Aquí viven ahora las antiguas
> `speckit-progress-tracking.md` (§SpecKit Progress Tracking; su aviso se retiró el 2026-10-22) y
> `speckit-vs-informe.md` (§SpecKit e informe). El porqué y lo que no se trasladó: `_archive/2026-10-19/README.md` §Sub-ola 1.06.

---

## 📁 Estructura SpecKit

```
.specify/
├── memory/
│   └── constitution.md    # Principios globales (NO CAMBIA)
└── sessions/
    └── [ID] - [Nombre]/
        ├── spec.md        # Qué hacer
        ├── plan.md        # Cómo hacerlo + paralelización
        └── tasks.md       # Checkboxes con puntos de aprobación
```

**IDs:** `[PREFIJO]-N` → BM-1, ELV-2, TP-1

---

## 📊 Tracking de Progreso

| Archivo | Qué contiene | Cuándo actualizar |
|---------|--------------|-------------------|
| `tasks.md` (en session) | Checkboxes de tareas | Al completar cada tarea |
| `.claude/PROGRESS.log` | Log con timestamps | Cada acción significativa |
| `.claude/CHECKLIST.md` | Tareas sin SpecKit | Solo cuando NO hay sesión activa |

**Con SpecKit:** Progreso en `tasks.md`, actividad en `PROGRESS.log`
**Sin SpecKit:** Progreso en `CHECKLIST.md`, actividad en `PROGRESS.log`

### 📊 Dashboard HTML del plan (recomendado)

Al crear un plan, genera **también** el **informe interactivo** para revisarlo bien y **tomar
decisiones** que persistan. El sistema es el **report-kit** (`rules/report-kit.md`): el `tasks.md`
de la sesión se convierte en `report.json` con `tasks_to_items.py`, `build.py` materializa las
páginas y `server.py` guarda cada decisión en disco.

```bash
K=.claude/templates/report_kit ; PLAN=.docs/plans/<fecha>-<slug>
cp "<sesión>/tasks.md" "$PLAN/tasks.md" && python3 $K/tasks_to_items.py "$PLAN" --profile proyecto
python3 $K/build.py "$PLAN"
```

El `tasks.md` de la sesión es la **única fuente de verdad**: se copia en el mismo comando que genera,
nunca por separado, o el informe enseña una wave abierta que ya estaba cerrada
(§I3, abajo). La antigua skill `/plan-dashboard` se archivó el 2026-08-22 y
`speckit_dashboard/`, el 2026-10-19 (`_archive/2026-10-19/templates/`).

---

## 🔄 Workflow Completo

```
1. SETUP
   ├── Leer .specify/memory/constitution.md
   ├── Crear session: .claude/scripts/new-session.sh PREFIX "Nombre"
   └── Verificar RAM: bash .claude/hooks/check-ram.sh (en verde, o no se lanza)

2. PLANIFICACIÓN (crear en session/)
   ├── spec.md → Requisitos, scope, constraints
   │     Si el proyecto pasó por /arrancar, NO se reescribe: se DERIVA de sus requisitos
   │       python3 .claude/scripts/requisitos_to_spec.py <plan> <sesión> --check   # qué saldría
   │       python3 .claude/scripts/requisitos_to_spec.py <plan> <sesión>           # escribe spec.md
   │     (spec_lint.py pasa por construcción: verbo normativo y Gherkin ya vienen de la fase 1b)
   ├── plan.md → Diseño técnico + ESTRATEGIA DE PARALELIZACIÓN
   └── tasks.md → Checkboxes con puntos de aprobación

3. COMUNICAR PARALELIZACIÓN AL SUPERVISOR
   ├── Notificar: cuántos Tech Leads, qué worktrees, qué tareas cada uno
   ├── Esperar confirmación antes de crear worktrees
   └── Documentar en plan.md la estructura

4. CREAR WORKTREES (si aprobado)
   # ⚠️ 2026-08-27: las ramas `feature/*` de este flujo son SIEMPRE ramas DE WORKTREE.
   #    En el caso normal —un solo frente— se commitea directamente en `develop` y no se abre
   #    ninguna rama (`code-style.md` §Branches, decisión del Usuario). El worktree, con su
   #    rama, es la respuesta a DOS FRENTES SIMULTÁNEOS, no el paso previo a trabajar.
   # ⚠️ 2026-09-11: esta rule decía `git worktree add` a pelo y CONTRADECÍA a la skill de
   #    worktrees de entonces (hoy `parallelization.md` §3). El flag nativo hace las dos cosas que el modo manual NO hace:
   #    procesa `.worktreeinclude` (se lleva el `.env`, que está gitignorado y por tanto NO
   #    viaja solo) y crea el worktree DENTRO del repo, donde alcanza el allow de permisos.
   #    Con `git worktree add`, el worker nace sin credenciales y lo descubre a mitad de su
   #    primera tarea. El modo manual queda solo para una rama existente concreta (`parallelization.md` §3).
   ├── claude --worktree [nombre]        # → .claude/worktrees/[nombre]/ + rama worktree-[nombre]
   ├── cp .claude/PROGRESS.log .claude/worktrees/[nombre]/.claude/
   ├── ⚠️ AISLAR LOS DATOS, no solo los ficheros: base, puertos y COMPOSE_PROJECT_NAME
   │     propios por frente → `rules/parallelization.md` §Worktrees. Saltárselo hace que
   │     dos frentes escriban en la MISMA base sin que nada avise.
   └── Notificar al Supervisor qué worktrees se crearon

5. IMPLEMENTACIÓN (por waves)
   ├── Ejecutar tareas según tasks.md
   ├── Marcar checkboxes al completar
   ├── Tests unitarios por módulo
   └── Actualizar PROGRESS.log

6. TESTING
   ├── Unit tests: pytest apps/[module]/ -v
   ├── E2E tests: pytest tests/e2e/ -v (si existe)
   ├── Playwright: npx playwright test (si frontend)
   └── Build: npm run build

7. MERGE (⏳ requiere aprobación)
   ├── → NOTIFICAR AL SUPERVISOR: "READY_MERGE: [worktree] tests OK"
   ├── ESPERAR confirmación
   ├── git merge feature/[branch]
   ├── Tests post-merge (unit + E2E + Playwright)
   └── → NOTIFICAR resultado

8. COMMIT (autónomo, governance.md §2) · PUSH (⏳ requiere aprobación)
   ├── git commit -m "feat([módulo]): descripción"   # a la rama de trabajo, sin preguntar
   ├── → PEDIR CONFIRMACIÓN para el push (READY_COMMIT)
   ├── ESPERAR aprobación
   └── git push

9. CLEANUP (⏳ requiere aprobación)
   ├── → PEDIR CONFIRMACIÓN para borrar worktrees
   ├── git worktree remove worktrees/[nombre]
   └── Consolidar PROGRESS.log
```

---

## 🎯 PARA EL SUPERVISOR - QUÉ MONITOREAR

### Al Iniciar Sesión SpecKit

1. **Verificar plan.md tiene estrategia de paralelización:**
   ```bash
   cat .specify/sessions/[ID]*/plan.md | grep -A20 "Paralelización"
   ```

2. **Aprobar/ajustar** número de Tech Leads y worktrees antes de crear

### Durante Implementación (cada 15 min)

1. **Ver progreso en tasks.md:**
   ```bash
   grep -E "^\- \[.\]" .specify/sessions/[ID]*/tasks.md | head -30
   ```

2. **Ver worktrees creados:**
   ```bash
   git worktree list
   ls -la worktrees/
   ```

3. **Ver progreso en cada worktree:**
   ```bash
   for wt in worktrees/*/; do
     echo "=== $wt ==="
     tail -10 "$wt/.claude/PROGRESS.log" 2>/dev/null
   done
   ```

4. **Ver Tech Leads activos:**
   ```bash
   ps aux | grep claude | grep -v grep
   tmux list-sessions
   ```

5. **Si Tech Lead para antes de completar TODO:**
   - Verificar tasks.md - ¿hay checkboxes sin marcar?
   - Si sí → Relanzar automáticamente para continuar

### Pre-Merge Checklist (verificar antes de aprobar)

- [ ] Todos los checkboxes de la wave están marcados en tasks.md
- [ ] PROGRESS.log tiene registro de cambios
- [ ] Tests del worktree pasaron (según log del Tech Lead)
- [ ] Build pasó

### Post-Merge Checklist

- [ ] Tests completos en develop pasan
- [ ] E2E tests pasan (si existen)
- [ ] Playwright tests pasan (si frontend)
- [ ] Build final OK

### Pre-Commit Checklist

- [ ] TODOS los tests pasan
- [ ] El Usuario aprobó
- [ ] Mensaje de commit es descriptivo

### Post-Cleanup

- [ ] Worktrees borrados
- [ ] PROGRESS.log consolidado
- [ ] Sesión marcada como DONE en tasks.md

---

## 📋 PLAN.MD - Sección Paralelización (OBLIGATORIA)

Todo plan.md DEBE incluir esta sección:

```markdown
## Estrategia de Paralelización

### Tech Leads Necesarios

| TL | Responsabilidad | Worktree | Branch | RAM Est. |
|----|-----------------|----------|--------|----------|
| TL-1 | Wave 1 + coordinación | - | develop | 1 sesión |
| TL-2 | Wave 2 backend | worktrees/w2-backend | feature/w2-backend | 1 sesión |
| TL-3 | Wave 2 frontend | worktrees/w2-frontend | feature/w2-frontend | 1 sesión |

### Subagentes por Tech Lead

| TL | Subagentes | Skills/MCPs |
|----|------------|-------------|
| TL-1 | Architect | context7 |
| TL-2 | Backend Dev | django-orm, postgresql |
| TL-3 | Frontend Dev | context7 |

### Worktrees a Crear

| Worktree | Branch | Tech Lead | Tareas |
|----------|--------|-----------|--------|
| worktrees/w2-backend | feature/w2-backend | TL-2 | API endpoints |
| worktrees/w2-frontend | feature/w2-frontend | TL-3 | Componentes UI |

### Orden de Merge

1. TL-2 (backend) → develop (primero, sin dependencias)
2. TL-3 (frontend) → develop (después, puede depender de backend)
```

---

## 📋 TASKS.MD - Puntos de Comunicación (OBLIGATORIO)

Tasks.md DEBE incluir estos puntos de comunicación con el Supervisor:

```markdown
### Setup
- [ ] **→ NOTIFICAR AL SUPERVISOR:** Plan de paralelización listo, [N] Tech Leads, [M] worktrees
- [ ] **⏳ ESPERAR APROBACIÓN** antes de crear worktrees

### Por cada Wave
- [ ] **→ NOTIFICAR AL SUPERVISOR:** "Wave [N] iniciada"
- [ ] ... tareas ...
- [ ] **→ NOTIFICAR AL SUPERVISOR:** "Wave [N] DONE, tests OK"

### Pre-Merge (por worktree)
- [ ] **→ NOTIFICAR AL SUPERVISOR:** "READY_MERGE: [worktree]"
- [ ] **⏳ ESPERAR APROBACIÓN**
- [ ] Merge
- [ ] Tests post-merge
- [ ] **→ NOTIFICAR AL SUPERVISOR:** "Merge [worktree] OK"

### Pre-Commit
- [ ] Commit a la rama de trabajo (autónomo, `governance.md` §2)
- [ ] **→ NOTIFICAR AL SUPERVISOR:** "READY_COMMIT: todos los tests OK" (para el push)
- [ ] **⏳ ESPERAR APROBACIÓN** del push
- [ ] Push
- [ ] **→ NOTIFICAR AL SUPERVISOR:** "Push realizado"

### Cleanup
- [ ] **→ NOTIFICAR AL SUPERVISOR:** "¿Borrar worktrees mergeados?"
- [ ] **⏳ ESPERAR APROBACIÓN**
- [ ] Borrar worktrees
- [ ] **→ NOTIFICAR AL SUPERVISOR:** "Cleanup completo, sesión DONE"
```

---

## 👤 Human-in-the-Loop (OBLIGATORIO)

| Acción | Notificar | Esperar | Quién aprueba |
|--------|-----------|---------|---------------|
| Crear worktrees | Supervisor | ✅ Sí | Supervisor |
| Instalar dependencias **de sistema** (`apt`, `brew`) | Supervisor | ✅ Sí | Supervisor |
| Merge worktree | Supervisor | ✅ Sí | Supervisor |
| Push · merge a `main` | Supervisor → Usuario | ✅ Sí | Usuario |
| Borrar worktrees | Supervisor | ✅ Sí | Supervisor |
| Migraciones **destructivas** (`DROP`, `DELETE` masivo) | Supervisor → Usuario | ✅ Sí | Usuario |

### Cómo Notificar

```bash
python3 .claude/scripts/avisar.py "[PROYECTO] [ESTADO]: [mensaje]"   # Telegram; exit 1 y motivo si no llega
```

**Estados:** `READY_MERGE` | `READY_COMMIT` | `BLOCKED` | `DONE` | `QUESTION` | `ERROR`

---

## 🧪 Testing Protocol

### Instalación Playwright (si frontend)

```bash
# 1. Pedir confirmación
python3 .claude/scripts/avisar.py "[PROYECTO] QUESTION: ¿Instalo playwright?"

# 2. Esperar aprobación

# 3. Instalar
pip install playwright
playwright install chromium
```

### Tests por Fase

| Fase | Tests | Comando |
|------|-------|---------|
| Por módulo | Unit | `pytest apps/[mod]/ -v` |
| Pre-merge | Unit del worktree | `pytest apps/[mod]/ -v` |
| Post-merge | Unit completos | `pytest apps/ -v --ignore=tests/e2e/` |
| Post-merge | E2E | `pytest tests/e2e/ -v` |
| Post-merge | Playwright | `npx playwright test` |
| Pre-commit | TODO | Todos los anteriores |

---

## ⚠️ Límites del Sistema

| Recurso | Límite |
|---------|--------|
| Tech Leads simultáneos | derivado de la RAM libre — `check-ram.sh --explain` |
| RAM por Tech Lead | la «RAM por sesión» de `check-ram.sh --explain` |
| RAM libre mínima | la calcula `check-ram.sh --explain` — no se escribe aquí |
| Workers pytest | los de `check-ram.sh --explain` |

### Verificar Antes de Lanzar

```bash
bash .claude/hooks/check-ram.sh --explain   # umbral, tope de sesiones y cuántas hay
# (NO cuentes con `ps aux | grep claude | wc -l`: engloba el daemon y los bg-* — ram-pytest.md)
```

La columna «RAM Est.» de la plantilla de `plan.md` de arriba cuenta **sesiones**, no gigas: cuánta RAM
es una sesión lo dice `--explain`. Hasta el 2026-10-20 la plantilla y esta tabla escribían cada una su
cifra y se contradecían (LI-29); desde la sub-ola 2.04 ninguna escribe cifras (MO-44).

---

## 🤖 AUTONOMÍA DEL TECH LEAD

### DEBE hacer sin preguntar:
- ✅ Ejecutar migraciones de base de datos
- ✅ Instalar dependencias de proyecto (pip, poetry, npm, yarn)
- ✅ Crear archivos/componentes nuevos
- ✅ Refactorizar código
- ✅ Escribir tests
- ✅ Arreglar errores que encuentre

### PREGUNTAR antes de:
- ⏳ Instalar paquetes de sistema (apt, brew, etc.) → Pedir al Supervisor
- ⏳ Crear worktrees (plan de paralelización)
- ⏳ Merge a develop/main
- ⏳ Push (el commit a la rama de trabajo no se pregunta: `governance.md` §2)
- ⏳ Borrar worktrees

### Diferencia clave:
| Tipo | Ejemplo | Acción |
|------|---------|--------|
| Deps proyecto | `pip install`, `npm i`, `poetry add` | ✅ Hazlo |
| Deps sistema | `apt install`, `brew install` | ⏳ Pedir permiso |

### NUNCA diferir items por:
- ❌ "Requiere migración" → HAZLA
- ❌ "Es complejo" → HAZLO
- ❌ "No existe el modelo" → CRÉALO
- ❌ "Necesita más diseño" → DISEÑA Y HAZLO

### SOLO diferir si:
- 🔴 Depende de decisión de negocio del Usuario (pricing, features, UX crítico)
- 🔴 Depende de servicio externo no disponible
- 🔴 Explícitamente marcado como "Wave 8 - diferido" en el spec

**REGLA:** Si está en el spec/tasks.md y es técnicamente posible → **HAZLO**

---

## SpecKit Progress Tracking — Regla CRÍTICA

*Antes `rules/speckit-progress-tracking.md` (su aviso se retiró el 2026-10-22 a
`_archive/2026-10-20/rules/`).*

> **Regla inmutable**: cuando estás trabajando en una sesión SpecKit
> (`.specify/sessions/[ID]*/tasks.md`), **DEBES** marcar cada checkbox
> **inmediatamente** al completar el item correspondiente.

> **Contradicción resuelta el 2026-10-21 (sub-ola 2.16):** la fusión de la 1.06 dejó a la vista que esta
> sección pide un commit por item y el workflow de arriba (paso 8, la tabla de Human-in-the-Loop y
> §Autonomía) pedía aprobación para commitear. Ahora el commit sigue a `governance.md` §2: commitear
> a la rama de trabajo es autónomo; el **push** pide aprobación por la regla 3 de `CLAUDE.md` y
> `code-style.md` §Branches (`governance.md` §2 solo nombra el force-push), y merge a `main`,
> dependencias de sistema, migraciones destructivas y borrar worktrees, por `governance.md` §2.
> Dos gates son **propios de SpecKit** y más estrictos que `governance.md`: crear worktrees y el
> merge de un worktree a `develop` se notifican y esperan al Supervisor (pasos 3-4 y 7).

### Por qué importa

Sin tracking en vivo:
- Supervisor (supervisor) pierde visibilidad de progreso
- Usuario no sabe si una wave está al 20% o al 90%
- Cuando retomes la sesión en otro contexto (compacted conversation, new session), no sabrás dónde lo dejaste
- Las reglas de Human-in-the-Loop (§👤 Human-in-the-Loop, arriba) no pueden dispararse si el estado de las tasks está desactualizado

**Lección aprendida**: ejecutar varias waves sin marcar tasks en vivo lleva a reconstruir el estado leyendo commits cuando la conversación se compacta. Esto **no debe volver a pasar**.

### Cuándo marcar

#### Marca `[x]` en el MOMENTO en que:

- Haces un `Edit`/`Write` que resuelve el item
- Ejecutas el test de aceptación del item y pasa
- Haces el commit local del item

**NO esperes a:**
- Agrupar varios items (fractura el feed de progreso)
- Terminar la wave (Supervisor pierde visibilidad)
- Final del día (riesgo de compaction)

#### Marca `[>]` cuando:

Empiezas a trabajar en un item pero aún no lo terminas (útil cuando un item lleva > 15 min).

#### Marca `[!]` cuando:

El item está bloqueado por decisión externa (Usuario, deps, servidor). **Añade inline la razón**:

```markdown
- [!] H4 — Añadir 2 testimoniales reales  <!-- blocked: espero casos reales del Usuario, ETA 2026-04-25 -->
```

### Cómo marcar

Usa el tool `Edit` con `replace_all: false`, buscando el checkbox exacto por contexto. Ejemplo:

```
old_string: "- [ ] Editar `src/sections/Hero.jsx` — añadir overline"
new_string: "- [x] Editar `src/sections/Hero.jsx` — añadir overline"
```

O si hay varios items idénticos en el archivo, incluye 1-2 líneas antes para hacerlo único.

### Integración con TaskCreate/TaskUpdate

Los tasks del runtime (`TaskCreate`/`TaskUpdate`/`TaskList`) y los checkboxes de `tasks.md` son **capas diferentes**:

- **Runtime tasks**: granulares, ephemeral (persisten solo en la conversación actual)
- **tasks.md**: canónico, persistente, es la fuente de verdad

Regla: cuando un runtime task se marca `completed`, marca **también** el checkbox equivalente en `tasks.md` si existe.

### Verificación al terminar cada wave — GATE ARITMÉTICO (SPEC-1, aprobado 2026-08-07)

El conteo ya NO es disciplina, es mecanismo. Antes de notificar "Wave N DONE":

```bash
python3 .claude/scripts/task_progress.py "/ruta/a/tasks.md" --gate --wave "Wave N"
# exit 1 = quedan [ ]/[>] en esa wave → NO se cierra (lista los pendientes con línea exacta)
# [!] bloqueadas no impiden el gate, pero exigen su razón inline documentada
```

Sin `--wave` audita el fichero entero; acepta directorios (busca todos los tasks.md); `--json`
para consumo de otro agente. Cuenta también las **subtareas indentadas** — la lección de OpenSpec:
anclar la regex en columna 0 hacía invisibles las subtareas y se archivaba incompleto sin aviso.

Si el gate falla → marca o reabre. El grep a mano queda obsoleto.

**Hook `TaskCompleted` (sub-ola 2.11, CL-39):** `hooks/task-completed-gate.sh` corre este mismo gate al
cerrar una tarea de la lista de tareas de la sesión cuyo asunto empiece por `Wave N` (`TaskCreate` con
`subject: "Wave 3 …"`): con casillas abiertas en esa wave del `tasks.md` más reciente de
`.specify/sessions/` que tenga esa wave (la raíz es `CLAUDE_PROJECT_DIR`, no el `cwd` del evento), sale con 2 y la tarea no se cierra. Una tarea que no se llame «Wave N» pasa sin
mirar. Es un freno de la lista de tareas, no sustituye al gate de arriba: `onFailure: "block"` no aplica a
`TaskCompleted`, así que si el script se rompe, la tarea se cierra (límites en la cabecera de
`scripts/eventos_harness.py`).

### El caso medido — y por qué es un problema de CAPA, no de disciplina (2026-08-25)

En una sesión con **4 frentes trabajando en paralelo** sobre un `tasks.md` de 61 items, el recuento
era: **50 en `[ ]`, 0 en `[>]`**. El anti-patrón nº1 de esta sección, exactamente. Y lo detectó **el
Usuario preguntando** —«¿se están siguiendo todos los pasos?»—, no el sistema.

Lo que se habría perdido si la sesión se rompe en ese momento: **qué estaba a medias**. Los cuatro
frentes tenían trabajo abierto y ninguno figuraba como abierto en ninguna parte. La reconstrucción
habría sido leer commits, que es justo el trabajo que esta sección existe para no tener que hacer.

**El diagnóstico honesto es de `rules/layer-decision.md` pregunta 1:** la norma está escrita, es
correcta, lleva meses escrita, y se ignoró igual. Subir el tono no arregla nada — `CLAUDE.md` y las
rules son *advisory* por definición. Lo que corresponde es **bajar de capa**.

El gate ya existe y es aritmético, así que la comprobación es de una línea:

```bash
# ¿hay trabajo en curso que no figura como en curso?
python3 .claude/scripts/task_progress.py "<sesión>/tasks.md" --json \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print(d)"   # mira doing == 0
```

**Regla práctica mientras no sea hook:** si hay **más de un frente vivo**, tiene que haber **al
menos un item en `[>]`**. Cero items en curso con varios agentes trabajando no es un estado
posible: es un recuento que miente.

> **Lo que falta, dicho como propuesta y no como hecho.** El sitio natural es un **Stop hook** que
> se niegue a cerrar el turno cuando hay subagentes vivos y ningún item en `[>]`
> (`rules/verification.md` §nivel 3). No está instalado: registrarlo toca `settings.json` y eso
> requiere aprobación del Usuario (`rules/governance.md` §2). Y llevaría su aviso escrito —el
> harness **anula un Stop hook tras 8 bloqueos consecutivos** sin tools entre medias; el matiz, en
> `verification.md` nivel 3—, así que el mensaje de bloqueo
> tendría que decir exactamente qué marcar y cómo. Hasta entonces esto es disciplina, y la
> disciplina falló una vez ya medida.

### Anti-patrones (NO HAGAS)

1. **Marcar todo al final**: "voy a hacer los 8 items y luego marco todo" → violación.
2. **Marcar antes de hacer**: optimista pre-check que luego no se ejecuta.
3. **Saltar el test de aceptación**: un item "hecho" sin su test verde no es `[x]`, es `[>]`.
4. **Omitir commit por item**: cada checkbox debería tener su commit o estar claramente agrupado.
5. **Varios frentes vivos y CERO items en `[>]`**: no es que nadie haya empezado — es que nadie
   está marcando. Medido: 4 frentes, 50 items en `[ ]`, 0 en `[>]`.
6. **No actualizar estado de frontmatter**: `spec.md`/`plan.md`/`tasks.md` deberían reflejar `in_progress` → `done` en el metadata.

### Checklist rápido por sesión

Al iniciar sesión SpecKit:

1. [ ] Leer `.specify/memory/constitution.md`
2. [ ] Leer `spec.md` + `plan.md` + `tasks.md` de la sesión activa
3. [ ] Identificar próximo item `[ ]` (ID ascendente)
4. [ ] Marcarlo `[>]` antes de empezar
5. [ ] Trabajar en él
6. [ ] Ejecutar su test de aceptación
7. [ ] Si test verde + commit → marcar `[x]`
8. [ ] Si test rojo → mantener `[>]` + diagnosticar
9. [ ] Si bloqueado → marcar `[!]` + explicar
10. [ ] Repetir desde 3

---

## SpecKit e informe — qué artefactos genera este trabajo (y cuándo los dos)

*Antes `rules/speckit-vs-informe.md`.* **Cuándo:** una vez por trabajo grande, al decidir **qué se
crea**: ¿una sesión SpecKit en `.specify/sessions/`, un informe report-kit en `.docs/plans/`, los
dos, o ninguno? Es la pregunta que se hace justo después de saber que la tarea es grande, y hasta
ahora no la respondía nadie: `governance.md` §1 dice **cuándo un trabajo de construcción merece
SpecKit**, `report-kit.md` dice **cómo** se entrega un informe, y la relación entre los dos se
re-deducía en cada plan. **No:** para decidir si algo es "tarea grande" (eso es tamaño →
`plan-gates.md` §1) · para el CÓMO del SpecKit (waves, gates, human-in-the-loop → el resto de esta
rule) · para el CÓMO del informe (schema, páginas, persistencia de decisiones → `report-kit.md`) ·
para tareas triviales, que no generan ninguno de los dos. **Relacionado:** `plan-docs-structure.md`
(dónde vive cada carpeta) · §SpecKit Progress Tracking (los checkboxes que alimentan el puente).

### I1. Son dos ejes, no dos formatos del mismo documento

| | **SpecKit** (`.specify/sessions/<ID>/`) | **Informe report-kit** (`.docs/plans/<fecha>-<slug>/`) |
|---|---|---|
| Responde a | **¿en qué orden lo construimos?** | **¿esto se hace, y quién lo decide?** |
| Es un plan de | **EJECUCIÓN** | **DECISIÓN** y comunicación |
| Su unidad | la tarea con checkbox, dentro de una wave | el item con `decision` + `note` del Usuario |
| Su lector | quien ejecuta (el TL, el `/loop`) | quien decide (el Usuario) y quien tiene que entender |
| Su salida | código mergeado y gates en verde | decisiones que **persisten** y se exportan |
| Se cierra cuando | la última wave pasa `task_progress.py --gate` | no quedan items sin decidir (`meta.closed_at`) |

**La confusión nace de que los dos tienen un `tasks.md` con checkboxes, y no es el mismo fichero.**
En SpecKit el checkbox es *progreso de ejecución* (` `→`>`→`x`, en vivo). En el informe el checkbox
solo siembra el `status` inicial del item: lo que importa ahí es el campo `decision`, que escribe el
Usuario y ningún agente toca. Vocabulario y semántica de cada uno: §SpecKit Progress Tracking y
`report-kit.md` §Reglas.

### I2. La tabla — qué genera cada trabajo

Se contesta con **dos preguntas**, en este orden:

> **P1 · ¿Hay que CONSTRUIR algo por fases, con gates y aprobaciones?** → SpecKit.
> **P2 · ¿Hay decisiones que las toma OTRO, y tienen que quedar registradas?** → informe report-kit.

Las dos son independientes: por eso hay cuatro respuestas y no tres.

> **Cómo se lleva esto con `governance.md` §1.** Aquella tabla decide **SpecKit vs cambio directo**
> por tamaño de lo que se construye, y **sigue mandando en cuanto P1 es sí**: si hay que construir y
> toca >5 ficheros o varios módulos, SpecKit es obligatorio, lo diga esta sección o no. Lo que añade
> esta es el caso que aquella no contempla — **trabajo grande que no construye nada todavía**. Un
> plan de análisis puede tocar cien ficheros al leerlos y no ser una "feature multi-módulo": no
> necesita waves, necesita decisiones.

| P1 | P2 | Genera | Cuándo es este caso | Ejemplo real en este repo |
|:--:|:--:|---|---|---|
| ✅ | ❌ | **Solo SpecKit** | El qué ya está decidido y solo falta construirlo por waves | `_archive/2026-10-20/specify-sessions/AITB-1 - AI Team Builder System/` — spec+plan+tasks, sin ningún set en `.docs/plans/` (archivada el 2026-10-20: era de la época del gateway de avisos retirado y su tasks.md quedó con 40 casillas sin marcar aunque la spec dice DONE) |
| ❌ | ✅ | **Solo informe** | Análisis, propuestas, auditoría o feedback: hay que decidir antes de que exista nada que construir | `_archive/2026-10-19/planes-cerrados/2026-08-07-ai4dev-specs-adopcion/` — 197 propuestas de adopción, 84 ya con `decision: aprobar`, **sin sesión SpecKit** |
| ✅ | ✅ | **Los dos, con el puente de §I3** | Construcción larga que además hay que enseñar y aprobar por partes | `.specify/sessions/TPL-1 …/` + `_archive/2026-10-19/planes-cerrados/2026-08-07-tpl-batch-1/` (60 items, páginas = las 9 waves) |
| ❌ | ❌ | **Ninguno: markdown** | Un veredicto, un research, un one-pager — no hay waves que ordenar ni decisiones por item que persistir | `_archive/2026-10-19/planes-cerrados/2026-08-05-graphify-adopcion/INFORME.md` (un veredicto: *adoptar con reservas*) · `_archive/2026-10-19/planes-cerrados/2026-08-05-rita-pattern-keeper/RESEARCH.md` |

**El caso que faltaba escrito es la segunda fila**, y es el más común en trabajo de análisis: un plan
de propuestas **no tiene sesión SpecKit** porque no hay nada que ejecutar todavía — lo que hay es
que decidir. Cuando esas decisiones se aprueban y hay que construirlas, *entonces* nace la sesión, y
se pasa a la tercera fila.

### I3. Cuando van los dos: el puente ya existe

`tasks_to_items.py` convierte el `tasks.md` de la sesión en los items del informe, y entiende las
waves de forma nativa: una cabecera `## Wave 3 — Report-kit` se convierte en **página** del informe
y en **epic `W3`**. Se ve en los dos `report.json` reales, y el contraste es la mejor prueba de que
son ejes distintos:

| Plan | Páginas del informe | Epics |
|---|---|---|
| `2026-08-07-tpl-batch-1` (nace de SpecKit) | `Wave 0 — …` … `Wave 8 — Cierre` | `W0`…`W8` (derivadas de la wave) |
| `2026-08-07-ai4dev-specs-adopcion` (sin SpecKit) | temas: `Seguridad y riesgo`, `Producto y priorización`… | fuentes: `OS`, `M1`, `GR`, `OF`… |

**El `tasks.md` de la sesión es la única fuente de verdad.** `tasks_to_items.py` lee `<plan>/dashboard.md`
y `build.py` lee `<plan>/report.json`, así que el fichero tiene que estar en la raíz del plan — y ahí
está la trampa: se copia, y la copia envejece. Ya pasó. En `tpl-batch-1` la copia del plan tiene
T8.1–T8.4 sin marcar mientras en la sesión están `[x]`/`[>]`: el informe enseñaba una wave abierta
que en realidad estaba cerrada.

Se evita copiando **en el mismo comando** que genera, nunca antes ni por separado, y **no editando
jamás el lado del plan**:

```bash
K=.claude/templates/report_kit ;  PLAN=.docs/plans/<fecha>-<slug>   # el caso real fue 2026-08-07-tpl-batch-1
SESION=".specify/sessions/TPL-1 - Batch-1 report-kit Otto Pol project-setup Rita"
cp "$SESION/tasks.md" "$PLAN/tasks.md" && python3 $K/tasks_to_items.py "$PLAN" \
   --project tech-lead-template --plan-id tpl-batch-1 --profile proyecto
python3 $K/build.py "$PLAN"        # el resto del flujo: rules/report-kit.md §Flujo canónico
```

Es idempotente y no pisa decisiones (el merge por `id` está en `report-kit.md` §Reglas 8). Al cerrar
cada wave, se regenera: el informe es la **vista**, la sesión es el **estado**.

> Layout alternativo, también usado (en `_archive/2026-10-19/planes-cerrados/2026-06-21-visual-plans/`): el plan guarda su sesión dentro del plan
> (`<plan>/speckit/{spec,plan,tasks}.md`), como describe `plan-docs-structure.md`. Vale igual —
> cambia de dónde sale el `cp`, no la regla.

### I4. Informe sin SpecKit — cómo se escribe entonces el `tasks.md`

No hay waves que copiar, así que el `tasks.md` se escribe a mano **como fuente de items**, no como
plan de ejecución. Tres consecuencias prácticas (formato exacto: `templates/report_kit/MANUAL.md` §"Qué se escribe en
`dashboard.md`", que es el `tasks.md` de antes):

1. **Las cabeceras `##` agrupan por tema, no por wave** — son las páginas del informe, y con ellas
   se navega. `2026-08-07-ai4dev-specs-adopcion` usa 14 temas y epics por fuente.
2. **El checkbox no es progreso, es estado de partida.** `[x]` significa "ya está adoptado", no "el
   Usuario dijo que sí". El sí lo dice `decision`, y eso lo escribe el Usuario en el propio informe.
3. **No inventes gates de wave.** `task_progress.py --gate` cierra waves de SpecKit; aquí no hay
   ninguna que cerrar y forzarlo solo produce un gate que nadie puede satisfacer.

### Anti-patterns de SpecKit e informe

- ❌ Abrir una sesión SpecKit para un plan de análisis "porque es grande" → waves vacías, gates que
  nunca pasan y un `tasks.md` que finge ser ejecución cuando es una lista de propuestas.
- ❌ Entregar 100 propuestas en markdown para que el Usuario responda por chat → las decisiones no
  persisten, no se exportan y se re-preguntan en la siguiente sesión. Para eso está el informe.
- ❌ Generar el set del report-kit para **un** veredicto o un research → cuarta fila: markdown.
- ❌ Editar el `tasks.md` del lado del plan cuando existe la sesión → dos verdades, y la que se
  enseña es la vieja (le pasó a `tpl-batch-1`).
- ❌ Copiar el `tasks.md` "cuando toque" en vez de en el mismo comando que el build.
- ❌ Leer el `status` del informe como decisión del Usuario, o escribir en `decision`/`note` desde un
  agente (`report-kit.md`: `note` es siempre del Usuario; la recomendación del agente va en `tl_rec`).
- ❌ Decidir esto a mitad del trabajo: si el informe aparece cuando ya hay 8 waves hechas, sus items
  se escriben mirando el código en vez de mirando lo que había que decidir.

---

_Rule version: 3.0 · 2026-10-20 (LI-29, sub-ola 1.06): absorbe `speckit-progress-tracking.md`
(v1.1 · 2026-08-25: el caso medido —4 frentes, 0 items en `[>]`— y el diagnóstico de capa: la norma
estaba escrita y se ignoró igual, así que lo que toca es bajarla a hook; el hook queda PROPUESTO, no
instalado, porque toca `settings.json`; antes v1.0 · 2026-04-22) y `speckit-vs-informe.md` (v1.0 ·
US-4, adopción AI4DEVS, 2026-08-08), con sus `paths:`; y la plantilla de `plan.md` deja de
contradecir a la tabla de límites en la RAM por TL. Antes: v2.0 · 28 Feb 2026._
