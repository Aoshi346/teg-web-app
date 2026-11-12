---
name: "harness-telemetry"
description: >-
  Usar cuando haya que responder con datos sobre nuestro uso del harness: '¿qué agente/wave salió
  caro?', '¿cuánto costó este plan?', '¿este workflow compensa?', 'activa OpenTelemetry en Claude
  Code', '/harness-telemetry'. NO usar para: la sesión del usuario (/insights), monitorizar la
  aplicación que construimos ni la calidad de un agente auditor (su trend.json, rules/qa-loop.md).
user-invocable: true
metadata:
  version: 1.0.0
  author: AGT-5 (absorbe SEC-7 y ND-7)
  category: meta
  updated: 2026-08-08
---

# harness-telemetry — medir nuestro propio uso del harness

## Principio

No medimos nada de lo que hacemos. Sabemos cuántas waves cerramos, pero cuando una sale cara no hay
forma de saber **qué se comió el presupuesto**: si fueron los 16 agentes de un workflow, un `/loop`
que se quedó dando vueltas, o simplemente que el plan era grande. Esta skill recoge lo que **ya es
legible en disco** y lo convierte en un informe por periodo, para poder decidir con datos qué
mecanismos compensan y cuáles no.

> **Esta skill absorbe tres propuestas que se solapaban** (AGT-5 telemetría de agentes, SEC-7 rule
> de observabilidad y alertas, ND-7 preset de OpenTelemetry). Se decidió el enfoque **una vez**:
> escribir tres piezas que se pisan produce el mismo efecto que no escribir ninguna — nadie sabe
> cuál abrir. Las alertas viven en §5 y el preset en §2.

## Cuándo activar

- Al **cerrar un plan o una wave grande**: cuánto costó y dónde se fue.
- Cuando alguien propone **montar un workflow** y hay que decidir si compensa (`/otto` pide
  este dato para justificar el gasto).
- **Mensualmente**, si el harness está en varios proyectos.
- Al **activar la telemetría** de Claude Code por primera vez en una máquina (§2).
- Cuando haya que montar **alertas** sobre algo (§5).

**No la actives** para una sola sesión corta: el informe no dice nada útil con 20 tool calls.

Disparadores: '¿qué agente/wave salió caro?', '¿cuánto costó este plan?', '¿este workflow
compensa?', 'mide el coste en tokens', 'telemetría del harness', 'activa OpenTelemetry en Claude
Code', 'monta alertas que no acabemos silenciando', '/harness-telemetry'. Lee el audit log de los
hooks, la telemetría OTel si está activa y los .jsonl de los agentes, y emite un informe por periodo
con coste, actividad, latencia y reintentos. · NO usar para: analizar la sesión del USUARIO y sus
patrones de fricción (eso es el comando integrado /insights), monitorizar la APLICACIÓN que
construimos (métricas de negocio, uptime de producción), ni medir la calidad de un agente auditor
(eso es su trend.json y rules/qa-loop.md).

---

## 1. Qué se puede medir HOY, y qué no (léelo antes de prometer nada)

Esta tabla es la mitad del valor de la skill. Prometer un panel de coste por subagente y entregar
otra cosa quema la credibilidad de la medición entera.

| Pregunta | ¿Se puede? | Fuente |
|---|---|---|
| ¿Cuánto costó en € y tokens esta **máquina/usuario** este mes? | ✅ Sí | OTel (§2) |
| ¿Cuántas **sesiones**, commits y PRs? | ✅ Sí | OTel (§2) |
| ¿Qué **actividad** hubo por día/hora, y de qué tipo (Write/Edit/Bash)? | ✅ Sí | audit log (§3) |
| ¿Qué **ficheros** concentran el trabajo (churn)? | ✅ Sí | audit log (§3) |
| ¿Cuánto duró de reloj una wave? | ✅ Sí | audit log (§3) |
| ¿Se **aceptan** las sugerencias de Otto y los hallazgos de Rita? | ✅ Sí | `suggestions.jsonl`, `telemetry.jsonl` (§4) |
| **¿Cuánto costó CADA subagente por separado?** | ❌ **NO** | ver el aviso de abajo |
| ¿Cuántos reintentos hizo un subagente? | ⚠️ Solo si el workflow lo registra | salida del workflow (§4) |

