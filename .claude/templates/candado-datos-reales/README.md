# Candado de datos reales — las piezas que se copian al proyecto

El patrón, el porqué y dónde va cada pieza: `.claude/patterns/stack/backend-candado-datos-reales.md`.
El gate que lo comprueba: `.claude/scripts/gate_datos_reales.py` (y su `--autoprueba`). Cosechado de
`accounting_AMC` en la sub-ola 2.29 de la revisión integral (SE-49).

| Fichero | Dónde va en el proyecto | Qué se toca al copiarlo |
|---|---|---|
| `candado.py` | `backend/core/seguridad/candado.py` (lo transversal) | `VARIABLE`, `MODOS`, `REQUISITOS_CON_DATOS_REALES`, `NIVELES_HASTA_LA_RAIZ` |
| `test_candado.py` | junto al candado, en sus `tests/` | el import de la cabecera |
| `estado-datos-reales.json` | `.claude/estado-datos-reales.json` | `variable` y las condiciones del proyecto; lo rellena **una persona** |
| `estado-datos-reales.sh` | `.claude/hooks/`, registrado en el SessionStart | nada |

Y dos cosas que no son ficheros: `"Edit(.claude/estado-datos-reales.json)"` en el `deny` de
`.claude/settings.json`, y el paso de CI que demuestra que bloquea (el YAML está en el patrón).
Las dos tocan configuración sensible: piden aprobación (`rules/governance.md` §2).

Al terminar de copiarlo:

```bash
python3 .claude/scripts/gate_datos_reales.py . --completo                          # protegido y cableado
python3 .claude/scripts/gate_datos_reales.py . --demostrar --python .venv/bin/python   # y se niega de verdad
```

Medido en la 2.29: la autoprueba del gate, 34/34 (con `--python` de un Django 5.2); `test_candado.py`,
8/8 en verde y los 5 mutantes del candado cazados.
