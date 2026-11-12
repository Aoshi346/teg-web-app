---
paths:
  - ".claude/agents/**"
  - ".claude/commands/qa-loop.md"
  - ".claude/hooks/judge-write-guard.sh"
  - ".claude/scripts/judge_write_guard.py"
  - ".claude/scripts/gate_auditor.py"
  - ".claude/scripts/agent_registry.py"
  - ".claude/scripts/fleet_policy.py"
  - ".claude/scripts/incident_cases.py"
  - ".claude/scripts/drift_sweep.py"
  - ".claude/scripts/zona.py"
  - ".claude/templates/zonas.yaml"
  - ".claude/zonas.yaml"
  - ".claude/smoke/jueces/**"
  - ".docs/feedback/**"
  - ".docs/evals/**"
  - "**/acta.json"
---
# Equipo de auditores — quien revisa no es quien hizo, por puertas y con topes

> **Cuándo aplicar:** al cerrar cualquier puerta de trabajo (plan, código, UI, cierre, producción) o
> una wave/sub-ola; al decidir **cuántos jueces** lanzar y **cuántas rondas**; al diseñar un juez nuevo
> o tocar sus herramientas; al medir si un juez sirve; y al montar los barridos periódicos de un
> proyecto (incidentes como evals, deriva del código, mapa de zonas).
>
> **NO aplicar:** para promocionar a un agente de fase (`agent-autonomy-ladder.md`) ni para el
> formato del veredicto (`verdict-contract.md`). Tampoco a un bugfix de 1-3 ficheros sin wave: ahí
> basta el nivel 1-2 de `verification.md` §Gate de verificación.
>
> **Relacionado:** `qa-loop.md` (la puerta de UI en detalle) · `verification.md` §Nivel 4 (el verificador
> con contexto limpio y GRF-6) · `parallelization.md` §Agent Teams (RAM) · `governance.md` §3.1 ·
> `self-improvement-loop.md` · `AGENT-SYSTEM.md` §Puertas (generado).
>
> **Origen:** sub-ola 3.11 de la revisión integral (EQ-1, EQ-D8, EQ-D13, EQ-D14, EQ-19, EQ-20, EQ-36,
> EQ-40, EQ-41, EQ-D24), aprobados por el Usuario el 18-10 con su recomendación. §6b: sub-ola 3.01
> (EQ-3).

---

## 1. El principio: siempre un auditor detrás, y nunca es quien hizo el trabajo

El mismo agente no es un escéptico honesto de su propio trabajo, y dejar a su memoria que se acuerde
de lanzar a alguien es lo que fallaba: los auditores existían y se lanzaban «cuando alguien se
acordaba». Por eso cada fase tiene su auditor obligatorio **y** un gate que lo comprueba:

| Fase | Auditor obligatorio | Gate determinista |
|---|---|---|
| Plan (>3 ficheros) | `pol-product-advisor` o un verificador con contexto limpio sobre el `[PLAN]` | `plan-gates.md` (Gate 0b, 0) |
| Código (pre-merge) | `code-review-gate` + verificador limpio; con bot, `nadia`/`dario`; lógica, `marco` | `gate_auditor.py` sobre el acta · `/code-review` |
| UI (cierre de wave con UI) | Lidia + Vera + Ignacio (`/qa-loop`); Aitor/Lena si hay a11y o idiomas | `gate_diseno.py` + `gate_auditor.py` |
| Seguridad / datos | `sofia-pentester` en staging, `priya-privacy-auditor` | `smoke/seguridad/correr.sh` · gates G1-G8 |
| Cierre de wave o sub-ola | verificador con contexto limpio contra los items | `task_progress.py --gate` + `gate_auditor.py` |
| Producción | `bruno-perf-cop`; `nadia` sobre trazas si hay bot | `/deploy` (con OK) |

