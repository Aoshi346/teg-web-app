---
paths:
  - "MEMORY.md"
  - ".ai/**"
  - ".claude/memory.json"
  - ".claude/memory/**"
  - ".claude/skills/auto-dream-memory/**"
  - ".claude/agents/*/memory.md"
  - ".claude/agents/*/herencia/**"
---
# Memoria — qué se guarda, dónde, quién lo escribe y cuándo se poda

> **Cuándo aplicar:** al **arrancar o retomar** una sesión (¿qué leo para ponerme al día?), al
> **cerrarla** (¿qué merece sobrevivir?), al montar la memoria de un proyecto o de un agente nuevo,
> y al decidir si algo va a la memoria o a otro sitio. Es el **único** documento que describe la
> arquitectura: si una skill, un agente o un README la vuelve a explicar, esa copia es la que está
> mal.
>
> **NO aplicar:** para el **estado de la tarea en curso** — eso es `PROGRESS.json`
> (`rules/progress-tracking.md`) y no es memoria · para una **decisión cara de revertir**, que tiene
> su formato propio en `rules/adr.md` · para el **avance de una sesión SpecKit**, que vive en los
> checkboxes de `tasks.md` · para decidir **qué sobra del harness entero** (skills, rules, agentes),
> que es `rules/self-improvement-loop.md` §5.
>
> **Relacionado:** skill **`auto-dream-memory`** — la única que EJECUTA lo que aquí se describe
> (traer contexto y consolidar; y desde el 2026-10-19 también §C, el informe de la semana, y §D, lo
> estable sube a `CLAUDE.md` con diff y confirmación — antes `retro` y `weekly-review`) ·
> `rules/harness-gotchas.md` §Caché (por qué editar `CLAUDE.md` a mitad de sesión sale caro) · `rules/adr.md` · `rules/progress-tracking.md` · `rules/harness-gotchas.md` §CLAUDE.md — cómo se escribe (antes la skill `boris-claude-md`, retirada el 2026-10-20).

---

## 0. Lo que hay HOY en disco (medido, no declarado)

Antes de la tabla de capas, los ficheros reales de **este** repo. Se mide porque la parte que más
envejece de un documento de memoria es su propio inventario:

```bash
for f in .claude/CLAUDE.md .ai/memory.md MEMORY.md .claude/memory.json; do
  printf '%-22s %s\n' "$f" "$([ -e "$f" ] && echo "existe ($(wc -l <"$f") líneas)" || echo 'NO EXISTE')"
done
# .claude/CLAUDE.md      existe (103 líneas)
# .ai/memory.md          existe (216 líneas)
# MEMORY.md              existe (55 líneas)
# .claude/memory.json    existe (8 líneas)
```

Las cuatro existen. **Ninguna la escribe un mecanismo automático** — §4.

Y una que se creía y no es cierta: la capa 2 **no está ignorada por git**, está versionada.

```bash
git check-ignore -v .ai/memory.md || echo "NO está ignorado"   # NO está ignorado
git ls-files --error-unmatch .ai/memory.md                     # .ai/memory.md  (o sea: trackeado)
grep -n "\.ai" .gitignore || echo "(.gitignore no menciona .ai/)"   # no lo menciona
```

La skill `sync-memory` afirmaba lo contrario —*«`.ai/memory.md` está en `.gitignore` — es contexto
efímero, no persistente en git»*— y llevaba a escribir ahí como si nadie fuera a verlo. **Escribe en
la capa 2 sabiendo que va a un commit**: nada que no meterías en el repo. Cambiarlo (ignorarla de
verdad, o asumirla versionada) es una decisión con consecuencias para los derivados y no se toma de
paso en una poda: queda declarada aquí.

---

## 1. Las capas — la única tabla

