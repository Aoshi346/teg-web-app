---
name: html-suelto
description: >-
  Usar cuando markdown se queda corto y hace falta un HTML autocontenido (espacial, comparativo,
  interactivo o un documento que se escanea): 'hazme un HTML de', 'status report en HTML', 'diagrama
  de arquitectura HTML', 'deck de slides', '/html-suelto' (antes /html-artifact). Se sirve en
  127.0.0.1 con túnel, nunca como Artifact de claude.ai. NO usar para: respuestas conversacionales,
  un párrafo o un snippet (markdown), ni un informe con decisiones (report-kit, rules/output-choice.md).
user-invocable: true
---

# HTML suelto — una página que explica UNA cosa

Convierte un pedido en un **único `.html` autocontenido** de calidad editorial. Codifica la
convención de `.claude/rules/html-output.md` — léela antes de generar. Qué salida toca en cada caso
(chat, `.md`, PDF, report-kit…): `.claude/rules/output-choice.md`.

> **Se llamaba `html-artifact` hasta el 31-10** (AN-D2): el nombre invitaba a publicarlo como Artifact
> de claude.ai, y eso es justo lo que no se hace con un informe (decisión del Usuario). Se sirve en
> `127.0.0.1` y se llega por túnel SSH; el enlace que se da es `http://localhost:<puerto>/…`.

## Cuándo usar
- Output **espacial** (diffs, diagramas), **comparativo** (N opciones), **interactivo** (sliders,
  drag, toggles) o un **documento recurrente** (status, post-mortem, explainer).
- NO para respuestas conversacionales, un párrafo o un snippet → eso es markdown.
- Disparadores: "hazme un HTML de", "genera un artefacto HTML", "status report en HTML", "PR writeup
  visual", "diagrama de arquitectura HTML", "deck de slides", "explainer interactivo",
  "/html-suelto", "make this an HTML", "render this as HTML". Un solo archivo, CSS/JS inline, sin
  deps. Delega en el plugin playground para casos interactivos si está instalado.

## Argumentos
`/html-suelto <caso> [tema/fuentes]`. Casos rápidos (atajos del día a día):

| Atajo | Tier | Genera |
|-------|------|--------|
| `status` | 1 | Status report semanal: métricas + shipped/slipped + chart + timeline |
| `plan` / `approaches` | 1 | Grid de N enfoques lado a lado con trade-offs |
| `explainer` | 1 | Explainer con secciones colapsables + code tabs |
| `review` / `pr` | 2 | PR writeup: diff anotado por severidad + jump links |
| `prototype` | 2 | Componente con sliders de parámetros + copy |
| `architecture` | 2 | Diagrama SVG con nodos clicables |
| `slides` | 3 | Deck navegable por flechas |
| `editor` | 3 | Editor configurable (toggles/cards) + botón export |

Si no se pasa caso, pregunta cuál encaja o infiérelo del contexto.

## Cómo generar (5 pasos)

1. **Lee** `.claude/rules/html-output.md` (convención + tiers + galería de referencia).
2. **¿Playground disponible?** Si el caso es interactivo (prototype, editor, prompt tuner) y el
   plugin `playground` está instalado, **delega en él** (`/playground …`) — formaliza el patrón
   de 3 paneles. Si no, genera el HTML a mano siguiendo la convención.
3. **Genera** un solo `.html`: CSS/JS inline, tipografía del sistema, sin CDN/deps. ⚠️ **La única excepción** son los artefactos de MARCA y los BOCETOS de diseño (`brand.html`, `disenar-pantalla`), que sí pueden cargar la tipografía real con fallback declarado y aviso en la página: su trabajo es enseñar cómo se va a ver (`rules/html-output.md` §2 · `rules/motores-de-diseno.md` §F5). Un informe del report-kit NO entra en la excepción: tiene que abrir sin red. Incluye
   **botón "copy back"** (copia el resultado/prompt/diff al portapapeles).
4. **Guarda** en `.docs/html/<slug>-<YYYY-MM-DD>.html` (nunca en la raíz del repo; si es de un plan,
   en la carpeta del plan).
5. **Verifica visualmente**: `python3 -m http.server <puerto> --bind 127.0.0.1` en esa carpeta + abrir
   con Playwright; confirmar render sin errores de consola (el `favicon.ico` 404 es inofensivo). El
   `file://` suele estar bloqueado en el MCP de Playwright. Al Usuario se le da
   `http://localhost:<puerto>/<fichero>`, comprobado con `templates/report_kit/enlace.py`, y llega por
   `ssh -L <puerto>:127.0.0.1:<puerto>`. **Nunca** se publica como Artifact de claude.ai.

## Listón de calidad
La galería **https://thariqs.github.io/html-effectiveness/** (20 demos / 9 categorías). Si el
artefacto no se acerca a ese nivel, no está listo. Aplica los criterios de `vera-art-director`
si hay duda sobre la calidad visual.

## Anti-patterns
- ❌ CDN / Google Fonts / `<script src>` remoto → no es autocontenido.
- ❌ CSS en `assets/*.css` relativo "temporal" → **inline desde el primer Write**. Check pre-DONE:
  `grep -L 'stylesheet' *.html` debe listar todos (ninguno enlaza CSS externo).
- ❌ Tokens HSL crudos como `var(--token)` directo en color → transparente; usa `hsl(var(--x))`
  (ver gotcha en `rules/html-output.md`).
- ❌ Guardar en la raíz del repo.
- ❌ Publicarlo como Artifact de claude.ai, o servirlo en `0.0.0.0` (`rules/output-choice.md`).
- ❌ Sin botón "copy back" (rompe el loop humano↔agente).
- ❌ Reportar hecho sin abrir el HTML en un browser.
- ❌ Usar HTML para output trivial.

## Related
- `.claude/rules/html-output.md` — convención completa
- `MCP_PLUGINS.md` — instalación del plugin `playground`
- `.claude/agents/vera-art-director.md` — gate de calidad visual
