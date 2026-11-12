---
name: "documentar"
description: "Usar cuando hay que ESCRIBIR LA DOCUMENTACIÓN de un proyecto que ya tiene código, por capas (resumen llano + detalle técnico) y entregarla como PDF: 'vamos a redactar la documentación', 'documenta el proyecto', 'necesito la doc de arquitectura, datos, API…', 'quiero un PDF con toda la documentación', 'manual de usuario', 'DAFO del sistema', 'customer journey', 'documentación para subir a Drive', '/documentar'. Pregunta primero qué documentos y para quién, reparte la redacción entre agentes en paralelo con reglas comunes, hace las capturas desde la maqueta, pasa la revisión de Pol (huecos) y Priya (qué no sale de la máquina) y genera el PDF completo y uno por capítulo con `construir_pdf.py`, que aborta si un diagrama no se lee. Escribe en `.docs/documentacion/`. NO usar para: el primer CLAUDE.md de un repo (`codebase-onboarding`); un PDF suelto de propuesta, factura o informe (`pdf-premium`); un mapa visual del sistema (`/visual-map`); un ADR (`templates/adr-template.md`); auditar el harness (`mapear-sistema`); ni documentación que todavía NO tiene código detrás (eso es definir: `/arrancar`, `/producto`)."
user-invocable: true
metadata:
  version: 1.1.0
  author: Tech Lead Template
  category: workflow
  updated: 2026-10-03
  version_notas: "1.1 — mide el enredo (cruces, abanicos, rodeos, etiquetas pisadas), elige dagre/ELK por diagrama y aborta por encima de 3 puntos."
  origen: "Sesión «Docs ERP» de aquila-erp, 2026-09-30: 12 capítulos, 147 págs, aprobado por el Usuario («quedaron muy bien»). Los diagramas eran lo flojo → v1.0 mide la letra y apaisa."
---

# documentar — la documentación de un proyecto, por capas, en PDF

## Principio

La documentación que sirve tiene **dos lectores a la vez** (el dueño del negocio y el dev que llega
nuevo) y **una sola fuente de verdad: el código**. Se escribe en paralelo con agentes especialistas,
pero con UN bloque de reglas común para que los capítulos casen; la revisan dos criterios
independientes con el material delante (huecos/contradicciones y qué no debe salir de la máquina);
y se entrega en PDF porque un `.md` en Drive no pinta los diagramas y lleva lo que no debe salir.

## Cuándo activar

- El Usuario pide «la documentación», «documenta el proyecto», un capítulo concreto (arquitectura,
  datos, API, instalación, operación, manual, DAFO, journey) o «un PDF para Drive».
- Tras una salida a producción, cuando el overview dice algo que ya no es verdad.
- **Requisito:** hay código. Si no lo hay, NO es esta skill (ver `description`).

## Input contract — qué hace si falta algo

| Falta | Qué hace |
|---|---|
| Código (repo vacío o solo plan) | **Para** y deriva a `/arrancar` / `/producto`: documentar lo que no existe es inventar |
| La respuesta del Usuario a las preguntas del paso 1 | **No escribe nada.** Sin índice acordado no hay reparto |
| Una maqueta con datos simulados | Hace el manual **sin capturas** y lo dice; NUNCA captura datos reales |
| Un agente especialista en el proyecto (p. ej. `arquitecto-apis`) | Usa `general-purpose` con el mismo bloque de reglas y la misma tarea |
| Marca del proyecto (`design-system.md`, fuentes, logo) | PDF con la marca neutra del generador; avisa de que se puede vestir |
| Red (marked/mermaid van por CDN) | El generador aborta («no terminó de pintarse»); no hay PDF a medias |

## Procedimiento

### Paso 0 — Inventario (antes de preguntar)
`ls .docs/` y lo que haya de doc. Anota: qué existe, **qué está desfasado** (un overview que dice
«sin código» con el proyecto en producción es lo típico) y qué se genera solo (mapas, esquema
OpenAPI, ER): **lo que se genera no se reescribe a mano**, se enlaza o se regenera.

