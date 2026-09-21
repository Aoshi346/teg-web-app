# Calibration v2 — Shared rules & thresholds

> **Fuente**: deep research 2026-04-22 (2374 líneas, 58 sources)
> **Usado por**: Vera, Lidia, Ignacio (audit agents)
> **Versión**: 2026-08-08.1
>
> Esta es la **fuente única de verdad** para umbrales numéricos y protocolos.
> Si cambia aquí → bumpear `shared_utils_version` en los 3 agentes.
>
> ⚠️ **Este fichero es compartido por los tres: tocarlo los cambia a los tres a la vez.** Es una de
> las dos vías por las que un auditor cambia sin que nadie haya decidido cambiarlo (la otra es el
> alias del modelo). Por eso cada corrida registra qué versión usó — §11.

---

## 1. Baseline scoring philosophy

**Stop anchoring a 8.0/10**. El score de partida debe ser bajo:

| Agente | Baseline | Justificación |
|--------|----------|---------------|
| Vera | **5.0** | "Mediocre/funcional". Sube por excelencia verificada. |
| Lidia | (categórico) | Por defecto "Algo Claro". "Claro" requiere evidencia. |
| Ignacio | **3.0** | "Poor/fails". Debe estar ≥1.0 bajo Vera o no está haciendo su trabajo. |

**Justificación research**: LLMs tienen training bias hacia scores altos. Partir bajo
y subir con evidencia contrarresta la inflación sistémica.

---

## 2. Blind evaluation protocol

**Prohibido** en el prompt del agente:
- "Estos son los cambios desde Round X"
- "Delta vs versión anterior"
- "Mejoras implementadas en W1...W10"
- "Fixes aplicados en commit XYZ"

**Permitido**:
- URL target
- Audiencia objetivo (ej: "agencias paid media 5-25 personas")
- Goals de negocio
- Constraints técnicos

**Razón**: anchoring bias. Si LLM sabe "esta es v5", puntúa buscando evidencia de
"debería ser mejor que v1-v4" en vez de evaluar absolutamente.

---

## 3. Mandatory penalties (Vera + Ignacio)

Cada violación obliga a una penalización numérica **no negociable**.

### Typography

| # | Violación | Umbral | Penalización |
|---|-----------|--------|--------------|
| T1 | Font weights en 1 sección | 2-3 = OK · 4 = -0.5 · 5+ = -1.0 | Contar declaraciones `font-*` distintas en viewport |
| T2 | Line-height body text | <1.4 o >2.0 | -0.5 |
| T3 | Max-width body text | <40ch o >75ch | -0.3 a -0.5 |
| T4 | H1 rompe > 4 líneas 1440px | Conteo líneas | -0.5 |

### Color

| # | Violación | Umbral | Penalización |
|---|-----------|--------|--------------|
| C1 | Hue families distintas | 3-4 OK · 5 = -0.5 · 6+ = -1.0 | Excluir grays/blacks/whites |
| C2 | Saturación primary+secondary | >75% + >65% simultáneo | -1.0 (clickbait) |
| C3 | Elementos con sat >70% en viewport | 3+ | -1.0 |
| C4 | Bg element con sat >60% | Cualquiera | -0.5 |

### Animation

| # | Violación | Umbral | Penalización |
|---|-----------|--------|--------------|
| A1 | Hover opacity delta | >0.3 | -0.5 (clickbait) |
| A2 | Micro-interaction duration | >500ms · >1000ms | -0.5 · -1.0 |
| A3 | Secciones animándose simultáneamente | >3 | -1.0 |
| A4 | Gradient border rotation speed | <4s por ciclo | -1.0 (casino) |
| A5 | Shine sweep opacity | >25% | -0.5 |
| A6 | Urgency badge pulse scale | >1.05 · cycle <2s | -0.5 cada |

### Shadows

| # | Violación | Umbral | Penalización |
|---|-----------|--------|--------------|
| S1 | Single-layer shadow en hero CTA | 0 comas en `box-shadow` | -0.5 |
| S2 | Single-layer shadow en cards | 0 comas | -0.3 |

### CTA density

| # | Violación | Umbral | Penalización |
|---|-----------|--------|--------------|
| Q1 | CTAs prominentes en viewport | >2 | -1.0 (spam) |
| Q2 | Sticky header + hero + floating | 3 exposiciones | -1.5 |

### Spacing

| # | Violación | Umbral | Penalización |
|---|-----------|--------|--------------|
| P1 | Valores arbitrarios (23px, 37px) | Cada sección | -0.5 |
| P2 | Section sin clamp() responsive | No match | -0.3 |
| P3 | Line-heights no divisibles por 4 | 3+ valores | -0.3 |