| Capa | Fichero | Vida | ¿Va a git? | Quién la escribe |
|---|---|---|---|---|
| **1 · Estándares** | `.claude/CLAUDE.md` | Permanente, cambia poco | ✅ sí | Una persona, **al inicio de sesión** (a mitad no se aplica hasta `/clear`, `/compact` o reiniciar — `harness-gotchas.md` §Caché) |
| **2 · Sesión** | `.ai/memory.md` | Efímera, regenerable | ⚠️ hoy SÍ (ver aviso) | La skill `auto-dream-memory`, operación **traer** |
| **3 · Largo plazo** | `MEMORY.md` | Duradera, evoluciona | ✅ sí | La skill `auto-dream-memory`, operación **consolidar** |
| **4 · Metadata** | `.claude/memory.json` | Estado estructurado | ✅ sí | Al cerrar una tarea significativa (`lastSession`, cambios recientes) |
| **+ auto-memoria** | `~/.claude/projects/<proyecto>/memory/` (`MEMORY.md` + un fichero por tema; §1b, §4.3) | La lleva Claude Code; se carga sola | ❌ no está en el repo | Claude, solo (y tú, a mano o con `/memory`) |

**La pregunta que decide la capa: ¿cuánto tiene que durar esto?**

- Vale para siempre y para cualquiera que abra el repo → **capa 1**.
- Lo necesito mañana al retomar, y no después → **capa 2**.
- Lo va a necesitar alguien dentro de seis meses para no repetir un error → **capa 3**.
- Es un dato que lee otra herramienta, no una persona → **capa 4**.

> ⚠️ **Hay un segundo modelo de capas en el repo, y no es este.** El `MEMORY.md` de la raíz declara
> **3 capas** propias (`L1 .claude/memory/MEMORY.md` · `L2 .ai/memory.md` · `L3` del orquestador),
> que no son las de arriba: lo que aquí es la capa 3 allí es la L2, y su L1 (la carpeta
> .claude/memory/) ya no existe: su única pieza, la plantilla `MEMORY.example.md`, se archivó el 2026-10-19
> (`_archive/2026-10-19/README.md`, LI-18).
>
> ```bash
> grep -n "capas" MEMORY.md | head -1
> # 3:Pointer a la memoria persistente del agente. Define las **3 capas** estándar…
> ```
>
> Es una plantilla genérica del refactor 03-05-2026 que quedó viva. **Manda esta rule**; el
> `MEMORY.md` de la raíz se usa como lo que es —el fichero de la capa 3— y su cabecera de "3 capas"
> es deuda declarada, no una segunda arquitectura a la que hacer caso.

### 1b. Lo que trae Claude Code de serie — y en qué se diferencia de las capas

Contrastado el 2026-10-21 con la doc `code.claude.com/docs/en/memory` (descargada el 2026-10-20 a las
23:29 UTC) y Claude Code 2.1.304; en el template, el detalle con fuentes es la skill
`claude-code-referencia` §1 (§1.2 `AGENTS.md`, §1.5 `/doctor prompt-audit`, §1.6 auto memory).

- **La auto memory oficial** son notas que **Claude** escribe solo (preferencias, correcciones,
  contexto que no sale del código) en `~/.claude/projects/<proyecto>/memory/`: un `MEMORY.md` índice y
  un fichero por tema. **Se cargan las primeras 200 líneas o 25 KB de su `MEMORY.md`** —lo que llegue
  antes— al empezar cada conversación; los ficheros de tema, solo cuando Claude los lee. La comparten
  todos los worktrees del repo, no sale de la máquina y **no llega a los subagentes** (salvo a un
  fork). Si su `MEMORY.md` pasa del límite, la escritura sale bien pero Claude Code le pide reescribir
  el índice, porque lo de después no se carga.
- **No es la capa 3.** El `MEMORY.md` de la raíz de este repo es un fichero del proyecto que escribe
  la skill `auto-dream-memory` y Claude Code **no** lo carga solo; el de la auto memory es otro
  fichero, en otra ruta, con su propio tope de 200 líneas. Que se llamen igual es casualidad, y es
  justo el tipo de confusión que esta rule existe para evitar.
- **`/memory`** lista los `CLAUDE.md`, `CLAUDE.local.md` y demás ficheros de memoria, enciende o apaga
  la auto memory (guarda `autoMemoryEnabled` en `~/.claude/settings.json`) y abre su carpeta. Una
  sesión en segundo plano, o una lanzada por otra sesión de Claude, puede apagarla pero no encenderla.
