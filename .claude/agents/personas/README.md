# Personas — Multipersona Naive Testing

> Patrón para gestionar **varias personas no-técnicas** que prueban la app de forma recurrente, acumulando memoria y trend de score entre rounds.

> ## ⚠️ Estado: la multipersona es COSMÉTICA hasta que se demuestre lo contrario (AUD-16)
>
> **Ninguna persona ha corrido nunca.** Esta carpeta contiene solo `_example/` con
> `{"rounds": []}`. El único artefacto multipersona que existe en el repo
> (`_archive/2026-10-19/planes-cerrados/2026-06-21-visual-plans/feedback/lidia/maria-peluqueria/iter-1/`) está etiquetado
> **por su propio `RESULT.md`** como *«ejemplo de formato»*, y encima en un plan **sin UI**. Es
> formato, no medición.
>
> Y hay una razón estructural para sospechar que seguirá siendo cosmética: **todas las personas
> comparten el mismo modelo base, la misma rúbrica de 8 dimensiones y los mismos tests L-A…L-H.**
> La persona entra **solo por la prosa**; el score no puede divergir mucho por construcción.
>
> Hoy la lista de personas **no cuenta como cobertura**. Antes de añadir la segunda, se paga la
> comprobación de abajo — cuesta 3 pasadas.

## La comprobación, y su regla de poda escrita ANTES de mirar (AUD-16)

Protocolo completo: `.claude/agents/lidia-naive-tester/measurement-protocol.md` §6.

1. **La persona nueva debe diferir en el TRABAJO que viene a hacer** (jobs-to-be-done), no en la
   biografía. *Una peluquera y un coach que buscan lo mismo son el mismo agente con disfraz
   distinto.* La variable real de la multipersona es **el flujo que se le pide completar**.
2. **3 pasadas** sobre el mismo build congelado que se usó para medir la variabilidad de la
   persona existente (σ intra-persona).
3. Se calcula: **Jaccard** entre los conjuntos de hallazgos de las dos personas, y la **distancia
   entre sus medias** contra la σ intra-persona ya medida.
4. **Regla de decisión, pre-registrada** (si se escribe después, siempre aparece una lectura que
   justifica mantenerlo todo):

   > Si la diferencia entre personas **< σ intra-persona** **y** el Jaccard de hallazgos **> 0.7**
   > → **es un disfraz**: se poda y se queda una sola persona.

5. **Predicción falsable:** los *scores* apenas divergirán; si hay señal, aparecerá en **qué**
   encuentra cada una, no en la nota. Por eso decide el Jaccard de hallazgos y no la media.

**Higiene de identidad (fallo real que hay que no repetir):** la ficha de
`lidia-naive-tester.md` sigue con los huecos sin rellenar (`[Nombre Persona]`, `[edad]`) mientras
su memoria y sus trend corren como *«María, dueña de negocio»*. **La persona cambió entre la ficha
y la ejecución sin que quedara registro.** Si una persona corre, su identidad tiene que estar
escrita en el sitio del que se lee, y el `persona` del `trend-delta.json` tiene que coincidir.

## Estructura

```
.claude/agents/personas/
├── README.md                       ← este archivo
├── _example/                       ← skeleton de referencia (copiar para una persona nueva)
│   ├── memory.md
│   ├── trend.json
│   └── reports/
│       └── round-1.md
├── <persona-slug>/                 ← una persona real del proyecto
│   ├── memory.md                   ← qué probó antes, qué funciona, qué no, "known bugs"
│   ├── trend.json                  ← scores por ronda + delta cross-round
│   └── reports/
│       ├── round-1.md
│       ├── round-2.md
│       └── ...
└── <otra-persona>/
    └── ...
```

## Cómo crear una persona nueva

1. Copia `_example/` a un slug nuevo (ej. `peluquera-lidia`, `coach-ramon`, `cpo-ana`):
   ```bash
   cp -r .claude/agents/personas/_example .claude/agents/personas/<slug>
   ```
2. Edita `<slug>/memory.md` con: nombre, edad, oficio, contexto de uso, vocabulario propio, lo que le importa, lo que le da miedo.
3. Vacía `<slug>/trend.json` a `{ "rounds": [] }`.
4. Borra `<slug>/reports/round-1.md` (es un placeholder).

## Cómo lanzar un round con una persona existente

Invoca `lidia-naive-tester` en modo persona al vuelo (`skills/naive-user-playthrough/references/dynamic-persona.md`; hasta la 3.01 era el runner `naive-user-tester`) con:

- **Persona**: contenido de `personas/<slug>/memory.md` (sección "Quién soy")
- **Flow**: lista de pasos a simular
- **URL**: del proyecto
- **Focus**: `functional` | `aesthetic` | `mix`
- **Versión**: leer último round en `trend.json` y sumar 1

El runner DEBE:

1. **Antes**: leer `personas/<slug>/memory.md` + último `reports/round-N.md` para:
   - No repetir findings ya reportados (están en "Known bugs" del memory)
   - Marcar **regresiones** como P0 automático (algo que se "arregló" y vuelve a fallar)
   - Comparar score qualitativo vs ronda anterior
2. **Durante**: ejecutar el playthrough en character.
3. **Después**:
   - Escribir `personas/<slug>/reports/round-<N+1>.md` con el REPORT completo
   - Actualizar `personas/<slug>/memory.md` (añadir findings nuevos a "Known bugs" o "Wins")
   - Añadir entrada en `personas/<slug>/trend.json`

## Cuándo usar multipersona vs persona única

- **Multipersona** (este patrón): el proyecto tiene varios arquetipos de usuario relevantes (ej. SaaS B2B con CPO + dev + sales) y quieres testear cada uno por separado con su sesgo.
- **Persona única** (`agents/lidia-naive-tester.md` + `agents/lidia-naive-tester/memory.md`): el proyecto tiene UN arquetipo dominante (ej. peluquera para una app de gestión de salones). Mantén solo esa.

Ambos pueden coexistir: `lidia-naive-tester` (persona estrella, definición rica) + `personas/cpo-ana/` (arquetipos adicionales que aparecen ocasionalmente).

## Anti-patterns

- ❌ Personas inventadas sin contexto real del producto — pregunta al Usuario qué arquetipos REALES tiene su pipeline
- ❌ Memoria sin actualizar entre rounds (pierdes el valor cross-round)
- ❌ Mezclar reports de personas diferentes en la misma carpeta
- ❌ Reusar el mismo `<slug>` para personas distintas (rompe el trend)
- ❌ **Contar N personas listadas como N arquetipos cubiertos** cuando ninguna ha corrido
- ❌ Añadir una persona que difiere en biografía pero busca **lo mismo** → es un disfraz
- ❌ Decidir si la multipersona aporta **después** de ver los resultados (la regla va antes)
- ❌ Comparar personas por su **nota**: si hay señal está en qué encuentra cada una, no en la media
- ❌ Que el `persona` del `trend-delta.json` no coincida con la identidad escrita en la ficha
