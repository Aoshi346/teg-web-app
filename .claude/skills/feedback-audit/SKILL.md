---
name: feedback-audit
description: >-
  Usar cuando haya que auditar el feedback de un cliente contra el sitio en vivo, item por item, con
  informe HTML de evidencia: 'audita el feedback', 'verifica el feedback del cliente', 'qué falta de
  la web según el cliente', '/feedback-audit', '/feedback-verify'. NO usar para: QA con personas
  (/qa-loop), revisar un diff de código (/review-branch) ni el feedback sobre las respuestas de un
  bot (eso son scores al turno: instrumentar-agente §3b, agente-aprendizaje.md).
user-invocable: true
effort: xhigh
---

# Feedback Audit

## Cuándo se activa (detalle)

Disparadores: "audita el feedback", "verifica el feedback del cliente", "qué falta de la web según
el cliente", "revisa los comentarios del cliente contra producción", "feedback audit", "audit client
feedback", "/feedback-audit", "/feedback-verify" (el antiguo workflow suelto: hoy es el paso 4 de
esta skill). Convierte el feedback (docx/txt/md) en items trazables, verifica cada uno
página-por-página (código + en vivo con Playwright, fan-out de subagentes) con veredicto
estructurado, y genera un informe HTML autocontenido con evidencia ANTES/ACTUAL/DESPUÉS. Es la ÚNICA
puerta del sistema de feedback: conduce la plantilla templates/feedback_audit/ y lanza su workflow.
· NO usar para: /qa-loop (personas) ni /review-branch (diff de código).

Pipeline para **verificar el feedback de un cliente contra el sitio real**, item por item, y entregar
un informe con evidencia. Empaqueta: feedback → items trazables → verificación en vivo (fan-out de
subagentes) → **veredicto estructurado** → informe HTML autocontenido.

**Sistema:** scripts en `.claude/templates/feedback_audit/` + su workflow
`.claude/templates/feedback_audit/feedback-verify.js` (lo lanza esta skill en el paso 4; desde el
2026-10-19 ya no es un `/comando` suelto) + contrato `rules/verdict-contract.md`. **Reusa** (no duplica): `templates/html/base.html` (tokens),
el **report-kit** (`rules/report-kit.md`) para las decisiones interactivas.

> ⚠️ **Read-only sobre el sitio.** Capturas/auditoría no modifican el servidor. Solo sitios
> propios/staging o producción **con autorización**. RAM: los `capture_*` abren Chrome headless —
> cuentan ~doble (ver `rules/parallelization.md`); no solapar con `pytest`.

## Paso 0 — encuadre (pregunta lo mínimo)
Necesitas: (a) el **fichero de feedback** (.docx/.txt/.md), (b) la **base URL** del sitio a verificar
(local/staging/prod-autorizada), (c) la **carpeta de trabajo** (sugerencia: `.docs/plans/<fecha>-<slug>/feedback-audit/`
— usa `feedback-audit/`, **no** `feedback/`, que `rules/plan-docs-structure.md` reserva a los auditores-persona y `/qa-loop`).
Si el feedback mezcla páginas, conviene **taggear** cada item con `[CODE] ...` para asignarlo a su página.

## Flujo
```bash
DIR=.docs/plans/<fecha>-<slug>/feedback-audit ;  T=.claude/templates/feedback_audit
mkdir -p $DIR

# 1) feedback -> items.json (idempotente, cita verbatim para CTRL+F)
python3 $T/items_from_feedback.py <feedback> $DIR --page GEN

# 2) config de páginas (copia el ejemplo y EDÍTALO: base URL + páginas)
cp $T/pages_config.example.json $DIR/pages_config.json     # editar meta.base y pages[]

# 3) captura masiva + DOM + auditoría de enlaces (Playwright)
python3 $T/capture_pages.py $DIR

# 4) verificación 1 agente/página (fan-out) -> verdicts.json   (workflow, ver abajo)

# 5) captura enfocada por item + conciliar + informe
python3 $T/capture_items.py $DIR
python3 $T/reconcile.py $DIR
python3 $T/build_report.py $DIR        # -> $DIR/informe.html
```

## Paso 4 — lanzar el workflow de verificación

El fan-out por página es un workflow que vive **dentro de la plantilla** (`feedback-verify.js`), no
en `.claude/workflows/`: así esta skill es la única puerta y no hay un `/feedback-verify` suelto que
compita con ella. Se lanza con el tool `Workflow` apuntando al fichero:

```
Workflow(scriptPath=".claude/templates/feedback_audit/feedback-verify.js", args="<DIR>")
```

- Coste: un agente por página. **Aprueba antes de correr** (`.claude/workflows/README.md` §aviso:
  los subagentes del workflow editan en `acceptEdits`).
- Si el script falla con «falta args: la carpeta de la auditoría», el runtime no le pasó `args`
  por `scriptPath` (no está documentado que lo haga; comprobado el 2026-10-19 en
  `code.claude.com/docs/en/agent-sdk/typescript` §Workflow). Entonces, **a mano**: por cada página
  de `pages_config.json`, un subagente cruza `shots/pages/<CODE>.dom.json` + las capturas + el
  código y devuelve veredictos según `rules/verdict-contract.md`; los agregas en `verdicts.json`
  (el prompt y el esquema exactos están en el propio `feedback-verify.js`, fase Verify).
- Sin el tool `Workflow` (plan Pro sin activar), el mismo camino a mano.

## Cierre
- Abre `$DIR/informe.html` y **verifícalo** (sirve con `python3 -m http.server --bind 127.0.0.1` + `scripts/screenshot.py`;
  `file://` suele estar bloqueado). Revisa que las imágenes base64 cargan offline y sin errores de consola.
- Ofrece el **report-kit** (`rules/report-kit.md`) apuntado a `$DIR` para que el cliente/owner tome
  decisiones (aprobar/modificar/aplazar/descartar) sobre los **mismos** items — no crees otro dashboard.
- Resume: % hecho, nº pendientes, P0 abiertos, y enlace al informe.

## Notas
- **Veredictos**: los agentes devuelven el esquema de `rules/verdict-contract.md` (validado por `schema`
  del workflow, sin parseo). "done" exige doble evidencia (código + en vivo).
- **ANTES/DESPUÉS** (opcional): `OUT_SUB=items_pre PRE_BASE=<url-vieja> python3 $T/capture_items.py $DIR`
  para la columna ANTES; `OUT_SUB=items_after` tras aplicar los fixes.
- **Dependencias**: `playwright` (+ `playwright install chromium`); `Pillow` opcional (recomprime imágenes).
- **Idempotente**: re-correr no duplica items; `reconcile.py` guarda `deltas.json` entre rondas.

## Anti-patterns
- ❌ Verificar producción de un tercero sin autorización (es read-only, pero igual: pide permiso).
- ❌ Afirmar "done" con solo evidencia de código (sin ver el render) → es "partial".
- ❌ Duplicar el dashboard: usa el report-kit sobre los items ya generados.
- ❌ Hardcodear la URL o el binario de Chrome → van en `pages_config.json` / autodetección.
- ❌ Abrir el informe con `file://` en Playwright (bloqueado) → sírvelo con `http.server --bind 127.0.0.1`.

## Related
- `.claude/templates/feedback_audit/README.md` — detalle de scripts y estructura.
- `.claude/rules/verdict-contract.md` — el contrato de salida.
- `.claude/templates/feedback_audit/feedback-verify.js` — el fan-out por página (paso 4; antes `/feedback-verify`).
- `rules/report-kit.md`, `/qa-loop` (personas), `/review-branch` (diff), `rules/html-output.md`.
