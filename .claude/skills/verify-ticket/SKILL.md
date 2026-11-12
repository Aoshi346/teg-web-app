---
name: verify-ticket
description: >-
  Usar para verificar en el navegador los criterios de un ticket de un Django y sacar su informe:
  'verifica el ticket', 'capturas del ticket', 'informe de verificación', 'comprueba los criterios de
  aceptación en la app'. Login sin contraseña solo en desarrollo, capturas con guarda PII, report-kit
  y PDF. NO usar para: el E2E de la suite (frontend-demo), la foto de impacto (Pilar) ni una captura
  suelta (screenshot.py).
user-invocable: true
metadata:
  version: 1.0.0
  author: tech-lead-template (4.16, WA-4)
  category: verification
  updated: 2026-10-31
  source: "EvoPreven develop: sesion.py, pwlib.py y build_informe.py de EVO-2834, EVO-2913 y GENCAT-49 (generalizados)"
---

# verify-ticket — verificar un ticket Django es un comando

## Cuándo se activa (detalle)

Un ticket de un proyecto Django está programado y hay que **demostrar en la app** que cumple sus
criterios, con capturas y un informe que se pueda entregar. Antes, cada ticket escribía su
`sesion.py`, copiaba `pwlib.py` del anterior y reescribía un `build_informe.py` de ~750 líneas. Aquí
se escribe un `ticket.json` y se corre un comando.

**NO es:** la suite E2E del proyecto (`templates/frontend-demo/e2e/`), la medición antes/después de
Pilar (`templates/impacto/`), ni una captura suelta (`scripts/screenshot.py`).

## Reglas (no negociables)

1. **Solo en desarrollo.** `session_login.py` se niega con `DEBUG=False`, con cualquier BBDD no
   local (el guard de Pilar, más HOST vacío con el destino en `OPTIONS` o en `NAME`) y con las
   sesiones en una caché no local. Nunca se apunta a producción ni a una copia remota.
2. **Usuarios de prueba, sembrados por el proyecto.** El kit no crea usuarios ni toca contraseñas.
3. **La guarda de datos personales va siempre encendida.** Las celdas con nombres o documentos se
   declaran en `mask`; si queda un dato real, la captura se descarta y el criterio sale `blocked`.
4. **Antes de entregar, alguien MIRA cada captura** y la anota (`guarda_pii_capturas.py --registrar`).
   Hasta entonces el informe lleva `PII-REV` en «A revisar».
5. **No se escribe un generador de informe nuevo.** Si al informe le falta algo, se propone en el
   report-kit (`rules/output-choice.md` §4).
6. **Servidores en 127.0.0.1** (el de la app, el del informe y el del PDF).

## Input contract — `<plan>/verificacion/ticket.json`

```json
{
  "schema": "ticket-verify/1",
  "ticket": "EVO-1234", "title": "Filtro de centro en la lista de trabajadores",
  "base_url": "http://127.0.0.1:8000",
  "settings": "config.settings.local", "backend_dir": "backend",
  "forbidden_db": ["db.prod.example"],
  "diff_base": "origin/develop",
  "actors": {"tecnico": {"username": "prueba_tecnico"}},
  "wait_loader": [".blockUI"],
  "criteria": [
    {"id": "AC-1", "title": "El técnico ve solo sus centros", "actor": "tecnico",
     "url": "/workers/?center=3", "expect_status": 200,
     "expect_text": ["Centro Norte"], "expect_absent": ["Centro Sur"],
     "mask": ["td.nombre", "td.dni"]}
  ],
  "auditors": ["../impacto/impacto.json", "../codigo/findings.json"]
}
```

Sin `actor`, el criterio va sin sesión. `auditors` son rutas relativas a `ticket.json` a lo que dejaron
Roberto (`code-findings/1`), Pilar (`impacto/1`) o cualquier auditor con el contrato de veredicto.
Si falta algo obligatorio o `base_url` no es local, el comando sale con **2** y no mide nada.

## Uso

```bash
bash .claude/hooks/check-ram.sh                     # abre navegador: cuenta doble
python3 .claude/skills/verify-ticket/verify_ticket.py <plan>/verificacion/ticket.json \
    --django-python backend/.venv/bin/python --pdf
# mirar cada PNG de shots/ (Read) y anotarlo; después, otra vez el comando
python3 .claude/scripts/guarda_pii_capturas.py --registrar <plan>/verificacion/shots --por "<quién>" <png…>
cd <plan>/verificacion && python3 server.py --port 8840     # y enlace.py antes de dar el enlace
```

El python que corre `verify_ticket.py` necesita playwright; el de `--django-python`, el Django del
proyecto (puede ser el mismo). Salida: **0** todos los criterios `done` · **1** alguno no, o un guard
se negó · **2** no se pudo medir.

## Qué deja en la carpeta

| Fichero | Qué es |
|---|---|
| `shots/<id>.png` | Captura de cada criterio, tras enmascarar y pasar la guarda |
| `resultados.json` | Cada comprobación con lo visto (`ticket-results/1`); de un dato personal, solo la muestra tapada |
| `report.json` | Report-kit, perfil `minimo`: un item por criterio (epic AC), uno por auditor (AUD, «Anotaciones del auditor»), `PII-REV`, `meta.pedido` y `meta.diff` con el `diff_sha256` verificado |
| `index.html`, `results.html`, … | El set del kit, con las capturas embebidas (abre sin servidor) |
| `informe.pdf` | Con `--pdf`: `results.html` impreso |

## Piezas

- `session_login.py`: la cookie de sesión con el motor del proyecto (`db`, `cache`, `cached_db`,
  `signed_cookies`) y `set_expiry`. Vale suelta para un guion propio.
- `pw.py`: navegador (Chromium del sistema), contexto por actor, `wait_loader`, `pii_guard`, `capture`.
  Lo propio de la UI de cada proyecto (abrir una ficha, un nodo del árbol) se queda en el proyecto.
- `verify_ticket.py`: el comando. `--self-test` sin Django ni navegador.
- Prueba de punta a punta: `smoke/harvest/ticket_kit.py --python <con django y playwright>`.

## Límites

- Comprueba lo que se ve: estado HTTP y texto de la página. Lo que solo está en la BBDD se mide con
  la foto de Pilar, no aquí.
- Con sesión en `cache` (Redis), el Redis que lee el kit tiene que ser el mismo que el del runserver:
  en un worktree con Redis propio, los mismos settings para los dos.
- Las formas `cache` y `cached_db` no se han probado aquí (sí `db` y `signed_cookies`).
- El guard de BBDD y el sello del diff son `scripts/db_guard.py` y `scripts/diff_hash.py`, del núcleo
  y comunes con las fotos de Pilar: un solo criterio de «local» para los dos.
