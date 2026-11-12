# Governance — Decisiones de Workflow y Autonomía

> **Cuándo aplicar:** al decidir **SpecKit vs cambio directo** (§1), si una acción **necesita aprobación** (§2), **cuánta cuerda** tiene un TL según su nivel (§3) y según el **tipo de tarea** (§3.1), y **quién toca cada capa** de la configuración (§6). Complementa `speckit-workflow.md` (que cubre el HOW del SpecKit) con el WHEN y el WHO-APPROVES.
>
> **NO aplicar:** para **promocionar a un agente** de fase ni para el freno que **el propio agente** acciona cuando duda — ese es el eje de proceso de `agent-autonomy-ladder.md`. Tampoco durante un incidente activo en producción (§8).
>
> **Relacionado:** `agent-autonomy-ladder.md` · `speckit-workflow.md` · `plan-gates.md` · `parallelization.md` · `security.md`.

---

## 1. Cuándo usar SpecKit vs Cambio Directo

| Situación | Approach |
|-----------|----------|
| Fix de 1-3 archivos | Cambio directo, sin SpecKit |
| Feature nueva multi-módulo | SpecKit obligatorio |
| Refactor > 5 archivos | SpecKit obligatorio |
| Bug con root cause claro | Cambio directo |
| Bug complejo multi-capa | SpecKit recomendado |
| Cambio de UI solo | Cambio directo + screenshot de verificación |
| Nuevo módulo (app Django, paquete frontend) | SpecKit obligatorio |
| Migración de schema simple (1 tabla, sin datos críticos) | Cambio directo |
| Migración con backfill o lock potencial | SpecKit obligatorio |

**Default:** si dudas, **usa SpecKit** — el coste de planear es bajo, el coste de re-trabajar sin plan es alto.

---

## 2. Approval Gates — Qué requiere aprobación del Supervisor

### Acciones AUTÓNOMAS (sin aprobación)

- Leer y editar código (frontend, backend, configs no críticas)
- Crear archivos y componentes
- Refactorizar código existente
- Run tests (respetando límites de RAM en `CLAUDE.md`)
- `git commit` a la branch de trabajo, con rutas explícitas. Default: `develop` (`code-style.md`
  §Branches); si el `CONFIGURACION.yaml` del proyecto dice otra cosa (`git_commit: usuario`,
  `git_branching: rama-por-issue`), manda el proyecto: entonces se deja listo y se avisa (`READY_COMMIT`)
- Install **project deps** (`pip install pkg`, `npm install pkg`, `poetry add pkg`)
- Crear migraciones Django y aplicarlas en dev/staging

### Requieren APROBACIÓN del Supervisor

- **Deploy a producción** (cualquier entorno con usuarios reales)
- **DB migrations destructivas**: `DROP`, `ALTER ... DROP`, `DELETE` masivo
- **Merge a `main`** (o branch protegida equivalente)
- **Install system deps** (`apt install`, `brew install`, paquetes del SO)
- **Borrar archivos o directorios importantes** (worktrees, migraciones aplicadas, configs de producción)
- **Modificar configuración crítica**: `settings.py` producción, `nginx.conf`, secrets, CORS, auth
- **Gasto externo** (APIs de pago, infraestructura cloud, modelos comerciales)
- **Force-push**, `git reset --hard` sobre commits compartidos, reescritura de historia

### Requieren APROBACIÓN del Usuario (escalada desde Supervisor)

- Cambios de **scope** del producto (añadir/quitar features no acordadas)
- Cambios de **pricing** o lógica de billing
- Decisiones de **UX crítico** (rediseño de flujos principales)
- Borrar datos de usuarios reales

---

## 3. Escalado de Autonomía

Cada Tech Lead puede operar en uno de 3 niveles, configurable según el contexto del proyecto y la madurez del equipo:

| Nivel | Qué hace el TL | Cuándo usar |
|-------|----------------|-------------|
| **Supervised** | Todo requiere aprobación del Supervisor antes de ejecutar | Proyecto nuevo, equipo nuevo, alto riesgo |
| **Semi-autonomous** (default) | Solo requiere aprobación para acciones de la lista "Requieren Aprobación" arriba | Proyecto estable, TL probado en el dominio |
| **Autonomous** | Solo requiere aprobación para deploy a producción y migraciones destructivas | Tareas batch repetitivas, waves de SpecKit ya aprobadas, /loop |

**Cambio de nivel:** lo decide el Supervisor (o el Usuario) explícitamente. **Nunca** auto-escala el propio TL.

### 3.1 Autonomía graduada por TIPO de tarea

Los tres niveles de arriba gradúan por **madurez del TL**, y §2 gradúa por **acción**. Falta el eje que más autonomía regala gratis: **qué clase de trabajo es**. Convertir un módulo de una sintaxis a otra es mecánico y el test dice si está bien; diseñar lógica de negocio nueva no tiene test que lo diga. Hoy ambos piden lo mismo.

| Tipo de tarea | Autonomía | Guardrails obligatorios (todos, antes de cerrar) |
|---|---|---|
| **Mecánica y verificable** — transpilación, migración de sintaxis, renombrado masivo, aplicar un patrón ya decidido a N ficheros, actualizar imports, formateo | **Alta**: ejecuta el lote entero sin ir preguntando fichero a fichero | (a) tests del módulo **en verde antes y después** · (b) diff **acotado a los ficheros previstos** — cualquier fichero fuera de la lista para el lote · (c) cero cambios de comportamiento intencionados · (d) commit por lote, revisable de un vistazo |
| **Semi-mecánica** — refactor con criterio (extraer módulo, partir un fichero), aplicar un fix conocido a variantes distintas | **Media**: plan corto primero, luego ejecuta el plan | Los de arriba + el plan escrito antes (`[PLAN]` en `PROGRESS.log`) |
| **Lógica nueva o decisión de producto** — reglas de negocio, contratos de API públicos, esquema de datos, UX de un flujo principal, pricing | **Baja**: SpecKit y los gates de §2 y §2-Usuario | Todo lo anterior **no basta**: aquí el test verde no prueba que la decisión sea correcta |