### Paso 1 — Preguntar (AskUserQuestion, dos rondas como máximo)
Ronda 1: **qué documentos** (multiSelect en dos grupos: técnicos —arquitectura · modelo de datos ·
API y fronteras · instalación · operación y despliegue · guía de desarrollo— y de negocio —overview
al día · seguridad y privacidad · flujos de trabajo · customer journey · manual de usuario · DAFO),
**para quién** (dev · negocio · ambos por capas ← recomendado) y **dónde** (Markdown en el repo +
PDF ← recomendado). Ronda 2, solo si eligió alguno ambiguo: **DAFO de qué** (del sistema frente a
la alternativa comprada · del negocio · ambos), **journey de quién** (del cliente final · del
usuario interno · no aplica), **PDF único o por capítulo**.

### Paso 2 — Índice y estado
Escribe el índice acordado en `PROGRESS.json` (un ítem por bloque de capítulos) y numera los
ficheros `NN-nombre.md` en `.docs/documentacion/` (el 01 puede ser `.docs/core/overview.md`).
Da el ETA y los hitos (`rules/communication-fast-ack.md`).

### Paso 3 — Repartir la redacción (agentes en paralelo, en UN mensaje)

| Capítulo | Agente (si no existe → `general-purpose`) |
|---|---|
| Modelo de datos | `desarrollador-backend` |
| API y fronteras / contratos | `arquitecto-apis` |
| Seguridad y privacidad | `code-review-gate` §Seguridad Django/DRF + `sofia-pentester` |
| DAFO | `pol-product-advisor` |
| Arquitectura + guía de desarrollo · instalación + operación · flujos + journey + manual | `general-purpose` (uno por pareja/trío) |

Cada prompt = la tarea concreta del capítulo (qué secciones, qué ficheros de código mirar) **+ este
bloque literal** (es lo que hace que doce capítulos casen):

```
FORMATO COMÚN (obligatorio):
- La verdad es el CÓDIGO y la config, no los docs (di cuáles están desfasados).
- Por capas: frontmatter YAML (título, origin: escrito, reviewed: <hoy>, reviewed_by: "pendiente — <Usuario>"),
  `# Título`, `## En corto` (5-10 líneas llanas, sin jerga, para negocio), luego el detalle técnico.
- Diagramas en ```mermaid siguiendo las «Reglas de dibujo» de abajo (uno por idea, ≤12 nodos, camino principal
  recto, salidas comunes en una nota y no en N flechas). Nada de «;» en mensajes de sequenceDiagram.
- Cita el código como `ruta/fichero.py:línea`.
- CERO datos personales reales (ejemplos inventados y evidentes) y CERO secretos (ni tokens, ni .env,
  ni IP/host de redes privadas → `<host-privado>`).
- Lo que no puedas confirmar: «no verificado». Al final, una sección «Incoherencias» código↔docs.
- Solo escribe tu(s) fichero(s). Solo lectura del resto. No ejecutes tests ni builds pesados.
Devuelve: ruta(s), secciones, e incoherencias encontradas.
```

⚠️ **Al recibir cada informe, comprueba DÓNDE escribió.** Un agente que corre aislado en worktree
deja el fichero en `.claude/worktrees/agent-*/…`: cópialo al repo y borra el worktree al final.

### Paso 4 — Capturas (mientras redactan)
Solo desde la **maqueta con datos simulados** (`npm run dev:mock` o equivalente), servida en
`127.0.0.1`, con `.claude/scripts/screenshot.py` o Playwright. **Sustituye en el DOM el nombre de la
persona del marco** (el simulado suele llevar el del dueño) antes de capturar. Una captura que no
enseña lo que su pie dice (el panel no se abrió) se borra, no se deja. Las referencias del manual a
capturas que no existen se quitan antes de generar (el generador aborta con imágenes rotas).

### Paso 5 — Revisión independiente (dos agentes, en paralelo, con el material delante)
- **`pol-product-advisor`**: huecos (qué pregunta de un lector no responde nadie), **contradicciones
  ENTRE capítulos** (cifras, plazos, nombres) con `fichero:línea` de cada lado, «En corto» con jerga,
  y UNA lista deduplicada de las incoherencias código↔docs de todos los capítulos.