> ⚠️ **El límite duro, y por qué.** Claude Code **no propaga las variables `OTEL_*` a los
> subprocesos que lanza** (Bash, hooks, servidores MCP). Y el audit log de los hooks **no lleva
> identificador de sesión ni de agente**: sus campos son `ts`, `tool`, `file`/`cmd`, `prev`, `h`.
> Con esas dos cosas juntas, **el coste no se puede atribuir a un subagente concreto** — solo a la
> sesión que lo lanzó.
>
> Lo que haría falta para cerrarlo: añadir `session_id` (y, si existe, el nombre del agente) al
> registro que escribe `.claude/hooks/audit-log.sh`. Es un cambio de una línea en el diccionario
> `rec`, **pero toca un hook registrado y eso requiere aprobación** (`rules/governance.md` §2).
> Propónlo; no lo apliques por tu cuenta desde esta skill.
>
> Hasta entonces: **informa de coste por sesión y de actividad por agente, y di que son ejes
> distintos.** No los multipliques para "estimar" el coste de un agente; eso es inventarse el dato.

---

## 2. Activar la telemetría OTel (el preset — absorbe ND-7)

**Qué es OpenTelemetry, sin jerga.** Un estándar para que una herramienta emita métricas hacia un
sistema que las guarda y las pinta. Claude Code lo trae de serie: se enciende con una variable y
empieza a mandar coste, tokens, sesiones, líneas de código, commits y PRs.

**Preset listo para copiar:** `documentation/settings-examples/settings.otel.json`.

```jsonc
"env": {
  "CLAUDE_CODE_ENABLE_TELEMETRY": "1",
  "OTEL_METRICS_EXPORTER": "otlp",
  "OTEL_LOGS_EXPORTER": "otlp",
  "OTEL_EXPORTER_OTLP_PROTOCOL": "grpc",
  "OTEL_EXPORTER_OTLP_ENDPOINT": "http://localhost:4317"
}
```

Métricas que emite (nombres con prefijo `claude_code.`): `cost.usage` · `token.usage` ·
`session.count` · `lines_of_code.count` · `commit.count` · `pull_request.count` ·
`active_time.total`.

⚠️ **Verifica los nombres de variables y métricas contra la doc oficial antes de desplegar.** Este
contrato lo fija Anthropic y cambia entre versiones; un preset desactualizado da un panel vacío que
parece que funciona.

**Para probar sin montar nada** (no hace falta un backend de métricas):

```bash
CLAUDE_CODE_ENABLE_TELEMETRY=1 OTEL_METRICS_EXPORTER=console claude -p "di hola"
```

**Antes de encenderlo, decide dos cosas** — un preset de telemetría sin esa decisión es
configuración muerta que da falsa sensación de observabilidad:

1. **A dónde va.** ¿Un colector local? ¿Un servicio de pago? Si no hay destino, `console` y ya.
2. **Quién lo mira y cuándo.** Sin lector, es coste recurrente sin retorno — el mismo argumento que
   frena a `competitive-intel`.

⚠️ **Privacidad:** `OTEL_LOG_USER_PROMPTS=1` **manda el contenido de tus prompts** al colector. En
un repo de cliente eso es una fuga de datos con otro nombre (`rules/ai-assistant-risk.md`). Déjalo
apagado salvo decisión explícita y escrita.

---

## 3. Informe desde el audit log (funciona ya, sin activar nada)

Fuente: `~/.claude/audit/<proyecto>.jsonl`, que escribe el hook `audit-log.sh` en cada `Write`,
`Edit` y `Bash`. Está **fuera del repo** a propósito y lleva cadena de hashes.

**Paso 0 — integridad primero.** Un informe sobre un log manipulado no vale nada:

```bash
bash .claude/hooks/audit-log.sh --verify
```

**Paso 1 — agregación.** Verificado contra un log real de 2.548 entradas:

```bash
python3 - <<'PY'
import json, collections, os, sys, datetime
proj = os.path.basename(os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd()))
path = os.path.expanduser(f"~/.claude/audit/{proj}.jsonl")
DAYS = int(sys.argv[1]) if len(sys.argv) > 1 else 30
cut = (datetime.datetime.now(datetime.timezone.utc)
       - datetime.timedelta(days=DAYS)).strftime("%Y-%m-%dT%H:%M:%SZ")

byday, bytool, files, hours = (collections.Counter() for _ in range(4))
first = last = None; n = bad = 0
for line in open(path, encoding="utf-8"):
    line = line.strip()
    if not line: continue
    try: r = json.loads(line)
    except json.JSONDecodeError: bad += 1; continue
    ts = r.get("ts", "")
    if ts < cut: continue
    n += 1
    first = first or ts; last = ts
    byday[ts[:10]] += 1; hours[ts[:13]] += 1; bytool[r.get("tool", "?")] += 1
    if r.get("file"): files[r["file"]] += 1

print(f"# Telemetría del harness · {proj} · últimos {DAYS} días")
print(f"tool calls: {n}   ventana: {first} → {last}   líneas ilegibles: {bad}")
print(f"por tool:   {dict(bytool)}")
print(f"días activos: {len(byday)}   horas activas: {len(hours)}   "
      f"pico: {max(byday.values(), default=0)} calls/día")
print("\n## Ficheros con más churn (candidatos a refactor o a conflicto entre frentes)")
for f, c in files.most_common(10):
    print(f"  {c:4d}  {f}")
print("\n## Actividad por día")
for d in sorted(byday):
    print(f"  {d}  {'#' * min(60, byday[d] // 10)} {byday[d]}")
PY
```

