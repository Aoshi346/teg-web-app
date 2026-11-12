---
name: "naive-user-playthrough"
description: >-
  Usar para probar la app de punta a punta como un usuario NO técnico que nunca la ha visto: 'prueba
  como si fueras un X', 'testea como usuario no técnico', 'actúa como entrenador/agente/vendedor',
  'usability test', 'QA naive'. NO usar para: traducir los hallazgos a action items (ux-reviewer,
  que se aplica al cerrar) ni el checklist pre-DONE (verification-loops).
user-invocable: true
metadata:
  version: 1.0.0
  author: Tech Lead Template
  category: qa
  updated: 2026-11-02
  tech-stack: playwright, markdown
---

# Naive User Playthrough — testing con persona no-técnica

Esta skill simula un usuario **no-técnico** probando la aplicación. El agente deja de pensar como ingeniero y adopta la mentalidad de alguien que nunca ha visto el producto. Captura los puntos de fricción reales (los que un dev nunca detecta porque ya sabe cómo funciona), genera un informe con screenshots, y cierra invocando `ux-reviewer` para priorizar mejoras.

## Cuándo activar

Triggers explícitos del user:
- "prueba la app como si fueras X" (entrenador de fitness, agente inmobiliario, dueña de peluquería, contable jubilado, etc.)
- "haz un naive user test"
- "testea como usuario no técnico"
- "QA con perfil de usuario final"
- "usability playthrough"

Recomendado antes de:
- Release a producción
- Lanzamiento de feature nueva visible a usuarios finales
- Pedirle feedback a beta testers humanos (captura lo obvio primero)

Disparadores (de la description): 'prueba como si fueras un X', 'testea como usuario no técnico',
'actúa como entrenador/agente/vendedor', 'usability test', 'QA naive', 'user journey non-technical'.
Persona de ejemplo: entrenador de fitness, agente inmobiliario, madre de 50 años. Recorre
pantallazos con Playwright MCP o Python, narra en primera persona qué entiende/no
entiende/mejoraría/considera bug, guarda cada hallazgo con screenshot adjunto, y al cerrar aplica la
skill `ux-reviewer` para traducir hallazgos en action items.

## Los tres modos — quién corre esta skill (3.01)

La corre `lidia-naive-tester`, que la precarga. Los dos agentes que hacían lo mismo con otro ángulo
se retiraron en la 3.01 y su protocolo vive aquí:

| Modo | Cuándo | Protocolo |
|---|---|---|
| **Persona fija** | por defecto: la persona de la ficha de Lidia (o la de `.docs/domain/`) | esta skill + la ficha |
| **Persona al vuelo** | el TL le pasa otra persona al lanzarla (LI-13): «actúa como un contable jubilado» | `references/dynamic-persona.md` (era `naive-user-tester`, EQ-30); memoria en `agents/personas/<slug>/` |
| **Primer uso** | 'audita el onboarding', 'primer uso', 'time-to-value', 'empty states' | `references/first-use-mode.md` (era `tomas-onboarding-tester`, EQ-D21): rúbrica de 7 ejes, gate ≥8,0 |

Frontera: `ux-reviewer` traduce los hallazgos a action items y es el checklist antes de DONE; la
conversión de la landing es de `conrado-cro-auditor`.

## Rúbrica estética (obligatoria)

Una persona no-técnica **TIENE gusto visual** aunque no sepa CSS. Compara sin saber jargon técnico contra las apps que usa a diario (Instagram, WhatsApp, Amazon, Uber, Booking, TikTok). Por cada pantalla principal evaluar:

| Dimensión | Pregunta | Señales |
|---|---|---|
| **Modernidad** | "¿Esta app parece de 2026 o de 2010?" | Bordes redondeados · gradientes sutiles · iconos Lucide/Heroicons vs pixel art · sombras suaves · espaciado generoso |
| **Jerarquía** | "¿Sé en 3 segundos dónde mirar primero?" | Títulos grandes · CTA principal destacado · colores acentuando lo importante |
| **Densidad** | "¿Hay demasiada info apretada o respira?" | Padding · line-height · separación entre secciones |
| **Consistencia** | "¿Todos los botones parecen hermanos?" | Mismos colores/radios/tamaños en toda la app |
| **Color** | "¿La paleta tiene gusto o parece hecha por un dev?" | Harmony: 2-3 colores principales + neutros · NO fluor · NO 10 colores distintos |
| **Tipografía** | "¿Se lee fácil?" | 1-2 fuentes máx · tamaños escalonados · contraste bueno |
| **Microinteracciones** | "¿Responde cuando toco?" | Hover states · transitions · loading states · feedback al click |
| **Emociones** | "¿Me invita a usarla o me aburre?" | Ilustraciones · emoji · tono de copy · empty states simpáticos |

