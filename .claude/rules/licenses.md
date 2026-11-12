---
paths:
  - "**/package.json"
  - "**/requirements*.txt"
  - "**/pyproject.toml"
  - "**/Pipfile"
  - "**/composer.json"
  - "**/go.mod"
  - "**/Cargo.toml"
  - ".claude/skills/*/LICENSE*"
  - ".claude/patterns/stack/ARRANQUE.md"
  - ".claude/patterns/stack/frontend-stack.md"
  - ".claude/rules/licenses.md"
---
# Licencias — qué se puede usar, para qué uso

> **Cuándo aplicar:** al añadir una dependencia, una herramienta de desarrollo, un servicio o una skill
> de terceros; y en el Gate C de un plan (`plan-gates.md`), donde cada pieza de fuera va con su
> licencia en la misma línea. **NO aplicar:** como asesoría legal. Es el criterio de casa para no
> equivocarse de lado; con un uso dudoso (se vende, se modifica y se ofrece por red a la vez), la
> pregunta va al asesor antes de construir.

La licencia se lee en la **fuente**, con fecha, nunca de memoria: `npm view <pkg> license`, la API
JSON de PyPI (`https://pypi.org/pypi/<pkg>/json` → `info.license`) o el `LICENSE` del repositorio en
el commit que se usa. Una licencia cambia entre versiones (Shepherd.js pasó de MIT a AGPL en la 14.0.1).

## La regla, en dos líneas (decisión AN-D3, opción A, 18-10)

1. **En desarrollo, sin distribuir**: LGPL y GPL valen (linters, analizadores, herramientas de QA que
   corren en nuestra máquina o en CI y no viajan con lo que se entrega).
2. **AGPL y PolyForm, vetadas en todo lo que se entrega a un cliente**: dentro del producto, en lo
   que corre en su navegador (un overlay de QA, una visita guiada) o en lo que se le instala. AGPL
   solo vale como servicio aparte, sin modificar, al que se llama por su API y que no viaja.

## La tabla

| Licencia (SPDX) | Se empaqueta, se vende o se entrega a un cliente | Herramienta interna, sin modificar |
|---|---|---|
| `MIT` · `Apache-2.0` · `BSD-2-Clause` · `BSD-3-Clause` · `ISC` | vale (se conserva el aviso de copyright) | vale |
| `MPL-2.0` | vale; si se modifican **sus** ficheros, esos cambios se publican (el resto del producto, no) | vale |
| `LGPL-*` | vale enlazada como librería aparte y **sustituible** (quien la recibe puede cambiarla por otra versión); sus cambios se publican | vale |
| `GPL-2.0` · `GPL-3.0` (django-easy-audit, Kiwi TCMS, TestLink) | **no**, si se entrega con ella dentro: la obligación nace al distribuir. Usada solo por red, o como servicio aparte, no se activa | vale |
| `AGPL-3.0` (Shannon, OpenReplay, Grafana, Loki, OpenObserve) | **no**, ni dentro de lo que se entrega ni modificada y ofrecida por red. Solo como servicio aparte, sin modificar, tras un adaptador | vale |
| `PolyForm-*` (Shield, Noncommercial…): no es software libre | **no** | solo si el uso cabe en su texto (Shield: no competir con el licenciante); ante la duda, no |
| `FSL-1.1-Apache-2.0` (Sentry) | **no** para un producto que compita con el suyo; a los dos años de cada versión pasa a Apache-2.0 | vale |
| `BUSL-1.1` (immudb) | según su *Additional Use Grant* (la de immudb permite producción salvo una oferta de pago que compita) | vale |
| Licencia propia de reglas o datos (Semgrep Rules License v1.0, 13-12-2024) | **no**: solo uso interno; ni redistribuir ni ofrecer como servicio | vale para uso interno; las reglas YAML propias de la casa son nuestras, no «the rules» de Semgrep |
| Sin licencia, o no se sabe | **no vale**: sin licencia no hay permiso de uso | no vale hasta saberla |

## Las que ya se han mirado (verificación V3/V4 de la revisión integral, 17-10)

| Pieza | Licencia | Veredicto |
|---|---|---|
| eslint-plugin-sonarjs · SonarQube Community | LGPL-3.0 | vale como herramienta de desarrollo (devDependency que no se entrega) |
| pylint | GPL-2.0+ | vale como herramienta de desarrollo |
| Opengrep (fork de Semgrep) | LGPL-2.1 | vale como herramienta de desarrollo; con reglas propias |
| Reglas del registro de Semgrep | Semgrep Rules License v1.0 | solo uso interno; no se copian a un proyecto que se entrega ni se sirven a terceros |
| Shepherd.js ≥ 14.0.1 · intro.js | AGPL-3.0 | **no** en nada que vea el cliente (visitas guiadas, overlay). Shepherd ≤ 13.x es MIT, pero esa línea ya no se mantiene |
| Agentation | PolyForm Shield | **no** en el overlay ni en nada que se entregue |
| ZAP · Trivy + trivy-db · Prowler · Strix (verificación R2, 17-10) | Apache-2.0 | vale en el producto de pentest (ADR-0002) |
| Nuclei + nuclei-templates · Gitleaks · Schemathesis | MIT | vale; Nuclei con la versión de plantillas fijada y Schemathesis solo contra staging con restauración |
| DefectDojo | BSD-3-Clause | vale |
| opengrep-rules | Commons Clause | **no** en el producto; el motor de Opengrep sí, con reglas propias |
| WPScan | WPScan Public Source License (dual) | solo como herramienta del pentester; como servicio o dentro de un producto, licencia comercial de pago → **no** sin ella |
| Shannon | AGPL-3.0 | solo interna, sin modificar, como servicio aparte; **no** en el núcleo de ninguna web app |

Una skill vendorizada lleva su licencia en la nota de procedencia (`vendoring.md`) y pasa por esta
tabla igual que una dependencia.

_Rule version: 1.0 · 2026-10-31 — sub-ola 3.18 (AN-D3): la tabla sale de `plan-gates.md` §Gate C
(MO-29) a una rule propia con `paths:` en los manifiestos, y se añaden PolyForm, la licencia de
reglas de Semgrep y las herramientas ya verificadas · v1.1 · 2026-11-01 — sub-ola 4.01 (WA-D4, ADR-0002): los motores
de pentest verificados en la R2._
