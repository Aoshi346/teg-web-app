---
name: prompt-contracts
description: >-
  Usar al empezar una feature de más de 3 ficheros o de alcance incierto: contrato antes de codear
  (GOAL / CONSTRAINTS / FORMAT / FAILURE CONDITIONS). Incluye la rúbrica de prompt, el checklist
  anti-alucinación y la escalera 'explica antes de codear'. NO usar para: bugfixes de 1-3 ficheros,
  exploración o spikes, ni con el enfoque aún sin decidir (primero elicitar: rules/plan-gates.md
  §1b).
user-invocable: false
metadata:
  source: info.md research
  version: 1.1.0
  author: tech-lead-template
  category: workflow
  updated: 2026-08-07
  tech-stack: any
---

# Prompt Contracts — Scope + Constraints + Failure conditions

## Principio
"Vibe coding" genera incertidumbre. Prompt contracts definen scope EXPLÍCITO antes de escribir una sola línea, convirtiendo gambling en shipping.

## Estructura del contrato (5 secciones)

```
GOAL: <qué construir — una frase clara>
CONSTRAINTS: <tech/arch constraints>
FORMAT: <dónde va cada pieza>
FAILURE CONDITIONS: <qué NO debe pasar>
```

## Ejemplo completo

```
> Build the /dashboard page.

GOAL: Display user's active projects with real-time updates.
First meaningful paint under 1 second. User can create, archive,
and rename projects inline.

CONSTRAINTS: Convex useQuery for data, no polling, no SWR.
Clerk useUser() for auth check. Redirect to /sign-in if
unauthenticated. Max 150 lines per component file.

FORMAT: Page component in app/dashboard/page.tsx (server component
wrapper), client component in components/dashboard/ProjectList.tsx,
Convex query in convex/projects.ts. Tailwind only.

FAILURE CONDITIONS:
- Uses useState for data that should be in Convex
- Any component exceeds 150 lines
- Fetches data client-side when it could be server-side
- Uses any UI library besides Tailwind utility classes
- Missing loading and error states
- Missing TypeScript types on any function parameter
```

## Por qué funciona
- **GOAL pinnea el WHY** — Claude entiende intención
- **CONSTRAINTS evita drift** — stack decisions no se re-debaten
- **FORMAT evita file scatter** — Claude sabe dónde va cada cosa
- **FAILURE CONDITIONS da red line** — Claude puede auto-verificar

## Cuándo aplicar
- Features nuevas que afectan >3 archivos
- Componentes que van a production
- Tasks donde el stack/approach importa
- Cuando quieres output "right" en primer intento

Qué trae además del contrato: la rúbrica de calidad de prompt (7 elementos ordenados por peso), el checklist anti-alucinación de 8 puntos y la escalera de 5 pasos «explica antes de codear». Evita el scope creep, la implementación desalineada y las regresiones de 'vibe coding'.

## Cuándo NO aplicar
- Bug fixes pequeños (<1 archivo)
- Exploración/research
- Prototipos throw-away
- Tasks donde no conoces aún las constraints

> ⚠️ **Excepción documentada — baja confianza en el enfoque** (`rules/plan-gates.md` §1b, DEC-3).
> El contrato es el default en cuanto la tarea toca >3 archivos, **pero el andamiaje es una
> restricción y las restricciones se pagan con confianza**. Si no sabes aún cuál es el enfoque
> correcto, un contrato escrito sobre el enfoque equivocado convierte el error en requisito. En ese
> caso el contrato **no se salta: se retrasa** — primero elicitas (Gate 0b) o exploras 2-3 enfoques,
> y lo escribes después, cuando ya sabes qué estás fijando. Las dos rules están de acuerdo en esto;
> si algún día divergen, manda `plan-gates.md` §1b.

## Workflow
1. Escribe el contrato ANTES de ejecutar
2. Revisa: ¿está completo? ¿failure conditions son verificables?
3. Ejecuta con el contrato como prompt
4. Valida output contra FAILURE CONDITIONS
5. Si falla → iterar sobre el contrato, no sobre el output

---

# Rúbrica de calidad de prompt — 7 elementos EN ORDEN de peso (PRM-2)

El contrato dice **qué secciones escribir**. Esta rúbrica dice **cuál pesa más**: úsala cuando el
prompt tiene que ser corto (qué sacrificar primero) y cuando el resultado sale mal (qué falta y en
qué orden probar). Están ordenados de mayor a menor impacto.

