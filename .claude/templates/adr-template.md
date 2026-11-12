<!--
Plantilla de ADR (Architecture Decision Record). Uso:
  cp .claude/templates/adr-template.md .docs/adr/000N-<slug>.md
Reglas (rules/adr.md): una página · ≥2 alternativas descartadas con su razón ·
consecuencias negativas obligatorias · no se edita un ADR viejo, se reemplaza.
Borra estos comentarios y los [corchetes] al rellenar.
-->

# ADR-000N — [Título en una línea: la decisión, no el problema]

| Campo | Valor |
|---|---|
| **Estado** | Propuesto \| Aceptado \| Rechazado \| Reemplazado por ADR-XXXX \| Obsoleto |
| **Fecha** | YYYY-MM-DD |
| **Autor(es)** | [nombre / agente] |
| **Ámbito** | [módulo, servicio o "todo el sistema"] |
| **Relacionado** | [ADR-XXXX, plan `.docs/plans/<fecha>-<slug>/`, sesión SpecKit, issue] |

## Contexto

[Qué problema hay que resolver AHORA y por qué aparece ahora. Restricciones reales del momento:
plazo, equipo, stack existente, volumen de datos, presupuesto, compliance. Escríbelo para alguien
que no estuvo en la conversación. 5-10 líneas. Sin adjetivos: hechos y cifras si las hay.]

## Decisión

**[Lo que se hace, en una frase imperativa. Ej.: "Usamos PostgreSQL con esquema por tenant."]**

[2-5 líneas de detalle: cómo se materializa, qué queda dentro y qué queda fuera del alcance de esta
decisión.]

## Alternativas descartadas

<!-- Mínimo 2. Una alternativa sin razón concreta de descarte no cuenta. -->

| Alternativa | Por qué se descarta |
|---|---|
| [Opción B] | [Razón concreta y verificable, no "no nos gustó"] |
| [Opción C] | [Razón concreta] |
| [No hacer nada / seguir como estamos] | [Qué pasaría si no decidimos] |

## Consecuencias

**Ganamos**
- [Beneficio concreto y observable]
- [Beneficio concreto y observable]

**Aceptamos perder / asumimos**  <!-- obligatorio: si está vacío, no has terminado de pensarla -->
- [Coste, límite o deuda que esta decisión introduce]
- [Qué se vuelve más difícil a partir de ahora]

**Impacto operativo**
- [Migraciones, despliegue, monitorización, coste recurrente, formación del equipo]

## Cómo se revisa

- **Qué la invalidaría:** [la condición concreta que, si ocurre, obliga a reabrir esta decisión —
  ej. "si superamos 500 tenants" o "si el proveedor deja de ofrecer plan gestionado"]
- **Cuándo mirarla otra vez:** [fecha o hito, o "cuando se cumpla la condición de arriba"]

## Referencias

- [Docs, benchmarks, spikes, PRs, hilos que sostienen el contexto]
- [Plantillas por tipo de decisión: adr.github.io]