**Hasta que Roberto (auditor de código) y Pilar (impacto/BBDD) existan y pasen su fixture (sub-ola
3.07)**, su hueco lo cubre `code-review-gate` + un verificador con contexto limpio. Desde la 3.07
están medidos con fixture (`smoke/calibracion/auditores/`, `calibrar_auditor.py --clave`) y siguen en
fase 1: informan **junto a** `code-review-gate`, no en su lugar, hasta que el Usuario firme el paso.

**El acta de puerta** es lo que hace comprobable el principio. Al cerrar una puerta, el orquestador
deja `acta.json` junto a los informes (en `/qa-loop`: `.docs/feedback/qa-loop/<WAVE>/iter-<n>/acta.json`)
y corre el gate:

```bash
python3 .claude/scripts/gate_auditor.py --ejemplo                      # un acta mínima válida
python3 .claude/scripts/gate_auditor.py <ruta>/acta.json               # 0 cumple · 1 no · 2 ilegible
```

Comprueba: ≥1 auditor y ninguno es el `autor` (A1); cada informe existe y no es un esqueleto (A2); los
topes de §3 (A3, A4); la validación de §4 en las puertas de código y UI (A5); y que un `pass` no
lleve un P0 abierto (A6). **`/qa-loop` no cierra sin él** (`commands/qa-loop.md`, paso 6). Lo que no
comprueba: que el auditor mirase bien ni que el autor declarado sea el real (eso lo da el registro, §6).

## 2. El flujo por puertas y el organigrama (EQ-20)

El orden es **plan → código → UI → cierre → producción**, y no se mezclan: fitapp lanzó 11 jueces
dos veces mezclando la puerta de código con la de UI en la misma ronda. Las tres reglas de orden:
la foto de impacto (Pilar PRE) antes del código; los jueces de código antes que los de UI (la UI de un
código que no pasa no se audita); la pentester al final, en staging.

| Rol | Quién | Qué hace |
|---|---|---|
| Tech Lead | **la sesión principal** | Orquesta, hace de arquitecto en plan mode, integra y aplica los arreglos |
| Constructores | `desarrollador-backend`, `ivan-agent-runtime`, `rafa-retrieval-engineer`, `desarrollador-frontend` (3.13: portador de skills, opcional) | Construyen en worktree con sus skills precargadas. Tienen Edit |
| Jueces | todos los agentes sin Edit | Informan, no arreglan (§5). Por puertas, con topes (§3) |

**No se crean** un arquitecto, un orquestador ni un SRE como agentes: el orquestador-agente «mete una
capa de opinión» entre el Usuario y el trabajo, y el arquitecto es el TL en plan mode. La tabla de
puertas con sus jueces la genera `gen_agent_system.py` en `AGENT-SYSTEM.md` §Puertas, con los que aún
no existen tachados. Sin prueba A/B todavía: se mide en un issue real (§6).

## 3. Topes: ≤5 jueces por puerta, ≤3 rondas solo sobre el diff (EQ-D8)

| Tope | Valor | Por qué |
|---|---|---|
| Jueces por puerta | **≤5** | *«Three focused teammates often outperform five scattered ones»* (doc oficial de agent teams) |
| Jueces con navegador a la vez | **≤3** | RAM: el navegador cuenta doble (`check-ram.sh --explain`) |
| Rondas de una puerta | **≤3**; de la 2ª en adelante, **solo sobre el diff** | Perseguir todos los hallazgos de un revisor lleva a sobreingeniería |
| Batería completa (todos los jueces) | **solo en un hito de release**, nunca por issue | Multiplica coste y tiempo sin evidencia de que encuentre más |

En el acta: `hito_release: true` levanta los dos primeros topes y el de rondas; sin él, el gate los
exige (A3, A4). Pasado el tope sin converger, se escala al Usuario con lo que hay, no se abre una
cuarta ronda. Decisión aplicada: opción A de EQ-D8 (la recomendada; reversible).

## 4. Cada hallazgo P0/P1 lo valida un segundo agente (EQ-D13)