| # | Elemento | Cómo se degrada el resultado si falta | Dónde vive en el contrato |
|---|---|---|---|
| 1 | **Instrucción** | Sin una acción explícita el modelo adivina la tarea. Es el único elemento sin el cual no hay prompt. Nada de saludos ni relleno conversacional | `GOAL` |
| 2 | **Estructura lógica** | Todo mezclado en un párrafo → el modelo no distingue requisito de fondo y pondera mal. Orden que funciona: contexto → instrucción → constraints → salida esperada. Markdown y listas, no prosa corrida | Las 4 secciones |
| 3 | **Claridad y precisión** | Lo ambiguo se resuelve por deriva semántica, y no en tu dirección ("una descripción de trabajo para un dev que use IA" → salió un ingeniero de ML) | `GOAL` + `FAILURE` verificables |
| 4 | **Contexto adecuado** | Salida genérica y plausible en vez de código que encaja aquí. **Es el elemento que más mueve la aguja en asistentes de código**: versiones, ficheros concretos, fragmentos, los controllers que ya existen | `CONSTRAINTS` |
| 5 | **Formato de salida** | Recibes prosa cuando querías un fichero, o un fichero cuando querías un diff. Barato de pedir, caro de arreglar | `FORMAT` |
| 6 | **Tono, estilo y longitud** | Sale correcto pero inservible: demasiado largo, demasiado explicado, o con un registro que no es el del repo | `FORMAT` |
| 7 | **Rol** | **Casi nada.** Ver abajo | (opcional) |

## La calibración contraintuitiva: el ROL ha perdido peso

*"A día de hoy ya no es tan relevante, ya que las últimas versiones de los LLMs más conocidos son
MoEs (Mixtures of Experts) […] Además, el rol no es tan relevante en asistentes de código porque ya
están pre-entrenados como desarrolladores. No hay un gran cambio cuando especificas si debe ser
backend, frontend, QA, DevOps. **Es más importante dar el contexto adecuado** respecto a las
tecnologías usadas o añadir fragmentos de código."*

Traducción operativa: **el rendimiento viene del elemento 4, no del elemento 7.** Si un prompt sale
mal, añadir "actúa como un desarrollador senior" no lo arregla; añadir el fichero que importa, sí.

> **Matiz importante para nuestros agentes-persona.** Que el rol pese poco **no** significa quitar
> la personalidad a Lidia, Vera, Ignacio, Otto o Rita. Esos agentes valen por su **protocolo** (qué
> pasos siguen, qué puntúan, qué prohibiciones tienen), por su **memoria** (`agents/*/memory.md`) y
> por su **calibración** acumulada — no por el "actúa como". La persona sirve además para que el
> humano sepa a quién está llamando. Lo que **no** debes esperar es que el disfraz haga el trabajo
> que hace el contexto: un auditor sin su rúbrica y sin la URL a auditar no audita nada.

---

# Checklist anti-alucinación — 8 puntos (PRM-3)

Citable desde cualquier sitio; orientado a **generación de código**. No bloquea nada: es un
recordatorio corto que se lee antes de un prompt que va a producir código que te vas a creer.

1. **Prompt conciso y al grano.** Menos es más. Y el matiz que casi nadie aplica: **pedir 5 cosas
   por separado da mejor resultado que pedir las 5 juntas** — una petición por mensaje, revisas, y
   sigues. Pon ejemplos (few-shot) cuanto más raro sea el dominio.
2. **Dale ejemplos.** Un `INSERT` de muestra junto al DDL, un test que ya existe, una respuesta JSON
   real. Un ejemplo concreto vale más que tres frases describiéndolo.
3. **Dale el contexto adecuado.** El mismo prompt con *"considera que soy un ingeniero junior"* o
   *"soy DBA con 20 años"* produce salidas distintas. Fija el nivel y el entorno.
4. **Usa el modelo adecuado.** Y el effort adecuado (`rules/research-driven-planning.md`): `medium`
   por defecto, `high`/`xhigh` para quien verifica o audita.
5. **Acepta que hay límites.** Un LLM manipula texto con estadística: no "sabe" si tu endpoint
   existe. La alucinación no se elimina, se acota y se detecta.
