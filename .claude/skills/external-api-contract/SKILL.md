---
name: external-api-contract
description: >-
  Usar antes de afirmar que la API de un tercero no puede algo o al tocar una integración: 'la API
  no soporta X', 'no existe ese endpoint', 'hay que preguntar al proveedor', 'tenemos su
  Postman/OpenAPI'. Indexa el contrato real y lleva su gotchas.md. NO usar para: el Gate E
  (plan-gates), el simulador (mocks-externos.md) ni el código (backend-integrations.md).
user-invocable: true
metadata:
  version: 1.0.0
  author: tech-lead-template (3.22, AN-23)
  category: domain
  updated: 2026-10-31
  source: "proxera_musa/.claude/skills/flowww-api (generalizada)"
---

# external-api-contract — el contrato real antes que la memoria

## Principio

La fuente de verdad de una API de terceros es **su contrato publicado** (colección de Postman,
OpenAPI, Swagger), no el docstring de nuestro cliente ni lo que recordamos. Nuestro código implementa
un **subconjunto**, y no avisa de que lo es. En musa se dieron por inexistentes, dos veces, endpoints
que llevaban meses documentados en una colección de 13 MB (`GET /client/{id}/history`,
`POST /diary/{id}/move`), y el plan de un P0 proponía preguntar al proveedor algo que ya estaba escrito.
Un fichero de 13 MB no se lee a mitad de un diagnóstico: por eso esta skill trae el índice
(`index_contract.py`, 334 endpoints en 0,4 s) y una memoria de gotchas por proveedor.

## Cuándo activar

**Obligatorio** antes de:
- escribir o decir «<proveedor> no permite / no existe / habría que preguntarles»;
- añadir, cambiar o borrar un método del cliente de un tercero, o una ruta de su simulador;
- diagnosticar un 4xx que venga del proveedor;
- planificar una feature que dependa de lo que el tercero ofrece.

**Input:** el proveedor y su contrato. Si no sabes dónde está el contrato, el paso 1 lo busca; si no
existe en el repo, **para y dilo** («no tenemos su contrato»): no se sustituye por memoria ni por una
búsqueda web sin fecha.

## Procedimiento

### 1. Localizar el contrato (y dejarlo en un sitio fijo)

```bash
find . -path ./node_modules -prune -o -type f \( -iname "*postman_collection*" -o -iname "openapi*.*" \
  -o -iname "swagger*.*" \) -print
```

Si está en una carpeta de un plan viejo, se apunta su ruta en el `contract.md` del proveedor (paso 2):
la ruta escrita a mano en una skill caduca en cuanto alguien mueve el fichero.

### 2. Indexarlo, una vez por versión del contrato

```bash
python3 .claude/skills/external-api-contract/index_contract.py <contrato> \
  --provider <proveedor> --out <carpeta-de-la-integración>/contract/
```

Deja `contract.md` (índice por grupo: método, ruta, nombre, campos del cuerpo con `*` si son
obligatorios, campos de la respuesta), `contract-index.json` y, **solo si no existe**, `gotchas.md`
desde la plantilla. El `gotchas.md` que haya **no se pisa nunca**: es la memoria acumulada.

| Salida | Significa |
|---|---|
| 0 | Hay endpoints (con `--search`: hay coincidencias) |
| 1 | `--search` sin coincidencias: «no aparece en ESTE contrato» |
| 2 | No se pudo leer: formato desconocido, YAML sin PyYAML, o **0 endpoints** — un índice vacío no demuestra que nada exista |

### 3. Antes de decir «no se puede»

⚠️ Recordatorio, repetido a propósito: **no se escribe «la API no lo soporta» sin haber hecho esta tabla
entera**, aunque parezca obvio. Si parece obvio, es justo cuando más falla.