**Cómo se lee la salida:**

| Señal | Lectura |
|---|---|
| Un fichero muy por encima del resto en churn | O es el corazón del proyecto, o dos frentes se lo están disputando (`parallelization.md` §file claims) |
| Muchísimos `Bash` frente a `Write`/`Edit` | Se está explorando/verificando más que produciendo. Normal en una auditoría; sospechoso en una wave de implementación |
| Un pico de un día con el resto plano | Ahí hubo una wave. Cruza con `git log --since` para ponerle nombre |
| `líneas ilegibles > 0` | El log tiene entradas corruptas — corre `--verify` y averigua por qué |

---

## 4. Address-rate de los agentes que ya se auto-registran

Dos agentes ya escriben su propia telemetría. Es el eje de **si sirven**, distinto del de cuánto
cuestan:

```bash
# Otto: ¿cuántas de sus sugerencias se aplicaron?
python3 -c "
import json,collections
c=collections.Counter(json.loads(l)['outcome'] for l in
  open('.claude/agents/otto-copilot/suggestions.jsonl') if l.strip())
print('Otto ·', dict(c))"

# Rita: hallazgos en sombra y su desenlace
wc -l .claude/patterns/telemetry.jsonl 2>/dev/null
```

Regla de lectura (la misma que aplica Otto a sí mismo, regla O-3): **si un TIPO de sugerencia se
ignora 3 veces seguidas, el problema es la sugerencia, no el lector.** Un address-rate bajo
sostenido es la señal para degradar de fase al agente (`rules/agent-autonomy-ladder.md`), no para
insistir más fuerte.

**Reintentos de un workflow:** solo se pueden contar si el workflow los registra. Si estás
escribiendo uno, emite una línea por reintento con el agente y el motivo — es el dato que dice si
el fan-out está fallando por diseño (`skill workflow-creator`). Recuerda el tope: **máximo 1
reintento y escalar al humano** (`parallelization.md` §0).

---

## 5. Alertas que no se acaben silenciando (absorbe SEC-7)

Aplica a las alertas del **harness** y a las de la aplicación por igual. La distinción de fondo:
**la monitorización responde CUÁNDO algo va mal; la observabilidad responde POR QUÉ.** Hacen falta
las dos y se diseñan distinto — un panel con todo en verde no te dice por qué el pico de ayer.

Cuatro prácticas, en orden de impacto:

| # | Práctica | Qué evita | Cómo se hace |
|---|---|---|---|
| 1 | **Umbrales precisos** | El ruido que enseña a ignorar | El umbral sale del percentil real observado (p95 de la última semana), no de un número redondo elegido a ojo |
| 2 | **Agrupar avisos parecidos** | 40 mensajes del mismo incidente | Una alerta por **causa**, no por síntoma. Si diez servicios caen porque cayó la base de datos, es una alerta |
| 3 | **Foco en lo persistente** | Despertar a alguien por un pico de 20 segundos | La alerta exige duración (`for: 5m`): "por encima del umbral **durante** X", no "una vez" |
| 4 | **Alertas como código** | Que nadie sepa quién cambió el umbral ni por qué | El fichero de alertas vive en el repo, se revisa en PR y se despliega con el resto de la infra |

**La prueba de que una alerta está bien puesta**, y es una sola pregunta: *cuando salte a las 3 de
la madrugada, ¿hay algo que la persona que la reciba pueda hacer?* Si la respuesta es no, no es una
alerta: es un panel. Muévela al panel.

> ⚠️ Una alerta que se silencia sistemáticamente es **peor que no tenerla**: entrena al equipo a
> ignorar el canal, y el día que llegue la que importa también se ignorará. Es el mismo mecanismo
> que la fatiga de aprobación (`agent-security.md`, ASI09) y el gate de patrones que grita contra
> código viejo (`refactor-progresivo.md` §0). Si una alerta lleva un mes sin accionarse, **se borra
> o se recalibra** — no se deja "por si acaso".