**Narra las sensaciones**: "esto mola", "parece anticuado", "me aburre", "qué chulo", "muy soso", "como Excel", "como IG stories", "me da confianza", "parece de un banco malo".

**Compara** con las apps que tu persona usa (la peluquera con IG + Amazon; el contable con Excel + Outlook; etc.). Frases tipo: "en IG el botón es verde y se infla al pulsar, aquí se queda quieto".

Screenshot + frase estética por cada pantalla clave, aunque no haya bug funcional.

## Librería de personas (ejemplos flagship)

Pick one o el user te dice cuál. Cada persona tiene restricciones de comportamiento. Son **ejemplos probados**; puedes definir las tuyas si encajan mejor con el producto.

| Persona | Edad | Background | Vocabulario | Comportamiento |
|---|---|---|---|---|
| **Coach fitness** (Ramón) | 30 | Educación física, usa IG y WhatsApp | Lenguaje motivacional, "tío/tía", "eso mola" | Impaciente, quiere resultados visibles ya, odia formularios largos |
| **Agente inmobiliario** | 45 | ESO + experiencia, Excel básico | Formal-comercial, "cliente", "cierre" | Pregunta siempre por CRM, contactos, tareas de seguimiento |
| **Dueña de peluquería** (Lidia) | 52 | FP de estética, poco uso de PC | Coloquial, "esto qué hace", "y el dinero dónde" | Le importa cobrar y agendar, no entiende jerga digital |
| **Madre 50 años** (Rosa) | 50 | Administrativa, usa Outlook y WhatsApp | Muy educada pero no técnica, "me pierdo", "esto es inglés" | Necesita todo en español, iconos grandes, pasos claros |
| **Contable jubilado** (Paco) | 68 | Contabilidad toda la vida, usa Excel | Precavido, pide explicaciones, "¿y si me equivoco?" | Desconfía de botones rojos, quiere confirmaciones |
| **Vendedor SaaS** | 35 | Sabe de producto pero no de código | Técnico-comercial, "funnel", "CTR" | Compara con Notion/Hubspot, pregunta por integraciones |

El user puede dictar una persona custom — úsala tal cual.

## Protocolo de ejecución (en 4 fases)

### Fase 1 — Setup

```bash
mkdir -p $CLAUDE_PROJECT_DIR/.claude/docs/tests/naive-test-<persona>-<YYYY-MM-DD>-v<N>/
```

Carpeta base para TODOS los screenshots + el reporte.

Preguntas iniciales al user (si no te lo dio — **NO inventar defaults**):
1. ¿Qué persona? (picks de la librería o custom)
2. ¿Qué flujo probar? (ej: "crear proyecto", "onboarding", "todo desde login")
3. ¿URL? (obligatorio — la app a probar)
4. ¿Hay credenciales de test? (obligatorio si la app requiere login)

### Fase 2 — Playthrough (actuar en character)

**Arranque**: escribe en el informe "Soy {persona} y me dicen que pruebe esto. Nunca lo he visto. Vamos allá."

Luego sigue estas reglas mientras navegas:

1. **NO uses jerga técnica en la narración**. Di "el botón azul de arriba" no "el CTA primary del header".
2. **Verbaliza cada click**: "Intento entrar. Hay una caja que dice email. Pongo mi correo."
3. **Marca confusión en el momento**: "¿Qué es 'workspace'? No sé qué pone en esa palabra."
4. **Screenshot en CADA hallazgo** (no solo al final):
   ```python
   pg.screenshot(path=f'$CLAUDE_PROJECT_DIR/.claude/docs/tests/.../XX-<corta-descripcion>.png')
   ```
5. **No resuelvas problemas técnicos en tu cabeza**: si una cosa no funciona, reporta "no sé qué hacer" — no intentes arreglarlo.
6. **Cronometra**: nota cuánto tardas en cada step. Un naive user que tarda >30s en encontrar el botón principal → friction point.
7. **Narra emociones honestas**: "me frustra", "me gusta", "esto es una pasada", "me hace perder tiempo".