Tras cada puerta de **código** y de **UI**, un segundo agente con contexto limpio intenta confirmar o
tumbar cada hallazgo P0/P1; al Usuario solo le llegan los confirmados, y el acta los distingue
(`validacion: confirmado | descartado`, `validador`, `evidencia`). Es lo que hace el plugin oficial
`code-review` (un subagente valida cada incidencia: *«If you are not certain an issue is real, do not
flag it»*) y lo que ya hacía `workflows/review-branch.js` en su fase Verify.

Dos condiciones para que la validación valga (`verification.md` §Nivel 4, GRF-6): el validador **recibe
el material crudo** (el diff, el DOM, la captura), no solo la conclusión del juez; y **cita lo que vio**
(`evidencia`: `fichero:línea`, selector, salida del comando). Un «confirmado» sin evidencia propia es
un eco, y el gate lo rechaza (A5). Coste: una pasada más por puerta, a cambio de menos ruido.
Decisión aplicada: opción A de EQ-D13 (código y UI; la de plan y cierre no lo exigen).

## 5. Los jueces no escriben fuera de su zona — un hook, no una intención (EQ-D14)

De los 29 agentes, 24 no tienen Edit y se presentaban como jueces «sin poder de escritura», pero
tienen Write y Bash: Write reescribe un fichero entero y Bash hace `sed -i`. Si el juez puede «arreglar
de paso», su veredicto deja de ser independiente.

**El mecanismo:** `hooks/judge-write-guard.sh` (PreToolUse sobre Write, Edit, MultiEdit, NotebookEdit y
Bash, registrado en `settings.json`). Claude Code le pasa `agent_type` cuando la tool la llama un
subagente; si ese agente tiene ficha en `.claude/agents/` con `tools:` y **sin Edit**, es un juez, y
solo puede escribir en su zona (`agents/shared/judge-write-zones.json`): `.docs/feedback/`, su carpeta
`.claude/agents/<él>/` (memoria, trend), `/tmp/` y las extra de cada uno (`.docs/negocio/` para los de
negocio, `.docs/plans/*/feedback/` para Pol, `.docs/plans/*/impacto/` para Pilar…; Roberto, solo
`.docs/feedback/`). Fuera → exit 2 y el motivo, que lee el juez.

- La sesión principal y los agentes con Edit no pasan por aquí (vía rápida en bash, sin python).
- Si el detector se rompe, bloquea **solo** las llamadas de subagentes; la sesión principal nunca.
- **Bash es heurístico**: ve redirecciones (también tras un heredoc), `tee`, `sed -i`, `cp`/`mv`/`rm`,
  `curl -o`, `git` que escribe, el código en línea que abre ficheros, lo de dentro de `bash -c`/`eval` y
  los `cd` del comando; no ve un script en fichero que escribe por su cuenta ni rutas en variables. Por
  eso el hook es la segunda capa: el juez sigue sin Edit y su encargo dice qué no toca.
- Un juez nuevo que necesita escribir en otra carpeta: se añade a `extra` en el JSON, no se le da Edit.

Comprobado con un intento plantado (el «Verifica» de la sub-ola): `python3 .claude/smoke/jueces/correr.py`
— Vera escribiendo `frontend/src/App.tsx`, `sed -i`, `git commit`, `mv` de vuelta al código, `..` para
salir de la zona → bloqueado; su REPORT, su memoria, `/tmp`, `git diff` → pasa. Decisión aplicada:
opción A de EQ-D14, con el OK del plan para `settings.json`.

## 6. Medir el equipo — sin medición, el organigrama es opinión (EQ-19)