- **`AGENTS.md`** se lee como instrucciones de proyecto **solo si no hay `CLAUDE.md`** (opción por
  defecto, desde la v2.1.277). Aquí existe `.claude/CLAUDE.md`, así que el `AGENTS.md` de la raíz no lo
  lee Claude Code: es un puntero para personas y para Codex.
- **`/doctor prompt-audit [ruta]`** (v2.1.283+) revisa `CLAUDE.md`, `CLAUDE.local.md`, `AGENTS.md`,
  rules, skills, comandos, subagentes y output styles buscando instrucciones para modelos viejos,
  rutas o comandos que ya no existen y ficheros que se contradicen; propone cambios y no toca nada
  hasta que se lo pides. Es el complemento de la consolidación de §3, no un sustituto.

---

## 2. Qué se guarda y qué NO

| Se guarda | No se guarda | Por qué no |
|---|---|---|
| Decisiones **con su porqué** y las alternativas descartadas | El código actual | Está en el repo, y la copia envejece |
| Gotchas del stack que costaron media hora de descubrir | El historial de git | Para eso está `git log` |
| El **próximo paso exacto** al retomar | Ruido de depuración de una tarde | No sobrevive al día siguiente |
| Rutas, nombres y comandos que no son obvios | Lo que ya dice `CLAUDE.md` | Duplicar es cómo empiezan a contradecirse |
| Lo que se probó y **no** funcionó | El avance de la tarea en curso | Es `PROGRESS.json` |
| — | **Secretos, tokens, claves** | En ninguna capa, nunca |

Y la regla que ahorra más trabajo: **una fecha relativa no se guarda nunca**. "El jueves pasado" es
falso a los ocho días; se escribe `2026-08-22`.

---

## 3. Cuándo se consolida — los tres disparadores (fuente única)

La consolidación (podar, fusionar duplicados, borrar lo contradicho) se dispara cuando ocurre
**cualquiera** de estas tres cosas:

1. Se **cierra una sesión SpecKit** entera.
2. Han pasado **5 sesiones** sin consolidar.
3. `MEMORY.md` supera las **150 líneas**.

Y una cuarta que no es periódica sino causal: **después de un refactor que mueva o renombre
ficheros**, porque es cuando la memoria se llena de rutas que ya no existen.

> Estos tres números estaban escritos **literalmente en tres skills a la vez** (`memory-system`,
> `auto-dream-memory` y, citándolas, `boris-dream`). Ahora están aquí y en ningún otro sitio: quien
> los cambie, los cambia una vez. El **procedimiento** de consolidar —las cuatro fases— vive en la
> skill, no aquí: esto dice *cuándo*, la skill dice *cómo*.

### 3b. Memorias de agente — tope, herencia y template limpio (sub-ola 3.14: EQ-5, AN-12)

`agents/<x>/memory.md` es la memoria de un agente; la lee entera cada vez que se lanza. Medido el
31-10 en un bot derivado: siete pasaban de 300 líneas y cuatro de 1.000 (~15k tokens antes de empezar).

| Qué | Regla | Lo comprueba |
|---|---|---|
| **Tope** | Más de **300 líneas** → consolidar (`auto-dream-memory` §B, «Memorias de agente») | `scripts/check_agent_memory.py`; `otto-briefing.sh` avisa al arrancar y calla si no hay nada |
| **Herencia** | Un proyecto nuevo puede heredar la memoria de otro del mismo tipo en `agents/<x>/herencia/<origen>-memory.md`: **de solo lectura**, con cabecera de origen y fecha, consolidada antes (la copia se niega por encima de 300 líneas). Se consulta por tema, no se lee entera; lo aprendido va a `memory.md`. Se borra con OK cuando lo propio ya lo cubre | `scripts/inherit_agent_memory.py <origen> <destino> [--apply]` (paso 4d de `project-setup`) |
| **Template** | Las memorias del template son **plantillas**: esqueleto + «Lecciones de método» sin nombres de proyecto, cliente, tenant, dominio ni clave de issue. Sin `herencia/` | `check_agent_memory.py --clients` (nombres de `packs/CONFIGURACION.yaml` + los fijos del script) = 0 |

