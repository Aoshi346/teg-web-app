---
name: "migration-integrity-checks"
description: >-
  Usar antes y después de una migración que mueva o transforme datos (backfill, cambio de tipo,
  import, unificar bases): 'verifica la migración', '¿migraron bien los datos?', 'faltan registros
  después de migrar', 'huérfanos'. NO usar para: el rendimiento de queries (django-orm,
  optimization.md) ni decidir qué migraciones necesitan aprobación (governance.md).
user-invocable: true
metadata:
  version: 1.0.1
  author: Tech Lead Template
  category: qa
  updated: 2026-10-21
  tech-stack: "Django + PostgreSQL (los principios valen para cualquier RDBMS)"
---

# migration-integrity-checks — demostrar que los datos llegaron enteros

## Principio

`governance.md` exige aprobación para las migraciones destructivas, y `speckit-workflow.md` las mete
en el flujo de aprobación — pero **ningún sitio dice cómo se comprueba que los datos migraron bien**.
En la práctica se comprueba mirando la app cinco minutos y diciendo "parece que está".

Una migración de datos es correcta cuando puedes **demostrarlo con números tomados antes y después**.
Y la palabra clave es **antes**: si no mediste el origen, después no tienes nada contra qué comparar.
Ese es el error que hace irrecuperable una migración mala.

## Cuándo activar

| Migración | ¿Aplica? |
|---|---|
| Backfill de una columna nueva a partir de datos existentes | **sí** |
| Split/merge de columnas, cambio de tipo, normalización | **sí** |
| Renombrar/mover tabla, cambiar la FK a otro modelo | **sí** |
| Import masivo o unificación de dos bases de datos | **sí, con muestreo obligatorio** |
| Borrado masivo o soft-delete retroactivo | **sí** |
| Añadir columna nullable / índice / choice nuevo | no (no hay datos que mover) |

Disparadores: 'verifica la migración', '¿migraron bien los datos?', 'integridad post-migración',
'backfill', 'faltan registros después de migrar', 'checksum de la tabla', 'huérfanos',
'/migration-integrity-checks'. Demuestra que los datos llegaron íntegros: conteos, checksums
independientes del orden, filas huérfanas, constraints validados y muestreo. Stack Django +
PostgreSQL. · NO confundir con django-orm (rendimiento de queries: su referencia optimization.md) ni
con governance.md (que dice QUÉ migraciones necesitan aprobación; esta skill dice CÓMO comprobar que
salió bien).

## Procedimiento

### Fase 0 — Snapshot ANTES (el paso que nadie hace y sin el cual no hay verificación)

```bash
# En la MISMA base sobre la que se va a migrar (staging con copia real de prod, o prod tras backup)
# Las consultas de las fases 1-3 de abajo, adaptadas a tus tablas, en un fichero tuyo: la skill no
# trae ninguno (citaba un `checks.sql` que no existió nunca; verificador de la 2.17)
psql "$DATABASE_URL" -f .docs/migrations/<fecha>-checks.sql > /tmp/pre-migracion.txt
git add /tmp/pre-migracion.txt 2>/dev/null || cp /tmp/pre-migracion.txt .docs/migrations/<fecha>-pre.txt
```

Antes de nada, y aparte: **backup verificado** (que exista el fichero no es un backup; que restaure
en otro sitio, sí). Sin backup restaurable, no se lanza una migración destructiva — eso es
`governance.md`, no esta skill.

### Fase 1 — Conteos (necesarios, nunca suficientes)

```sql
-- Total, y desglose por las dimensiones que importan al negocio
SELECT count(*) AS total,
       count(*) FILTER (WHERE estado = 'pagado')     AS pagados,
       count(*) FILTER (WHERE estado = 'pendiente')  AS pendientes,
       count(*) FILTER (WHERE cliente_id IS NULL)    AS sin_cliente,
       min(created_at) AS mas_antiguo,
       max(created_at) AS mas_reciente
FROM pedidos;
```

Dos avisos que cuestan caro:

- **`count(*)` igual no significa "datos iguales".** Una transformación puede conservar el número de
  filas y corromper el contenido de todas. Por eso existe la fase 2.
- **No uses `pg_stat_user_tables.n_live_tup` ni `reltuples` como conteo**: son **estimaciones** del
  planificador y pueden desviarse mucho. Para verificar, `count(*)` real.

### Fase 2 — Checksums independientes del orden

Un checksum agregado detecta que **el contenido** es el mismo aunque el orden de las filas cambie
(y en una migración cambia casi siempre). Suma de hashes por fila:

```sql
SELECT count(*) AS filas,
       sum(('x' || substr(md5(ROW(id, importe, estado, cliente_id)::text), 1, 8))::bit(32)::int)::bigint
         AS checksum,
       sum(importe) AS suma_importes           -- el checksum de negocio, el que entiende un humano
FROM pedidos;
```

- **Enumera las columnas explícitamente** dentro de `ROW(...)`. Con `tabla.*::text` cualquier cambio
  de orden o de columnas de la tabla altera el hash aunque los datos sean idénticos — y en una
  migración eso pasa por definición.