| Medida | De dónde sale | Cómo |
|---|---|---|
| **Uso por agente** | `~/.claude/registry/<proyecto>/agentes.jsonl` (cada lanzamiento, hook `agent-registry-log.sh`) y el audit log, que desde la 3.11 lleva `by` (el `agent_type` de cada tool call) | `agent_registry.py report` · `audit_log.py buscar` |
| **Acierto y falsos positivos por juez** | el fixture con errores plantados (`qa-loop.md` §4b, `calibrar_auditor.py`) | al estrenar, al cambiar su prompt y cada trimestre |
| **Validados ÷ emitidos** | la validación de §4, registrada al cerrar la puerta | `agent_registry.py add … --puerta ui --validados 5 --descartados 2` |
| **Ablación** | repetir un issue cerrado **con y sin** el juez al cambiar de modelo | si su ausencia no cambia el resultado, sale del núcleo |
| **Coste por puerta** | `/usage` (reparto por subagente) u OTel (`harness-telemetry`) | `agent_registry.py report` agrupa rondas y hallazgos por puerta; los tokens, de ahí |

**El umbral:** con ≥10 hallazgos juzgados, un juez con menos del 50 % validado se **recalibra** (fixture,
prompt) o se **jubila**; `agent_registry.py report` lo lista. Lo decide el Usuario con el dato
delante, igual que la promoción de fase. Agent teams multiplica los tokens: una ablación con teams,
solo con aprobación.

### 6b. Política de flota: alta con 4 condiciones, baja con el dato (EQ-3)

Sin criterio escrito, la flota solo crece y los proyectos heredan agentes sin dueño. Un agente se
gana su sitio; si deja de sostener peso, sale (*«removing pieces that are no longer load-bearing»*).

**Alta — las cuatro, o no entra:**

| # | Condición | Dónde se ve |
|---|---|---|
| a | Aporta **juicio con contexto limpio** que no da una skill (si solo trae saber, es una skill: Elena → `agent-evals`) | su `## No soy` / `## No hago` / `What You Do Not Do` y el «NO usar para» |
| b | Declara su **`error_cost`** | frontmatter y cuerpo (`agent-autonomy-ladder.md` §6.1) |
| c | Si es **juez** (sin Edit), tiene **fixture** con errores plantados (`qa-loop.md` §4b) | `fixture:` en el frontmatter, o `agents/<x>/fixtures/`, o `agents/<x>/calibracion.md` |
| d | Tiene **dueño**: una persona o un rol que responde de él | `owner:` en el frontmatter |

**Baja:** un juez sin fixture y con **0 usos en un trimestre** es candidato a pack o a `_archive/`
(nunca se borra: el protocolo pasa antes a la pieza que lo absorbe, medido como en la 3.01). Lo decide
el Usuario con el dato delante, igual que el umbral de §6. «0 usos» es «0 observados»: un proyecto sin
registro en esta máquina no aporta un cero.

```bash
python3 .claude/scripts/fleet_policy.py [--root <proyecto>] [--strict]   # tabla a·b·c·d, usos y candidatos
python3 .claude/scripts/fleet_policy.py --self-test                       # un defecto plantado por condición
```

Lo corre `check-agent` (aviso, no bloquea). Primera pasada, el 02-11-2026 en el template: 31 de 32 sin
`owner:`, 24 de 26 jueces sin fixture y 4 sin frontera en el cuerpo (Lidia, Marco, Rita, Sofía: la
tienen solo en la description, que no cuenta porque la lleva todo agente). Quién es el dueño de cada uno lo decide el Usuario; el script
solo hace visible que falta. Sin telemetría por cron (la 2.21 no se hace, decisión del 01-11): el uso
sale del registro de `agent_registry.py`, que hoy cubre pocos proyectos.

## 7. Cada incidente o revert, un caso del auditor de código (EQ-40)

*«Any incidents are now an eval»* (equipo de Claude Code): el diff que causó un incidente o un revert
se guarda como caso, y el auditor de código tiene que marcarlo. Probar al auditor con ejemplos
inventados mide otra cosa.

```bash
python3 .claude/scripts/incident_cases.py add --sha <revert-o-commit> --marca backend/x.py:42
python3 .claude/scripts/incident_cases.py encargo <id>          # el prompt ciego para el auditor
python3 .claude/scripts/incident_cases.py score <id> <REPORT.md> --agente <juez>   # 0 cazado · 1 no
python3 .claude/scripts/incident_cases.py report                # recall por agente
```

