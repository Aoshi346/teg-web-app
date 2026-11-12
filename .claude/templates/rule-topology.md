---
# Plantilla (AN-25, cosechada de elvion): cópiala a `.claude/rules/topologia.md` del proyecto y
# ajusta `paths:` a los ficheros que tocan los datastores (settings, compose, scripts de datos).
paths:
  - "docker-compose*.yml"
  - "**/settings/**"
  - "scripts/**"
  - ".claude/rules/topologia.md"
---

# Topología y datos — invariantes de <PROYECTO>

> **Cuándo aplicar:** antes de cualquier query, endpoint, script de datos, migración, restore o
> reindexado que toque uno de los datastores, y antes de montar el proyecto en otra máquina. Es la
> fuente de verdad de **puertos**, **counts canónicos** y **aislamiento**. **NO aplicar:** al código de
> negocio (sus rules) ni a la seguridad (`security.md`).
>
> En una rule y no en `CLAUDE.md`: solo importa al tocar datos, y con `paths:` no se paga en cada sesión.

## Topología — medida, no recordada

Medida el <AAAA-MM-DD> con `docker compose ps` y `systemctl cat <unidad>`. **Si no la has medido, no
la escribas**: una tabla de memoria es justo la que acaba con cinco de seis filas falsas.

| Store | Rol | Puerto host | Puerto contenedor |
|---|---|---|---|
| **PostgreSQL** | BD principal | **<54xx>** | 5432 |
| **Redis** | broker + caché | **<63xx>** | 6379 |
| App (tras nginx) | gunicorn | **<81xx>** | — |

Comprobación, en un segundo (la tabla contra lo que escucha; 2 si no encuentra la tabla):

```bash
python3 .claude/scripts/check_topology.py .claude/rules/topologia.md
```

## Aislamiento — invariante

<cómo se separa cada tenant o cliente: base por tenant, colección por tenant, prefijo de claves; y
qué pasa fuera del ciclo de petición (workers, hilos), que es donde suele romperse>

## Counts canónicos — validar después de un restore o un reindexado

| Qué | Cuántos | Cómo se mide (el comando, pegado) | Medido |
|---|---|---|---|
| <productos del tenant A> | <n> | `<comando>` | <fecha> |

Un proceso que dice «OK» no es un count: el script de indexado puede salir 0 habiendo fallado. Se cuenta
en el destino (filas, `points_count`), no se lee el código de salida.

## Anti-patterns

- ❌ Copiar la tabla de puertos de otro proyecto o de la documentación del servicio: los de casa casi
  nunca son los de fábrica.
- ❌ Reindexar o recargar «desde el botón del panel» si ese camino no fija el tenant: siempre por CLI
  con el tenant explícito.
- ❌ Dar un restore por bueno sin los counts canónicos.