6. **Valida lo que te dice.** Trátalo como un **compañero junior**: competente, rápido y a veces
   convencido de algo falso. Espíritu crítico por defecto — y para "¿está hecho?", doble evidencia
   🔎 código / 👁 en vivo (`rules/verdict-contract.md`).
7. **Parte la tarea, no el razonamiento.** Pide primero la lista de partes del cambio y luego una
   parte por mensaje: menos información a la vez → menos superficie para inventar. La profundidad
   del razonamiento la pone el effort (punto 4), no un «piensa paso a paso».
8. **Instrúyele a aclarar dudas ANTES de ejecutar.** *"Antes de empezar, enumérame lo que te falta
   saber y pregúntame."* Es el mismo mecanismo que el **Gate 0b de clarificación inversa**
   (`rules/plan-gates.md`) visto desde el otro lado: allí es obligación del agente en tareas
   grandes; aquí es una línea que añades a cualquier prompt.

> Los puntos 1b y 8 son los que más rendimiento dan y los que más se olvidan. El resto son higiene.

---

# Escalera "explica antes de codear" — 5 pasos con aprobación humana (PRM-4)

Plantilla para una tarea de backend normal (una sesión, no SpecKit). Cada paso **para y espera tu
OK**; el valor está en que los errores se cazan en el paso de explicación, que cuesta segundos, y no
en el de código, que cuesta una revisión entera.

```
1. [contexto + contrato de datos exacto]
   "Empieza proponiendo la funcionalidad desde el archivo que llama a la base de datos,
    usando @Candidate.ts. NO escribas código aún: primero explícame lo que harás."

2. "Procede escribiendo la funcionalidad, empezando desde @Candidate.ts."

3. "Ahora el endpoint [X]. Sugiéreme una implementación teniendo en cuenta CASOS LÍMITE
    y posibles problemas. No escribas código hasta que te lo indique."

4. "Correcto. Crea el código, empezando por la base de datos."

5. "Por favor, EJECUTA algunas requests a los diferentes endpoints para validar que esta
    funcionalidad cumple su objetivo, y enséñame el resultado."
```

Por qué cada paso:

| Paso | Qué compra |
|---|---|
| 1 · explica sin código | El desacuerdo aparece en un párrafo, no en 300 líneas |
| 2 · escribe | Con el enfoque ya acordado |
| 3 · propón con casos límite, sin código | Los edge cases se piensan **antes**, que es cuando son baratos |
| 4 · escribe | Ídem |
| **5 · requests reales** | **El cierre que faltaba**: el endpoint que existe en el código y devuelve 500 al primer intento |

**El paso 5 es obligatorio y vive además en `rules/verification.md` §Smoke testing** (comando `curl` completo,
qué mirar en la salida, dónde guardar la evidencia). Mínimo por endpoint: camino feliz + un payload
inválido + una llamada sin auth.

**Su límite, dicho claramente:** en tareas triviales estos cinco pasos sobran y frenan. Es para
trabajo de backend con contrato de datos, no para cambiar un mensaje de error.

---

## Anti-patterns

- GOAL vago ("improve the dashboard")
- FAILURE CONDITIONS subjetivos ("no feo", "código limpio")
- Skip FORMAT (Claude decide dónde, file scatter)
- Contract de 500 líneas (si no cabe en 1 pantalla, descompón el task)
- ❌ Escribir el contrato cuando **aún no sabes el enfoque** → fijas el error como requisito (§1b)
- ❌ Arreglar un prompt malo añadiendo rol ("actúa como senior") en vez de contexto (elemento 4)
- ❌ Pedir 5 cosas en un mensaje y quejarse de que salieron 3 mal
- ❌ Aceptar código generado sin validar nada porque "suena bien" (punto 6)
- ❌ Saltarse el paso 5 de la escalera: DONE sin haber llamado al endpoint ni una vez
- ❌ Aplicar la escalera de 5 pasos a un cambio trivial → ceremonia que frena

## Related

- `rules/plan-gates.md` — §1b eje confianza (cuándo retrasar el contrato) · Gate 0b clarificación inversa
- `rules/verification.md` §Smoke testing — el paso 5 de la escalera, con el comando y la evidencia
- `rules/research-driven-planning.md` — política de effort (punto 4 del checklist)
- `rules/verdict-contract.md` — doble evidencia para verificar "¿está hecho?" (punto 6)
- `skills/skill-authoring` — si el prompt se repite >3 veces, quizá deba ser skill (filtro de existencia)
