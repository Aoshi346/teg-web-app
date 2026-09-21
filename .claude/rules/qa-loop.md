---
paths:
  - ".docs/feedback/**"
---

# QA Loop — Protocolo Lidia + Vera + Ignacio hasta avg ≥ 9.0

> **Cuándo aplicar:** al cerrar cualquier wave/feature **con UI**. Orquesta los tres auditores de
> persona que el template ya trae (`lidia-naive-tester`, `vera-art-director`, `ignacio-roig`) en un
> bucle convergente hasta una nota media ≥ 9.0.
>
> **NO aplicar:** waves backend-only u operacionales (sin UI) — para esas usa `verification-loops`
> / `ux-reviewer`. Tampoco sobre código que no compila (verifica build antes).
>
> **Relacionado:** `verification.md`, `verdict-contract.md` (esquema de veredicto reutilizable),
> **`e2e-stability.md`** (estado determinista + selectores estables: prerrequisito para que este
> bucle no mida ruido), skills `verification-loops`, `ux-reviewer`, `naive-user-playthrough`,
> `visual-regression` (diff objetivo contra baseline, complementa la crítica subjetiva de Vera),
> `feedback-audit`; agentes `lidia-naive-tester`, `vera-art-director`, `ignacio-roig`; skills
> `disenar-pantalla` + `nueva-pantalla` (quien construye lo que estos tres auditan).

---

## Disparo

- Manual: `/qa-loop` o "lanza qa-loop sobre la wave actual".
- Autónomo: dentro de `/loop` (plugin ralph-loop) con el prompt de cierre de wave.

---

## Protocolo (estricto)

### 1. Pre-flight
- RAM libre: `bash .claude/hooks/check-ram.sh` en verde — el umbral lo calcula el hook (`--explain`)
  (`rules/ram-pytest.md`). Ojo: 3 auditores con Chrome cuentan ~doble.
- Build limpio: el equivalente del proyecto a `npm run build` + check del backend pasa sin errores.
- URL viva: `curl -fsS http://localhost:<PORT>/ -o /dev/null` (sustituye `<PORT>` por el puerto del
  proyecto; usa `PROJECT_DOMAIN`/`BACKEND_PORT` de `settings.json` si están definidos, o producción
  cuando aplique).
- Anotar `WAVE_ID` y `iteration_n` (empieza en 1).
- **Congelar el build y anotar su sha** (`git rev-parse --short HEAD`) → es el `target_sha` de la
  ronda. Se lo pasas a los tres auditores. Ver §1b.
- **Declarar el perfil de rúbrica** del objetivo: `landing` | `herramienta-interna`. Decide si
  `fotos_videos` cuenta o es N/A (AUD-8) y no se cambia a mitad de ronda.

### 1b. El build NO se toca durante la ronda (AUD-3) — regla dura

> **Auditores en paralelo + arreglos en caliente = medición destruida.** No es teoría: pasó en
> TPL1-W3/iter-3. Mientras las tres auditorías corrían, el orquestador parcheó en caliente dos P0
> que Ignacio acababa de encontrar; Vera había mirado **antes** del parche. **Vera e Ignacio
> auditaron builds distintos y sus notas se promediaron en un único `score_wave` de 7.55** — un
> número que no describe ningún objeto real. El propio `RESULT.md` lo admite al pie: *«el 7.35 de
> Vera es pre-hot-patch»*. Ese 7.55 es el que cerró el bucle.

1. **Se congela** un sha antes de lanzar a nadie. Los tres auditores reciben el **mismo**
   `target_sha` y lo escriben en su salida (`run.target_sha`, `run.build_frozen: true`).
2. **No se toca nada** —ni un fix «de un minuto», ni un typo— hasta que **los tres** han
   terminado y entregado.
3. **Si aparece un P0 crítico a mitad: se ABORTA la ronda entera** y se reinicia sobre el build
   nuevo. **No se parchea en caliente.** Repetir una ronda es más barato que publicar una media
   inventada — y una media inventada contamina además todo lo que se compare con ella después.