---

## Formato de salida (estructurado, no prosa)

```
periodo:        <YYYY-MM-DD → YYYY-MM-DD>
proyecto:       <slug>
coste_eur:      <número> | "no medido (OTel apagado)"
tokens:         <número>  | "no medido"
sesiones:       <número>  | "no medido"
tool_calls:     <número>            ← audit log, siempre disponible
dias_activos:   <número>
top_churn:      [{fichero, calls}]  ← 10 primeros
address_rate:   {otto: <n aplicadas>/<n totales>, rita: …}
alertas_activas: <número> · silenciadas_sin_accion_30d: <número>
gaps:           ["coste por subagente: NO atribuible — ver §1", …]
```

El campo `gaps` **es obligatorio y no puede ir vacío**: si no declaras qué no mediste, el informe se
lee como si lo midiera todo.

---

## Anti-patterns

- ❌ Presentar coste **por subagente** — no es atribuible hoy (§1). Estimarlo repartiendo el coste
  de la sesión entre los agentes es inventarse el dato.
- ❌ Encender OTel sin haber decidido a dónde van los datos y quién los mira → configuración muerta
  con falsa sensación de observabilidad.
- ❌ `OTEL_LOG_USER_PROMPTS=1` en un repo de cliente sin decisión escrita → fuga de datos.
- ❌ Copiar los nombres de las métricas de esta skill sin verificarlos contra la doc oficial.
- ❌ Sacar el informe sin correr `audit-log.sh --verify` antes.
- ❌ Umbrales redondos elegidos a ojo (`>1000`) en vez del percentil observado.
- ❌ Una alerta por síntoma en vez de por causa → 40 mensajes del mismo incidente.
- ❌ Dejar una alerta que lleva un mes silenciándose "por si acaso".
- ❌ Escribir una rule/skill nueva de observabilidad → esta es el paraguas; amplíala aquí (fue la
  decisión explícita al fusionar AGT-5 + SEC-7 + ND-7).
- ❌ Medir para poner un número en un informe. Si nadie va a cambiar una decisión con el dato, no
  lo midas.

## Ejemplos

### User: "cerramos la wave 3, ¿cuánto nos ha costado este plan?"
TL: corre `--verify`, saca el informe de §3 acotado a los días de la wave, cruza con OTel si está
activo, y entrega el bloque estructurado **con `gaps` relleno** ("coste por agente: no atribuible").

### User: "¿monto un workflow para el review de cada rama?"
TL: mira en §3 cuántas ramas se revisaron el último mes (¿son ≥5, que es el umbral de Otto para que
compense un fan-out?) y en §4 si el gate se acepta o se ignora. Si se ignora, el workflow multiplica
por 16 algo que nadie lee.

### User: "quiero que me avise cuando el harness se dispare de coste"
TL: §5 — primero saca el p95 del gasto diario de las últimas semanas (§2), y ese es el umbral. Antes
de montarla, la pregunta de las 3 de la madrugada: ¿qué haría quien la reciba?

## Related

- `documentation/settings-examples/settings.otel.json` — el preset de §2 (ND-7)
- `.claude/hooks/audit-log.sh` — la fuente de §3; `--verify` comprueba la cadena de hashes
- `rules/agent-security.md` §9 — por qué existe el audit log (observabilidad ≠ prevención)
- **Tres cosas distintas que se confunden — quién mide qué** (heredado de el comando integrado `/insights` (la skill se archivó el 2026-08-22),
  archivada 2026-08-22: era la ficha de un comando integrado que ya se describe solo):

  | Pregunta | Herramienta | Sujeto |
  |---|---|---|
  | ¿Qué haces **tú** mal? (fricción, malentendidos, patrones) | `/insights`, integrado | el usuario |
  | ¿Qué **sobra** en la instalación? (skills/MCPs/plugins sin usar, hooks lentos) | `/doctor` (alias `/checkup`) | el harness |
  | ¿Cuánto **cuesta** y dónde se va el tiempo? | **esta skill** | el harness |

  `/insights` existe y es oficial en el build instalado — *"Generate a report analyzing your Claude
  Code sessions"* (v2.1.240, cadena verificada en el binario). Lo que la skill archivada añadía
  encima venía de una fuente fan-made y **ella misma lo marcaba `❓ sin verificar`**.
- `rules/agent-autonomy-ladder.md` — el address-rate de §4 es la evidencia para promocionar o
  degradar a un agente
- `rules/parallelization.md` §0 — el tope de 1 reintento que §4 mide
- `/otto` — el consumidor natural de este informe: justifica sus recomendaciones de coste
