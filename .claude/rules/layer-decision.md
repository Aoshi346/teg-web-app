---
paths:
  - "CLAUDE.md"
  - "CLAUDE.local.md"
  - ".claude/INDEX.md"
  - ".claude/skills/skill-authoring/**"
---
# La capa correcta — las 4 preguntas antes de escribir una norma

> **Cuándo aplicar:** siempre que vayas a **crear una norma nueva** para el agente (una regla, una
> prohibición, un procedimiento, un permiso) o a **podar** las que ya existen. Decide en qué CAPA
> vive: `CLAUDE.md` (intención) · hook (obligación) · skill (procedimiento) · MCP (acceso gobernado).
>
> **NO aplicar:** para decidir *qué leer* en una tarea — eso es `INDEX.md`. Ni para el contenido de
> la norma; esta rule solo decide **dónde va**.
>
> **Relacionado:** `harness-gotchas.md` (CLAUDE.md es advisory, caché, y §CLAUDE.md — cómo se
> escribe), `INDEX.md` (routing), skill `skill-authoring` (¿debe existir esta skill?) y, en el
> template, `claude-code-referencia` (§3 los 5 tipos de handler, §1 CLAUDE.md, §2 MCP, §8 permisos;
> sustituyó a las `boris-*`, retiradas el 2026-10-20).

---

## El principio (la frase que lo decide todo)

> **"CLAUDE.md instructions are advisory — Claude is allowed to ignore them."**
> — documentación oficial de Claude Code, best practices

No es un defecto: es la definición. `CLAUDE.md` es contexto que el modelo pondera junto con todo lo
demás, y bajo presión de contexto lo pondera menos. Los **hooks**, en cambio, los ejecuta el harness
pase lo que pase y pueden **bloquear** la acción (exit ≠ 0).

Consecuencia práctica: **escribir una regla crítica en prosa no es implementarla.** Si el peor caso
de que se ignore es caro, la prosa es el borrador; el hook es la implementación.

### El caso de casa

Los límites de RAM antes de `pytest` y la prohibición de datos mock estuvieron —y en parte siguen—
escritos en prosa de `CLAUDE.md`. Por eso existen `hooks/check-ram.sh` (PreToolUse sobre pytest) y
`hooks/pre-commit-check.sh` (anti-mock): el enforcement real no es el párrafo, es el script. La
prosa quedó como intención y routing, que es exactamente su trabajo.

---

## Las 4 preguntas

### 1. ¿Qué es lo PEOR que pasa si Claude lo ignora?

| Respuesta | Capa |
|---|---|
| "Perdemos unos minutos y re-prompteamos" | **`CLAUDE.md`** |
| "Se rompe una migración · se expone un secreto · OOM que mata el servidor · se despliega a producción sin aprobar" | **HOOK** (bloqueante) |

Es la pregunta que más se falla. Si dudas, pregúntate si aceptarías que ocurriera **una vez de cada
veinte sesiones** — porque eso es lo que significa "advisory".

### 2. ¿Vamos a correr este procedimiento exacto más de 3 veces este trimestre?

Sí → **SKILL**. Un procedimiento con pasos, orden y criterio de salida no cabe en un párrafo de
CLAUDE.md sin engordarlo, y engordar CLAUDE.md hace que se ignore *el resto*. Antes de crearla,
pasa el filtro de existencia de `skill-authoring` ("¿esto DEBERÍA ser una skill?").

No → déjalo en la conversación o en el plan de esa tarea. Una skill que corre una vez es ruido
permanente: una opción más que el modelo debe considerar en cada sesión.

### 3. ¿Toca sistemas externos con consecuencias reales?

Facturación, datos de cliente, deploys a producción, APIs de pago, borrado de datos → **MCP con
permisos acotados**, no un `bash` improvisado. El MCP da superficie explícita, auditable y con
scope; el bash da todo el sistema.

### 4. ¿Es contexto de EQUIPO o preferencia PERSONAL?

| Tipo | Dónde |
|---|---|
| Vale para cualquiera que abra el repo (stack, comandos, arquitectura, gates) | **`CLAUDE.md` commiteado** |
| Solo para tu máquina o tu gusto (rutas locales, verbosidad, atajos propios) | **`CLAUDE.local.md`** (gitignored) |