- **`priya-privacy-auditor`** como **filtro de salida** (no auditoría del sistema): datos personales
  en texto y capturas (que las abra), secretos e identificadores de la máquina, **lo que ayuda a un
  atacante** si el PDF circula, y promesas de privacidad que el sistema no cumple. Veredicto: puede
  salir · con cambios · no.

### Paso 6 — Aplicar
Lo que engaña, primero (Pol) y lo que bloquea (Priya). Lo que debe quedarse en el repo pero NO salir:
entre `<!-- pdf:omitir -->` y `<!-- /pdf:omitir -->` (filas de riesgos técnicos → a una subsección
aparte envuelta entera: una fila suelta envuelta rompe la tabla en el repo). Rutas y nombres de la
máquina → `sustituir` en la config, no en el texto (al operador le sirven).

### Paso 7 — Config del PDF
`.docs/documentacion/documentacion.json` (ver `documentacion.ejemplo.json` junto a esta skill):
`titulo`, `capitulos` (si no, toma `NN-*.md`), `sustituir`, y `marca` con colores, fuentes
(`ficheros` locales: nada de Google Fonts en un documento interno) y logo, sacados de
`.docs/core/design-system.md` y del bloque `@theme`.

### Paso 8 — Generar y verificar

⚠️ Recordatorio (repetido a propósito): un diagrama ilegible NO se arregla bajando el mínimo. Se parte.

```bash
python3 .claude/skills/documentar/construir_pdf.py --avisar      # 1ª vez: triaje (lista, no aborta)
python3 .claude/skills/documentar/construir_pdf.py --separados   # el bueno: aborta si algo no se lee
```
Lo que no cabe en vertical sale en **página apaisada** sola; si ni así llega a 10,5 px, **aborta**
diciendo capítulo, diagrama y sección → partirlo (por idea), girarlo (`TD`↔`LR`) o acortar etiquetas.
Si aborta por **enredado**, aplica las «Reglas de dibujo» (abajo) y repite.
Después, **comprueba lo omitido en el PDF, no en el Markdown**: `pdftotext` + `grep` de cada cosa que
Priya mandó quitar (debe dar 0) y mira 2-3 páginas renderizadas (`pdftoppm`).

### Paso 9 — Entregar y cerrar
Link por la red privada (servidor ligado a esa IP, nunca `0.0.0.0`; ciérralo por su puerto al
acabar) o un zip. `*.pdf`, `pdf/`, `_pdf/` y `*.zip` van al `.gitignore` de `.docs/documentacion/`.
Commit de los `.md`, la config y las capturas. En la memoria del proyecto: qué capítulos, cómo se
regenera, y **lo pendiente que salió al documentar** (riesgos e incoherencias que nadie ha decidido).

## Reglas de dibujo (las mide el generador; las que fallan, abortan)

Un diagrama se lee mal por tres causas, y la letra pequeña es solo una. Las otras dos son **enredo**
(líneas que se cruzan o pisan) y **ruido** (la misma regla dibujada N veces). Medido en la doc de
aquila-erp: el «mapa del viaje» tenía solo 2 cruces y aun así se veía desordenado por un abanico de
4 flechas «12 meses sin movimiento» hacia una misma caja.

| Regla | En vez de | Haz |
|---|---|---|
| **Un camino principal, recto** | el flujo feliz zigzaguea entre ramas | declara primero el camino principal, en orden; las ramas después |
| **Lo común no se dibuja N veces** | 4 flechas iguales a «Caducado» desde 4 cajas | UNA nota o leyenda («cualquier estado, tras 12 meses sin movimiento → caducado») o una tabla debajo |
| **Como mucho 1 flecha de vuelta** | volver / reactivar / deshacer cruzándolo todo | una sola, o dilo en el texto; los «deshacer» casi nunca merecen flecha |
| **Nada de atajos largos** | una flecha que salta 3 niveles y rodea el diagrama | otro diagrama, o una nota en la caja de destino |
| **Un concentrador = un diagrama** | 6 apps que dependen todas de todas | partir por capa (quién depende de `core`, quién de `crm`) o una tabla de dependencias |
| **Orientación según la forma** | una cadena larga en `TD` que no cabe | cadenas → `LR`; árboles y decisiones → `TD` |
| **Etiqueta corta en la flecha** | la explicación entera en la flecha | 1-3 palabras; el porqué en el texto |

