# Modo catálogo — qué tengo para esto y qué debería usar (antes `/sistema`)

> **Antes era la skill `sistema`**, fusionada en `otto` el 2026-10-19 (LI-25): tenía 0 usos y era
> una de las cinco puertas a «¿qué hago ahora?». El contenido es el mismo; lo que cambia es la
> puerta: `/otto <escenario>` o «¿qué tengo para esto?». Además, `dispatch-hint.sh` ya inyecta en
> cada prompt la fila que toca: este modo es para pedirla a propósito o para verlas todas.

## Principio

El harness tiene ~45 agentes, 67 skills, 22 commands, 8 workflows y un catálogo de plugins. **El
problema nunca fue que faltaran piezas: era que nadie te decía cuáles aplican en el momento de
trabajar.** `INDEX.md` rutea *qué leer*; este modo reparte *qué usar*.

No decide por ti y no ejecuta nada: te enseña la fila que te toca para que decidas con el mapa
delante en vez de de memoria.

## Cuándo activar / NO activar

| Activar | NO activar |
|---|---|
| Antes de arrancar un trabajo no trivial: "¿qué tengo para esto?" | Para saber **qué fichero leer** → `INDEX.md` |
| Cuando sospechas que hay una pieza que no estás usando | Para **configurar** un proyecto entero → `project-setup` |
| Al incorporarte a un proyecto y no saber qué hay montado | Para que alguien razone sobre **tu tarea concreta** y su estado → el modo jugada de `/otto` (`SKILL.md`) |
| Para ver todas las posibilidades de golpe (`/otto` en modo catálogo, sin escenario; antes `/sistema` sin argumento) | Para un typo o un cambio de una línea |

## Protocolo

### Con argumento — `/otto <escenario>`

Escenarios: `frontend` · `backend` · `revision` · `plan` · `qa` · `deploy` · `multiagente` · `config`.

```bash
python3 .claude/scripts/gen_agent_system.py --scenario frontend
```

Imprime la ficha: agentes, skills, plugins/MCP, workflows, rules y **el orden recomendado**.
Presenta la ficha tal cual y añade **una línea** de por qué esa pieza y no otra, si aplica al caso.

### Con texto libre — `/otto añade la pantalla de pedidos`

```bash
python3 .claude/scripts/gen_agent_system.py --detect "<lo que va a hacer>"
```

Si no reconoce el dominio sale con 1 y **no imprime nada**: entonces pregunta, no inventes un
escenario que no encaja.

### Sin argumento — una ronda de preguntas (solo si lo que se pide es el catálogo)

Usa `AskUserQuestion` (**una sola ronda**, nunca dos) con estas cuatro:

1. **¿Qué vas a tocar?** frontend · backend · infra/deploy · el propio harness · varias cosas
2. **¿Tamaño?** 1-3 ficheros · feature multi-fichero · módulo nuevo o refactor grande
3. **¿Va a producción?** sí · no (spike/desechable)
4. **¿Hay interfaz?** sí · no

Y con las respuestas devuelve **la jugada concreta**, no el mapa entero:

- La ficha del escenario que corresponda.
- Si tamaño ≥ feature multi-fichero → **recuerda el Gate 0**: el modo jugada de `/otto` y los gates
  de `rules/plan-gates.md`.
- Effort: `medium` por defecto, también para lo que va a producción; `high`/`xhigh` para el verificador y los auditores (`research-driven-planning.md` §Política de effort, CL-D4).
- Si hay interfaz → el cierre es screenshot + `ux-reviewer`, y `/qa-loop` si es una wave.
- Si el trabajo se puede partir → **antes** pasa el test de independencia
  (`parallelization.md` §0): repartir mal cuesta N contextos para una respuesta peor.

### Ver el mapa entero

`.claude/AGENT-SYSTEM.md` — está **generado**. Si sospechas que miente:

```bash
python3 .claude/scripts/gen_agent_system.py --check   # exit 1 si está desfasado
python3 .claude/scripts/gen_agent_system.py           # regenera
```

## Cómo se mantiene

Los escenarios viven en `SCENARIOS` dentro de `.claude/scripts/gen_agent_system.py`. Añadir una
pieza al harness y **no** añadirla ahí la deja invisible otra vez — que es exactamente el fallo que
este modo (antes la skill `sistema`) vino a arreglar. El generador avisa de las piezas declaradas que no existen en disco.

## Anti-patterns

- ❌ Volcar `AGENT-SYSTEM.md` entero en la conversación → son ~200 líneas; enseña **la fila**.
- ❌ Tratar la ficha como una lista de obligaciones: es lo que **tienes**, no lo que debes usar.
- ❌ Inventar un escenario cuando `--detect` calla → pregunta.
- ❌ Usar este modo para decidir por el Usuario lo que es suyo (`governance.md` §2).
- ❌ Editar `AGENT-SYSTEM.md` a mano → se regenera y pierdes el cambio.
- ❌ Hacer dos rondas de preguntas: una, y a trabajar.