Meter preferencias personales en el CLAUDE.md del repo es la forma más silenciosa de inflarlo.

### 5. ¿Cuántos criterios independientes hace falta, y de quién?

Es la pregunta que faltaba, y la que reparte entre **subagente, workflow, agent-teams y plugin**.

| Respuesta | Capa |
|---|---|
| Uno solo, el mío, mientras trabajo | Nada: hazlo en la sesión |
| **Uno independiente**, sin contaminar por haber hecho el trabajo | **Subagente** (contexto limpio) |
| **Varios a la vez**, y quiero el mismo resultado cada vez | **Workflow** (determinista, resumible) |
| Varios que además **necesitan rebatirse** entre sí | **agent-teams** (caro: 1 sesión por teammate) |
| Varios que solo **necesitan enterarse** de lo que hace el otro | **Pizarra** (`parallelization.md` §Pizarra), no teams |
| Una capacidad hecha por otros, **versionada y reutilizable entre proyectos** | **Plugin** |

⚠️ **Antes de repartir, el test de independencia** (`parallelization.md` §0): si la respuesta de B
cambiaría según la de A, es **una** tarea con dos sombreros. Repartir mal no es "un poco menos
eficiente": pagas N ventanas de contexto para producir una respuesta **peor**. Y el sesgo por
defecto en un repo de código es **paralelizar menos, no más**.

---

### El caso que lo demuestra: «un cartel no es una puerta» (TPL-3, cosecha de Xera)

En un sistema de agentes con sesiones efímeras, unas sesiones empezaron a dar órdenes a otras por
`tmux send-keys` — una llegó a decirle a una sesión de código «fusiona y despliega». **Se escribió la
regla en el prompt del job a las 12:35, y la sesión de las 13:00 la incumplió igual.** El arreglo
fue un `settings-despertador.json` con `Bash(tmux send-keys*)`, `paste-buffer` y `run-shell` en
`deny`. Palabras del sistema que lo pagó: *«un cartel no es una puerta: esto es la puerta»*.

Es la pregunta 1 de arriba con fecha y hora. Y el árbol de decisión que sale de ella, tal como lo
escribió su `INDEX.md`: **¿qué es lo PEOR que pasa si el agente lo ignora?** — «perdemos minutos» →
`CLAUDE.md`; «se manda un correo, se borra algo, se gasta dinero, se toca producción» → **hook**.

## Tabla de capas — y qué NO va en cada una

| Capa | Qué es | SÍ va aquí | **NO** va aquí |
|---|---|---|---|
| **`CLAUDE.md`** | Intención y routing | Stack, rutas, comandos, criterio, a qué rule ir | Reglas cuyo incumplimiento cuesta caro · procedimientos largos · preferencias personales |
| **Rule** (`.claude/rules/`) | Criterio de un dominio | Cómo se hace bien X, cuándo aplica, anti-patterns — **con `paths:`** a los ficheros de ese dominio | Algo que hace falta en TODAS las sesiones (eso es `CLAUDE.md`, y corto) · rules sin `paths:` "por si acaso": se cargan siempre |
| **Hooks** | Enforcement determinista | Bloqueos duros, validaciones que deben correr *siempre*, logging | Matices, juicio, cosas que dependen del contexto de la tarea |
| **Skills** | Procedimientos repetibles | Pasos, rúbricas, plantillas, criterios de salida | Datos estáticos del proyecto (eso es CLAUDE.md) · procedimientos de un solo uso |
| **MCP** | Acceso gobernado a lo externo | Herramientas con permisos y scope | Lógica de negocio · razonamiento (un MCP no arregla un mal criterio) |
| **Subagente** | Criterio independiente | Verificar, auditar, revisar con contexto limpio | Trabajo que necesita TODO el contexto de la sesión · orquestar a otros subagentes (no puede) |
| **Workflow** | Orquestación determinista | Fan-out/fan-in, review por dimensiones, migraciones a escala, research multi-ángulo | Una sola llamada · trabajo donde el control de flujo lo decide el criterio, no el script |
| **agent-teams** | Varias sesiones que se hablan | Hipótesis en competencia, review desde ángulos que deben rebatirse | Lo que se resuelve enterándose (→ pizarra) · cualquier cosa que quepa en un `/goal` |
| **Plugin** | Capacidad empaquetada de terceros | Lo que se comparte, se versiona y se reutiliza entre proyectos (LSP, integraciones, toolkits) | Lo específico de ESTE proyecto: eso es standalone en `.claude/` |

