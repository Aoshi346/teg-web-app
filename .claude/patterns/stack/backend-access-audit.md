# Auditoría de accesos en Django — quién leyó qué de quién, sin que nadie pueda reescribirlo

> **Cuándo aplicar:** en todo proyecto Django que trate datos personales de terceros y tenga que
> poder contestar «¿quién ha visto lo mío?» (art. 15 RGPD), y siempre con datos de salud (EEDS
> art. 9, ENS op.exp.8 si el cliente es sector público). Desde el primer modelo con datos de
> personas, no al final: añadirlo después deja un hueco que no se rellena.
>
> **NO aplicar:** para el historial de versiones del dato (`django-simple-history`, pghistory): ese
> guarda valores y vive con el dato, este guarda referencias y vive aparte (§1) · para los logs
> operativos (gunicorn, celery) ni para las trazas del LLM (`agente-observabilidad.md`) · para decidir
> el plazo de conservación, que firma el responsable con su DPD
> (`templates/cumplimiento-salud/registro-accesos.md`).
>
> **Relacionado:** `webapps/django-audit-trail/` (el paquete que lo instala en una app: §3 hecho
> librería) · `templates/access-audit/` (`schema.sql` y `chain.py`, lo que se copia) ·
> `smoke/harvest/access_audit.py` (la prueba contra un PostgreSQL desechable) ·
> `templates/cumplimiento-salud/registro-accesos.md` (la ficha que firma el DPD; su §Integridad es
> esto) · `scripts/check_pii_logs.py` (lo que nunca debe entrar) · `backend-observabilidad.md`.

## La regla (una frase)

**Cada acceso a un dato de una persona deja una fila con quién, cuándo, qué apartado y qué acción
—lecturas incluidas, valores nunca—, en una tabla donde la app solo puede insertar y cada fila
encadena con la anterior, con la cabeza de cada día publicada fuera del servidor.**

## 1. La ficha mínima — una fila sirve al ENS, al EEDS y al art. 15 a la vez

| Columna | Qué lleva | Por qué |
|---|---|---|
| `actor_id`, `actor_role` | Usuario **nominal** y su rol en ese momento. Nunca una cuenta compartida | Sin persona no se puede decir quién leyó |
| `ts` | Lo pone **el servidor de base de datos** (el trigger ignora lo que mande la app), con el reloj sincronizado y autenticado (chrony con NTS) | Una app con el reloj mal no fabrica coartadas |
| `subject_ref` | Seudónimo `HMAC(clave, id)` (`chain.pseudonym`). **Nunca** un hash sin clave | Con la clave se extrae por persona; sin ella el registro no identifica a nadie |
| `resource`, `fields` | Modelo#pk o apartado, y los **nombres** de los campos | «Sobre qué información» (op.exp.8.1), sin copiar la información |
| `action`, `result` | `read` · `create` · `update` · `delete` · `export`; `allowed` / `denied` | Las lecturas son lo que pregunta la persona; los denegados, lo que mira quien investiga |
| `reason`, `context` | Motivo si no hay vínculo asistencial u organizativo; tenant, sesión hasheada, IP truncada | Para revisar después, sin datos de más |
| `segment`, `seq`, `prev_hash`, `hash` | Los pone el trigger (§2) | La integridad |

**Nunca entra:** el valor de un campo, `str(instance)` (lleva nombres), el cuerpo de un POST. Es el
agujero clásico: se redacta al **mostrar** y el dato ya está guardado, replicado y en los backups.
La redacción es en origen y por **lista blanca**: lo que no está en la ficha no se escribe.

## 2. Tres barreras, de menos a más coste — y lo que para cada una

| Barrera | Qué hace (`schema.sql`) | La para | No la para |
|---|---|---|---|
| **Solo INSERT** | La app (`app_user`) tiene `INSERT, SELECT` y nada más; un trigger rechaza `UPDATE`, `DELETE` y `TRUNCATE` aunque alguien conceda el permiso por error. Solo `audit_purger` borra; que sean segmentos enteros caducados lo garantiza su tarea de purga, no el trigger (un borrado parcial lo caza el ancla) | La app comprometida, el ORM mal usado, el `UPDATE` de un desarrollador | A quien es dueño de la tabla: puede desactivar el trigger |
| **Cadena por segmento** | `hash = sha256(prev_hash ‖ forma canónica)`, una cadena por día UTC (`segment`, `seq`), con candado por segmento para que dos inserciones no lean la misma cabeza | Al que cambia una fila y no recalcula | Al que recalcula la cadena entera |
| **Ancla externa** | La cabeza de cada segmento (`chain.py heads`) se publica **fuera del servidor**: un repo git aparte, un correo o un Telegram al responsable, un sello RFC 3161 | Al que recalcula todo: su cabeza ya no casa con la publicada | Nada razonable por debajo de ENS ALTO |