Lo que un proyecto aprende y vale para todos sube con `/consolidate-agent-learnings`, que pasa
`--clients` sobre la propuesta antes de dejarla al Usuario.

---

## 4. Los tres mecanismos que la documentación daba por hechos — y que no existen

Es la parte más cara del clúster que esta rule sustituye: **tres automatismos citados como si
funcionaran, ninguno enchufado.** Un mecanismo que no existe es peor que no tenerlo, porque nadie
hace a mano lo que cree que ya se hace solo.

### 4.1 El Stop hook `update-memory.sh` — no está aquí, y donde está no hace lo que prometía

```bash
ls .claude/hooks/update-memory.sh                # No such file or directory
grep -c "update-memory" .claude/settings.json    # 0
```

Dos skills decían *"el Stop hook lo actualiza automáticamente al terminar"*. **En este repo no lo
actualiza nadie.**

Y una vuelta de tuerca, medida el 2026-08-22 al cerrar la migración (`CAP-MEMORYSYSTE`): el hook
**sí existía** — en el agente de ejemplo de Django+React, de donde arrancaban los proyectos
derivados, y ahí estaba **enchufado de verdad** (el ejemplo se archivó el 2026-10-19; la medida se
repite sobre la copia archivada):

```bash
E=_archive/2026-10-19/examples/django-react-agent/.claude
wc -l $E/hooks/update-memory.sh              # 13
grep -n "update-memory" $E/settings.json     # 120 (Stop, async: true)
```

Leídas las 13 líneas enteras, lo que hace es esto: **si** `claude` está en el PATH **y** existe
`PROGRESS.json`, añade **tres líneas** al final de `.ai/memory.md` — `## Sesión <fecha>`,
`Tarea: <lo que ya pone PROGRESS.json>` y una en blanco. No resume la sesión, no poda, no toca las
capas 1, 3 ni 4, y si falta cualquiera de las dos condiciones no escribe nada y sale en silencio.
O sea: **donde el mecanismo existe, tampoco hace lo que las skills decían.** Deja un encabezado.

Consecuencia operativa mientras siga así: la capa 2 se escribe **corriendo la skill**, no se da por
hecha, y un derivado que copie ese ejemplo no hereda memoria automática — hereda un encabezado.
Montar el hook aquí, o arreglar el del ejemplo, toca `settings.json` → aprobación del Usuario
(`governance.md` §2); esta rule no lo hace, lo declara.

### 4.2 El comando `/dream` — no existe en esta instalación

Tres skills lo daban como el disparador de la consolidación. No está en la referencia oficial
(verificado el 2026-08-08 contra `code.claude.com/docs/en/commands`: la lista va de `/doctor` a
`/effort`) y **tampoco está instalado aquí** (medido el 2026-08-22 sobre `2.1.240`):

```bash
ls ~/.claude/commands/ | grep -ix dream.md                        # 0
find ~/.claude/plugins -path '*commands*' -name 'dream*' | wc -l  # 0
ls .claude/commands/ | grep -ci dream                             # 0
```

Por eso la operación **consolidar** no depende de él: es un procedimiento que se ejecuta con las
herramientas normales. Si tu versión lo trae, `/help` lo dirá; sería un atajo, nunca el mecanismo.

### 4.3 `autoMemoryDirectory` apunta a un sitio vacío

```bash
grep -n '"autoMemoryDirectory"' .claude/settings.json   # 206: ".ai/auto-memory"
ls -d .ai/auto-memory                                   # No such file or directory
ls /root/.claude/projects/-home-tech-lead-template/memory/*.md | wc -l   # 6
```

El ajuste declara `.ai/auto-memory` y **ese directorio no existe**; los seis ficheros de auto-memoria
de este proyecto están en la ruta por defecto del harness. O el ajuste se puso después de que la
auto-memoria arrancara, o no se está aplicando: **con lo medido no se puede distinguir**, y no se
rellena el hueco con una suposición. Lo que sí se sabe y es lo que hay que usar: **la ruta buena es
la que tenga ficheros**, y se comprueba con un `ls` antes de leer nada.

