---
reviewed: <AAAA-MM-DD>
reviewed_by: <la persona que lo revisó, no el agente que lo escribió>
asvs_nivel: <L1 | L2 | L3, según el tipo de proyecto>
asvs_extra: <ids de un nivel superior que se suman, o «ninguno»>
datos_personales: <sí | no>
agentes_llm: <sí | no>
---
# Modelo de amenazas · <qué se construye, en una línea>

> Una página. Lo produce la skill `modelado-amenazas` y lo comprueba `scripts/gate_amenazas.py`
> (Gate F de `rules/plan-gates.md`). Solo se modelan las **fronteras de confianza** que este trabajo
> crea o cambia, no el sistema entero. Nivel y subconjunto ASVS:
> `.claude/skills/modelado-amenazas/references/asvs-por-tipo.md`.

## 1. Qué construimos: las fronteras

| Id | Frontera (de → a) | Qué cruza | Quién está al otro lado |
|---|---|---|---|
| F1 | <de dónde → a dónde> | <qué datos o qué orden> | <quién, y cuánto nos fiamos> |

## 2. Qué puede ir mal y qué hacemos (STRIDE por frontera)

S suplantación → autenticación · T manipulación → integridad · R repudio → registro · I divulgación →
confidencialidad · D denegación de servicio → disponibilidad · E elevación de privilegios → autorización
(OWASP Threat Modeling Cheat Sheet). Respuesta: mitigar · eliminar · transferir · aceptar. En ASVS va
el requisito `v5.0.0-x.y.z`; si la amenaza es del propio modelo (inyección, agencia excesiva), que ASVS
no cubre, el riesgo del OWASP Top 10 for LLM 2025 (`LLM01`-`LLM10`) o del Agentic (`ASI01`-`ASI10`).
Un payload o un trozo de código en una celda va entre comillas de código (`<script>`): suelto, el gate
lo lee como un hueco sin rellenar.

| Frontera | STRIDE | Amenaza | Respuesta | Defensa decidida | ASVS | Cómo se prueba |
|---|---|---|---|---|---|---|
| F1 | <letra> | <qué puede pasar, en concreto> | <respuesta> | <la defensa, o por qué se acepta> | <v5.0.0-x.y.z> | <test, sabotaje o caso de Sofía> |

## 3. Privacidad (LINDDUN GO) — solo si `datos_personales: sí`

Cartas de `references/linddun-go.md` que **sí** aplican en alguna frontera. Una carta que no aplica no se
escribe. Con categorías especiales (art. 9 RGPD), la base legal lleva la letra del art. 9.2 que se invoca.

| Carta | Frontera | Amenaza concreta | Defensa decidida | Base legal o ASVS |
|---|---|---|---|---|
| <código y nombre> | <F-id> | <qué pasaría aquí> | <qué se hace> | <artículo o v5.0.0-x.y.z> |

## 4. Agentes (Rule of Two) — solo si `agentes_llm: sí`

Por agente y sesión: [A] procesa entrada no confiable · [B] accede a datos privados o sistemas sensibles ·
[C] cambia estado o comunica hacia fuera. Con las tres a la vez, no opera en autónomo (Meta, 31-10-2025):
`interrupt`, una sesión nueva o la confirmación de una persona («el gestor aprueba», «confirmación del
cliente»).

| Agente (sesión) | [A] | [B] | [C] | Control si son las tres |
|---|---|---|---|---|
| <nombre> | <sí/no: por qué> | <sí/no: por qué> | <sí/no: por qué> | <interrupt, confirmación humana o sesión nueva> |

## 5. Lo que se acepta, por escrito

<riesgo aceptado, quién lo acepta y hasta cuándo — o «nada»>

## 6. ¿Lo hicimos bien?

<quién lo revisó, qué gate o auditor lo comprueba y cuándo se vuelve a mirar>
