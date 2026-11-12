# .claude/templates/translation/ — contrato de datos i18n

Plantillas del sistema de traducción (skill `translate-content`, que lleva dentro su motor de fan-out
`translate-pages.js` — antes el workflow `/translate-pages`).
Motor **LLM + glosario**; **revisión nativa obligatoria** antes de publicar (no MT cruda).

| Archivo | Qué es |
|---------|--------|
| `glossary.example.json` | **Glosario**: `dontTranslate` (marcas/códigos/URLs), `terms` (traducciones canónicas por idioma), `tone` (por idioma), `preserve` (HTML/placeholders/shortcodes). |
| `manifest.example.json` | **Inventario** de unidades traducibles `{id, page, file, key, source, context}`. Lo genera el adaptador del stack. |

## Flujo

```
/translate-content                      # pregunta idiomas + motor + stack
  → crea glossary.json (de glossary.example.json)
  → extrae translation-manifest.json (adaptador del stack)
  → translate-pages.js "<dir>|<lang>"   # motor de la skill (tool Workflow, scriptPath): fan-out por página → translations.<lang>.json
  → adaptador escribe al stack (WordPress: populate scripts + Polylang; Django: .po; genérico: i18n)
  → QA gate: glosario/HTML/placeholders + Vera (layout) + Lidia (idioma) + REVISIÓN NATIVA
```

## Esquema

- **glossary.json**: `{ source, targets[], dontTranslate[], terms{ "<src>": {"<lang>":"<trad>"} },
  tone{"<lang>":"..."}, preserve[] }`.
- **translation-manifest.json**: `{ source, stack, units:[{id, page, file, key, source, context}] }`.
- **translations.<lang>.json** (salida del workflow): `{ lang, units:{ "<id>":"<target>" }, reviewed:false }`.
  Idempotente: el workflow conserva targets ya revisados (merge por id).

## Adaptadores por stack
- **WordPress** → `knowledge/wordpress/translation.md` (Polylang + per-language populate scripts).
- **Django** → gettext (`makemessages` → `.po`, rellenar `msgstr`) + `django-modeltranslation`/`parler` para BD.
- **Genérico** → ficheros i18n JSON/markdown por idioma.

> El glosario y `dontTranslate`/`preserve` son la clave de consistencia y de no romper el código.