**Por qué segmentos y no una cadena única:** la purga por plazo (RGPD 5.1.e) borra **días enteros
caducados** sin romper la verificación de los vigentes. Una cadena única obliga a elegir entre
conservar de más o no poder verificar.

**Lo que no se usa, y por qué:** árboles de Merkle y sellos cualificados eIDAS, solo en ENS ALTO;
immudb es BSL 1.1 desde la 1.9; Trillian está en mantenimiento.

## 3. En Django

**Con el paquete `webapps/django-audit-trail/` (4.13) esto viene hecho**, con redacción por lista
blanca, decorador y mixin de lectura, escrituras por modelo registrado y los comandos del §4. Lo de
abajo es lo que hace por dentro, para quien no pueda instalarlo.

El modelo se declara **sin gestionar** (la tabla la crea el SQL, con sus triggers y permisos) y se
escribe con un único punto de entrada:

```python
# apps/audit/models.py
class AccessEvent(models.Model):
    ts = models.DateTimeField()
    actor_id = models.TextField()
    actor_role = models.TextField()
    subject_ref = models.TextField()
    resource = models.TextField()
    fields = models.TextField(default="")
    action = models.TextField()
    result = models.TextField()
    reason = models.TextField(default="")
    context = models.TextField(default="")

    class Meta:
        managed = False
        db_table = "access_event"


# apps/audit/services.py — el ÚNICO sitio que escribe; se llama desde la vista, no desde una señal
def record_access(*, user, subject_id, resource: str, fields: list[str], action: str,
                  allowed: bool, reason: str = "", tenant: str = "") -> None:
    AccessEvent.objects.create(
        ts=timezone.now(),  # lo sustituye el trigger
        actor_id=f"user:{user.pk}", actor_role=current_role(user),
        subject_ref=pseudonym(settings.AUDIT_HMAC_KEY, subject_id),
        resource=resource, fields=",".join(sorted(fields)),
        action=action, result="allowed" if allowed else "denied",
        reason=reason, context=f"tenant:{tenant}" if tenant else "",
    )
```

```python
# apps/audit/migrations/0001_access_event.py
SQL = (Path(__file__).resolve().parent / "access_event.sql").read_text()  # copia de schema.sql

class Migration(migrations.Migration):
    operations = [migrations.RunSQL(SQL, reverse_sql=migrations.RunSQL.noop)]
```

- La migración corre con el rol **dueño** (`audit_owner`); Django se conecta en producción con
  `app_user`. Si las dos cosas son el mismo usuario de base de datos, la barrera 1 no existe.
- **Lecturas desde la vista**, no desde señales: una señal no ve los GET, y las lecturas son la mitad
  que importa. Middleware solo si la ruta dice el apartado sin ambigüedad.
- `AUDIT_HMAC_KEY` sale del entorno y **no** es la `SECRET_KEY`: rotar una no debe romper la otra.
- Los tests de la app no necesitan PostgreSQL para esto: el servicio se prueba con un doble; el
  esquema, con la prueba de §5.

## 4. Verificar y anclar — tarea programada, no buena intención

```bash
psql -At -c "$(python3 chain.py export-sql)" > eventos.jsonl
python3 chain.py verify eventos.jsonl --anchors anclas.json   # exit 1 si algo no casa
python3 chain.py heads eventos.jsonl > anclas-hoy.json         # y se publica FUERA del servidor
```

Al cerrar cada día (cron o Celery beat): verificar contra el ancla de ayer, sacar las cabezas y
publicarlas. Un fallo de verificación es un **incidente** (skill `incident-review`), no un aviso.

## 5. La prueba — qué tiene que fallar

`python3 .claude/smoke/harvest/access_audit.py` (PostgreSQL 17 desechable, sin puertos publicados):

| Caso | Esperado |
|---|---|
| `UPDATE` / `DELETE` / `TRUNCATE` como `app_user` | falla |
| `UPDATE` con el permiso concedido por error | falla (lo para el trigger) |
| La cadena intacta (control) | verifica |
| El DBA desactiva el trigger y cambia `actor_id` de una fila | `verify` señala esa fila |
| El DBA además recalcula la cadena entera | `verify` sin ancla pasa; **con ancla, falla** |
| Sabotaje: sin el trigger de inmutabilidad | el `UPDATE` con permiso pasa (la prueba distingue) |

## Anti-patterns

- ❌ Guardar el valor «para poder enseñarlo luego» → eso es el historial de versiones, en otro sitio.
- ❌ `str(instance)` o `repr` en el log → lleva el nombre de la persona.
- ❌ Hash del id sin clave como seudónimo → se revierte por fuerza bruta.
- ❌ La app conectada con el rol dueño de la tabla → la barrera 1 es decorativa.
- ❌ Cadena sin ancla externa → no prueba nada frente a quien administra la base.
- ❌ Una sola cadena para siempre → la purga por plazo la rompe.
