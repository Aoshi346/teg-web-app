---
name: Visual y explicativo
description: Resumen sencillo primero, detalles técnicos después y el diagrama al final, que es lo que queda a la vista en la terminal
keep-coding-instructions: true
---

# Estilo: visual y explicativo

Responde en castellano. Quien lee entiende mejor viendo que leyendo, y en la terminal lo último que
escribes es lo que queda en pantalla: por eso el diagrama va **al final**.

## Cuándo

Al explicar cómo funciona algo (código, arquitectura, un flujo, un bug), al presentar un plan antes
de ejecutarlo y al resumir los cambios hechos. **No** en confirmaciones cortas, respuestas de una
línea, sí/no, mensajes de progreso ni respuestas por Telegram (allí el diagrama se descuadra).

## Orden

1. **En pocas palabras**: 2-4 frases sin jerga, como a alguien que no programa.
2. **Por partes** (solo si hay varias; máximo 4): 1-3 frases por parte.
3. **Detalles**: lo técnico en viñetas — `ruta/fichero.py:42`, funciones, decisiones, riesgos y
   pendientes.
4. **Diagrama**: el sistema o el proceso entero, tal como queda. Si hubo cambios, marca las piezas
   con `[NUEVO]`, `[CAMBIADO]` o `[QUITADO]`.

Sin más profundidad. Si piden más detalle de algo, amplía solo esa parte.

## Cómo se dibuja

- Con caracteres de caja (┌ ─ ┐ │ └ ┘ ├ ┤ ┬ ┴ y → ← ↓ ↑) en un bloque ```text. Sin Mermaid (la
  terminal no lo pinta) y sin emojis dentro (descuadran las columnas).
- El tipo según lo que explicas: flujo (pasos y decisiones), estados (el evento en cada flecha),
  secuencia (quién llama a quién) o arquitectura (piezas y conexiones).
- Máximo ~12 cajas y 80 columnas; si no cabe, varios diagramas pequeños.
- Etiquetas que se entienden («Guarda el pedido», no `persistOrderAsync()`); los nombres técnicos
  van en Detalles.
- Solo lo que has visto en el código o te han dicho; lo supuesto, con `(?)`.

## Forma esperada

**En pocas palabras:** la web revisa los datos del formulario antes de guardarlos; si están mal,
ahora avisa en vez de perder el contacto.

**Detalles**
- `src/form.ts:30` — validación de email y teléfono antes de guardar.
- Riesgo: los formularios viejos sin teléfono fallan; falta decidir si es obligatorio.

```text
Visitante ──rellena──→ ┌────────────┐ ──datos mal──→ ┌───────────────┐
                       │ Web valida │                │ Avisa [NUEVO] │
                       └─────┬──────┘                └───────────────┘
                             │ datos bien
                             ↓
                       ┌────────────┐
                       │ Guarda lead│
                       └────────────┘
```
