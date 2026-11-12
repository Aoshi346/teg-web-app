---
paths:
  - ".claude/improvements_tl.md"
  - ".claude/to_apply.md"
  - ".claude/DIVERGENCIAS-DELIBERADAS.md"
  - ".claude/examples/**"
  - ".claude/commands/consolidate-agent-learnings.md"
  - ".claude/scripts/cosechar_mejoras.py"
  - ".claude/cosecha-mejoras.json"
  - ".claude/scripts/corpus_lint.py"
  - ".claude/skills/auto-dream-memory/references/**"
---
# Bucle de auto-mejora — proyecto ↔ tech-lead-template

> **Cuándo aplicar:** cuando, trabajando en un proyecto derivado, detectas una mejora **de la
> configuración de Claude Code en sí** (un skill que falta, un agente que convendría, un workflow
> repetible, un hook, una regla) — NO una mejora del producto. El objetivo es que cada proyecto
> haga **mejor el template**, y que el template arme una **biblioteca de ejemplos** que arranque a
> los proyectos futuros ya mejorados.
>
> **Relacionado:** `improvements_tl.md` (el log), comando `/consolidate-agent-learnings`
> (cosecha proyecto→template), skill `update-agent` (template→proyecto), `create-agent` /
> `crear-flujo` (crear assets), `examples/CATALOG.md` (biblioteca tipada), `governance.md` (autonomía).

---

## Dirección del flujo

```
proyecto detecta mejora ──► improvements_tl.md (log)
        │
        ├─ ¿necesita un asset (skill/agente/workflow/hook/rule)?
        │     └─ PROPONE → (OK del Usuario) → lo crea en SU .claude/   ← create-agent / crear-flujo
        │
        └─ /consolidate-agent-learnings ──► template cosecha lo validado
                                              └─ examples/CATALOG.md (tipado por proyecto)
                                                    └─ proyectos FUTUROS arrancan con el ejemplo

        ▲                                                                    │
        └──────────────── PODA (§5) ◄────────────────────────────────────────┘
           lo que no dispara, se degrada o se retira — el bucle también RESTA
```

> El bucle tiene **dos sentidos**. Añadir es el fácil y el que se hace solo; **podar es el que hay
> que agendar** (§5). Sin la fase de poda, esto es un trinquete: el harness solo puede crecer.

## 1. Regla de oro: **proponer y registrar** (no crear a lo loco)

Autonomía por defecto (coherente con `governance.md`):

1. **Registrar siempre**: toda mejora de config detectada se anota en `.claude/improvements_tl.md`
   del proyecto con el formato del propio archivo (Qué pasó → Impacto → Cambio propuesto → Estado).
   Esto es autónomo, no requiere permiso. **Un solo fichero, en `.claude/`**: uno en la raíz no lo leía
   nadie (musa, 37 entradas) y, si hay dos con entradas, la cosecha se para (§3b).
2. **Proponer el asset**: si la mejora implica crear un skill/agente/workflow/hook/rule, el agente
   lo **propone** (qué, por qué, alcance) y lo crea **solo tras OK** del Usuario, y **solo dentro del
   `.claude/` del proyecto**. Usa `create-agent` (agentes) o `crear-flujo` (TL/flujos/subagentes).
3. **No tocar el template desde el proyecto**: el proyecto nunca edita el template directamente. La
   subida proyecto→template va por `/consolidate-agent-learnings` (no destructivo, genera propuesta).

## 2. Cómo un proyecto **referencia el template**