| Pregunta | Dónde mirar |
|---|---|
| ¿Existe el endpoint? | `index_contract.py <contrato> --search "<palabras>"`, y con sinónimos del dominio (`diary`/`agenda`/`appointment`) |
| ¿Lo tenemos implementado? | `grep -n "def " <cliente-del-proveedor>` |
| ¿Lo simula el simulador? | Sus rutas (`mocks-externos.md` §2) |
| ¿Ya nos mordió antes? | `gotchas.md` del proveedor |

Solo si falla la primera fila se puede escribir, y así: *«no aparece en el contrato que tenemos
(<fichero>, <fecha>)»*. Nunca *«la API no lo soporta»*.

### 4. Probar con el caso real

Un endpoint del índice existe **en el papel**. Antes de comprometer el plan, una llamada mínima con el
caso real del usuario (Gate E, `rules/plan-gates.md`), contra el entorno de pruebas del proveedor o el
simulador. **Escribir en el real (crear, mover, cancelar, pagar) pide OK del Usuario.**

### 5. Al añadir un endpoint

1. Su ficha con `--search`: campos obligatorios, tipos y el ejemplo de respuesta literal.
2. El cliente real con **lista blanca de campos** de salida (nunca reenviar el crudo).
3. El doble y el simulador con **la misma forma**, defectos incluidos: el simulador falla donde falla
   el real (`mocks-externos.md` §6.3-6.4). Una versión «mejorada» en el mock esconde el fallo hasta
   producción.
4. La forma del código (Protocol + real + doble + factoría): `patterns/stack/backend-integrations.md`.

### 6. Cada vez que muerda: una entrada en `gotchas.md`

**Síntoma → causa → cómo se descubrió → qué hacemos.** También cuando el contrato dice algo que
contradice lo que suponíamos aunque aún no haya fallado (en musa: el mismo campo `DiaryGStart` era una
hora en un endpoint y un número de franjas en otro).

## Anti-patterns

- ❌ Tomar nuestro cliente (o su docstring) como la lista de lo que la API ofrece.
- ❌ «Hay que preguntar al proveedor» sin haber corrido `--search`. En musa pasó dos veces.
- ❌ Contar un `--search` vacío como prueba de inexistencia sin probar sinónimos.
- ❌ Aceptar un 2 («0 endpoints», formato desconocido) como «no hay nada»: es un instrumento que no midió.
- ❌ Regenerar el índice borrando `gotchas.md`, o editar `contract.md` a mano (se regenera).
- ❌ Escribir la ruta del contrato en una skill: se mueve. Va en el `contract.md`, que se regenera.
- ❌ Regenerar una API key «para probar»: en muchos proveedores invalida la que está en uso.

## Ejemplos

### User: «¿Se puede saber qué citas tiene una clienta en Flowww?»
TL: `--search "client history"` → `GET /client/{{clientID}}/history`, con `AppointmentID`,
`AppointmentDate` y `AppointmentStart` en la respuesta. Respondo que sí, con la cadena (buscar la
clienta → su historial), y miro `gotchas.md` antes de prometer el estado de la cita.

### User: «Esa API no deja mover citas, hay que pedírselo al proveedor»
TL: antes de escribirlo, `--search "diary move"` → `POST /diary/{{diaryGID}}/move` existe. Saco su ficha,
apunto en `gotchas.md` lo que difiera del endpoint de crear, y lo pruebo contra el simulador.

### User: «Vamos a integrar <proveedor nuevo>; nos han pasado su OpenAPI»
TL: `--provider <nombre> --out integrations/<nombre>/contract/` → índice y `gotchas.md` vacío con la
plantilla. Primera llamada real mínima (Gate E) y su resultado, en el plan.

## Related

- `rules/plan-gates.md` §Gate E — que la fuente se pueda leer, con el caso real.
- `patterns/stack/mocks-externos.md` — el simulador y su paridad con el real.
- `patterns/stack/backend-integrations.md` — la forma del código de la integración.
- `integrar-crm` — el caso concreto de formularios hacia un CRM.
- Origen: `flowww-api` de proxera_musa (receta de consulta + `memory.md` de gotchas).