---

### La frontera plugin ↔ standalone (doc oficial)

> *"Standalone (`.claude/`): personal workflows, project-specific customizations, quick experiments.*
> *Plugins: sharing with teammates, distributing to community, versioned releases, reusable across projects."*
> — `code.claude.com/docs/en/plugins`

Y su consejo, que es el nuestro: **empieza standalone para iterar rápido, conviértelo en plugin
cuando vayas a compartirlo.** Un plugin puede traer dentro skills, agentes, hooks, MCP y LSP a la
vez — por eso instalar uno de terceros es una decisión de **cadena de suministro**, no de comodidad:
pasa siempre el grep de `agent-security.md` §5 (36% de las skills públicas auditadas traían prompt
injection).

**Y el mapa de qué hay para cada caso vive en `.claude/AGENT-SYSTEM.md`** (generado), no aquí: esta
rule da el *criterio*, aquel da el *inventario*.


## La prueba del incumplimiento (cómo se usa esto en la práctica)

**Si una norma ya está escrita y aun así se incumple, no la reescribas más fuerte: bájala de capa.**
Subir el tono ("IMPORTANTE", "NO NEGOCIABLE", mayúsculas) no cambia que sea advisory. En la fuente,
un hook de ~15 líneas que denegaba tocar `migrations/*` sin una env var de escape **sustituyó unas
30 líneas de reglas advisory que ya estaban en el fichero y ya se ignoraban**.

Cadencia sugerida: al hacer una poda de `CLAUDE.md` o una retro (§C/§D de `auto-dream-memory`), pasa
cada sección por la pregunta 1. *(Anécdota de la fuente, un solo equipo, sin metodología publicada:
en su primera auditoría con este criterio, 11 de 37 instrucciones fallaron la pregunta 1 y se
movieron a hooks esa misma semana. Sirve para motivar la auditoría, no como medida.)*

---

## Límites honestos

- Esta rule **no arregla nada por sí sola**: es el criterio que se aplica ANTES de escribir o podar.
- Los hooks tienen puntos ciegos (solo ven lo que su evento les da) y cuestan latencia en cada tool
  call — no conviertas todo en hook.
- **Las skills derivan.** Una skill que referencia un linter que borraste el mes pasado es peor que
  no tener skill. Lo que se crea, se mantiene (`self-improvement-loop.md`).

---

## Anti-patterns

- ❌ Escribir una regla crítica (migraciones, secretos, RAM, deploy) en prosa de `CLAUDE.md` y darla
  por implementada.
- ❌ Responder a "se ignoró la regla" subiendo el tono en vez de bajarla a hook.
- ❌ Convertir en skill algo que se hará una vez → una opción más que el modelo pondera para siempre.
- ❌ Dar acceso a un sistema externo con consecuencias vía `bash` suelto en vez de MCP con scope.
- ❌ Preferencias personales en el `CLAUDE.md` commiteado (van a `CLAUDE.local.md`).
- ❌ Hook para algo que requiere juicio → falsos positivos, y el equipo aprende a saltárselo.
- ❌ Montar un agent-team para algo que se resuelve con una pizarra o con un `/goal`.
- ❌ Partir en subagentes sin pasar el test de independencia (`parallelization.md` §0).
- ❌ Instalar un plugin de terceros como si fuera comodidad y no cadena de suministro.
- ❌ Empaquetar como plugin algo específico de un proyecto: eso es standalone.
- ❌ Añadir una capacidad al harness y no añadirla a `AGENT-SYSTEM.md` → nace invisible.

---

_Rule version: 1.1 · DEC-1 (2026-08-07) · v1.1 (2026-08-20): +pregunta 5 y las capas que
faltaban — subagente, workflow, agent-teams y plugin. Antes decidía entre 4 capas y el harness
tiene 8, así que las tres por las que más se pregunta no tenían criterio escrito._