El template es la fuente canónica. Un proyecto lo localiza con la env var **`TL_TEMPLATE_DIR`**
(default `/home/tech-lead-template`, **verificado en disco el 2026-08-08**). Antes aquí ponía
`/home/1_INSTALL/tech-lead-template` y en otros sitios `/home/1_install/…`; **ninguna de las dos
existe**, así que el mecanismo por el que un proyecto localiza el template llevaba tiempo roto en
los dos casos, y el aviso sobre mayúsculas distraía del fallo real: la ruta entera era otra.
Si mueves el template, cambia el default aquí **y** exporta `TL_TEMPLATE_DIR`. Si la ruta no es un
template, `cosechar_mejoras.py` (§3b) **para** con exit 2 en vez de seguir con una ruta vacía (musa #45).
Desde ahí puede:

- **Copiar/actualizar assets** existentes: skill `update-agent` (detecta qué hay en el template y
  falta en el proyecto, lo trae generalizado).
- **Ver ejemplos tipados**: `${TL_TEMPLATE_DIR}/.claude/examples/CATALOG.md` — qué assets han
  funcionado en proyectos de su mismo tipo (Django+React, FastAPI, chatbot, WordPress, analytics…).
- **Crear nuevos** a partir de los patrones del template: `create-agent`, `crear-flujo`,
  `workflow-creator`, `skill-authoring`.

## 2b. Encargos del template a un proyecto (`to_apply.md`) y su vuelta

Cuando un plan del template encarga trabajo a un proyecto (un arreglo que solo se puede hacer en su
repo, sea de config o de producto), no lo escribe en sus planes: lo pone en
**`to_apply.md`** en el `.claude/` del proyecto, que genera el plan del template con su
`herramientas/gen_to_apply.py` (hoy, el de `.docs/plans/2026-10-17-revision-integral-template/`). Sin
vuelta, el informe del template sigue diciendo `backlog` de algo hecho (medido el 2026-10-19: los 12
arreglos de T-094 seguían en `backlog` con 4 hechos en los proyectos — LI-4).

**Qué entra** (regla del Usuario, 2026-10-20): solo lo que la sesión del template **ya probó** (en el
laboratorio, sobre un clon o midiendo en el repo sin escribir), como acción exacta: el parche o los
comandos tal cual, cómo se probó y con qué resultado, y cómo comprobarlo después. Lo que falta por
probar, las decisiones y la hoja de ruta se quedan en el plan del template (`por_verificar.json`).

1. **El proyecto, al aplicar una entrada**, la marca en el propio `to_apply.md`: `- [x] … — hecho
   AAAA-MM-DD, commit <hash>` (o `- [!] … — no se aplica: <motivo>`). No la borra ni cambia su texto.
2. **La sesión del template que lleva el plan**, antes de regenerar, corre el simulacro
   (`gen_to_apply.py` sin `--aplica`): lista cada entrada **devuelta** y el generador conserva la marca.
3. **Esa misma sesión** pasa cada devuelta a su item del plan de origen (`status`, `evidence` con el
   commit, `history`) y, cuando ya no haga falta, la saca del generador. Cada línea conserva su casilla
   (`[>]` también), y una que añadió el proyecto se conserva como «huérfana». Lo que el template retira
   lo lista en `RETIRADAS` con su destino, y no se conserva al regenerar salvo que el proyecto lo haya
   marcado: regenerar nunca pierde lo que escribió el proyecto.

## 2c. Lo propio del proyecto, sin que la próxima sincronización lo pise (sub-ola 1.09)

La flecha template → proyecto también puede borrar: en elvion, el arreglo #17
(`hooks/auto-progress-log.sh` leyendo stdin, 2026-08-08) lo deshizo dos días después una
sincronización que copió encima la versión del template. Desde la 1.09, `template_diff.py` decide
por la **historia de git** si lo distinto es una versión vieja del template (se actualiza) o algo
escrito en el proyecto (LOCAL POSTERIOR o DIVERGENTE: `propagar.py` no lo pisa). Tres formas de que
lo propio sobreviva sin depender de eso:

1. **Una rule personalizada → fichero aparte** (MO-58): lo propio en `rules/<rule>-<proyecto>.md`
   con su `paths:` (o con otro nombre y `extiende: <rule>.md` en el frontmatter), y la del template
   intacta. Así se actualiza sin merge. Precedente: `seguridad-evo.md` junto a `security.md` en
   EvoPreven/develop, separados el 2026-10-14.
2. **Lo que diverge a propósito y no es una rule → `DIVERGENCIAS-DELIBERADAS.md`** (MO-57), en el
   `.claude/` del proyecto: tabla con la ruta (relativa a `.claude/`, entre comillas invertidas, en
   la primera celda), qué cambia y por qué, y la fecha en el título. El diff no la lista como STALE y
   avisa cuando el template cambió ese fichero después de la fecha. Precedente: webs, 2026-08-25.
   Es además la **única** protección de quien se queda a propósito con una versión VIEJA del
   template: para la historia de git eso es indistinguible de ir atrasado, y se actualizaría.
3. **Un arreglo que vale para todos → `improvements_tl.md`** (§1): cosechado en el template, deja de
   divergir. Es la salida buena de un LOCAL POSTERIOR.

## 3. Qué cosecha el template (y cómo lo archiva)

`/consolidate-agent-learnings` (ver su doc) lee de cada proyecto:

- `improvements_tl.md` (entradas no resueltas) → propuesta de cambios al template.
- **Memoria de agentes** (Lidia/Vera/… `memory.md`+`trend.json`) → calibración consolidada.
- **Assets nuevos creados en el proyecto** (skills/agents/workflows/hooks que no existen en el
  template) → candidatos a **`examples/`**, etiquetados por **tipo de proyecto** y con una nota de
  "por qué funcionó / cuándo usarlo". Así el template sabe **qué coger y para qué tipo**.

Un asset asciende de `examples/` (ejemplo concreto de un tipo) a asset **canónico** del template
cuando demuestra valor en **≥ 2 proyectos** o el Usuario lo aprueba como genérico.

### 3b. `improvements_tl.md` de ida y de vuelta — `scripts/cosechar_mejoras.py` (MO-38, 2026-10-21)

Medido el 2026-10-17: lo que proponían fitapp (12), evolution (#9-#12), elvion (≥8) y musa (37, en un
fichero de la raíz que no se leía) no llegaba al template, y **al revés nada volvía**: el proyecto no
se enteraba de que el template ya lo había resuelto y lo volvía a proponer. La ida y la vuelta usan lo
que ya existe — el `to_apply.md` de §2b — y un script, porque a mano se saltaba justo lo raro:

| Paso | Quién | Comando | Qué deja |
|---|---|---|---|
| **Ida** | el template | `cosechar_mejoras.py listar <proyecto>… \| --todos [--pendientes]` | Las entradas de `.claude/`, de la raíz y de cada worktree, cada una con su **clave** y su situación: sin cosechar · cerrada en el proyecto · decidida, falta la vuelta · devuelta. Dos ficheros con entradas → avisa y **no cosecha** ese proyecto (exit 1) |
| **Decidir** | el template (y el Usuario si toca) | `cosechar_mejoras.py registrar <proyecto> <clave> --estado resuelta\|cosechada\|descartada\|propia --donde "<commit · fichero §>"` | Una fila en `.claude/cosecha-mejoras.json` del template |
| **Vuelta** | el template | `cosechar_mejoras.py vuelta <proyecto> --json` | Por decisión sin devolver, la **acción exacta** para su `to_apply.md` (un `marcar` + commit por ruta), ya **probada sobre una copia** del fichero de ese día |
| **Marca** | el proyecto, desde su `to_apply.md` | `cosechar_mejoras.py marcar . <clave>` | Una línea en la sección final `## ↩ Vuelta del template` de su fichero; las entradas no se tocan (tampoco una tabla) y repetirla no duplica |

Una **entrada** es lo mismo que cuenta `gen_tareas_del_harness.py`: una sección `## ` o una fila de
tabla que empieza por fecha; una sección sin estado que no va numerada ni fechada (un índice, una
respuesta) es una nota. **La clave** es el número (`## 45. …` → `45`) o la fecha y las primeras
palabras: si el proyecto renumera, `listar` avisa de la clave que el registro tiene y el fichero ya no.
De EvoPreven (y de cualquier ruta de `SOLO_DOT_CLAUDE` del script) solo se lee `.claude/`.

## 4. Qué SÍ y qué NO va a este bucle

| Sí (config de Claude Code) | No (producto) |
|---|---|
| Un skill/agente/workflow/hook/rule útil | Una feature de la app |
| Un gotcha del harness (cache, permisos, OOM) | Un bug de negocio |
| Una mejora de un agente (calibración, protocolo) | Copy/diseño del producto |

Lo del producto va a la memoria/PROGRESS del proyecto, no a `improvements_tl.md`.

## 5. La fase de PODA (el bucle también RESTA)

Hasta aquí el bucle solo modela **añadir**. Con el inventario actual del template —22 rules, 61
skills, 34 agentes, 11 hooks— eso ya no es neutro: **el scaffolding de ayer es la jaula de hoy**.
Cada instrucción que no se usa compite por atención con las que sí, y un CLAUDE.md hinchado hace que
el agente ignore las reglas reales (lo dice la doc oficial: CLAUDE.md es *advisory*).

Podar **no es borrar**: casi siempre es **degradar de capa**. El contenido sobrevive donde se carga
solo cuando hace falta.

### El criterio 30/60

> ⚠️ **Aviso: la regla 30/60 es una heurística de un divulgador, NO de Anthropic.** No hay
> telemetría oficial que la respalde. Se adopta aquí como **criterio de auditoría** —una forma
> consistente de ordenar la conversación sobre qué sobra— **no como ley**. Un contraejemplo
> razonado gana a la regla: hay instrucciones que disparan poco y que, cuando disparan, evitan un
> desastre (el gate de RAM dispara en pocas sesiones y se queda).

| Señal | Lectura | Acción |
|---|---|---|
| Instrucción de **CLAUDE.md** que aplica en **<30%** de las sesiones | Está pagando contexto en el 70% de las sesiones que no la necesitan | **Baja a skill o rule con `paths:`** (sin `paths:` la rule se carga igual en todas las sesiones — `harness-gotchas.md` §Instrucciones) |
| **Skill** que dispara en **<60%** de las sesiones **donde sería relevante** | Casi siempre es la `description`, no la skill: el routing no la encuentra | **Reescribe la description** (triggers explícitos, ES+EN). Si tras el arreglo sigue sin dispararse → **skill muerta**, archívala |

El segundo caso es el que más se malinterpreta: un bajo disparo **no** prueba que la skill sobre.
Prueba que **no se encuentra**. Primero arreglas la puerta; solo si sigue sin entrar nadie, retiras
la habitación. Distinguir "mala description" de "asset muerto" es el trabajo real de esta fase.

### Qué mirar en cada barrido

- **Rules**: ¿alguna la cita el `INDEX.md`? Una rule sin ruta de entrada es una rule que nadie abre.
- **Skills**: solapes (dos skills para lo mismo → una gana, la otra se archiva) y descriptions sin
  triggers.
- **Agentes**: los que no se han invocado en todo el periodo; los que duplican a otro más afilado.
- **Hooks**: los que **no disparan** (verifícalo, no lo supongas — un matcher mal escrito falla en
  silencio; ver `harness-gotchas.md` §Los matchers de hook son regex y, en el template,
  `claude-code-referencia` §3) y los que ya no bloquean nada real.
- **Allowlist**: la poda trimestral de `permissions.allow` es parte del mismo barrido: cada entrada,
  ¿se usó?, ¿sigue siendo segura aquí?, ¿es más ancha de lo necesario?, ¿la cubre otra? Lo sano de
  `settings.local.json` se promociona; el `deny` no se poda. Criterio completo, en el template:
  `claude-code-referencia` §8.11 (antes `boris-permissions`, retirada el 2026-10-20).
- **CLAUDE.md**: ¿sigue por debajo del techo de ~120 líneas en root?

**Antes de hacerlo a mano, mide con `/doctor`** (alias `/checkup`). Hace automáticamente buena
parte de este barrido: encuentra skills, MCP y plugins sin usar **frente a su coste de
contexto**, marca los hooks lentos, deduplica y recorta los `CLAUDE.md` versionados. Reporta
primero y **pide confirmación antes de cambiar nada**, así que no choca con la regla de oro del
§1. Lo que no hace es decidir: la lista de arriba sigue siendo el criterio, y `/doctor` es de
dónde salen los números para aplicarlo (el 30/60 sin medición es una opinión).

### Dónde se engancha

En el **cierre semanal/trimestral**, no a mitad de una tarea: la retro o la revisión semanal
(§C/§D de `auto-dream-memory`) abre la fase de poda igual que abre la de mejoras. La salida es una **propuesta**, no un borrado: misma
regla de oro del §1 —se registra en `improvements_tl.md` y se retira con OK del Usuario—. Lo que se
poda del template va a `examples/` o al histórico con una nota de **por qué** se retiró, para que
nadie lo reintroduzca dentro de seis meses sin saber que ya se probó.

---

## 6. El círculo del DISEÑO — qué vuelve al sistema después de auditar

El §5 poda; esto añade, y con las mismas dos condiciones de siempre: que haya evidencia y que lo
firme un humano. Son **dos caminos distintos** porque los hallazgos de diseño son de dos clases.

### 6.1 De hallazgo a REGLA del gate (lo mecánico)

Candidata cuando el mismo tipo de hallazgo aparece **≥3 veces en ≥2 proyectos** (o en 3 iteraciones
del mismo) **y es detectable por una máquina**. El camino es obligatorio y no se acorta:

```
nace en `sombra`  →  par de fixtures `smoke/diseno/GD-XX/{malo,bueno}.html`  →  medición `--all`
   →  regla de inversión (¿marca >30 ficheros? entonces la mala es la regla)
   →  las 5 condiciones de `rules/refactor-progresivo.md` §4.5, incluida la quinta: la firma un
      humano, con fecha
```

**Una regla sin sus dos fixtures no sale de `sombra`**, y `gate_diseno.py --self-test` lo comprueba:
tiene que cazar su caso plantado **y** callar ante el gemelo conforme. Un detector que solo hace lo
primero no discrimina, hace ruido.

### 6.2 De hallazgo a entrada del CORPUS (lo de gusto)

Cuando el arreglo exigió una **decisión** y el resultado quedó bien, lo nuestro puede entrar como
referencia: `resources/referencias-diseno/propios/<proyecto>-<pantalla>/`, con el mismo manifiesto y
un `por_que_entra`. Tres condiciones:

1. Pasó el gate determinista.
2. Sacó **≥8,5 en el eje relevante durante dos rondas** — una no basta, porque una es ruido.
3. **Lo aprueba el Usuario.** El gusto no se auto-promociona, igual que ningún agente se
   auto-promociona de fase (`rules/agent-autonomy-ladder.md`).

Y entra con sus **defectos conocidos declarados**. Una entrada sin defectos no es una entrada
impecable: es una que nadie ha mirado — lo dice `scripts/corpus_lint.py`, y ya lo cazó el primer
día sobre dos entradas nuestras.

### 6.3 Que el corpus no envejezca — mecanismo, no buena intención

```bash
python3 .claude/scripts/corpus_lint.py     # 0 sano · 1 avisos · 2 no se pudo medir
```

Mide las tres formas en que un corpus de gusto se pudre sin que se note: **caduca** (>18 meses),
**se vuelve monocultivo** (una familia de sector por encima del 60 %, que produce exactamente el
mismo look genérico que el techo Stripe/Linear/Vercel que retiramos por eso) y **engorda** (tope de
15 entradas: meter una exige retirar otra con su razón escrita).

**No decide nada**: retirar una referencia es del Usuario. Lo que hace es que la decisión exista.

### 6.4 Cuándo

En el cierre de la retro o la revisión semanal (§C/§D de `auto-dream-memory`), junto a la poda del §5 — no a mitad de una tarea. Y
trimestralmente, `/consolidate-agent-learnings` sube al template lo que un proyecto haya aprendido.

---

## Anti-patterns

- ❌ **Modelar solo el "añadir"** y no agendar nunca la poda → el harness solo puede crecer.
- ❌ Aplicar el 30/60 como ley y borrar un gate crítico porque "dispara poco".
- ❌ Confundir "skill que no dispara" con "skill inútil" → primero arregla la `description`.
- ❌ Borrar en vez de degradar de capa (se pierde el contenido; casi siempre bastaba moverlo).
- ❌ Retirar un asset sin dejar escrito **por qué** → vuelve a nacer en seis meses.
- ❌ Podar a mitad de una tarea (y además lo que cambies en CLAUDE.md no se aplica hasta `/clear`,
  `/compact` o reiniciar — `harness-gotchas.md` §Caché).
- ❌ Crear skills/agentes en el proyecto sin proponer ni registrar en `improvements_tl.md`.
- ❌ Editar el template directamente desde un proyecto (rompe la fuente canónica; usa el comando).
- ❌ Subir como "genérico" algo que solo aplica a un proyecto (va a `examples/` tipado, no a canónico).
- ❌ Registrar mejoras de **producto** en `improvements_tl.md` (ese log es solo de config).
- ❌ Dejar `improvements_tl.md` con el ejemplo placeholder y nunca usarlo (el canal queda muerto).

---

_Rule version: 1.2 · 2026-08-08 — añadida la fase de PODA (§5) y el criterio 30/60 (TPL-9) ·
v1.2 (2026-08-22): §5 apunta a `/doctor` para medir el barrido, heredado de la retirada de
`rules/harness-gotchas.md` §comandos (rescató su contenido; la skill se archivó el 2026-08-22) (`_archive/2026-08-22/README.md`)._
