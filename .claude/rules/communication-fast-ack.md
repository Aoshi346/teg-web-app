---
paths:
  - "PROGRESS.json"
  - "**/PROGRESS.log"
  - ".claude/scripts/avisar.py"
  - ".claude/hooks/notify-telegram.sh"
  - ".specify/sessions/**"
---
# FAST-ACK — Acuse rápido con ETA antes de trabajo largo

> **La norma, en 3 líneas, está en `CLAUDE.md` (regla 4)** y se carga siempre. Este fichero es el
> detalle (patrón, cadencia, canales, anti-patrones) y entra solo al tocar `PROGRESS.json`, el
> canal de aviso o una sesión SpecKit (MO-46).

> **Cuándo aplicar:** siempre que vayas a iniciar una tarea que tardará más de unos segundos en
> producir output visible (research, generar un documento, una wave, un build, navegar la app).
> El usuario no debe quedarse en silencio sin saber qué estás haciendo ni cuánto tardarás.
>
> **NO aplicar:** respuestas inmediatas o triviales (un sí/no, un dato que ya tienes) — ahí
> responde directamente, sin preámbulo.

---

## Principio

Un acuse de <30s con un **ETA** mantiene al usuario en el loop y evita que repita la petición o
crea que el agente se colgó. Es barato y mejora mucho la percepción de control.

## Patrón

Antes de arrancar el trabajo largo, emite **una línea** que diga: (1) qué vas a hacer y
(2) cuándo vuelves con algo.

```
Voy a [acción concreta]; te enseño [resultado] en ~[N] min.
```

Ejemplos:
- "Voy a investigar las opciones de X; te traigo hallazgos en ~3-5 min."
- "Te preparo el plan; vuelvo en ~10 min con el draft."
- "Lanzo los tests del módulo; te aviso del resultado en ~2 min."
- "Genero el PDF y te paso el preview en ~1 min."

Si la tarea es muy larga (waves, /loop, research profundo), da **señales intermedias** en hitos
naturales ("Vera y Lidia ya terminaron; ahora aplico fixes") en vez de un único silencio hasta el final.

## Cadencia acordada para trabajo largo (AGT-9, aprobado 2026-08-07)

El ACK cubre el arranque. Para trabajo de más de ~20 minutos hay que cubrir también **el medio**:
entre el "vuelvo en 20 min" y el resultado no puede haber veinte minutos de silencio en los que el
Usuario no sabe si avanzas, te atascaste o te fuiste por otro camino.

**Al dar el ETA, nombra también los hitos y el canal.** Una línea más, no un párrafo:

```
Voy a [acción]; te enseño [resultado] en ~[N] min.
Te aviso además al [hito 1] y antes de [hito 2] — por [canal].
```

Ejemplos:
- "…te aviso al cerrar el backend y **antes de tocar la UI**."
- "…aviso al final de cada wave de la sesión SpecKit."
- "…un mensaje por iteración del `/loop`; si dos seguidas no mejoran, paro y te lo digo."

**Ata la señal a un hito real del trabajo, no a un reloj.** Avisar cada 10 minutos genera ruido y se
acaba ignorando; avisar cuando algo cambió de estado es informativo. Los hitos naturales ya existen
—son los puntos donde el agente para de todos modos— así que no hay mecanismo nuevo que montar:

| Trabajo | Hito natural donde se avisa |
|---|---|
| Wave de SpecKit | Cierre de cada wave (el gate `task_progress.py --gate` ya se corre ahí) |
| `/loop` | Cierre de cada iteración, y siempre al criterio de parada |
| QA loop | Fin de cada iteración con el score (`rules/qa-loop.md`) |
| Research largo | Cuando hay hallazgos que ya cambian el plan, sin esperar al informe |
| Cualquiera | **Al desviarse del plan acordado** — ese aviso no es opcional |

**Si un hito se pasa de largo**, el aviso es igualmente obligatorio y dice el nuevo ETA y por qué.
Un "voy tarde, me faltan 15 min por X" mantiene la confianza; el silencio la rompe.

## Integración con canales

- En canales asíncronos (Telegram, gateway), el acuse inicial **y** el cierre deben ser mensajes
  nuevos (no ediciones), para que el dispositivo del usuario notifique.
- Los estados canónicos siguen siendo los de `governance.md` (`INICIO`, `DONE`, `BLOCKED`, …);
  FAST-ACK es el `INICIO` con ETA explícito.
- **Se contesta por el canal por el que llegó el mensaje.** Si el turno entró como
  `<channel source="telegram" …>`, el acuse, las preguntas y el cierre van con la tool `reply` del
  plugin: lo que escribes en la terminal no le llega.
- **Preguntar cuando el canal es Telegram (MO-60):** la ventana de `AskUserQuestion` no llega allí y el
  comando se queda esperando una respuesta que nadie ve. Pregunta en texto, con opciones numeradas
  (`1) … 2) … 3) …` y «contesta con el número»), y sigue con la respuesta del siguiente mensaje. Vale
  para cualquier skill o comando que mande preguntar con `AskUserQuestion`.

## Anti-patrones

- ❌ Empezar un trabajo de minutos sin decir nada → el usuario no sabe si estás trabajando.
- ❌ Prometer un ETA y no volver a hablar hasta mucho después del plazo sin una señal intermedia.
- ❌ Acuse vacío sin contenido ("ok, lo hago") sin decir **qué** ni **cuándo**.
- ❌ Inflar el preámbulo: el acuse es **una línea**, no un párrafo.
- ❌ Prometer hitos intermedios y no emitirlos → peor que no haberlos prometido.
- ❌ Avisar a intervalo fijo de reloj ("cada 10 min: sigo trabajando") → ruido, se ignora.
- ❌ Desviarse del plan acordado y contarlo solo al final.

---

_Rule version: 1.3 · 2026-10-28 · la norma pasa a 3 líneas en CLAUDE.md y esto, bajo `paths:` (MO-46) ·
v1.2 · 2026-10-21 · +contestar y preguntar por el canal de entrada (MO-60, sub-ola 2.20) ·
v1.1 · +cadencia de reporte para trabajo largo (AGT-9, aprobado 2026-08-07)_