4. Al cerrar, el orquestador verifica que los tres `target_sha` coinciden. Si no coinciden,
   **la ronda no se promedia**: se anota como inválida en `RESULT.md` y se repite.

Los tres auditores llevan esta regla escrita en su ficha (Lidia §Contrato de salida, Vera §Bloque
`run`, Ignacio Regla #6). El orquestador es quien la hace cumplir.

### 2. Ejecución paralela de los 3 auditores

Lanzar **en un solo mensaje con 3 Agent tool calls** (paralelización, ver `parallelization.md`):

| Agente | Trigger | Output |
|--------|---------|--------|
| **Lidia** (`lidia-naive-tester`) | "Lanza naive test como [persona objetivo del proyecto], 30s, móvil+desktop" | `.docs/feedback/qa-loop/<WAVE_ID>/iter-<n>/lidia/REPORT.md` + `trend-delta.json` + screenshots |
| **Vera** (`vera-art-director`) | "Audita visual tier-1, gate 9.0, los 5 tokens son obligatorios" | `.docs/feedback/qa-loop/<WAVE_ID>/iter-<n>/vera/REPORT.md` + `findings.json` + screenshots 1440/768/390 |
| **Ignacio** (`ignacio-roig`) | "Crítica adversarial, ≥10 findings, delta ≥1.0 vs Vera" | `.docs/feedback/qa-loop/<WAVE_ID>/iter-<n>/ignacio/REPORT.md` |

El prompt de cada uno **debe** llevar el `target_sha` congelado (§1b) y el perfil de rúbrica (§1),
y **no debe** llevar la lista de cambios de la ronda anterior (evaluación ciega,
`shared/calibration-v2.md` §2).

### 2b. Quién cubre qué — y qué NO cubre nadie (AUD-5)

El template declara **13 auditores-persona; 10 no han corrido nunca.** Trece nombres en una lista
tranquilizan; tres que corren de verdad protegen. **Un agente que nunca ha corrido no cuenta como
cobertura** — y esto no es teórico: la accesibilidad de teclado figuraba «cubierta» por Aitor y en
3 rondas sobre un dashboard con modales y kanban drag&drop no la miró nadie.

**Dueño único por dimensión (reparto vigente, medido sobre TPL1-W3):**

| Dimensión | Dueño | Absorbido de |
|---|---|---|
| Contraste WCAG AA | **Vera** | `aitor-a11y-auditor` (nunca ha corrido) |
| Consistencia de componentes | **Vera**, prestado — vuelve a Rita cuando salga de modo sombra | `rita-pattern-keeper` (0 rondas) |
| Brand voice / AI-slop | **Vera** (eje 10 + AI1-AI4 + `red-flags.sh`) | `lena-i18n-auditor` (nunca ha corrido) |
| Onboarding · microcopy sin jerga · empty states | **Lidia** | `tomas-onboarding-tester` (nunca ha corrido) |
| Primeros niveles de conversión (oferta, confianza, CTA) | **Lidia** | `conrado-cro-auditor` (nunca ha corrido) |

**Huecos declarados — nadie los audita hoy.** No los cuentes como cubiertos:

1. **a11y que no es contraste**: teclado, foco visible, roles ARIA, target size ≥24px, alternativa
   a gestos de arrastre. Un drag&drop sin alternativa de teclado incumple WCAG 2.2 (2.5.7).
2. **Verificar que el fix declarado existe de verdad.** Es el hueco más caro y el mejor
   documentado: Ignacio cazó **3 fixes que el fixer declaró aplicados y no lo estaban**, y solo de
   forma incidental. Ocurrió en 1 de 3 rondas: la tasa base no es despreciable. Hoy no tiene dueño
   — existe como una línea en la memoria de Ignacio.
3. **Regresiones entre rondas.** Cada ronda introdujo defectos nuevos (iter-2 generó L-008; iter-3
   generó F-008 y F-012). La skill `visual-regression` existe en el repo y **no está cableada a
   este bucle**; la propia Vera escribió que *«un CI de regresión visual habría atrapado ambos
   antes de iter-3»*.
4. **Coherencia semántica de los datos mostrados** (¿el número de la página coincide con su
   fuente?) y **la salida imprimible** (`window.print()`, nunca auditada).

**Los ortogonales que no han corrido** (`sofia-pentester`, `priya-privacy-auditor`,
`quim-data-integrity`, `bruno-perf-cop`, `marco-qa-breaker`, `nadia-chatbot-evaluator`,
`aitor-a11y-auditor`, `lena-i18n-auditor`, `tomas-onboarding-tester`, `conrado-cro-auditor`) se
conservan, pero **como checklist, no como auditor**: se citan como «pendiente de correr una vez»,
nunca como cobertura de la wave. Salen de esa categoría cuando corran y dejen evidencia en disco.

### 3. Cálculo del score

```python
# Lidia: media de las dimensiones que APLICAN al perfil declarado en §1 (AUD-8).
# En `herramienta-interna`, fotos_videos es N/A: un informe no puede tener fotos de personas,
# y con L-D clavándola en 3/10 restaba 0.6 fijos, dejando su máximo en 9.125 con el gate en 9.0.
lidia_avg = score_profiled   # media de las 7-8 dimensiones aplicables. Se guarda también score_raw
vera_avg  = (sum de los 10 ejes de Vera) / 10
ignacio_score = score adversarial 0-10 (informativo)

score_wave = (lidia_avg + vera_avg) / 2   # Ignacio NO entra en la media (mide "qué falta", no PASS)
```

Recalculado sobre TPL1-W3 con los ficheros ya guardados: Lidia 6.6/7.1/7.75 →
**7.14/7.71/8.43**, y el `score_wave` de iter-3 habría sido **7.89** en vez de 7.55.
**Sigue por debajo de 9.0** — ver el aviso del gate.

### 4. Gate PASS estricto — **el categórico primero**

El orden importa y no es cosmético: **el veredicto categórico es la salida más fiable del bucle y
la media es la menos fiable.** En las 3 rondas de Lidia solo 4 de sus 8 dimensiones se movieron,
así que la media divide entre 8 una señal que llevan 4; su gate binario, en cambio, aguantó «con
ayuda» dos rondas mientras la media subía y solo cambió con evidencia en 3 anchos (AUD-11).

**Paso 1 — gates categóricos (bloqueantes, se evalúan antes que ningún número):**

| Criterio | Umbral |
|----------|--------|
| Lidia veredicto | «¿lo consigue sola / volvería mañana?» = **Sí** + ninguna página en "Confuso"/"Muy Confuso" (`con ayuda` NO es aprobado) |
| Findings P0 abiertos | **0** |
| `target_sha` de los 3 auditores | **idéntico** (§1b) — si no, la ronda es inválida y no se promedia |
| Ignacio delta vs Vera | ∈ [1.0, 3.0] (si <1.0 = no fue adversarial; si >3.0 = divergencia, escalar al Supervisor) |

**Paso 2 — umbrales numéricos (solo si el paso 1 pasa):**

| Criterio | Umbral |
|----------|--------|
| `score_wave` (con `score_profiled` de Lidia) | ≥ **9.0** |
| Vera promedio | ≥ **9.0** — fuente única del umbral; el `7.5` de su ficha y su `trend.json` era un segundo umbral contradictorio y está retirado |

> ⚠️ **Honestidad sobre este gate (AUD-15).** Excluir las dimensiones N/A corrige *una* causa —una
> dimensión imposible arrastrando la media— **sin relajar el listón**, que es lo que haría bajar el
> número. Pero **no rescata el 9.0**: el 7.89 recalculado sigue lejos, y el resto del hueco son los
> ejes de Vera y los descuentos de Ignacio, que es otra conversación. Mientras eso siga así, una
> wave como TPL1-W3 **escalará al Usuario igualmente** — es decir, la salida de emergencia se usa
> como camino normal. Si tras dos waves más el gate sigue sin discriminar nunca, hay que
> replantearlo por perfil de producto en vez de fingir que discrimina.

> ⚠️ **Y sobre la regla de parada de +0.3 (§6).** Hoy compara un delta (en iter-3 fue **+0.07**)
> contra un ruido **que nadie ha medido**. Si la σ de Lidia consigo misma resultara ~0.5 —
> plausible—, toda la progresión 6.6→7.1→7.75 cabría dentro del ruido y esa regla no significaría
> nada. Se mide en `.claude/agents/lidia-naive-tester/measurement-protocol.md` §5 (5 pasadas sobre
> un build congelado); **hasta entonces, la regla de parada se usa como señal para escalar a un
> humano, no como veredicto.**

### 4b. Fixture de calibración con errores plantados (KIT-8)

El aviso de arriba deja el bucle midiendo con un instrumento sin calibrar: no sabemos ni la σ del
auditor consigo mismo, ni **su tasa de falsos positivos**, y las dos entran en cada score que
publicamos. La σ se mide repitiendo (protocolo de Lidia §5). Esta sección resuelve la otra mitad, y
es barata: **un artefacto con defectos conocidos y contados de antemano.**

Es el Paso 6-7 del kit 08 traído aquí: *ejemplo de práctica con errores plantados a propósito, y
correr el sistema contra él*. Su lógica es que **un auditor que nunca se ha medido contra una
respuesta conocida no es un instrumento, es una opinión con decimales**.

**Cómo se monta** — cuatro pasos, ninguno necesita herramienta nueva:

1. **Congela un artefacto real** del proyecto (una pantalla, un informe, un correo, un documento) y
   duplícalo. Real, no sintético: un fixture de juguete mide la capacidad de leer juguetes.
2. **Planta N defectos catalogados** en la copia, cada uno con su tipo, su severidad esperada y su
   ubicación exacta. **La lista se escribe ANTES y se guarda fuera del alcance del auditor** — si
   puede leerla, la prueba no mide nada. Mezcla los fáciles con los que se ven de refilón: un
   fixture que solo lleva errores obvios mide lo obvio.
3. **Pasa el auditor a ciegas**, con su prompt normal, sin decirle que es un fixture ni cuántos
   defectos hay.
4. **Cuenta las dos cosas**: **recall** (cuántos de los N plantados cazó — medio punto al que
   detecta el defecto pero le pone la severidad equivocada) y **falsos positivos** (cuántos
   hallazgos marca que ni estaban plantados ni son defectos reales del artefacto). El segundo número
   es el que decide si al auditor se le puede hacer caso: uno con recall alto y FP alto no filtra,
   solo hace ruido caro.

**Las dos mediciones reales de esta casa** (plan `2026-08-16-agents-hq-reorg`):

| Fecha | Qué se midió | Resultado |
|---|---|---|
| **2026-08-16** (PRU-9) | Auditor de negocio contra un fixture de **15 errores plantados** | **14,5 / 15** cazados · **0 falsos positivos** |
| **2026-08-17** | El agente `nuria-receptora` ordenando **3 correos de calidad conocida** de antemano | Orden **correcto**, con **6,6 puntos** de distancia entre el mejor y el peor |

La segunda es una variante útil cuando no hay defectos que plantar: en vez de recall, se mide
**capacidad de ordenar**. Un auditor que pone el mejor y el peor caso a 6,6 puntos de distancia
discrimina; uno que los deja a 0,5 no, por mucho que su número parezca preciso.

> ⚠️ **El aviso honesto de PRU-9, y es lo más importante de esta sección: una prueba en la que se
> saca el 97 % está EN TECHO y por tanto NO discrimina.** Un 14,5/15 no demuestra que el auditor sea
> bueno: demuestra que el fixture era fácil para él. Con la puntuación pegada al máximo no se puede
> distinguir una versión del auditor de la siguiente, que es justo para lo que sirve calibrar. Para
> calibrar de verdad hacen falta **fixtures más difíciles** — defectos sutiles, defectos que parecen
> deliberados (`// workaround:`), y algún artefacto **sin ningún defecto plantado** para que el
> falso positivo tenga dónde aparecer. Mientras el fixture no haga fallar al auditor alguna vez, su
> resultado dice más del fixture que del auditor.

**Cuándo se corre** (no en cada ronda, o se convierte en ceremonia): al **estrenar** un auditor
—antes de que su score cuente para un gate, o sea, en la promoción a fase 4 de
`rules/agent-autonomy-ladder.md`—, al **cambiar su rúbrica o su prompt**, y una vez por trimestre
sobre los que ya operan. El resultado (fecha, N, recall, FP) se anota en el `memory.md` del auditor:
sin esa línea escrita, la siguiente sesión vuelve a no saber si su número vale algo.

### 5. Bucle de mejora (si score < 9.0)

1. **El fix lo aplica el Tech Lead en la sesión** — no un subagente: arreglar exige ver el código,
   el boceto y la conversación, que es justo lo que un contexto limpio no tiene. Consume:
   - `lidia/REPORT.md` (P0 y P1)
   - `vera/findings.json` (todo lo de severity ≥ medium)
   - `ignacio/REPORT.md` (UGLY + AMATEUR + PLACEHOLDER + INCONSISTENT)
2. Implementa fixes (en worktree si se está paralelizando; en main si es wave única) siguiendo
   `frontend/CLAUDE.md` y cerrando cada pantalla tocada
   con la skill `ux-reviewer`. Si un finding obliga a **replantear la forma** de la pantalla, eso ya
   no es un fix: es `disenar-pantalla`, media ronda.
3. `iteration_n += 1` → vuelve al paso 2 (re-ejecutar los 3 auditores).
4. Actualizar `.docs/feedback/qa-loop/<WAVE_ID>/RESULT.md` con la fila de la iteración.

### 6. Tope de iteraciones

- Máximo **5 iteraciones** consecutivas.
- Si tras 5 iteraciones no se alcanza `score_wave ≥ 9.0` **o** el score no mejora ≥ 0.3 entre dos
  iteraciones consecutivas:
  - **Escalar al Supervisor**: `openclaw gateway wake --text "BLOCKED [proyecto]: QA loop wave <ID> no converge — score actual <X> tras <n> iter" --mode now`
  - Documentar el bloqueo en `RESULT.md`.
  - Detener el loop.

### 7. Cierre

Al PASS:
- Marcar la wave como `[x]` en `tasks.md`.
- Actualizar `MEMORY.md` con la decisión final.
- Notificar: `openclaw gateway wake --text "DONE [proyecto]: QA loop wave <ID> PASS avg <X>" --mode now`

---

## Estructura de output

```
.docs/feedback/qa-loop/
└── <WAVE_ID>/
    ├── RESULT.md                        ← trazabilidad de versiones, score final
    ├── iter-1/
    │   ├── lidia/   { REPORT.md, trend-delta.json, screenshots/ }
    │   ├── vera/    { REPORT.md, findings.json, screenshots/ }
    │   └── ignacio/ { REPORT.md, screenshots/ }
    ├── iter-2/...
    └── iter-N/
```

> `.gitignore`: los screenshots son grandes — versiona solo `REPORT.md`/`findings.json`/`RESULT.md`
> (`.docs/feedback/*/**/screenshots/*.png`). Ver `claude-dir-staging.md`.

**Gate de formato antes de cerrar la iteración** (AUD-7) — cuesta un segundo y evita descubrir en
la ronda 4 que las rondas 1-3 no se pueden comparar:

```bash
python3 .claude/scripts/trend_lint.py .docs/feedback/qa-loop/<WAVE_ID>/    # exit 1 = arréglalo
```

Comprueba claves estables, que **la media declarada sea de verdad la media de las dimensiones**,
que el perfil y las N/A sean coherentes, que el bloque `run` esté completo (modelo exacto, no
alias) y qué cobertura de anclas trae la ronda. Esquema:
`.claude/templates/trend-delta.schema.json`.

---

## Anti-patrones

- ❌ Ignorar Ignacio porque "está siendo duro" → su delta vs Vera es métrica de salud del proceso.
- ❌ Cerrar la wave con `score_wave = 8.9` "está cerca" → el gate es ≥ 9.0 estricto.
- ❌ Re-lanzar sin haber tocado código entre iteraciones → estás malgastando contexto.
- ❌ Lanzar QA loop sobre código con errores de build → verifica build antes (paso 1).
- ❌ Saltar el verdict categórico de Lidia ("¿Volvería mañana?") aunque el score numérico esté bien.
- ❌ **Parchear en caliente mientras los auditores corren** → destruye la ronda (§1b). Ya pasó, y
  el 7.55 con el que se cerró TPL1-W3 no describe ningún objeto real.
- ❌ Promediar las notas de auditores que miraron **builds distintos**.
- ❌ Leer los `trend.json` de los auditores como su boletín de notas: miden **el producto** (AUD-1).
- ❌ Contar como cobertura un auditor que **nunca ha corrido** (§2b) — parece cobertura y no la da.
- ❌ Cambiar el perfil de rúbrica a mitad de ronda para que salga mejor el número.
- ❌ Cerrar la ronda sin pasar `trend_lint.py` sobre el `trend-delta.json` de Lidia (exit 1 = las
  rondas no se pueden comparar entre sí, y el fallo aparece al parsear, no al auditar).
- ❌ Tratar el `+0.3` de la regla de parada como un umbral con significado estadístico mientras la
  σ siga sin medirse.
- ❌ Promover a un auditor a que su score cuente para un gate **sin haberlo pasado nunca por un
  fixture de errores plantados** (§4b) → su tasa de falsos positivos es literalmente desconocida.
- ❌ Enseñarle al auditor la lista de defectos plantados, o dejársela donde pueda leerla → la
  prueba deja de medir.
- ❌ Presentar un 14,5/15 como prueba de que el auditor es bueno → **eso es techo**: mide que el
  fixture era fácil, no que él acierte (§4b).
- ❌ Contar solo el recall del fixture y no los falsos positivos → un auditor que lo caza todo y
  además marca lo que no existe no filtra nada, solo hace ruido caro.
- ❌ Plantar los defectos en un artefacto sintético en vez de en uno real del proyecto.

---

## Integración con SpecKit

En `tasks.md` de cada wave con UI, añade el item de QA como gate de cierre:

```markdown
## Wave N — [Feature]

- [ ] TN.1 ... [implementación]
- [ ] TN.QA — QA Loop (Lidia + Vera + Ignacio) hasta score ≥ 9.0
  - referencia: .claude/rules/qa-loop.md
  - output: .docs/feedback/qa-loop/WN/
```

---

_Rule version: 1.1 · 2026-08-08 · adaptada de un patrón en producción (productivity_system).
v1.1 (AUD-1/3/5/7/8/9/11/15): §1b build congelado — la causa raíz que invalidó iter-3 · §2b dueño
único por dimensión y huecos declarados · §3 el score de Lidia pasa a `score_profiled` · §4 los
gates categóricos se evalúan ANTES que los numéricos, con el aviso honesto de que el 9.0 sigue sin
alcanzarse y de que el `+0.3` no tiene σ detrás · gate de formato con `trend_lint.py`.
v1.2 (2026-08-17, KIT-8): §4b fixture de calibración con errores plantados — cierra la otra mitad
del hueco que declara §4 (la σ mide reproducibilidad; el fixture mide recall y falsos positivos),
con las dos mediciones reales de 2026-08-16 y 2026-08-17 y el aviso de techo. Fuente vendorizada en
`resources/kits-referencia/`._
