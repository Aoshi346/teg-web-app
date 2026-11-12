# /schema — Esquemas de ingeniería como HTML visual (lean-canvas, C4, casos de uso…)

> **Qué hace:** crea/edita los **artefactos de ingeniería de software** de un plan como HTML
> autocontenido y muy visual: Lean Canvas, preguntas clave, user stories, casos de uso (secuencia),
> C4 (Contexto/Contenedores/Componentes). Complementa a **`/visual-map`**, que cubre los esquemas
> **vivos derivados del código** (arquitectura runtime, modelo de datos ER, flujos de usuario).
>
> **Dónde viven:** `.docs/plans/<plan>/schemas/` + el config `schemas.json`. Galería en `schemas.html`.
> **Convención de plan:** ver `rules/plan-docs-structure.md` / `.docs/plans/<plan>/STRUCTURE.md`.

## Triggers
`/schema`, `/schema <id>`, "hazme el lean canvas", "diagrama C4 del proyecto", "caso de uso de X",
"esquema de secuencia de …", "qué esquemas me faltan".

## Catálogo (id · etapa · cuándo se sugiere)

| id | esquema | etapa | se sugiere | quién lo genera |
|----|---------|-------|-----------|-----------------|
| `lean-canvas` | Lean Canvas | idea | **al arrancar** el proyecto (primero) | /schema |
| `key-questions` | Preguntas clave | discovery | antes de codificar | /schema |
| `user-stories` | User stories + criterios | inception | al definir alcance | /schema |
| `use-case <n>` | Caso de uso (secuencia) | design | por feature compleja | /schema |
| `c4-context` | C4 · Contexto | arch | hay sistemas externos | /schema |
| `c4-container` | C4 · Contenedores | arch | al definir despliegue | /schema |
| `c4-component` | C4 · Componentes | arch | módulo complejo | /schema |
| `er` | Modelo de datos (ER) | data | con esquema de BD | **/visual-map** |
| `architecture` | Arquitectura runtime | code | con código | **/visual-map** |
| `user-flows` | Flujos de usuario | ux | con UI | **/visual-map** |

## Protocolo (NO crear sin confirmación)

1. **Lee `schemas.json`** del plan (créalo si no existe, con todos los `id` en `status:"todo"`).
2. **Sugiere** según `stage` del proyecto: lista los `recommended` que no están `done` (o están `stale`).
   Ejemplo: "Estás en etapa *idea* → te sugiero `lean-canvas` y `key-questions`. ¿Cuál creo?"
3. **El usuario elige** qué crear/editar. Para cada uno:
   - Copia la plantilla self-contained correspondiente (ver `templates/html/` cuando exista la del
     esquema; si no, genera una nueva respetando `rules/html-output.md`).
   - **Rellena el bloque `DATA`** con datos reales del proyecto (lee código/README/CLAUDE.md;
     para los de negocio, pregunta lo que falte: problema, segmentos, etc.).
   - Guarda en `schemas/<id>.html` y **actualiza `schemas.json`** (`status`, `file`, `updated`).
4. **Lifecycle / sentido común:** Lean Canvas al principio y se **edita** al cambiar de etapa; los
   esquemas vivos (ER/arquitectura/flujos) se regeneran con `/visual-map`. El usuario decide cuáles
   mantener al día (campo `edit:true`).
5. **Marca stale:** si el código cambió mucho desde `updated`, marca `status:"stale"` y avísalo en la
   galería (no regeneres sin permiso).

## Reglas
- 1 archivo `.html` autocontenido por esquema (CSS/JS inline, sin CDN). Comparte tokens de `base.html`.
- Botón "copiar como Markdown" donde aplique (loop humano↔agente).
- Siempre **proponer y dejar decidir**; nunca generar el set entero sin que el usuario lo pida.
- Verifica el render (`python3 -m http.server` + screenshot) antes de dar por hecho un esquema.

## Ejemplos
- `/schema` → te digo qué falta para tu etapa y eliges.
- `/schema lean-canvas` → crea/edita el Lean Canvas con los datos del proyecto.
- `/schema use-case "cerrar ronda"` → diagrama de secuencia de ese caso.
- `/schema c4-context` → diagrama C4 nivel 1 (personas + sistema + externos).

Ejemplos vivos (productivity_system): `_archive/2026-10-19/planes-cerrados/2026-06-21-visual-plans/schemas/`.