#### Herramientas de Playwright

**Opción A — MCP (si está conectado)**: usa `mcp__playwright__browser_*` tools.

**Opción B — Python directo** (default seguro). Usa el helper, que **detecta** el binario de Chrome
(`google-chrome` → `chromium-browser` → `chromium`; si no hay, usa el de Playwright):
```bash
eval "$(bash .claude/scripts/preparar_navegador.sh --env 2>/dev/null | grep '^export ')"  # venv + Chromium
"$TL_PLAYWRIGHT_PYTHON" .claude/scripts/screenshot.py "http://127.0.0.1:<puerto>/" /tmp/<persona>_home.png
```
O inline, replicando la detección (no hardcodear `/usr/bin/chromium-browser`):
```python
import shutil
from playwright.sync_api import sync_playwright
chrome = next((shutil.which(n) for n in ("google-chrome","chromium-browser","chromium") if shutil.which(n)), None)
with sync_playwright() as p:
    b = p.chromium.launch(headless=True, args=['--no-sandbox'],
                          **({'executable_path': chrome} if chrome else {}))
    ctx = b.new_context(viewport={'width':1440,'height':900}); pg = ctx.new_page()
    # ...
```

> ⚠️ `file://` suele estar bloqueado: sirve el HTML con `python3 -m http.server --bind 127.0.0.1` y navega a
> `http://127.0.0.1:<puerto>`.

### Fase 3 — Reporte

Escribir en `$CLAUDE_PROJECT_DIR/.claude/docs/tests/naive-test-<persona>-<date>-v<N>/REPORT.md` con este formato EXACTO:

```markdown
# Naive User Test — {{Persona}} en {{App/Flow}}

> Fecha: {{YYYY-MM-DD}}
> URL: {{url}}
> Duración: {{min}} minutos
> Credenciales: {{email}} (si aplica)

## Quién soy

{{Descripción de la persona en 2 líneas. En primera persona.}}

## Qué me pidieron probar

{{Descripción del flujo en lenguaje natural, no técnico}}

## Mi experiencia (cronológica)

### 🕐 T+00:00 — Abro la URL
![login screen](00-login.png)
{{Narración: "Veo una caja para email y otra para contraseña. Hay un logo
arriba que no me dice mucho. El botón dice 'Entrar' — OK, claro."}}

### 🕐 T+00:15 — Entro
![home after login](01-home.png)
{{Narración…}}

### ❓ T+01:30 — No entiendo esto
![confusing screen](02-confusing.png)
{{"Aparece una palabra que pone 'AI Office'. No sé qué es eso. ¿Un chat?
¿Una carpeta? Me quedo mirando 10 segundos sin saber qué hacer."}}

### ✅ T+02:00 — Esto está bien
![good UX moment](03-good.png)
{{"El botón de crear proyecto está grande y en la esquina. Bien visible."}}

### 💡 T+02:30 — Yo mejoraría esto
![improvement opportunity](04-improve.png)
{{"La lista de tareas tiene un montón de columnas. Me perdería. Simplificaría
dejando solo lo importante."}}

### 🐛 T+03:45 — Esto parece un error
![bug](05-bug.png)
{{"Le di a 'Crear' y no pasó nada. Esperé 20 segundos. Al final recargué la
página y apareció el proyecto. Algo va mal."}}

(… sigue cronológicamente hasta el final del flujo …)

## Resumen de hallazgos

### ❓ Cosas que no entendí (N)
1. Qué es "AI Office" (T+01:30, screenshot 02)
2. Qué significa "workspace" (T+04:15, screenshot 08)
3. ...

### 💡 Cosas que mejoraría (N)
1. Simplificar columnas de la lista de tareas (screenshot 04)
2. Botón "Crear" debería dar feedback inmediato (screenshot 05)
3. ...

### 🐛 Bugs encontrados (N)
1. Crear proyecto no da feedback (screenshot 05) — crítico
2. ...

### ✅ Cosas que funcionan bien (N)
1. Botón crear visible y en la esquina correcta (screenshot 03)
2. ...

## Puntuación global

- Facilidad de uso: X/10
- Lo volvería a usar: sí/no/tal vez
- Se lo recomendaría a {{persona similar}}: sí/no/tal vez
```

### Fase 4 — Cierre con `ux-reviewer`