> **Lo que dice la doc hoy (2026-10-21, `memory` §Storage location), y explica el vacío:** el valor
> *"must be an absolute path or start with `~/`"*, y `.ai/auto-memory` es una ruta **relativa**. Además,
> puesto en el `.claude/settings.json` de un proyecto, solo vale con la carpeta confiada (la misma
> regla que los hooks del repo). Lo más probable es que Claude Code lo esté descartando y use la ruta
> por defecto; **no se ha probado en vivo** (haría falta una sesión nueva con el ajuste corregido y
> ver dónde escribe). Arreglarlo es tocar `settings.json` —poner una ruta absoluta o quitar la clave—,
> así que va con la sub-ola que toca los settings del template (2.01), no aquí.

Claves confirmadas en la doc oficial, por si hay que tocarlas: `autoMemoryEnabled` (default `true`),
`autoMemoryDirectory` y la variable `CLAUDE_CODE_DISABLE_AUTO_MEMORY`.

---

## 5. Límites honestos

- **Nada de esto se aplica solo.** Sin el hook de §4.1, la memoria depende de que alguien corra la
  skill. Esta rule es intención y routing (`rules/layer-decision.md`): el día que la capa 2 tenga
  que actualizarse *siempre*, el sitio es un hook, no un párrafo.
- **La memoria compite con el contexto.** Una capa 2 de 200 líneas se lee entera cada vez que se
  arranca: si no cabe en una pantalla, poda antes de añadir.
- **Consolidar puede borrar algo que querías.** La operación no se da por buena sin mirar el
  resumen de qué se fusionó y qué se fue.
- **El segundo modelo de capas sigue en la raíz** (§1). Unificarlo toca ficheros que otros
  documentos citan; hasta entonces, esta rule manda y aquello es deuda declarada.

---

## Anti-patterns

- ❌ Volver a explicar la arquitectura de capas en una skill, un agente o un README → era el
  problema (cinco piezas para una idea); si falta algo, se añade **aquí**.
- ❌ Escribir los disparadores de consolidación en otro fichero (§3) → vuelven a divergir.
- ❌ Dar por hecho que un hook actualiza la memoria sin haber comprobado que existe **y qué
  escribe** — el del ejemplo existe, corre, y solo añade un encabezado (§4.1).
- ❌ Guardar el código, el `git log` o el avance de la tarea en la memoria — tienen su sitio y no es
  este.
- ❌ Fechas relativas ("la semana pasada") en cualquier capa.
- ❌ Secretos o tokens en cualquier capa.
- ❌ Consolidar sin haber usado el proyecto desde la última vez (no hay nada que consolidar) o a
  mitad de una tarea viva (la capa 2 aún está cambiando).
- ❌ Dejar `MEMORY.md` crecer sin podar: pasadas ~150 líneas deja de leerse entera, que es lo mismo
  que no existir.
- ❌ Editar `CLAUDE.md` a mitad de sesión para "apuntar una cosa" → no se aplica hasta `/clear`,
  `/compact` o reiniciar (no rompe el caché: `harness-gotchas.md` §Caché); se anota en la
  capa 2 y sube a la 1 al arrancar la siguiente (o vía §D de `auto-dream-memory`).

---

_Rule version: 1.2 · 2026-10-21 · sub-ola 2.16 (MO-79): §1b, lo que Claude Code trae de serie
(auto memory con su tope de 200 líneas o 25 KB, `/memory`, `AGENTS.md`, `/doctor prompt-audit`) y la
respuesta de la doc a §4.3 (`autoMemoryDirectory` tiene que ser absoluta). · v1.1 · 2026-08-22 · EJE-3 + CAP-MEMORYSYSTE (§4.1: el hook fantasma existe en
`examples/` y escribe tres líneas, no memoria). Sustituye a las skills `boris-memory`, `memory-system`,
`boris-dream` y `sync-memory`, archivadas en `_archive/2026-08-22/` con su porqué. El procedimiento
—traer y consolidar— vive en la skill `auto-dream-memory`, que es la que ejecuta._
