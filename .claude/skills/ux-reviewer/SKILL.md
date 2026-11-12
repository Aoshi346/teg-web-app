---
name: ux-reviewer
description: >-
  Usar como gate antes de marcar DONE cualquier tarea de UI; obligatorio en contenido de agentes,
  vistas de estado y modales. Junta anti-patrones de UX (IDs técnicos, acciones sin feedback) y las
  reglas de interfaz de Vercel sobre el código, con fichero:línea.
  NO usar para: la crítica visual (vera-art-director), probar como usuario (lidia-naive-tester) ni
  la accesibilidad (aitor-a11y-auditor).
user-invocable: true
metadata:
  version: 2.0.0
  author: tech-lead-template
  category: quality
  updated: 2026-10-31
  tech-stack: any (React, Vue, plantillas Django…); la parte B está escrita para JSX/CSS
  rules_source: "vercel-labs/web-interface-guidelines@434b7f9 (MIT), en references/; vía fitapp T-065"
---

# ux-reviewer — la revisión de interfaz antes de DONE

## Principio

El código puede estar técnicamente bien y entregar una mala experiencia. Esta skill es **la única
revisión de interfaz del template** y mira dos cosas a la vez, porque por separado se pisaban:

| Parte | Qué mira | Sobre qué | De dónde sale |
|---|---|---|---|
| **A · Anti-patrones de UX** | Lo que ve el usuario: IDs técnicos, acciones sin respuesta, datos en crudo, estados que se contradicen | La pantalla corriendo (captura) | De la casa: fallos que se repiten |
| **B · Reglas de interfaz** | Lo que está mal escrito en el código de la interfaz: foco, etiquetas, `inputmode`, `transition: all`, cifras tabulares… | Los ficheros del cambio, con `fichero:línea` | Vercel Web Interface Guidelines, **fijadas** a `434b7f9` y en castellano: `references/web-interface-guidelines.md` |

Hasta el 31-10-2026 (sub-ola 3.65, UX-D11) la parte A era esta skill sola, en un checklist genérico, y
la B vivía solo en fitapp como comando aparte. **Lo que es WCAG no se juzga aquí**: la parte B lo marca
como linter previo y el veredicto es de Aitor.

**Peso de su voz** (`rules/motores-de-diseno.md` §1 y §8): la parte A es criterio de la casa
(escalón 7); la B es prosa de un tercero (escalón 8). Ninguna gana a un medidor (`gate_diseno.py`,
`contraste.py`) sobre lo que ese medidor mide.

## Cuándo activar

**Obligatorio** — componentes con contenido generado por agentes · vistas de estado o de workflow ·
modales y formularios · vistas que enseñan IDs, claves o datos de sistema.

**Recomendado** — cualquier cambio en frontend, plantillas o HTML · páginas o secciones nuevas ·
refactor de componentes.

Disparadores: 'revisa la UX de esto', 'pasa el ux-reviewer', 'antes de cerrar esta pantalla',
'revisa la interfaz', 'web interface guidelines', 'lint de la interfaz'.

## Contrato de entrada

| Necesito | Si no lo tengo |
|---|---|
| **Los ficheros del cambio** (parte B) | `git diff --name-only <base>` filtrado a `*.tsx`, `*.jsx`, `*.vue`, `*.html`, `*.css`. Si no hay ninguno, la parte B sale «sin ficheros de interfaz» y se dice |
| **Una URL viva** (parte A) | Se levanta en `127.0.0.1` (`rules/security.md`). Si no se puede, la parte A sale **«no medida: sin URL»**, nunca «OK» |
| El idioma del producto | Se lee de `CONFIGURACION.yaml` o del propio copy. Las reglas **(ES/CA)** de la parte B solo aplican si el producto está en castellano o catalán |

## Procedimiento

### 1. Parte A — la pantalla, como la ve el usuario

Captura a los tres anchos del canon (`patterns/diseno/README.md` §Chequeo a 3 anchos):

```bash
for w in 1440 768 390; do
  python3 .claude/scripts/screenshot.py "http://127.0.0.1:<PUERTO>/<ruta>" /tmp/ux-<feature>-$w.png $w 900 3000
done
```

Y sobre las capturas, los ocho puntos:

1. **Lenguaje del usuario** — sin UUIDs, IDs técnicos, rutas de sistema ni trazas · estados en
   lenguaje natural («En curso», no `IN_PROGRESS`) · errores con un mensaje útil, no el error crudo.
2. **Respuesta a cada acción** — el botón enseña que está procesando · al terminar, toast o cambio
   visible · nunca silencio después de enviar.
3. **Confirmación explícita** — lo destructivo pide confirmación o permite deshacer · nada se guarda en
   silencio en un `onBlur` · lo guardado lo dice («Guardado»).
4. **Contenido de agentes** — el Markdown se renderiza · el JSON o los datos estructurados salen
   formateados · las URL son clicables · el código, con resaltado si aplica.
5. **Estados coherentes** — lo que dice la pantalla coincide con el backend · no hay estados que se
   contradicen en la misma vista · listas y contadores cuadran entre sí.