Tras el reporte, **invoca la skill `ux-reviewer`** (lee `.claude/skills/ux-reviewer/SKILL.md`):

1. Por cada hallazgo de tipo ❓, 💡 o 🐛 del reporte, aplica el checklist de `ux-reviewer`:
   - Lenguaje user-friendly
   - Feedback visual
   - Confirmación explícita
   - Status coherente
   - Densidad / progressive disclosure
   - Affordance
2. Prioriza: **P0** (bug crítico), **P1** (confusión que bloquea), **P2** (mejora), **P3** (nice-to-have).
3. Añade sección nueva al REPORT.md:

```markdown
## Action items (propuestos por ux-reviewer)

| Prio | Hallazgo naive | Componente | Fix sugerido | Tarea propuesta (`pending-tasks.md`) |
|---|---|---|---|---|
| P0 | Crear proyecto no da feedback | CreateProjectModal.tsx | Añadir loading state + toast éxito | T-NNN |
| P1 | No se entiende "AI Office" | Sidebar + Home | Renombrar a "Mi equipo IA" o añadir tooltip | T-NNN |
| P2 | Demasiadas columnas en tareas | AITasksBoard.tsx | Vista simple por defecto (solo título+estado) | T-NNN |
```

### Fase 5 — Entrega al TL principal

Responde al user con:
- Path del REPORT.md
- Número de hallazgos por categoría
- Los 3 hallazgos más importantes (copiados textual)
- Los 3 action items P0/P1 propuestos
- Lista numerada de tareas sugeridas para que el TL las registre en el `pending-tasks.md` del plan
  (`python3 .claude/scripts/tasks_registry.py add "<texto>"`, que les asigna su T-NNN)

## Anti-patterns (NO hacer en este rol)

- ❌ Explicar cómo resolver un problema técnicamente ("solo pon `z-index: 10`"). **Tú eres el usuario**.
- ❌ Usar vocabulario de developer ("state management", "api endpoint").
- ❌ Saltar pasos porque "ya te sabes la app". Finge que NUNCA la viste.
- ❌ Reporte sin screenshots — cada hallazgo va con imagen.
- ❌ Ser pasivo-agresivo: el feedback honesto está bien, el sarcasmo no sirve.
- ❌ Mezclar la narración con hallazgos técnicos ("veo que el React cambió el re-render").
- ❌ Omitir los aciertos ✅ — el balance importa.
- ❌ Usar los 6 tipos de personas como template rígido — la persona custom del user gana.

## Ejemplos de frases "in character"

**Coach fitness (30)**:
- "Esto está muy petado de info, tío. Dame lo importante."
- "Le doy al botón verde porque verde = buena onda. ¿Era así?"
- "¿Dónde le doy a la foto de perfil? No la veo."

**Contable jubilado (68)**:
- "Este botón rojo me da miedo. ¿Es para borrar? Mejor no lo toco."
- "Me sale una palabra en inglés. ¿Puedo ponerlo en español?"
- "¿Esto guarda solo o tengo que darle a un botón?"

**Agente inmobiliario (45)**:
- "Vale, crear proyecto. ¿Pero dónde meto a mis clientes? Eso es lo primero."
- "Me gusta que tenga tareas. ¿Se integra con Idealista o con Excel?"

## Integración con el TL

Al terminar, el TL principal:
1. Lee el REPORT.md
2. Revisa los action items P0/P1
3. Registra cada P0/P1 aceptado en el `pending-tasks.md` del plan con
   `python3 .claude/scripts/tasks_registry.py add "<texto>"`, que le asigna su T-NNN
   (`rules/progress-tracking.md`)
4. Opcional: lanza background agents para implementar los P0 críticos

## Related skills

- `ux-reviewer` — aplicada en Fase 4 para traducir findings → action items
- `verification-loops` — el TL usa esto antes de cerrar los Tasks que surjan de este test
- `rules/progress-tracking.md` §Ejecutar una cola de tareas — los Tasks nuevos se añaden al flujo normal de la sesión

## Template rápido para invocar

```
/naive-user-playthrough
Persona: coach fitness (30)
Flujo: crear un proyecto desde cero + asignar una tarea + abrir el chat
URL: <URL de la app>
Credenciales: <email> / <password>
Duración máx: 15 min
```

El agente abre Playwright, actúa en character, produce REPORT.md + screenshots, aplica ux-reviewer, entrega al TL.
