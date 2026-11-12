# Rúbrica de priorización — los 7 factores (PRO-1)

> **Cuándo aplicar:** siempre que Pol ordene un backlog, un lote de sugerencias o los items de un
> plan. Sustituye a "valor × esfuerzo" (2 ejes) como criterio de razonamiento.
>
> **NO aplicar:** como 7 columnas nuevas en el dashboard. El dashboard sigue mostrando
> severidad × esfuerzo; los 7 factores son **cómo se razona el orden** y **qué se escribe en la
> justificación**. Tampoco para ordenar 3 items — ahí sobra la rúbrica.
>
> **Relacionado:** `.claude/agents/pol-product-advisor.md` (§ marco de análisis), `rules/report-kit.md`
> (el dashboard y su `report.json`), `rules/plan-gates.md`.

---

## Por qué 7 y no 2

Con severidad × esfuerzo se cuela un caso concreto y caro: **una tarea de severidad media que
desbloquea otras cinco** parece menos urgente de lo que es, porque el eje "dependencias" no existe.
Lo mismo pasa con lo que hay que hacer ahora por una fecha externa (urgencia ≠ valor) y con lo que
depende de una tecnología que aún no está madura.

**Límite honesto:** sin datos reales de usuario, "feedback de usuario" y "valor de negocio" siguen
siendo estimaciones. La rúbrica **ordena la conversación, no la sustituye** — su valor es que dos
personas que ordenen el mismo backlog lleguen a un orden parecido y puedan explicar por qué.

## Los 7 factores

| # | Factor | La pregunta que responde | Escala | Señales concretas |
|---|---|---|---|---|
| 1 | **Valor de negocio** | ¿Qué gana el negocio si esto existe? | Alto / Medio / Bajo | Ingreso, coste evitado, riesgo eliminado, retención. Atado a **qué persona** lo pide |
| 2 | **Urgencia** | ¿Por qué ahora y no en tres meses? | Alta / Media / Baja | Fecha externa, compromiso adquirido, ventana de mercado, algo que **empeora** con el tiempo. Sin fecha ni consecuencia, la urgencia es Baja |
| 3 | **Dependencias** | ¿Qué desbloquea, y qué lo bloquea a él? | nº que desbloquea / nº que lo bloquean | El factor que faltaba: un item de valor medio que desbloquea 5 sube por encima de uno de valor alto aislado |
| 4 | **Coste de implementación** | ¿Cuánto trabajo real es? | S / M / L | Estimación honesta, no un deseo. Si no se puede estimar, primero un **spike** (item propio del backlog) |
| 5 | **Riesgos y obstáculos** | ¿Qué puede salir mal o pararlo? | Alto / Medio / Bajo | Migración de datos, dependencia de un tercero, permiso pendiente, zona sin tests, decisión de negocio sin tomar |
| 6 | **Feedback de usuario** | ¿Quién lo ha pedido de verdad? | Evidencia / Anécdota / Suposición | Cita textual, ticket, sesión observada. **"Suposición" no invalida el item, pero se escribe como tal** |
| 7 | **Madurez tecnológica** | ¿La pieza en la que se apoya está lista? | Madura / En movimiento / Experimental | API en beta, librería sin releases, feature del harness marcada como experimental (p. ej. agent-teams) |

## Cómo se combina (sin inventar una fórmula)

No hay puntuación ponderada: un número compuesto esconde el razonamiento, que es justo lo que se
quería ganar. El orden se construye con **reglas de desempate explícitas**:

1. **Quick wins primero**: valor Alto + coste S, sin riesgo Alto.
2. **Desbloqueadores antes que bloqueados**: si A desbloquea a B, A va antes aunque B valga más.
   Un ciclo de dependencias es un error del backlog, no un empate.
3. **Urgencia rompe empates de valor**, nunca los crea: urgente y sin valor sigue sin entrar.
4. **Riesgo Alto + madurez Experimental** ⇒ el item se parte: primero el **spike** que reduce la
   incertidumbre, después la implementación.
5. **Feedback = Suposición** baja un escalón frente a otro item equivalente con evidencia.
6. **Bloqueado por compliance o por decisión del Usuario** no es prioridad baja: es **bloqueado**
   (línea roja, no opción a valorar).

## Cómo se escribe en el informe

Una línea por item, con **los factores que movieron el orden** (no los siete siempre — solo los que
decidieron):

```
[A3] Exportar el informe a PDF — valor Medio · coste S · desbloquea 0 · feedback: EVIDENCIA
     (3 clientes lo pidieron por email, ver citas) · riesgo Bajo · madurez Madura
     → Quick win: entra antes que A1 pese a valer menos, porque A1 es coste L y depende de G2.
```

Y en la tabla de sugerencias vivas de `memory.md`, las columnas siguen siendo las de siempre
(`Valor`, `Esfuerzo`, `Ancla`); los otros cinco factores viven en la **frase de por qué**.

## Paso previo obligatorio: enriquecer el backlog antes de ordenarlo

Ordenar bien una lista incompleta sigue dando un plan incompleto. Antes de priorizar, Pol ejecuta el
prompt de enriquecimiento sobre lo que ya existe:

> **"Analiza las funcionalidades existentes e identifica los 5 problemas más comunes que los usuarios
> podrían enfrentar, y sugiere mejoras."**

Reglas de este paso:

- Se aplica **por persona usuaria declarada** (en este template: el programador dueño, los agentes/TL
  que lo ejecutan, y quien lee un informe sin ser técnico). Cinco problemas del usuario equivocado no
  sirven de nada.
- Lo que salga entra al backlog **marcado como `feedback: Suposición`** hasta que alguien lo confirme.
  Es material para preguntar, no para dar por hecho.
- Si el problema ya está en la lista, **no se duplica**: se sube su factor 6 con la nueva evidencia.

---

## Anti-patterns

- ❌ Convertir los 7 factores en 7 columnas de la UI → nadie las rellena y vuelve el orden a ojo.
- ❌ Inventar una fórmula ponderada (`0.3·valor + 0.2·urgencia…`): el número tapa el razonamiento.
- ❌ Marcar todo como urgente. Sin fecha ni consecuencia por esperar, la urgencia es Baja.
- ❌ Presentar una suposición propia como "feedback de usuario" (factor 6 exige decir cuál de los tres).
- ❌ Priorizar sin el paso de enriquecimiento: ordenar impecablemente una lista a la que le faltan
  cosas.
- ❌ Colar un item bloqueado por compliance como "prioridad baja" en vez de como bloqueado.

---

_Rúbrica v1.0 · PRO-1 (adopción AI4DEVS, 2026-08-08). Los 7 factores vienen del material de origen
(AI4DEVS M5, "Historias de usuario"); las reglas de desempate y el tratamiento de `Suposición` son
adaptación nuestra._