- **`sum(importe)` vale más que el md5** para hablar con negocio: si la suma de importes cambia, no
  hace falta explicar nada más. Añade uno por cada magnitud crítica (importes, cantidades, saldos).
- Si el tipo cambia en la migración (`varchar` → `numeric`), normaliza en ambos lados antes de hashear
  (`trim`, `lower`, `round(x, 2)`), o compara solo los checksums de negocio.

Comparación:

```bash
diff /tmp/pre-migracion.txt /tmp/post-migracion.txt || echo "REVISAR: los agregados no coinciden"
```

### Fase 3 — Huérfanos (lo que la migración rompe sin avisar)

```sql
-- FK que apunta a nada (aparece cuando se migra la tabla padre o se re-mapean ids)
SELECT count(*) AS huerfanos
FROM pedidos p LEFT JOIN clientes c ON c.id = p.cliente_id
WHERE p.cliente_id IS NOT NULL AND c.id IS NULL;

-- Duplicados en lo que debería ser único (aparece al fusionar dos bases)
SELECT email, count(*) FROM clientes GROUP BY email HAVING count(*) > 1;

-- NULLs nuevos en columnas que no deberían tenerlos (backfill incompleto)
SELECT count(*) FROM pedidos WHERE importe IS NULL;
```

**Los tres sitios donde el motor NO te protege y hay que mirar a mano:**

1. **`ForeignKey(db_constraint=False)`** — Django no crea la constraint: el huérfano es legal para
   la base de datos.
2. **Relaciones genéricas** (`GenericForeignKey`, `content_type_id` + `object_id`) — nunca hay FK.
   Al migrar hay que re-mapear los `content_type_id`, y si no se hace, apuntan a otro modelo.
3. **Referencias "blandas"**: ids guardados en un `JSONField`, en un CSV, en una columna de texto.

```sql
-- Huérfanos en relación genérica (el clásico olvido)
SELECT count(*) FROM comentarios cm
LEFT JOIN django_content_type ct ON ct.id = cm.content_type_id
WHERE ct.id IS NULL;
```

### Fase 4 — Constraints e índices realmente validados

```sql
-- Constraints declaradas pero NO validadas (típico tras un ADD CONSTRAINT ... NOT VALID)
SELECT conrelid::regclass AS tabla, conname, contype
FROM pg_constraint WHERE NOT convalidated;

-- Índices inválidos (un CREATE INDEX CONCURRENTLY que falló a medias)
SELECT indexrelid::regclass AS indice FROM pg_index WHERE NOT indisvalid;
```

```sql
-- Patrón seguro en tablas grandes: añadir sin bloquear y validar después
ALTER TABLE pedidos ADD CONSTRAINT pedidos_cliente_fk
  FOREIGN KEY (cliente_id) REFERENCES clientes(id) NOT VALID;
ALTER TABLE pedidos VALIDATE CONSTRAINT pedidos_cliente_fk;   -- no bloquea escrituras
```

Que la constraint exista **no** significa que los datos preexistentes la cumplan: `NOT VALID` es
exactamente eso. Si la query de arriba devuelve filas, la migración no ha terminado.

Y del lado de Django:

```bash
python manage.py migrate --check          # ¿queda alguna migración sin aplicar?
python manage.py makemigrations --check --dry-run   # ¿el modelo y el schema divergen?
python manage.py check --database default
```

### Fase 5 — Muestreo (los agregados pueden mentir)

Coge **N filas al azar** (y las 3 más antiguas, las 3 más nuevas y los casos raros conocidos) y
compara campo a campo origen vs destino. Es donde aparecen los errores que ningún agregado detecta:
codificación (`Ã±` en vez de `ñ`), zonas horarias desplazadas una hora, decimales redondeados,
booleanos invertidos, cadenas truncadas al límite del `varchar`.

```sql
SELECT * FROM pedidos ORDER BY random() LIMIT 20;
```

```sql
-- Sospechas típicas, baratas de comprobar
SELECT count(*) FROM clientes WHERE nombre ~ '[ÃÂ]';                    -- mojibake
SELECT count(*) FROM pedidos  WHERE length(referencia) = 50;            -- truncado al límite
SELECT min(created_at), max(created_at) FROM pedidos;                   -- fechas imposibles/desplazadas
```

### Fase 6 — Dejarlo escrito y repetible

Empaqueta las queries de las fases 1-4 en un management command para que la verificación sea un
comando y no una sesión de copiar y pegar:

```python
# apps/core/management/commands/check_integrity.py
import json
from django.core.management.base import BaseCommand
from django.db import connection

CHECKS = {
    "pedidos_total":      "SELECT count(*) FROM pedidos",
    "pedidos_checksum":   "SELECT sum(('x'||substr(md5(ROW(id, importe, estado, cliente_id)::text),1,8))"
                          "::bit(32)::int)::bigint FROM pedidos",
    "pedidos_suma":       "SELECT coalesce(sum(importe), 0) FROM pedidos",
    "huerfanos_cliente":  "SELECT count(*) FROM pedidos p LEFT JOIN clientes c ON c.id = p.cliente_id "
                          "WHERE p.cliente_id IS NOT NULL AND c.id IS NULL",
    "constraints_sin_validar": "SELECT count(*) FROM pg_constraint WHERE NOT convalidated",
}
# Lo que DEBE valer 0 pase lo que pase
CERO = ("huerfanos_cliente", "constraints_sin_validar")


class Command(BaseCommand):
    help = "Snapshot de integridad. --compare <fichero> falla (exit 1) si algo no cuadra."

    def add_arguments(self, parser):
        parser.add_argument("--compare", help="snapshot previo en JSON")

    def handle(self, *args, **opts):
        with connection.cursor() as cur:
            actual = {}
            for name, sql in CHECKS.items():
                cur.execute(sql)
                actual[name] = cur.fetchone()[0]

        fallos = [k for k in CERO if actual.get(k)]
        if opts["compare"]:
            previo = json.load(open(opts["compare"]))
            fallos += [f"{k}: {previo[k]} -> {actual[k]}"
                       for k in previo if k not in CERO and previo[k] != actual[k]]

        self.stdout.write(json.dumps(actual, indent=1, default=str))
        if fallos:
            raise SystemExit(f"INTEGRIDAD KO: {fallos}")
        self.stdout.write(self.style.SUCCESS("INTEGRIDAD OK"))
```

```bash
python manage.py check_integrity > /tmp/pre.json      # antes
python manage.py migrate
python manage.py check_integrity --compare /tmp/pre.json   # después: exit 1 si algo cambió
```

Ese `exit 1` es lo que convierte la verificación en un **gate** (nivel 3 de `rules/verification.md`)
en vez de en un informe que alguien lee por encima.

> Ojo con qué se espera que cambie: en un backfill, `pedidos_total` debe ser **igual** pero
> `huerfanos` debe bajar a 0 y una columna antes NULL debe estar llena. Declara **antes de migrar**
> qué agregados deben moverse y cuáles no; si no, cualquier resultado se puede racionalizar
> después. Los de la lista `CERO` no se negocian nunca.

### Fase 7 — Y la vuelta atrás

Verifica también que **se puede volver**: `python manage.py migrate <app> <migración_anterior>` en
staging, y re-corre las mismas checks. Una migración de datos sin reversa probada es una decisión
irreversible disfrazada de commit.

## Anti-patterns

- ❌ **No tomar el snapshot previo.** Sin el "antes", el "después" no demuestra nada.
- ❌ Verificar solo con `count(*)`: mismo número de filas, contenido corrupto.
- ❌ Usar `reltuples`/`n_live_tup` como conteo (son estimaciones del planificador).
- ❌ Checksums con `tabla.*` en vez de columnas explícitas → cambian por el propio cambio de schema.
- ❌ Dar por buena una constraint recién añadida sin comprobar `convalidated`.
- ❌ Olvidar las relaciones sin FK real (`db_constraint=False`, genéricas, ids en JSON).
- ❌ Verificar en una BD de prueba con 12 filas y extrapolar a los 4 millones de producción.
- ❌ Migrar sin backup **restaurable** (probado en otro sitio, no solo "el fichero existe").
- ❌ Decidir después de migrar qué agregados "tenían que cambiar" — se declara antes.

## Ejemplos

### User: "hay que partir `nombre_completo` en `nombre` y `apellidos`"
TL: snapshot previo (total, checksum, `count(*) FILTER (WHERE nombre_completo IS NULL)`) → migración
con backfill → post: total idéntico, 0 filas con `nombre` NULL entre las que tenían
`nombre_completo`, y muestreo de 20 filas al azar más los casos raros (un solo apellido, apellidos
compuestos, nombres con partícula). Reporta los números antes/después, no "parece correcto".

### User: "unificamos la base de clientes de las dos marcas"
TL: caso de máximo riesgo. Checksums y sumas por marca **antes**, en las dos bases; después:
`total_destino = total_a + total_b − duplicados_esperados` (número declarado antes de migrar),
0 huérfanos, la query de duplicados por email revisada una a una, y muestreo obligatorio de las dos
procedencias. Sin la reversa probada en staging, no se toca producción.

## Related

- `pilar-impacto-produccion` (agente) — clasifica cada migración del diff
  (`scripts/clasificar_migraciones.py`) y mide el comportamiento antes/después; me invoca para las
  `data-migration`. Yo compruebo los datos fila a fila; ella, qué ve cada cliente

- `rules/governance.md` — qué migraciones necesitan aprobación (esta skill es el **cómo** verificar)
- `rules/verification.md` — el `exit 1` del command es un gate de nivel 3
- `rules/verdict-contract.md` — formato del veredicto al reportar el resultado
- `django-orm` (skill, `references/optimization.md`) — rendimiento e índices
- `priya-privacy-auditor` (agente) — si la migración toca PII o borrado (soft delete vs GDPR)
- `rules/verification.md` §Smoke testing — tras verificar los datos, que la app siga viva