El diff y el encargo van al repo (`.docs/evals/incidentes/<id>/`); la **clave**, fuera
(`~/.claude/evals/<proyecto>/`), como la del fixture de diseño: si el auditor puede leerla, la prueba
no mide nada. Al cerrar un incidente o revertir un commit, añadir el caso es parte del cierre
(`self-improvement-loop.md`: el error repetido se convierte en sensor). Pasar la batería de forma
periódica es capa 5 (`/schedule` o `claude -p`): gasta tokens, se monta con OK.

## 8. Sensores de deriva, fuera del ciclo del cambio (EQ-41)

Lo rápido va antes del commit; lo caro, fuera del ciclo. `drift_sweep.py` barre el repo entero y deja
un informe con el delta frente al anterior: **D1** bloques duplicados, **D2** funciones y clases de
Python que nadie nombra, **D3** dependencias sin fijar o con rango y lockfiles, **D4** tests frente a
código. Todo son candidatos (D2 no ve la reflexión): la señal es lo que **sube** de una semana a otra.

```bash
python3 .claude/scripts/drift_sweep.py --root .        # → .docs/feedback/deriva/<fecha>.json · exit 2 = sin código
```

Se programa semanal por proyecto, como Hugo a diario (capa 5, con OK); `bug-sweep` sigue siendo el
barrido con modelo y bajo demanda.

## 9. El mapa de zonas verde, amarilla y roja lo dibuja una persona (EQ-D24)

| Zona | Qué es | Qué puede el agente |
|---|---|---|
| **Verde** | bien testeada y aislada | trabaja en bucle cerrado (la autonomía alta de `governance.md` §3.1) |
| **Amarilla** | calidad mixta | tests de caracterización **antes** de tocar; plan corto primero |
| **Roja** | auth, facturación, permisos, datos de personas | humano en cada paso, o no se toca |

`templates/zonas.yaml` → `zonas.yaml` en el `.claude/` del proyecto, rellenado y **firmado** (`firmado_por`) por
el Usuario en una sesión. `zona.py <rutas>` (o `git diff --name-only … | xargs zona.py`) dice qué zona
toca un cambio y sale con el color más alto (0/1/3). Sin mapa o sin firma, todo es amarillo: un mapa
que deduce el agente es justo el juicio que no se le quiere delegar. Una zona cambia de color si se lo
gana, y el cambio lo firma también una persona. Decisión aplicada: opción A de EQ-D24.

---

## Anti-patterns

- ❌ Cerrar una puerta sin acta, o con un acta donde el auditor es el autor → `gate_auditor.py` (A1).
- ❌ Lanzar la batería completa en cada issue → solo en hito de release (§3).
- ❌ Una cuarta ronda «para cerrar los últimos hallazgos» → escalar con lo que hay.
- ❌ Pasarle al Usuario hallazgos sin validar en código o UI, o validar pasando solo la conclusión (§4).
- ❌ Darle Edit a un juez porque «necesita escribir su informe en otra carpeta» → `extra` en el JSON (§5).
- ❌ Un juez que «arregla de paso» con Bash → su veredicto ya no es independiente; el hook lo para.
- ❌ Mantener un juez con la tasa de validados por los suelos «porque a veces acierta» (§6).
- ❌ Probar al auditor de código solo con ejemplos inventados, o con la clave a su alcance (§7).
- ❌ Meter el barrido de deriva en cada cambio (§8), o que el agente se dibuje su propio mapa de zonas (§9).

---

_Rule version: 1.1 · 2026-11-02 · §6b política de flota (EQ-3, sub-ola 3.01) · v1.0 · 2026-10-31 · sub-ola 3.11 (EQ-1, EQ-D8, EQ-D13, EQ-D14, EQ-19, EQ-20, EQ-36,
EQ-40, EQ-41, EQ-D24)._
