---
título: "<Nombre del producto o de la funcionalidad>"
estado: borrador          # borrador | en revisión | aprobado | obsoleto
autor: "<quién>"
fecha: YYYY-MM-DD
revisado: YYYY-MM-DD      # obligatorio si se promueve a .docs/core/ — rules/plan-docs-structure.md
---

# PRD · <nombre>

> **Qué es un PRD, sin jerga:** el *documento de requisitos de producto*. Reúne en un solo sitio
> **qué se va a construir, para quién y cómo sabremos que está bien**. No dice cómo se programa —
> eso es el `plan.md` de la sesión SpecKit.
>
> **Cuándo escribirlo:** producto nuevo, módulo grande, o cualquier trabajo donde haya más de una
> persona con opinión sobre el resultado. **Cuándo NO:** una feature dentro de algo ya definido (con
> `spec.md` basta) y cualquier cosa de 1-3 ficheros.
>
> **Dónde vive:** `.docs/plans/<YYYY-MM-DD-slug>/prd.md` mientras el trabajo está vivo. Si describe
> el producto de forma estable, se promueve a `.docs/core/` (`rules/plan-docs-structure.md`).
>
> **Relacionado:** `/schema` (lean canvas, C4, casos de uso — piezas que se enlazan desde aquí, no
> se copian) · `rules/speckit-workflow.md` (el PRD alimenta el `spec.md`) · `templates/ticket-template.md`
> (el nivel de abajo) · `rules/adr.md` (las decisiones caras van a un ADR, no aquí) ·
> `pol-product-advisor` (revísalo con él antes de darlo por bueno).

**Regla de oro al rellenarlo: una sección vacía se borra o se marca `pendiente: <quién · cuándo>`.**
Un apartado con texto de relleno es peor que uno ausente — el ausente se ve, el de relleno se cree.

---

## 1 · Introducción y objetivos

**El problema.** Qué duele hoy, a quién y con qué frecuencia. Con un dato o un ejemplo concreto, no
con una generalidad.

**El objetivo.** Qué será verdad cuando esto exista. En resultado observable, no en tarea.

| Objetivo | Cómo se medirá | Valor hoy | Objetivo |
|---|---|---|---|
| | | | |

**Fuera de alcance (explícito).** Lo que alguien va a asumir que está incluido y **no lo está**.
Es la sección que más discusiones ahorra y la que más se omite.

---

## 2 · Personas implicadas

| Rol | Quién | Qué necesita de esto | Quién decide qué |
|---|---|---|---|
| Responsable de producto | | | decide alcance y prioridad |
| Usuario final | | | — |
| Quien lo construye | | | decide el cómo |
| Quien lo mantiene después | | | veto técnico |
| Quien paga | | | decide el presupuesto |

> Si la columna "quién decide qué" queda vacía, la primera discusión de alcance no tendrá árbitro.

---

## 3 · Historias de usuario

Formato: **Como `<rol>`, quiero `<acción>`, para `<beneficio>`.** El "para" es la parte que se salta
todo el mundo y la única que permite descartar una historia cuando hay que recortar.

| ID | Historia | Prioridad | Esfuerzo |
|---|---|---|---|
| US-1 | Como … quiero … para … | P0 | M |

Prioridad: `P0` imprescindible para lanzar · `P1` importante · `P2` deseable · `P3` algún día.
Esfuerzo: `S` · `M` · `L` · `XL` — **la misma escala que el resto de la casa** (report-kit:
S=1 · M=3 · L=5 · XL=10 días).

> **Si todo es P0, nada es P0.** Un PRD donde más de la mitad de las historias son P0 no está
> priorizado: está pidiendo un deseo.

---

## 4 · Componentes y mapa de pantallas

Qué piezas tiene el sistema y cómo se llega de una a otra. Un esquema vale más que la lista.

```
<mapa de pantallas o de módulos — texto plano vale>
```

Para el diagrama de verdad, **enlaza `/visual-map`** (arquitectura · modelo de datos · flujos) en
lugar de dibujarlo aquí: el generado se mantiene solo, el copiado envejece en silencio.

---

## 5 · Funcionalidades

Una fila por funcionalidad. **Enlaza** a su historia de usuario en vez de repetirla.

| ID | Funcionalidad | Historias | Prioridad | Notas |
|---|---|---|---|---|
| F-1 | | US-1, US-3 | P0 | |

---

## 6 · Diseño y experiencia

- **Principios de la interfaz** para este producto (2-3, no una lista de buenas intenciones).
- **Estados que hay que diseñar y siempre se olvidan:** vacío, cargando, error, sin permisos,
  primera vez.
- **Enlaces** a maquetas o al sistema de diseño. No pegues capturas: caducan.
- **Accesibilidad:** nivel objetivo (por defecto WCAG 2.2 AA — `aitor-a11y-auditor`).

---

## 7 · Requisitos técnicos

| Requisito | Valor | Por qué ese número |
|---|---|---|
| Volumen esperado | | |
| Rendimiento (p95) | | |
| Disponibilidad | | |
| Datos personales tratados | | ⚠️ si hay, `priya-privacy-auditor` antes de construir |
| Integraciones externas | | |
| Navegadores / dispositivos | | |

**Restricciones conocidas:** lo que no se puede cambiar (stack, proveedor, presupuesto, fecha).

> **Las decisiones de arquitectura NO van aquí**: van a un ADR con sus alternativas descartadas
> (`rules/adr.md`, Gate D de `plan-gates.md`). Aquí solo se enlazan.

---

## 8 · Planificación

| Hito | Qué incluye | Fecha objetivo | De qué depende |
|---|---|---|---|
| | | | |

**Riesgos**, con plan y no solo con adjetivo:

| Riesgo | Probabilidad | Impacto | Qué haremos si pasa |
|---|---|---|---|
| | | | |

---

## 9 · Criterios de aceptación

**El apartado que decide si el PRD sirve para algo.** Se escriben en Gherkin porque así cada
criterio **ya trae dentro el plan de su propia verificación** (`rules/verdict-contract.md`
§Gherkin→verificación):

```gherkin
Dado que <contexto: el estado inicial que hay que montar>
cuando <acción: el paso reproducible>
entonces <resultado: UNA aserción observable>
```

| ID | Criterio | Funcionalidad |
|---|---|---|
| AC-1 | Dado que… cuando… entonces… | F-1 |

> **Si el "entonces" no es observable, el criterio está mal escrito.** "Entonces la experiencia es
> fluida" no se puede verificar; "entonces aparece el aviso «Sin stock» y el botón de pagar sigue
> deshabilitado", sí. Devuélvelo a redacción antes de construir nada.

**Definición de terminado** (aplica a todo el PRD): `rules/verification.md` + evidencia según
`rules/trunk-based-flow.md` §4.

---

## 10 · Apéndices

- Glosario de los términos del dominio que usa este documento.
- Enlaces: investigación, feedback de clientes, competencia (`/competitor-report`), ADRs, esquemas
  de `/schema`.
- **Preguntas abiertas**, con dueño y fecha. Esta lista **debe estar vacía** antes de pasar el
  estado a `aprobado`.

| Pregunta | Dueño | Para cuándo |
|---|---|---|

---

_Template version: 1.0 · PRO-3, aprobado 2026-08-08. SPEC-5 (la capa de producto completa sobre
SpecKit) fue **descartada**, así que estas plantillas van sueltas y no dentro de aquella._
