---
paths:
  - "**/providers/**"
  - "**/adapters/**"
  - "**/llm/**"
  - "**/*provider*.py"
  - "**/*adapter*.py"
  - "**/mocks/**"
  - ".claude/patterns/stack/mocks-externos.md"
  - ".claude/patterns/stack/agente-modelo-y-coste.md"
---
# Proveedores externos — qué hace el producto cuando falta la clave o cae el proveedor

> **Cuándo aplicar:** al escribir o correr código que habla con un proveedor externo que no
> controlamos —un LLM, voz en tiempo real, transcripción, síntesis, un juez LLM, un CRM— y al definir
> un agente o un test que dependa de uno. Dice **por dónde pasa la llamada**, qué rastro deja y **qué
> responde cada contexto** cuando el proveedor no está: degradar, bloquear o rechazar.
>
> **NO aplicar:** a los servidores MCP de la sesión de Claude Code (`security.md` §MCP) · a elegir
> proveedor o modelo, que es una decisión con spike (`patterns/stack/agente-modelo-y-coste.md`) · a
> cómo se construye el simulador y su pantalla (`patterns/stack/mocks-externos.md`; su §9 es el caso
> del LLM).
>
> **Relacionado:** `llm-in-product.md` (qué se le manda y qué decide el modelo) · `security.md`
> (dónde viven las claves) · `verification.md` (anti-mock: una medida sobre simulador no es una medida).
>
> Cosechada de cold_calling_coach (`rules/external-provider-dependency.md`, 25-08-2026) y del
> registro con simulador por defecto de risk-couple (`apps/insights/adapters/registry.py`).

## 1. Toda llamada pasa por una interfaz, y deja rastro

Ningún módulo llama al proveedor directamente: llama a la interfaz (`LLMProvider`, `STTProvider`,
`JudgeProvider`…) y el adaptador elige la implementación por configuración (`LLM_PROVIDER=mock|
openai|anthropic`). El adaptador escribe **una fila por llamada** (`provider_run`): hash de la
petición, modelo exacto, versión del prompt, latencia, tokens, coste, estado y el error **redactado**.
Sin esa fila no se pueden comparar dos proveedores, explicar una factura ni reproducir un análisis.

**El simulador es el valor por defecto** (`mock`): el producto arranca y se desarrolla sin clave y sin
gasto. El real se enciende por entorno. Código del registro: `mocks-externos.md` §9.

## 2. Qué responde cada contexto cuando falta la clave o cae el proveedor

| Contexto | Sin clave o con el proveedor caído | Por qué |
|---|---|---|
| **Tests y desarrollo** | **Degrada** al simulador o a las fixtures grabadas, **y lo anuncia** en voz alta | Trabajar sin red ni gasto; el aviso impide creer que se midió contra el real |
| **Golden set, gate de publicación, comparación A/B de modelos** | **BLOQUEA** | Un número sobre fixtures no mide nada; publicarlo es fabricar la medida |
| **Un usuario real esperando una respuesta que el producto puede dar peor sin el modelo** (un resumen, una redacción de números ya calculados) | **Degrada** al simulador **sin pantalla de error**, y registra el motivo con nivel `warning` y una métrica | La caída es problema nuestro, no del usuario; caer al simulador en silencio y sin rastro es como un proveedor pasa tres semanas caído sin que nadie se entere |
| **Un usuario real esperando algo que sin el proveedor no existe** (una sesión de voz, el turno de un bot) | **RECHAZA** con un error explícito y una salida (reintentar, pasar a una persona) | Aquí no hay fixture que valga: hay una persona al otro lado |

La fila 2 es la que más se rompe: **una latencia o un acierto medidos contra una grabación no miden
nada.**

```
🔌 SIN OPENAI_API_KEY: corriendo contra el simulador (mocks/llm).
   Resultado NO válido para golden set, comparación de modelos ni producción.
```

## 3. La caída al simulador se cuenta

Un fallback que funciona bien también **esconde**: si el real da 400 en cada llamada (un parámetro que
el modelo nuevo rechaza, `agente-modelo-y-coste.md` §Roturas), el usuario ve el texto del simulador y
nadie se entera. Por eso:

- Cada caída registra **el motivo** (`timeout`, `http_400`, `schema_invalida`, `sin_clave`) en el
  `provider_run`.
- **Una métrica con alerta**: porcentaje de respuestas servidas por el simulador en producción. Por
  encima de un umbral bajo (p. ej. 5 % en una hora), aviso.
- El test de humo contra la API real (`agente-modelo-y-coste.md` §Spike) va **antes** de dar por bueno
  un cambio de modelo: el fallback no es una prueba de que el real funciona.

## 4. Cómo lo declara un agente del harness

En los dos sitios, porque cada uno sirve para algo:

- **Frontmatter**, para el inventario (el harness ignora las claves que no conoce):
  ```yaml
  requires_provider: [LLMJudgeProvider]
  provider_env: [ANTHROPIC_API_KEY]
  provider_degrade: fixture-replay
  ```
- **Cuerpo**, sección `## Dependencia de proveedor externo`: qué interfaz necesita y qué hace sin ella
  (según la tabla de §2).

## 5. Dónde viven las claves

En `.env`, con `.env.example` declarándolas vacías. Nunca en el repo, en un log, en un prompt, en el
bundle del frontend ni en `.mcp.json` (que conecta la sesión de Claude Code, no la aplicación). Si el
navegador necesita hablar con el proveedor (voz), recibe una **credencial efímera** acotada a modelo,
herramientas y duración; la clave maestra no sale del servidor. Una clave dedicada y con tope de gasto
para pruebas, nunca la de producción de otro proyecto (lección del spike de modelos, U.03-5).

## Anti-patterns

- ❌ Publicar una métrica de calidad o latencia medida contra el simulador o las fixtures.
- ❌ Caer al simulador en silencio, sin motivo registrado ni métrica → el proveedor real puede llevar
  semanas roto.
- ❌ Llamar al proveedor sin pasar por el adaptador → sin `provider_run` y sin poder cambiarlo.
- ❌ El proveedor real como valor por defecto → cada arranque de desarrollo gasta y necesita clave.
- ❌ Reutilizar la clave de otro entorno «para probar rápido».
- ❌ Dar por buena una comparación A/B de proveedores sin los `provider_run` de las dos ramas.

---

_Rule version: 1.0 · 2026-10-31 · sub-ola 3.26 de la revisión integral (CB-86). Generalizada de
cold_calling_coach `rules/external-provider-dependency.md` v1.0 (25-08-2026), con la fila de §2 y
§3 que aporta el registro de risk-couple._