**`/batch`** (la skill integrada que parte un cambio en 5-30 unidades, cada una en su worktree) **solo para
la fila «mecánica y verificable»**, y siempre después de `bash .claude/hooks/check-ram.sh --explain`: cada
unidad es un subagente con su worktree y cuenta contra el tope de la máquina (decisión BATCH-G9-14 del
Usuario, 22-10; `rules/goal-vs-loop.md`).

**Y por zona** (`audit-team.md` §9): con el `zonas.yaml` del proyecto firmado, una ruta **roja** baja a autonomía baja sea cual sea el tipo de tarea (`zona.py <rutas>`).

**Cuándo NO aplica "mecánica y verificable"** (el límite honesto): si el módulo **no tiene tests**, o los que tiene no fallarían ante el error que temes, la tarea deja de ser verificable y baja a autonomía media aunque el trabajo sea mecánico. El guardrail es el test, no la etiqueta.

> Referencia del sector citada en el material de origen (AI4DEVS M17.4): Amazon publica en torno al **70% del código transpilado por IA sin supervisión humana** — *"ya son muy buenos haciendo transpiling […] incorporando ciertos guardrails puedes arriesgar más"*. Es un dato de terceros sobre su contexto, no una medición nuestra; lo que adoptamos es el criterio, no el porcentaje.

---

## 4. Protocolo de Comunicación

### Cuándo notificar
Por el canal que exista en la máquina; en la de casa es Telegram, con
`python3 .claude/scripts/avisar.py "[PROYECTO] [ESTADO]: [mensaje]"` (sale con 1 y dice por qué si no
llega; `--comprobar` mira el canal sin mandar nada). `DONE` y `BLOCKED` los manda además solo el hook
`notify-telegram.sh` (Stop) cuando `PROGRESS.json` pasa a `completed` o `blocked`. Estados canónicos:

- `INICIO`: empiezo tarea
- `READY_MERGE`: worktree listo, esperando aprobación de merge
- `READY_COMMIT`: cambios listos, esperando aprobación de commit
- `BLOCKED`: necesito decisión/recurso externo
- `QUESTION`: duda concreta, espero respuesta
- `DONE`: tarea completa
- `ERROR`: algo falló, requiere revisión

### Fuente de verdad de estado
**`PROGRESS.json` en la raíz del proyecto** es la única fuente de verdad para el estado de la tarea. El Supervisor lo lee sin parsear logs. Mantén `task`, `status`, `checklist[*].done` actualizados en vivo (no en batch).

Formato canónico de `PROGRESS.json`: `rules/progress-tracking.md`.

---

## 5. Reglas de Modificación del Repo

### Templates compartidos
- Cambios en templates afectan a TODOS los proyectos derivados
- Requieren review explícito antes de merge
- Documentar el cambio en el changelog del template

### Configs específicas del proyecto (`.claude/`)
- Son específicas del proyecto actual
- Se pueden modificar sin afectar otros proyectos
- Preferir editar archivos existentes sobre crear nuevos

### Configs de producción
- `nginx.conf`, `systemd units`, secrets, dotenv de prod → tocar SOLO con aprobación explícita
- Mantener idempotencia en scripts de deploy

---

## 6. Las 5 capas por ROL HUMANO

Quien no programa **solo ejecuta slash commands**; `CLAUDE.md`, skills, hooks, `settings.json` y lo
programado los toca solo el rol técnico (y `settings.json`, además, con aprobación, §2). Tabla y
consecuencias: `rules/human-role-layers.md` (entra sola al tocar settings, comandos o hooks).

---

## 7. Anti-patterns

- ❌ Diferir items técnicamente posibles porque "es complejo" → si está en el spec, **hazlo**
- ❌ Pedir aprobación para cada commit cuando estás en `Semi-autonomous` → solo para los gates de la lista
- ❌ Auto-escalar tu nivel de autonomía porque "la tarea es urgente"
- ❌ Borrar worktrees mergeados sin aprobación (puede haber trabajo no sincronizado)
- ❌ `git push --force` sobre branch compartida sin coordinar con el Supervisor
- ❌ Tratar una transpilación con tests verdes con la misma cautela que un cambio de lógica de negocio → §3.1
- ❌ Llamar "mecánica y verificable" a una tarea sobre un módulo **sin tests** → el guardrail es el test, no la etiqueta
- ❌ Pedirle a un rol no técnico que edite un fichero de configuración → si hace falta, es que falta un comando (§6)

---

## 8. Cuándo este documento NO aplica

- **Hotfixes en producción**: el Supervisor puede saltarse niveles de aprobación si hay incidente activo. Documentar post-mortem en `PROGRESS.log`.
- **Tareas de exploración / spike**: no requieren PROGRESS.json formal; basta con notificar al Supervisor al cerrar.

---

_Rule version: 1.2 · 2026-10-28 — el detalle de §6 pasa a `human-role-layers.md` (con `paths:`, MO-46) ·
v1.1 · 2026-08-08 — añadidos §3.1 (autonomía por tipo de tarea, AGT-6) y §6 (las 5 capas
por rol humano, ND-4); anti-patterns y "cuándo NO aplica" pasan a §7 y §8. El eje de PROCESO
(promoción de agentes, escalado por incertidumbre, coste FP/FN) vive en `agent-autonomy-ladder.md`._