El generador lo comprueba solo: pinta cada flujo y cada diagrama de estados con dos motores (dagre y
ELK), se queda el menos enredado y lo puntúa (`enredo.js`: cruces ×3, etiquetas pisadas ×3, líneas
sobre cajas ajenas ×3, rodeos ×1, abanico de ≥4 flechas +2, etiqueta repetida en ≥3 flechas +2).
**1-3 puntos = aviso; más de 3 = ERROR** con el diagrama, la sección y qué falla.

⚠️ Recordatorio (repetido a propósito): ni el enredo ni la letra se arreglan subiendo `enredo_max` o
bajando `letra_minima_px`. Se reorganiza el diagrama con la tabla de arriba.

## Salida (lo que se le reporta al Usuario)

`capítulos` (nº · fichero · para quién) · `pdf` (ruta · páginas · nº de apaisadas) · `omitido_del_pdf`
(qué y por qué) · `verificacion` (pdftotext limpio sí/no, ilegibles 0) · `pendiente` (riesgos,
incoherencias, capturas que faltan) · `commits`.

## Anti-patterns

- ❌ Escribir antes de que el Usuario apruebe el índice (paso 1) — doce capítulos de lo que no pidió.
- ❌ Agentes sin el bloque común → capítulos que no casan (uno dice 9 operaciones, otro 17).
- ❌ Fiarse de los docs existentes en vez del código: el overview desfasado se propaga a doce sitios.
- ❌ Capturas con datos reales, o con el nombre del dueño en el marco del simulado.
- ❌ Subir los `.md` a Drive: llevan lo `pdf:omitir` y los diagramas salen como texto.
- ❌ Un revisor al que solo se le pasa la conclusión de otro agente (`rules/verification.md` §nivel 4).
- ❌ Bajar `letra_minima_px` o subir `enredo_max` para que «pase»: es apagar el instrumento.
- ❌ Dibujar la misma regla como N flechas (el abanico de «12 meses» del ERP): va en una nota.
- ❌ Dar por omitido algo sin `pdftotext | grep` sobre el PDF generado.
- ❌ Arreglar en esta sesión las incoherencias código↔docs que salen: se listan y decide el Usuario.

## Ejemplos

**Usuario:** «Vamos a redactar la documentación del ERP, pregúntame antes los documentos.»
**TL:** paso 0 (detecta el overview desfasado) → AskUserQuestion ronda 1 y 2 → 7 agentes en un
mensaje con el bloque común → capturas de la maqueta → Pol + Priya → `pdf:omitir` → PDF de 147 págs
+ 12 sueltos → link por tailnet → memoria. (aquila-erp, 2026-09-30.)

**Usuario:** «Solo quiero el manual de usuario en PDF para el equipo.»
**TL:** paso 1 reducido (para quién, ¿capturas?) → un agente para el manual → capturas → Priya (sin
Pol: no hay capítulos que contrastar) → `--separados` y entrega el `pdf/…-NN-manual-de-usuario.pdf`.

**Usuario:** «Los diagramas del PDF se leen mal.»
**TL:** `construir_pdf.py --avisar` → lista de ilegibles con capítulo y sección → partir/girar cada
uno → repetir sin `--avisar` hasta código 0.

## Related

- `pdf-premium` — el método Playwright del que sale el generador (para PDFs sueltos, no colecciones).
- `codebase-onboarding` — el CLAUDE.md inicial; esta skill documenta para personas, no para el agente.
- `rules/verification.md` — el instrumento que no puede medir aborta; nivel 4 con material delante.
- `rules/html-output.md` — servir por red privada, nunca `0.0.0.0`.
- Agentes: `pol-product-advisor`, `priya-privacy-auditor`, `desarrollador-backend`, `sofia-pentester` (y `code-review-gate` §Seguridad).
