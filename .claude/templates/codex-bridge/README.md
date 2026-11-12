# `codex-bridge/` — las reglas críticas, para Codex

La fuente de lo que `scripts/gen_codex_bridge.py` escribe en un proyecto que usa Codex además de
Claude Code (AN-21, 3.22). Codex lee `AGENTS.md` y `.agents/skills/`, y no pasa por los hooks ni los
permisos de Claude Code: sin esto, lo único que le frena es lo que alguien copió a mano, y esas copias
ya divergían de las rules (elvion tenía seis).

| Fichero | Qué es |
|---|---|
| `agents-block.md` | El bloque `CODEX-CRITICAS` que se pone en el `AGENTS.md` del proyecto. Lo de fuera del bloque es del proyecto y no se toca |
| `skills/<nombre>/SKILL.md` | Una skill por regla crítica: `ram-before-pytest`, `no-push-merge-deploy`, `local-only-network` |
| `manifest.json` | De qué sección de qué rule sale cada pieza, con el sha de esa sección cuando se escribió; y `replaces`, los nombres con los que un proyecto ya la tiene a mano |

```bash
python3 .claude/scripts/gen_codex_bridge.py --dest <proyecto>          # escribe (o --dry-run)
python3 .claude/scripts/gen_codex_bridge.py --check --dest <proyecto>  # 1 si la copia está desfasada
python3 .claude/scripts/gen_codex_bridge.py --check                    # 1 si una rule cambió sin revisar su pieza
```

**Al cambiar una rule citada**, `--check` sale 1: se revisa la pieza que sale de ella, se ajusta si
hace falta y se corre `--rehash`. **Al añadir una pieza**: su fichero aquí, su entrada en el manifiesto
con las secciones de las que sale, y `--rehash`. La `description` no pasa de 1.024 caracteres
(Codex descarta la skill sin avisar: `check_skills_codex.py`).

`{{pytest}}` es el único parámetro: cómo se lanza pytest en el proyecto. Sale de `codex_bridge.pytest`
en su `.claude/CONFIGURACION.yaml`, o `pytest` si no está.

Lo genérico que no sale de una rule concreta (`doble-evidencia`, `lote-acotado`, el subagente
`revisor`) va por el plugin de `.codex-plugins/`, que se instala por máquina; esto va por repositorio.
