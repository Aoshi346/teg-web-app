---
name: translate-content
description: >-
  Usar para traducir páginas o contenido de un proyecto a varios idiomas con glosario, tono y
  HTML/placeholders intactos, y revisión nativa antes de publicar: 'traduce las páginas', 'traducir
  el sitio a inglés/catalán', 'multi-idioma', '/translate-content', 'translate the site'. NO usar
  para: AUDITAR traducciones hechas, strings sin traducir o locale de fechas y monedas
  (lena-i18n-auditor).
user-invocable: true
---

# Translate Content — traducción multi-idioma consistente

## Cuándo se activa (detalle)

Disparadores: 'traduce las páginas', 'traducir el sitio a inglés/catalán', 'multi-idioma', 'i18n del proyecto', 'traducción', '/translate-content', '/translate-pages', 'translate the site', 'make it multilingual' · Stack-aware (WordPress/Polylang, Django/gettext, genérico); motor LLM + glosario; gate de revisión nativa (no publica MT cruda) · Es la única puerta de la traducción: a escala lanza su propio motor de fan-out (translate-pages.js, en esta carpeta; antes el workflow /translate-pages) · NO usar para: AUDITAR traducciones ya hechas, strings sin traducir o locale de fechas y monedas (agente lena-i18n-auditor).

Sistema **general y stack-agnóstico** para traducir todo el contenido de un proyecto. El motor de
traducción es **LLM (Claude) + glosario**; el resultado **siempre pasa por revisión nativa** antes de
publicar (es contenido de cara al usuario — no se publica MT cruda).

## Paso 0 — Preguntar (AskUserQuestion)
1. **Idiomas destino** (origen detectado del proyecto). Ej: ES→EN, CA.
2. **Motor**: LLM (default) · DeepL+pulido · plugin nativo. Para web comercial → LLM+glosario+revisión.
3. **Stack** (auto-detecta; confirma): **WordPress** · **Django** · **genérico**.

## Paso 1 — Glosario (consistencia)
Crea/usa `glossary.json` (ver `.claude/templates/translation/glossary.example.json`):
- `dontTranslate`: marcas, nombres propios, códigos (p.ej. "BCNLIP", "Instituto Cervantes", "DELE").
- `terms`: traducciones canónicas por idioma de términos/CTAs recurrentes (consistencia).
- `tone`: tono por idioma (formal/cercano), audiencia.
- `preserve`: NO tocar HTML/`<span class>`, placeholders `{var}`/`%s`/`%(name)s`, URLs, shortcodes.

## Paso 2 — Manifest (qué traducir)
Extrae las **unidades traducibles** según el adaptador del stack → `translation-manifest.json`
(ver `manifest.example.json`): lista de `{id, file, key, source, context}`.
- **WordPress** (ver `knowledge/wordpress/translation.md`): atributos JSON de bloques en
  `inc/populate_page_*.php`; defaults de `block.json`; `_e()/__()` de `render.php` → `.po` del tema.
- **Django**: `{% trans %}`/`gettext()` → `makemessages` (`.po`, Claude rellena `msgstr`); contenido
  en BD → `django-modeltranslation`/`parler`.
- **Genérico**: ficheros i18n JSON/markdown por idioma.

## Paso 3 — Traducir
- **Pocas unidades** → traduce inline (con glosario).
- **Muchas (escala)** → lanza el motor de fan-out de esta skill, **`translate-pages.js`** (fan-out
  por página/unidad, pipeline extraer→traducir→verify, idempotente por idioma) →
  `translations.<lang>.json`. Vivía en `.claude/workflows/` como `/translate-pages`; desde el
  2026-10-19 está aquí, para que la traducción tenga una sola puerta. Se lanza con el tool `Workflow`:
  ```
  Workflow(scriptPath=".claude/skills/translate-content/translate-pages.js", args="<dir>|<lang>")
  ```
  Coste: un agente por página — **aprueba antes de correr**. Si el script se para con «ARGS
  requeridos», el runtime no le pasó `args` por `scriptPath` (no está documentado que lo haga): haz
  el mismo fan-out con subagentes, uno por página, con los prompts de las fases Translate y Verify
  del script, y escribe tú `translations.<lang>.json` (fase Write). Igual si el tool `Workflow` no
  está disponible.

## Paso 4 — Escribir al stack (adaptador)
Convierte `translations.<lang>.json` al formato del stack (WordPress: per-language populate scripts +
Polylang link; Django: `.po`/model; genérico: i18n files). Ver el doc del adaptador.

## Paso 5 — QA gate (obligatorio antes de publicar)
- Consistencia de glosario (mismos términos canónicos en todo el sitio).
- HTML/placeholders/URLs intactos; no se tradujo lo de `dontTranslate`.
- **Longitud**: el texto traducido cambia de tamaño → **Vera** revisa layout (puede romper diseño).
- **Lidia** en el idioma destino (¿una persona nativa lo entiende?).
- **Revisión humana/nativa** marcada como pendiente. **No publicar MT cruda.**

## Anti-patterns
- ❌ Publicar traducción automática sin revisión nativa en web comercial.
- ❌ Traducir marcas/códigos/placeholders/HTML (usa `dontTranslate`/`preserve`).
- ❌ Términos inconsistentes entre páginas (para eso está el glosario canónico).
- ❌ Pisar traducciones ya revisadas al regenerar (el workflow es idempotente por id).
- ❌ Asumir el stack: detecta/pregunta y usa el adaptador correcto.

## Related
- `translate-pages.js` (en esta carpeta) — motor fan-out (antes el workflow `/translate-pages`).
- `.claude/templates/translation/` — glossary/manifest examples + README (contrato).
- `knowledge/wordpress/translation.md` — adaptador Polylang.
- `rules/html-output.md`, agentes `vera-art-director`/`lidia-naive-tester` (QA del idioma destino).
