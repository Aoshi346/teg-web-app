# `.claude/smoke/` — Evidencias y specs de smoke-test

Carpeta para smoke-tests atómicos (HTTP headers, screenshots, gates de fase). Ver la convención
completa en `.claude/rules/verification.md` §Smoke testing.

Ejemplos de archivos:
- `01-root.txt` — `curl -sI` de la home
- `02-admin.txt` — `curl -sI` del admin/login
- `<fase>-<tema>.md` — nota de gate: qué se validó, resultado, si pasa

`.gitignore` sugerido (screenshots grandes):
```
.claude/smoke/**/*.png
```

## `flujo/` — los sabotajes del harness

| Script | Qué prueba | Cuándo |
|---|---|---|
| `flujo/correr.sh` | Los gates del flujo de arranque, sobre una copia (30 casos, sin modelo) | Tras tocar un gate, y al cerrar cada sub-ola |
| `flujo/herencia-permisos.sh` | Que un `deny` del padre vale en un subagente, en un fork y en un subagente reanudado tras revocarlo (MO-75). Con `claude -p` de verdad: 8 llamadas, ~2 min, con la suscripción; `--autoprueba` comprueba su oráculo sin modelo | Al cambiar de versión o de canal de Claude Code |

## `catalog/` — «catálogo listo para vender» (CB-78)

| Script | Qué prueba | Cuándo |
|---|---|---|
| `catalog/run.sh` | `scripts/catalog_readiness.py` contra la semilla de `elvion-autoparte-demo` pasada a JSON (`autoparte_seed.json`: huecos de atributos, complementos y políticas), contra un catálogo completo sintético (`complete.json`: verde con una API real en 127.0.0.1) y 10 sabotajes, cada uno contra su comprobación. Sin modelo, segundos | Tras tocar el script o el formato del export |

## `harvest/` — la cosecha de proyectos de la sub-ola 3.20

| Script | Qué prueba | Cuándo |
|---|---|---|
| `harvest/run.py` | Los hooks opcionales de AN-19 con eventos reales por stdin (cada bloqueo con su control) y el `--self-test` de los scripts cosechados (sabotaje, ids, lanzador de frentes, turno de pytest, control de producción, fork, reparto por módulos, topología). Sin modelo ni red, segundos | Tras tocar cualquiera de esas piezas |
| `harvest/contrast_fixture.py` | El compositor de contraste de Vera contra una página con defectos contados; `--js` para ver fallar una versión saboteada. Abre navegador (python con playwright) | Tras tocar el instrumento |
| `harvest/access_audit.py` | (3.21, AN-8) El registro de accesos contra un PostgreSQL 17 desechable (imagen local, sin puertos): UPDATE/DELETE/TRUNCATE de la app fallan, la cadena caza una fila alterada y el ancla caza la cadena recalculada; sabotaje sin el trigger. `check-ram.sh` antes; ~20 s | Tras tocar `templates/access-audit/` |
| `harvest/compose_wrapper.py` | (3.21, AN-15) El envoltorio de compose con `docker compose config` (no levanta nada): sin marcador, sin prefijo o con el nombre de un contenedor vivo de otro proyecto, se niega; los controles pasan | Tras tocar `templates/compose-wrapper/` |
| `harvest/demo_e2e.py` | (3.22, AN-22) `templates/frontend-demo/e2e/run-e2e.mjs` contra un Django mínimo y un PostgreSQL 17 desechable en `127.0.0.1`: login real, backend solo en `127.0.0.1` (`ss`), la base no sobrevive (tampoco con la contraseña mala), nombres de base y puerto ocupado → 2, conservar/reutilizar, y sabotaje sin el borrado. Pide `--python` con django y psycopg; `check-ram.sh` antes; ~1 min | Tras tocar `templates/frontend-demo/e2e/` |
| `harvest/ticket_kit.py` | (4.16, WA-4) La skill `verify-ticket` contra un Django mínimo en SQLite desechable y runserver en `127.0.0.1`: sesión sin contraseña (BBDD y cookie firmada), captura enmascarada, report-kit con anotaciones del auditor y PDF, el DNI real en ningún fichero; controles: texto ausente → 1, python de Django ausente o runserver caído → 2, DNI sin enmascarar → captura descartada, `DEBUG=False` y BBDD remota → 1 sin capturar; sabotaje sin el guard de DEBUG. Pide `--python` con django y playwright; `check-ram.sh` antes; ~1 min | Tras tocar `skills/verify-ticket/` |
| `harvest/django_audit_trail.py` | (4.13, WA-11) El paquete `webapps/django-audit-trail` contra un PostgreSQL 17 desechable en `127.0.0.1`: migrar con el rol de la app se niega; como `app_user`, lecturas y escrituras por HTTP de test sin nombre ni diagnóstico en el registro, UPDATE/DELETE fallan, `check --database` sin E003 (y con E003 conectado como dueño); `audit_trail_verify` caza la fila alterada y, con `--anchors`, la cadena recalculada; coste por guardado (N=300). Pide `--python` con django y psycopg2; `check-ram.sh` antes; ~30 s | Tras tocar `webapps/django-audit-trail/` o `templates/access-audit/` |

## `widget-venta/` — la compra con el chat de venta (sub-ola 3.68, UX-8)

| Script | Qué prueba | Cuándo |
|---|---|---|
| `skills/probar-widget/probar_widget.py --autoprueba` | Levanta `widget-venta/fixture_server.py` en 127.0.0.1 (anfitrión HTML, tienda con tema hostil, bot de respuestas fijas: 0 €) con el widget de referencia `widget-venta/widget.js`: limpio en los dos anfitriones a 1440 y 390, y once sabotajes (`?sabotage=`), cada uno contra su check CW1-CW10. Python con playwright (`preparar_navegador.sh`); `check-ram.sh` antes; ~1 min | Tras tocar `probar-widget`, el widget de referencia o `chat-ui-comercio.md` |
