# `.claude/patterns/` — el canon de patrones del proyecto (sistema de Rita)

> Estado versionado en git, NUNCA por usuario (Google: la config por usuario destruye la
> consistencia que el guardián defiende). Diseño completo:
> `_archive/2026-10-19/planes-cerrados/2026-08-05-rita-pattern-keeper/` (plan v2 + RESEARCH.md con la evidencia; archivado el 19-10).

| Fichero | Qué es |
|---|---|
| `catalog.yaml` | Las filas: id, enunciado, **mecanismo** (escalón), ámbito, **dominancia medida**, estado, baseline |
| `<id>.md` | Doc canónico del patrón: qué, por qué, ≥2 precedentes `file:line`, contraejemplo |
| `baseline/<id>.json` | **Deuda aceptada** (ratchet): violaciones preexistentes — prohibido comentarlas en PRs que no las tocan; solo un humano la amplía |
| `telemetry.jsonl` | `{patron_id, sha, desenlace}` — address-rate por patrón; el que se ignora se retira SOLO |
| `ownership.yaml` | **Contrato de propiedad por directorio** (AGT-8): `owns` · `can_modify` · `forbids` · `needs_approval` · `depends_on` · `rules` citables, con **herencia vertical** |
| `ownership_check.py` | La capa determinista del contrato: comprueba ficheros cambiados, `--lint` la herencia, `--explain <ruta>` el contrato efectivo |

## Medido vs declarado — los TRES cuerpos del canon

| | `catalog.yaml` (patrones) | `ownership.yaml` (contrato) | `diseno/catalogo-diseno.yaml` (gusto) |
|---|---|---|---|
| De dónde sale | Se **mide** en el repo (dominancia) | Se **declara** por escrito, con `source:` a la rule que lo justifica | Se mide en un corpus **AJENO a este repo** (`resources/referencias-diseno/`) |
| Qué responde | "¿así se escribe aquí?" | "¿quién manda en esta carpeta y qué no puede tocar?" | "¿cómo se ve bien esto?" |
| Cómo lo usa Rita | Precedentes `file:line` (≥2 o silencio) | Lo **cita literalmente** como regla dura | **No lo usa. Rita no lo lee** |
| ¿Bloquea? | Sí, los `activo` | Sí, los `forbids` | **Nunca.** Lo que bloquea es `scripts/gate_diseno.py` y el humano |
| Si envejece | La dominancia se re-mide y el patrón se degrada solo | **Nadie lo re-mide**: si no se mantiene, manda el catálogo medido | `scripts/verificar_precedentes.py` falla si una cita deja de resolver; `corpus_lint.py` vigila la caducidad |

> **Por qué el tercero puede existir sin romper la regla de dominancia (§1).** Porque **no la invoca**:
> diez diseños de un solo equipo NO son dominancia, y el fichero lo dice en su cabecera. Es el mismo
> trato que **GAP-1** le da a las reglas `ag-*` —medidas en dos repos, los dos nuestros, y por eso
> congeladas en `sombra`—, un escalón más abajo: aquí ni siquiera se aspira a promocionar. El gusto
> entra como evidencia citable, no como ley. Detalle y límites: `diseno/README.md`.

Ejecutar el contrato:

```bash
python3 .claude/patterns/ownership_check.py                      # ficheros cambiados (exit 1 si forbids)
python3 .claude/patterns/ownership_check.py --from .claude/templates/report_kit/   # prohibiciones cross-scope
python3 .claude/patterns/ownership_check.py --explain .claude/agents/rita-pattern-keeper.md
python3 .claude/patterns/ownership_check.py --lint                # el hijo no amplía lo que el padre prohíbe
```

## Cómo se usa

- **Tier 0 (0 tokens)**: `.claude/hooks/pattern-check.sh` — greps del catálogo sobre los ficheros
  CAMBIADOS. Como pre-push: `ln -s ../../.claude/hooks/pattern-check.sh .git/hooks/pre-push`.
  Bloquea SOLO violaciones nuevas de patrones `activo`; los `debil` avisan; el baseline nunca falla.
  **Pendiente de cablear** (`.claude/hooks/` exige aprobación, `governance.md` §2): añadir al final
  de `pattern-check.sh` la línea `python3 .claude/patterns/ownership_check.py || FAIL=1`, para que el
  contrato declarado bloquee en el mismo sitio que los patrones medidos. Hasta entonces se corre a mano.
- **Tier 1 (Rita, barato)**: skill `pattern-gate` — Rita juzga los candidatos que el hook le da
  (nunca busca ella). Requiere ≥2 precedentes + diff aplicable. NUNCA bloquea (no es reproducible).
- **Tier 2 (caro)**: inventario profundo → actualizar catálogo — solo al arrancar proyecto o refactor.

## Reglas duras (del research — RESEARCH.md §2-4)

1. **Dominancia medida antes de fijar**: la frecuencia bruta NO es el criterio; ≥85% = activo,
   60-85% = débil, <60% = no hay patrón (decisión del owner, clasificada por reversibilidad).
   > **La excepción viva, declarada (GAP-1):** las 10 reglas `ag-*` (agentes IA) están medidas en
   > **dos repos y los dos son nuestros** — mismo equipo, mismo stack. Eso no es dominancia; puede
   > ser nuestra manera de escribir. Por eso siguen todas en `sombra`, su comprobador imprime esa
   > procedencia en cada ejecución, y no suben de escalón hasta medirse en un tercer repo ajeno.
   > Números y criterio de promoción: `stack/REGLAS.md` §Mitad AGENTES.
2. **Regla de inversión**: si una regla nueva marcaría >20-30 sitios existentes, la mala es la regla.
3. **FPR <5-10%** sobre ficheros conformes antes de activar cualquier regla.
4. **Excepciones**: `<!-- pattern-exempt: <id> — razón -->` (o comentario equivalente del lenguaje) —
   auditables, permanentes, Rita las respeta siempre.