6. **Densidad** — historial, comentarios y logs largos empiezan plegados y se despliegan a demanda;
   si importa, el estado se recuerda al navegar.
7. **Acciones visibles** — las acciones importantes se ven (no solo al pasar el ratón o con clic
   derecho) · el estado vacío dice qué hacer («No hay X. Crear la primera →»).
8. **Dónde estoy** — migas o indicador de posición en vistas anidadas · el hijo enlaza al padre ·
   desde un elemento se crean o se ven sus hijos.

### 2. Parte B — el código, regla por regla

Lee `references/web-interface-guidelines.md` y comprueba **solo los ficheros del cambio** contra sus
reglas. Salida con su formato: por fichero, `fichero:línea - hallazgo`, sin preámbulo.

> ⚠️ Recordatorio, repetido a propósito: las reglas de la sección «Accesibilidad» y «Estados de foco»
> son un **linter previo**. Un hallazgo ahí se reporta; el veredicto WCAG lo da `aitor-a11y-auditor`,
> y un «sin hallazgos» aquí **no** es «accesible».

### 3. El veredicto

```
ux-reviewer · <feature> · <fecha>
A · pantalla   : <n> hallazgos (puntos 1-8) | no medida: <por qué>
                 capturas: /tmp/ux-<feature>-{1440,768,390}.png
B · código     : <n> hallazgos en <m> ficheros | sin ficheros de interfaz
                 <fichero:línea - hallazgo> …
para Aitor     : <hallazgos de accesibilidad o foco de la parte B, si los hay>
veredicto      : pasa | no pasa (<qué bloquea>)
```

**Bloquea el DONE**: cualquier hallazgo de los puntos 1, 2, 3 o 5 de la parte A, o un anti-patrón de
la lista final de la parte B. El resto se reporta y se decide.

## Anti-patrones

| Anti-patrón | Síntoma | Arreglo |
|---|---|---|
| ID técnico en la UI | El usuario ve `abc123-def-456` o `c__N_M` | Nombre o etiqueta legible |
| JSON crudo | Un campo enseña `{"key": "value", ...}` | Componente que lo pinte |
| Acción sin respuesta | Clic en «Guardar» y no pasa nada visible | Spinner + toast de confirmación |
| Estado incoherente | La insignia dice «Activo» y el formulario «Pendiente» | Una sola fuente de verdad del estado |
| Historial siempre abierto | La vista carga 50 entradas a la vista | Plegado por defecto |
| Vacío sin llamada a la acción | Lista vacía sin decir cómo crear | «No hay X. [Crear X →]» |
| Destructivo sin confirmar | «Eliminar» actúa al instante | Confirmación o deshacer |

Y de uso de la propia skill:

- ❌ Dar la parte A por buena sin captura → sin URL es «no medida», no «OK».
- ❌ Correr la parte B sobre todo el repo → solo los ficheros del cambio; lo heredado va por
  `rules/refactor-progresivo.md`.
- ❌ Bajarse las reglas de Vercel de `main` «para estar al día» → se suben de commit a propósito
  (`references/`, cabecera).
- ❌ Leer un «sin hallazgos» de la parte B como accesible → eso lo dice Aitor.
- ❌ Aplicar las reglas **(ES/CA)** a un producto en inglés, o al revés.

## Ejemplos

### Usuario: «ya está la pantalla de pedidos, ciérrala»
TL: levanta el front en `127.0.0.1`, captura a 1440/768/390, pasa los ocho puntos (parte A) y la
parte B sobre los `.tsx` del diff. Sale: *«A: 1 hallazgo (punto 2, "Guardar" sin respuesta). B: 3 en
2 ficheros — `OrderForm.tsx:41 - campo sin autocomplete`, `OrderList.tsx:12 - transition: all`,
`OrderList.tsx:88 - botón de icono sin aria-label` (este, para Aitor). No pasa: punto 2.»*

### Usuario: «revisa la interfaz de este componente» (sin servidor)
TL: parte B sobre el componente; parte A **no medida: sin URL**, y lo dice en el veredicto.

### Usuario: «es un panel en inglés»
TL: la parte B entera salvo las tres reglas (ES/CA), que dejan paso a las de inglés del original.

## Integración

```
implementar → tests (verification-loops) → build → ux-reviewer ← aquí → captura como evidencia → DONE
                                                        └─ si es wave con UI: /qa-loop (Lidia + Vera + Ignacio)
```

## Related

- `references/web-interface-guidelines.md` — la parte B, fijada a `434b7f9`, con su licencia
- `rules/motores-de-diseno.md` §8 — dónde encaja esta skill en el paquete UI/UX y cuánto pesa
- `patterns/diseno/README.md` §Chequeo a 3 anchos — los anchos de la captura
- `aitor-a11y-auditor` — el veredicto de accesibilidad · `vera-art-director` — la crítica visual ·
  `lidia-naive-tester` — el usuario de verdad
- `naive-user-playthrough` — se cierra con esta skill
- `scripts/screenshot.py` — capturas con la detección de navegador de la casa
