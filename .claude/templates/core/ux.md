---
title: UX — decisiones y principios
reviewed:
reviewed_by:
---

<!--
  CAPA 4 del core (.docs/core/ux.md) — el porqué de la interfaz.
  Complementa a `user-flows.html`, que SÍ se genera del código: ahí está el recorrido
  paso a paso; aquí está el criterio con el que se decidió ese recorrido.

  ⚠️ `reviewed:` (YYYY-MM-DD) es obligatorio para que el índice confíe en esta página.
  Vacío → el índice lo marca SIN FECHA, en rojo. Ver .claude/templates/core/overview.md.

  Se revisa al cerrar cada plan que toque UI.
-->

# UX — decisiones y principios

## Principios de producto

Los criterios con los que se resuelve una duda de diseño sin volver a discutirla.

- [PERSONALIZAR — p.ej. "ninguna acción destructiva sin confirmación con nombre escrito"]
- [PERSONALIZAR]

## Patrones fijados

Esta tabla es **donde la skill `disenar-pantalla` anota la variante aprobada** (su paso 9) y de
donde la lee antes de bocetar la siguiente (su paso 1). Sin fila = no está decidido = se decide con
el Usuario en la próxima pantalla que lo necesite, y entonces se anota aquí.

| Patrón | Cómo se resuelve aquí | Dónde se ve |
|---|---|---|
| Listado de una entidad: ¿tabla, tarjetas o lista + detalle? | [PERSONALIZAR] | [PERSONALIZAR — pantalla] |
| Estados vacíos | [PERSONALIZAR] | [PERSONALIZAR — pantalla] |
| Carga / espera: ¿esqueleto, spinner o nada hasta que llega? | [PERSONALIZAR] | [PERSONALIZAR] |
| Errores de formulario: ¿al escribir o al enviar? | [PERSONALIZAR] | [PERSONALIZAR] |
| Error de red: ¿banner, aviso flotante o pantalla completa? | [PERSONALIZAR] | [PERSONALIZAR] |
| Confirmación de acciones destructivas | [PERSONALIZAR] | [PERSONALIZAR] |
| Dónde vive la acción primaria de una pantalla | [PERSONALIZAR] | [PERSONALIZAR] |
| Densidad: ¿cómoda o compacta? | [PERSONALIZAR] | [PERSONALIZAR] |
| *Solo si hay un chat que vende* — cada fila apunta a su regla en `patterns/stack/chat-ui-comercio.md` §1 y se comprueba con la skill `probar-widget` | | |
| Chat: sugerencias clicables (cuántas, qué siguiente paso; en WhatsApp, 3 botones como máximo) | [PERSONALIZAR] | [PERSONALIZAR — widget / WhatsApp] |
| Chat: tarjeta de producto (qué datos, ≤2 acciones, «Sin precio» y «Sin stock») | [PERSONALIZAR] | [PERSONALIZAR] |
| Chat: carrusel o lista (3-8 tarjetas en web; lista de 10 en WhatsApp) | [PERSONALIZAR] | [PERSONALIZAR] |
| Chat: carrito y venta cruzada (dónde se ve el total, cómo se etiqueta el complemento, deshacer) | [PERSONALIZAR] | [PERSONALIZAR] |
| Chat: paso al checkout (a qué checkout nativo lleva; el chat no cobra) | [PERSONALIZAR] | [PERSONALIZAR] |
| Chat: handoff a una persona (dónde está el botón, horario, qué ve la persona) | [PERSONALIZAR] | [PERSONALIZAR] |

Los **valores** del sistema de diseño (paleta, escala, tipografía) NO van aquí: viven en
`design-system.md`, y lo que falta se añade al origen (`patterns/stack/frontend-design-system.md`
§Paso 4). Aquí van decisiones de patrón e interacción.

## Recorridos principales

El detalle paso a paso está en `user-flows.html` (generado). Aquí solo el mapa mental:

1. [PERSONALIZAR — recorrido crítico: de dónde parte el usuario y dónde termina]

## Decisiones de UX que ya se tomaron

Lo que alguien podría querer "arreglar" sin saber que fue deliberado. **Y lo descartado, que vale
tanto como lo aceptado**: sin él, la misma propuesta vuelve dentro de dos meses.

| Decisión | Por qué | Cuándo |
|---|---|---|
| [PERSONALIZAR] | [PERSONALIZAR] | [PERSONALIZAR — fecha] |
| [PERSONALIZAR — descartado: p.ej. "tarjetas en el listado de pedidos"] | [PERSONALIZAR — "se pierde el orden por fecha"] | [PERSONALIZAR — fecha] |

### Preferencias del Usuario

Dichas por él, no deducidas. Cambian todos los bocetos siguientes, y si no se anotan se pierden con
la conversación en que se dijeron.

| Prefiere | Dicho el | Contexto |
|---|---|---|
| [PERSONALIZAR] | [PERSONALIZAR — fecha] | [PERSONALIZAR — en qué pantalla salió] |

## Deuda de UX conocida

Lo que sabemos que está mal y aún no se ha arreglado. Escribirlo evita que se reporte diez veces.

- [PERSONALIZAR]