### AI-slop tells

| # | Violación | Umbral | Penalización |
|---|-----------|--------|--------------|
| AI1 | LLM copy phrases (revolutionary, potencia tu, etc.) | >3 por sección | -0.5 |
| AI2 | Gradientes multi-hue >90° rotación en 2+ secciones | Sí | -0.5 |
| AI3 | Poppins/Montserrat display + Inter body | + 3 otras violaciones | -0.3 |
| AI4 | Triple parallel construction 2+ secciones | Sí | -0.3 |

### Technical rendering

| # | Violación | Umbral | Penalización |
|---|-----------|--------|--------------|
| R1 | Tailwind opacity fuera de scale (15/35/45/85) | Cada instancia | -0.5 |
| R2 | Text con `color: transparent` computed | P0 BUG | -1.5 |
| R3 | Navbar contraste verificado al scroll | Bug | -1.5 |

### Template derivatives

| # | Violación | Umbral | Max score |
|---|-----------|--------|-----------|
| D1 | Bootstrap/WordPress/Webflow reconocible | 2+ patterns | 6.0 |
| D2 | Tailwind UI unmodificado | Sí | 6.5 |
| D3 | Chart-junk ratio >35% | Medición | 6.5 |
| D4 | Chart-junk ratio >50% | Medición | 5.0 |

---

## 4. Reference comparison (mandatory para score >7.0)

Antes de asignar score >7.0, el agente debe explicitar paridad con:
- Stripe.com
- Linear.app
- Vercel.com

Formato obligatorio:

```
Comparación con referencias premium:
- Stripe: [aspecto específico donde iguala o no]
- Linear: [aspecto específico]
- Vercel: [aspecto específico]
```

Si el agente no puede identificar 3+ aspectos de paridad → **score ≤7.0**.

---

## 5. Nielsen heuristics adversarial application

Baseline Nielsen = 10.0. Restar por cada violación:

| # | Heurística | Penalización |
|---|-----------|--------------|
| N1 | Visibility of system status (missing loading state) | -1.0 |
| N2 | Match system/world (unexplained jargon) | -0.5 |
| N3 | User control (destructive action sin confirmación) | -1.0 |
| N4 | Consistency (spacing/button inconsistency) | -0.5 |
| N5 | Error prevention (form sin validation) | -1.0 |
| N6 | Recognition (icon sin label) | -0.5 |
| N7 | Flexibility (missing keyboard shortcut) | -0.3 |
| N8 | Aesthetic minimalism (visual redundancy) | -0.5 |
| N9 | Error recovery (generic error message) | -1.0 |
| N10 | Help (critical task needs docs) | -0.5 |

- Sites fallando 2+ heurísticas: **Cannot score >6.0**
- Sites fallando 4+: **Cannot score >4.0**

---

## 6. Awwwards rejection criteria (auto-max-score)

| Condición | Max score |
|-----------|-----------|
| Template derivative reconocible | 6.0 |
| Sin responsive (broken mobile) | 5.0 |
| Copy completamente genérico (zero brand voice) | 6.0 |
| Unclear what product/company does in 5s | 6.0 |
| Sacrificed usability for aesthetics | 7.0 |
| Chart-junk >50% | 4.0 |

---

## 7. Scoring output format

Todos los agentes con score deben producir:

```markdown
Score: X.X / 10

Penalizaciones aplicadas:
- [Violación ID]: -X.X ([evidencia específica])
- [Violación ID]: -X.X ([evidencia])
...

Total penalizaciones: -X.X

Comparación referencias premium (si score >6.5):
- Stripe: [comparación]
- Linear: [comparación]
- Vercel: [comparación]

Justificación final: [por qué este score refleja el estado real]
```

---

## 8. Multi-agent cross-check

- **Vera**: scoring con penalizaciones de esta tabla
- **Ignacio**: scoring adversarial (baseline 3.0) — su score DEBE ≥1.0 por debajo de Vera
  - Si delta < 1.0: Ignacio no está siendo suficientemente adversarial → fail
  - Si delta > 3.0: flag para revisión humana (posible disagreement genuino)
- **Lidia**: híbrido — 8 dim numérico + categorical gate
  - Si cualquier dimensión es "Muy Confuso" → verdict global = "No contactaría"
  - Promedio numérico sirve como color coding, no como gate principal

---

## 8b. Qué mide un score, y qué no (AUD-1)

