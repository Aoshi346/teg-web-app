# `frontend-demo/` — la demo de un Django + React, de serie

Piezas que el Usuario pidió en fitapp y que se copiaban a mano de allí (AN-22, 3.22). Generalizadas:
sin nombres de fitapp, identificadores en inglés y lo propio del proyecto en variables.

| Pieza | Va a | Qué resuelve |
|---|---|---|
| `e2e/run-e2e.mjs` | `frontend/e2e/` | E2E con base **desechable**: RAM, puertos, crear + migrar + sembrar, servidores en `127.0.0.1`, tests, y borrar la base pase lo que pase. El prefijo de la base tiene que acabar en `_e2e`: un prefijo mal puesto no convierte la base de desarrollo en desechable |
| `e2e/playwright.config.ts` | `frontend/e2e/` | Playwright sin `webServer` (arranca y limpia el runner), un trabajador, sin reintentos en local |
| `mockup/mockup.ts` | `frontend/src/testing/` | La maqueta con los handlers de MSW **sin su service worker** (no se pelea con el de la PWA) y con el **login real**; los dominios ya conectados pasan a la API real |
| `pwa/UpdateNotice.tsx` | `frontend/src/lib/pwa/` | «Hay una versión nueva · Actualizar», con sus cuatro piezas escritas en la cabecera |
| `nginx/demo.conf` | el vhost | gzip (el `gzip_types` de Debian viene comentado), HTTP/2, `/assets/` immutable y `sw.js`/`index.html` en `no-cache`. En fitapp: Lighthouse móvil 49 → 92-94 |
| `deploy/deploy-demo.sh` | `infra/` | Despliega un **commit** (no el árbol de trabajo) montado entero aparte y cambiado con dos `mv`, siembra sintética y comprobación al final. Desplegar pide OK (`governance.md` §2) |

## Cómo se engancha

```jsonc
// frontend/package.json
"e2e": "E2E_DB_PREFIX=miapp_e2e E2E_MANAGE='backend/.venv/bin/python backend/manage.py' node e2e/run-e2e.mjs"
```

`E2E_MANAGE` se ejecuta desde la raíz del repo (`E2E_ROOT`, por defecto dos niveles por encima del
runner), así que con la estructura `backend/` + `frontend/` el valor por defecto
(`python backend/manage.py`) ya vale. La base la eligen los settings por `POSTGRES_DB` (`E2E_DB_ENV`
si es otra variable). Todas las variables, en la cabecera del runner.

`seed_demo` es del proyecto: usuarios **sintéticos** con contraseña del entorno, idempotente, y con las
fechas **ancladas a hoy** al sembrar. Una demo con «hace 3 días» deja de decir la verdad en una semana;
en fitapp hizo falta un `--reanclar` para eso.

## Cómo se sabe que funciona

```bash
bash .claude/hooks/check-ram.sh
python3 .claude/smoke/harvest/demo_e2e.py --python <python con django y psycopg>
```

Monta un Django mínimo con login de verdad y un PostgreSQL desechable en `127.0.0.1`, y comprueba el
verde (entra con usuario y contraseña, el backend escucha solo en `127.0.0.1`, la base no sobrevive),
la contraseña mala (1, y la base se borra igual), los nombres de base que no valen (2), el puerto
ocupado (2), conservar y reutilizar la base, y un sabotaje: el runner sin el borrado deja la base viva
y la prueba lo ve. `nginx/demo.conf` se probó con `nginx -t` y sirviéndolo en `127.0.0.1` (cabeceras
de caché y gzip comprobadas). `mockup.ts` y `UpdateNotice.tsx` no se compilaron aquí (el template no
tiene `node_modules`): se comprueban con el `npm run build` del proyecto que los adopte.

Quién lo cita: `nueva-pantalla` (modo `--mockup`) y `project-setup` (proyecto Django + React nuevo).
