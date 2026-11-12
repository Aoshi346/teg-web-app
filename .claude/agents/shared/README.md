# Shared utilities for audit agents

Utilities used by **all** visual audit agents (Vera, Lidia, Ignacio).

## Portabilidad → techlead-template

**IMPORTANTE**: estas utilities + los 3 agentes (vera-art-director, lidia-naive-tester,
ignacio-roig) son **portables** al techlead-template (el creador de agentes).

Cuando se sincronice al techlead template:
- Copiar `.claude/agents/vera-art-director.md` + memory
- Copiar `.claude/agents/lidia-naive-tester.md` + memory
- Copiar `.claude/agents/ignacio-roig.md` + memory
- Copiar `.claude/agents/shared/*` completo

Los agentes referencian los shared utils con rutas relativas (`./shared/red-flags.sh`),
así que la estructura debe preservarse.

## Files

- `red-flags.sh` — grep patterns para detección automática de anti-patrones (Tailwind opacity
  inválida, clickbait CSS, AI-slop copy, single-layer shadows, arbitrary spacing).
  Ejecutable. Uso: `bash .claude/agents/shared/red-flags.sh [target-dir]`

- `multi-modal-checklist.md` — checklist de verificación Playwright multi-modal:
  DOM + computed styles + visual diff + hover states + scroll positions + responsive +
  axe-core accessibility. Los 3 agentes lo referencian.

- `calibration-v2.md` — la base del sistema de penalizaciones y umbrales numéricos
  derivados del deep research (Apr 2026). Los 3 agentes heredan de aquí.

## Versioning

Cada agente declara qué versión de shared utils requiere en su frontmatter:

```yaml
shared_utils_version: "2026-04-22"
```

Si los shared utils se actualizan → bumpear versión en los 3 agentes también.

## Deep research source

La calibración actual deriva del deep research ejecutado 2026-04-22 y guardado en:
`.specify/sessions/ELV-5 - Production Polish + Legal + Chatbot/AI Design Audit Agent Calibration  Professional Visual Critique Methodology & Score Inflation Mitigation.md`

(2374 líneas, 58 sources)