**El `trend.json` de un auditor mide el PRODUCTO auditado, no la habilidad del auditor.** No es su
boletín de notas, y leerlo así ha llevado a dar por confirmada una mejora que nadie ha demostrado.

La prueba está en nuestros propios datos: los tres auditores corrieron sobre **el mismo objetivo**
en **las mismas 3 rondas**, sin que se les tocara a ellos, y **divergen en signo** — en iter-3
Lidia sube (7.1→7.75) y Vera baja (7.85→7.35). Si esos números midieran habilidad del auditor
sobre un objetivo fijo, eso no podría pasar. Cada uno mide una faceta distinta *del artefacto*.

Consecuencias operativas:

- Todo `trend.json` de auditor lleva `"measures": "producto-auditado"`.
- **La métrica que sí habla del agente** es del tipo `address_rate` de `rita-pattern-keeper`
  (sugerencias atendidas / emitidas, con retirada automática del patrón que se ignora; éxito =
  volumen **decreciente**). Es el modelo a copiar; hoy ningún auditor visual tiene una.
- «Este auditor ha mejorado» **no se afirma sin la medición que lo demuestre**. Protocolo:
  `.claude/agents/lidia-naive-tester/measurement-protocol.md`. **Nada de eso se ha ejecutado.**

## 8c. Objetivo congelado y contexto de corrida (AUD-3 + AUD-9)

Aplica a los tres. El detalle operativo del bucle está en `rules/qa-loop.md` §1b.

1. **El objetivo no se toca durante la ronda.** Todos reciben el mismo `target_sha`; nadie parchea
   en caliente; un P0 a mitad **aborta la ronda**, no la parchea. En TPL1-W3/iter-3 se hizo al
   revés y dos auditores acabaron puntuando builds distintos, promediados en un mismo número.
2. **Cada salida declara con qué corrió**: `model_id` (el identificador **exacto** — `sonnet` es un
   alias móvil y no vale), `calibration_version` (la de este fichero), `target_sha`, `agent_sha`
   (`sha256sum` de la propia ficha) y `run_index`.
3. Con eso queda habilitado el **control de deriva**: volver a correr la misma versión dentro de
   unos meses sobre el mismo sha y ver cuánto se ha movido el agente **solo**.

## 8d. Perfil de rúbrica — dimensiones N/A (AUD-8)

Una dimensión que el producto **no puede** cumplir no se puntúa baja: se marca **N/A** y sale de
la media. Caso medido: `fotos_videos` de Lidia clavada en **3/10** las tres rondas sobre una
herramienta interna (informes HTML, sin fotos de personas posibles), restando **0.6 fijos** a su
media y dejando su máximo aritmético en **9.125** con el gate en 9.0 — inalcanzable por
construcción antes de empezar.

Reglas: (a) el perfil se declara **antes** de la ronda y no cambia a mitad; (b) se guardan **los
dos números**, `score_raw` (todas las dimensiones, comparable con el histórico) y `score_profiled`
(las que aplican); (c) **no toca el gate categórico** — no es una vía para inflar veredictos.

## 9. Grep patterns compartidos

Ver `./red-flags.sh` para implementación ejecutable.

Patterns incluidos:
- R1 Tailwind opacity inválida
- R2 Clickbait CSS (shine, gradient-border animados)
- R3 AI-slop copy (LLM phrases)
- R4 Single-layer shadows
- R5 Arbitrary spacing
- R6 Emojis en UI
- R7 Hex hardcoded
- R8 Animation duration excesiva
- R9 Urgency scarcity copy
- R10 TODOs/placeholders

---

## 10. Multi-modal verification

Ver `./multi-modal-checklist.md` para el checklist completo Playwright.

Checks mínimos obligatorios por sesión de audit:
- Check 1 DOM + computed styles
- Check 2 Screenshots multi-posición (8+ viewports/scrollY)
- Check 3 Hover/focus states
- Check 8 Console errors

Checks opcionales:
- Check 4 Axe accessibility (si @axe-core/playwright instalado)
- Check 5 Font rendering
- Check 6 Responsive breakpoints
- Check 7 Interactive elements real test

---

_Last updated: 2026-08-08.1_
_Changelog 2026-08-08.1 (AUD-1/3/8/9): +§8b qué mide un score · +§8c objetivo congelado y contexto de corrida · +§8d perfil de rúbrica con dimensiones N/A. Sin cambios en los umbrales de penalización de §3-§7._
_Source: deep research `.specify/sessions/ELV-5*/AI Design Audit Agent Calibration*.md`_
