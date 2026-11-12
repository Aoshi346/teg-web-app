# Modelos y migraciones — patrón de casa

> **Cuándo aplicar:** al crear o modificar cualquier modelo, y en toda migración de datos.
> **Verificado contra la doc oficial de Django 5.2** el 2026-08-08.

## La regla (una frase)

**El esquema declara sus invariantes en la base de datos (constraints, índices, tipos exactos), y
toda migración de datos sabe deshacerse.**

Por qué esta y no "escribe modelos limpios": el modelo es la única capa cuyos errores **no se
arreglan con un deploy**. Una vista mala se reescribe; una columna con el tipo equivocado ya tiene
diez millones de filas dentro. Y una validación que solo vive en Python no protege de nada al
script de importación, al `manage.py shell` ni al backfill de la migración de al lado.

## Dónde viven las opciones — `choices.py`, y por qué no dentro del modelo

Un campo con opciones cerradas (estado, tipo, canal) las declara en **`<app>/choices.py`**, no en el
cuerpo del modelo. El motivo no es estético: esas mismas opciones las necesitan **el serializer**
(para validar), **el frontend** (para pintar el desplegable) y **los tests** (para no escribir la
cadena a mano). Declaradas dentro del modelo, o se importa el modelo entero desde sitios que no
deberían, o se acaban duplicando en tres ficheros y divergiendo en el cuarto.

```python
# apps/pedidos/choices.py — una clase por conjunto, con TextChoices
from django.db import models

class EstadoPedido(models.TextChoices):
    BORRADOR   = "borrador",   "Borrador"
    CONFIRMADO = "confirmado", "Confirmado"
    ENVIADO    = "enviado",    "Enviado"
    ANULADO    = "anulado",    "Anulado"
```

```python
# apps/pedidos/models/pedido.py — el modelo IMPORTA, no declara
from apps.pedidos.choices import EstadoPedido

class Pedido(BaseModel):
    estado = models.CharField(max_length=20, choices=EstadoPedido.choices,
                              default=EstadoPedido.BORRADOR)
```

**`TextChoices` y no una lista de tuplas**, por tres cosas concretas: el valor se referencia como
`EstadoPedido.ENVIADO` (y un typo revienta al importar, no en producción), la etiqueta viaja sola al
serializer y al admin, y `get_estado_display()` funciona sin escribir nada.

> **Y el que expone las opciones al frontend es un endpoint, no un fichero copiado.** Si React tiene
> su propia lista de estados en TypeScript, hay dos verdades y una de ellas se quedará vieja: la
> forma que aguanta es que el backend las sirva (`/api/opciones/` o dentro del propio serializer) y
> el frontend las pinte. Es el mismo criterio de `frontend-contrato-con-el-backend.md`.

**Dónde NO van:** en `models.py` mezcladas con los campos · en `constants.py` junto a cosas que no
son opciones de un campo · en el frontend como fuente de verdad · repetidas en el serializer.

## Implementación de referencia

`_fixtures/conforme/apps/facturacion/models.py`:

```python
class Factura(models.Model):
    class Estado(models.TextChoices):
        BORRADOR = "borrador", "Borrador"
        EMITIDA = "emitida", "Emitida"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cliente = models.ForeignKey(
        "clientes.Cliente",
        on_delete=models.PROTECT,          # una factura emitida sobrevive al borrado del cliente
        related_name="facturas",
    )
    numero = models.CharField(max_length=32, unique=True)
    concepto = models.CharField(max_length=200, blank=True, default="")
    importe = models.DecimalField(max_digits=12, decimal_places=2,
                                  validators=[MinValueValidator(Decimal("0.00"))])
    estado = models.CharField(max_length=16, choices=Estado.choices, default=Estado.BORRADOR)
    creada_en = models.DateTimeField(auto_now_add=True)
    actualizada_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-creada_en"]
        indexes = [
            models.Index(fields=["cliente", "-creada_en"], name="factura_cliente_fecha_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(importe__gte=Decimal("0.00")),
                name="factura_importe_no_negativo",
                violation_error_message="El importe de una factura no puede ser negativo.",
            ),
            models.UniqueConstraint(
                fields=["cliente", "numero"],
                condition=~Q(estado="borrador"),
                name="factura_numero_unico_por_cliente_emitida",
            ),
        ]
```

Y la migración de datos (`_fixtures/conforme/apps/facturacion/migrations/0002_backfill_numero.py`):

```python
def rellenar_numero(apps, schema_editor): ...
def vaciar_numero(apps, schema_editor): ...

operations = [migrations.RunPython(rellenar_numero, vaciar_numero)]
```

Notas que sostienen las decisiones:

- **`condition=`, no `check=`.** El argumento `check` de `CheckConstraint` está **deprecado desde
  Django 5.1** —emite un warning, sigue funcionando— y la página de deprecaciones de la doc oficial
  lo retira en **6.0**. En 5.1/5.2 el código con `check=` corre; en código nuevo se escribe
  `condition=`. Es el error más probable de un agente que escribe de memoria, porque `check=` fue
  lo correcto durante cinco versiones.

  > ⚠️ **Corrección de un error de hecho de este mismo documento** (EVO-10, 2026-08-08). Hasta hoy
  > esta línea decía *"Django 5.1 **eliminó** el argumento"*. Es falso: la lista de *features
  > removed in 5.1* de la doc oficial no lo incluye, y la de retirada está fechada en 6.0. La
  > diferencia no es un matiz: con la versión anterior, un agente que revisara un proyecto en
  > Django 5.2 reportaría como roto un código que funciona, y alguien perdería media mañana
  > persiguiendo un problema inexistente. Un dato falso en el patrón se propaga a cada revisión.
- **`on_delete` es una decisión de negocio, no un trámite.** `PROTECT` en una factura es
  deliberado: borrar un cliente no puede evaporar su historial contable. `CASCADE` por defecto en
  todas las FK es cómo se pierden datos sin que salte ningún error.
- **`related_name` siempre.** Sin él Django inventa `factura_set`, que no aparece en ninguna
  búsqueda de texto: renombrar el modelo rompe queries en silencio.
- **`Decimal` para dinero.** `FloatField` no representa `0.10`; los totales se desvían céntimo a
  céntimo y el error aparece en la suma del mes, lejos de su causa.
- **`blank=True, default=""` en vez de `null=True`.** Un campo de texto con `null=True` tiene dos
  estados vacíos (`''` y `NULL`) y cada query tiene que comprobar los dos; el día que alguien
  olvide uno, la fila desaparece del listado. Es la recomendación de la propia doc de Django.

## De qué HEREDA un modelo — la decisión que este documento no cubría

Todo lo de arriba va campo a campo. En un proyecto de cientos de modelos, **de qué heredan
determina el día a día mucho más que cualquier `CheckConstraint`** — y hasta ahora este documento
no decía nada al respecto. Es el hueco que cierra REF-3, y la fuente es un backend Django real:
**316 modelos heredan la rama CRUD de casa y 300 de ellos arrastran historial** (y, del recuento
anterior, 357 de 360 declaran el mismo `Meta`). Una consistencia así no se consigue pidiéndola en
una guía de estilo; se consigue heredándola.

La cifra se mide, no se recuerda. Así se sacó — 2026-08-24, 894 ficheros `.py`; `grep` y un recuento
por AST hechos por separado coinciden exactamente en las once bases contadas:

```bash
cd <raíz del backend>
for base in CRUDModel HistoricalCRUDModel OrderMixin IntCodeMixin ActiveMixin \
            FixtureMixin NamedMixin SignatureMixin; do
  grep -rEc "^class \w+\(.*\b${base}\b.*\):" --include=*.py . | awk -F: '{s+=$2} END {print s+0}'
done
# HistoricalCRUDModel 300 · IntCodeMixin 275 · NamedMixin 197 · ActiveMixin 119 · FixtureMixin 87
# CRUDModel directo, sin historial 16   →   rama CRUD completa: 300 + 16 = 316
# (el \b protege: "\bCRUDModel\b" NO casa dentro de "HistoricalCRUDModel", así que no hay doble conteo)
```

El mismo recuento dos semanas antes daba 294 · 271 · 195 · 118. Que se mueva +6/+4/+2/+1 y ni una
proporción cambie es la mejor prueba de que la cifra mide algo real: los patrones siguen igual, lo
que ha crecido es el proyecto.

> ⚠️ **Lo que cuesta ese 300, y no se ve en ninguna review:** heredar historial no es "un mixin
> más" — es **una fila de auditoría por cada escritura en 300 modelos**. Y en el backend de
> referencia esa fila **no se escribe dentro de la transacción**: el `HistoricalRecords` de casa
> sobrescribe `create_historical_record` y la encola en Celery. Consecuencia: **si el worker de esa
> cola está caído, la escritura de negocio va bien y el historial se pierde sin un solo error
> visible.** En un producto cuyo valor *es* el registro auditable, ese es un modo de fallo de primer
> orden, y el síntoma llega meses después — cuando alguien busca quién cambió qué y no hay fila. Si
> el historial es asíncrono, esa cola se monitoriza como se monitoriza la base de datos. (Mismo
> agujero por otra vía, y también real: allí los cambios de **M2M** no se registran, con el `TODO`
> abierto en el propio fichero.)

Implementación de referencia: `_fixtures/conforme-casa/core/models.py`.

```python
class MetaDeCasa:
    """Registro de metadatos del modelo. Aquí, los permisos de casa."""
    default_permissions = ("add", "change", "delete", "view", "relate")


class CRUDModel(models.Model):
    """Auditoría y propiedad. Todo modelo de dominio hereda de aquí."""
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
                              related_name="%(class)s_en_propiedad")
    created_by = models.ForeignKey(..., related_name="%(class)s_creados")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta(MetaDeCasa):
        abstract = True
```

Y un modelo de app:

```python
class Expediente(CRUDModel, CodigoVisibleMixin):
    ...
    class Meta(MetaDeCasa):
        constraints = [...]
```

**Por qué esto y no repetir los campos:**

- **El `owner` de la base ES el mecanismo de seguridad.** El filtrado por usuario filtra por ese
  campo. Un modelo que no hereda la base no es que se le olvide el filtro: es que para él **el
  filtro no puede existir**. La decisión de base deja de ser estética en cuanto se mira así.
- **El `Meta` compartido no es solo config del ORM: es un registro.** Ahí caben los permisos de
  casa, y en proyectos con framework CRUD propio también el `slug` que da la URL, el icono y la
  etiqueta de menú — todo derivado de una sola declaración.
- **El quinto permiso.** Django trae `add/change/delete/view`. En un dominio con muchos M2M,
  *"puedo ver X"* y *"puedo asociarle Y"* son permisos distintos, y por eso la base de casa añade
  `relate`. Es un ejemplo, no una obligación: lo obligatorio es que **haya un sitio único** donde
  se declare qué permisos tiene todo modelo.

> ⚠️ **El agravante que hace que esta regla sea `activo` y no un consejo:** Django crea los
> permisos por defecto **al migrar**. Un modelo cuyo `Meta` no herede la base no falla, no avisa y
> no aparece en ningún log — simplemente su permiso `relate_<modelo>` no existe. Y **arreglar la
> herencia después NO crea el permiso que faltó**: hace falta un paso explícito
> (`manage.py createpermissions` de `django-extensions`, o una migración de datos). En el backend
> de referencia eran 8 modelos, y el síntoma que llegó fue "este usuario no puede hacer algo que
> debería poder", meses después.

**Un matiz sobre la referencia, para no copiar lo raro con lo bueno:** allí la base del `Meta`
heredaba de `ModelBase` (la metaclase de Django) y **nunca se usaba como `metaclass=`** — verificado,
cero apariciones. Heredar de la metaclase no aportaba nada y confundía a quien leía el código. Un
mixin plano hace exactamente el mismo trabajo, y es lo que recoge el fixture.

**Cuándo NO aplican estas dos reglas:** en un proyecto nuevo no hay ninguna base compartida, y el
checker no la inventa — las dos reglas están **gateadas por descubrimiento**: si no encuentra una
base de modelo abstracta en un módulo compartido (`core/`, `common/`, `shared/`…), no disparan. Es
la misma decisión que ya tomaba `be-form-base-de-casa`, y por la misma razón: acusar a un proyecto
de no seguir un patrón que todavía no tiene sería el peor falso positivo posible.

## Credenciales y caducidad de cuenta: se extiende `AbstractUser`, no se inventa un `Login`

Es la decisión que más veces se toma mal al describir un backend **de memoria** en vez de leyéndolo
—un modelo `Login` con `login_attempts`, `is_locked`, `password_reset_token`… es lo que sale de
escribir "autenticación segura" sin abrir el fichero— y en el backend de referencia está tomada
bien. Tres reglas, y las tres van contra el impulso de crear una tabla nueva:

- **No hay modelo `Login`.** Las credenciales viven en el `User` del proyecto (`AbstractUser` más la
  base de casa) y lo que se añade son **campos**, no una tabla paralela. Un modelo de sesión aparte
  duplica la identidad y obliga a mantener a mano dos filas que Django ya mantiene en una.
- **Los tokens de reseteo NO se guardan en columnas.** Django los firma (`default_token_generator`) y
  la caducidad la fija el ajuste `PASSWORD_RESET_TIMEOUT`: sin estado, sin tabla y sin limpieza de
  tokens muertos. Un campo `password_reset_token` es *peor* diseño, no mejor. ⚠️ Con una
  contrapartida que hay que decir: **si `PASSWORD_RESET_TIMEOUT` no se declara en `settings.py` se
  corre con el default de Django y nadie ha decidido nada** — que es el caso del backend de
  referencia. Decláralo, aunque sea con el mismo valor: una caducidad heredada por descuido no es
  una política.
- **La caducidad de contraseña sí son campos**, y son tres: si esa cuenta caduca, cada cuántos días,
  y cuándo se cambió la última vez. Más un punto de comprobación en el login que redirige al cambio,
  y un historial de hashes previos para impedir la reutilización.

El tercer punto es el que conecta con `be-model-caducidad-no-comprobada` (más abajo): un campo de
caducidad **sin ese punto de comprobación** no es una política de seguridad, es una columna.

## `bulk_create` y las invariantes que viven en `save()`

```python
class CodigoVisibleMixin(models.Model):
    codigo = models.CharField(max_length=32, unique=True, null=True, blank=True)

    class Meta(MetaDeCasa):
        abstract = True

    def save(self, *args, **kwargs):
        if not self.codigo:
            self.codigo = f"{self._meta.model_name.upper()[:3]}-{self.pk or 'NUEVO'}"
        super().save(*args, **kwargs)
```

`bulk_create()` **no llama a `save()`** ni emite `post_save`. No es teoría: en el backend de
referencia hay filas en producción con ese código a **NULL** y **sin fila de historial**, en un
sistema cuyo producto *es* el registro auditable. Nadie protestó, porque el campo admite nulos y
PostgreSQL acepta N nulos en una columna única. El daño apareció al buscar por un código que no
existía.

La regla no prohíbe `bulk_create` — prohíbe usarlo **por descuido** sobre un modelo cuyo `save()`
calcula algo. Dos salidas, las dos explícitas:

```python
# a) rellenar después de la inserción
creados = Expediente.objects.bulk_create(objetos)
Expediente.objects.filter(pk__in=[o.pk for o in creados], codigo__isnull=True).update(...)

# b) declarar por qué aquí da igual
# no-bulk: el código lo asigna el proveedor externo en el fichero de entrada
Expediente.objects.bulk_create(objetos)
```

**Alcance calibrado con la medida, no a ojo:** solo `bulk_create`, y **fuera de `scripts/` y
`management/`**. Incluir `.update()` subía de 7 hallazgos a 43, y el 84% eran mantenimiento
legítimo — justo el punto en el que la regla de inversión dice que la mala es la regla.

## El nombre de una tabla no se escribe a mano — `RunSQL` y el trigger que tumbó otra app

Una migración creaba un trigger con SQL crudo sobre `audit_event`, escrito a mano. Django, sin
`db_table` en el modelo, había llamado a esa tabla `audit_auditevent`. La migración falla con
`relation "audit_event" does not exist` — y **se lleva por delante los tests de `customers`**, una
app que no tocaba nada de eso: la suite construye la base de test aplicando **todas** las
migraciones, así que una rota ahí abajo no hunde su app, hunde la base entera. Por eso el error
aparece donde nadie ha cambiado nada, que es la peor forma de perder una mañana.

Lo grave no es el typo: es que **no hubo señal**. `manage.py check` decía *no issues* y
`makemigrations --check` decía *No changes detected*. Los dos verdes, y con razón: los dos leen los
**modelos en Python**, y el nombre equivocado vivía dentro de una cadena de SQL que nadie ejecuta
hasta que la migración corre contra una base de datos de verdad.

```python
def _crear_trigger(apps, schema_editor):
    # apps.get_model, no un import: la migración tiene que seguir corriendo dentro de un año.
    # Y el nombre sale del esquema, así que sigue al modelo si alguien lo renombra.
    tabla = apps.get_model("audit", "AuditEvent")._meta.db_table     # → audit_auditevent
    schema_editor.execute(f'CREATE TRIGGER … ON {tabla} …')
```

La interpolación en `f''` no es una inyección y **no se "arregla" con un parámetro** —un
identificador no se puede parametrizar—: lo que la hace segura es que el valor venga de `_meta`.

Y si el nombre de la tabla **es parte de un contrato** —hay un ETL, un informe o SQL fuera de Django
que la nombra—, entonces se **declara** en el `Meta` con el porqué al lado
(`db_table = "audit_event"  # el ETL nocturno de BI lee esta tabla por su nombre`), en vez de
dejarlo al azar de cómo Django concatene `app_label` y nombre de clase.

**Cómo se buscan los que ya hay.** Es una lista para revisar, no un veredicto: hay SQL crudo que no
nombra ninguna tabla (`CREATE EXTENSION`, un `SET`) y sale igual.

```bash
# ficheros con SQL crudo que NUNCA derivan el nombre de tabla del modelo
grep -rl -E "RunSQL|schema_editor\.execute" --include=*.py . | xargs -r grep -L "_meta.db_table"
```

(No se ha medido cuántos casos así hay en los proyectos de casa: el incidente documentado es **uno**.
La regla no se sostiene en una frecuencia, sino en que el fallo **no tiene señal** hasta que rompe.)

## Índices vectoriales: se mide antes de indexar

Un frente de catálogo **no construyó** el índice HNSW de pgvector, y la decisión se sostiene en una
medición y no en una opinión: con **100.000 filas y 10.000 por inquilino**, la ganancia era **1,0×**
y el coste **781 MB**.

El porqué es arquitectónico, y es lo que hay que entender antes de copiar la decisión: la consulta
filtra **primero** por `tenant_id`. El planificador se queda con las 10.000 filas de ese inquilino y
el índice global no tiene ocasión de ahorrar nada. Peor: con filtro, HNSW recorre el grafo de
**todos** los inquilinos y descarta después — que es exactamente el mecanismo por el que se acaba
devolviendo **menos resultados de los pedidos**, el clásico "pedí 10 y me devuelve 3".

La decisión no es para siempre. Se vuelve a medir cuando pase **cualquiera** de estas tres:

| Se remide cuando… | El número | Por qué cambia la respuesta |
|---|---|---|
| **Un solo inquilino** pasa de ~100.000 filas | 10× lo medido | El barrido deja de ser trivial: lo que hoy es un `Seq Scan` de milisegundos sobre 10.000 filas pasa a ser el coste dominante |
| Aparece una consulta que **no filtra por inquilino** | basta **una** en producción | El índice recupera su razón de ser: sin filtro, recorrer el grafo entero es lo que se quiere, no lo que se desperdicia |
| La latencia **p95 medida** de la consulta real cruza el presupuesto del producto | el que esté declarado (una búsqueda interactiva suele vivir en la franja de 200 ms) | Si no hay presupuesto declarado, se declara **antes** de discutir el índice: sin umbral, "va lento" no es medible y la discusión no se cierra nunca |

```sql
-- 1) ¿cuánto tarda HOY, con el filtro real y el inquilino grande? (no con uno de juguete)
EXPLAIN (ANALYZE, BUFFERS)
SELECT id FROM catalogo_item
 WHERE tenant_id = '<un inquilino real, del grande>'
 ORDER BY embedding <=> %(consulta)s::vector
 LIMIT 10;

-- 2) la distribución que decide todo: filas POR INQUILINO, no filas totales
SELECT tenant_id, count(*) FROM catalogo_item GROUP BY 1 ORDER BY 2 DESC LIMIT 5;

-- 3) el coste, medido DESPUÉS de crear el índice en una copia — nunca estimado
SELECT pg_size_pretty(pg_relation_size('catalogo_item_embedding_hnsw_idx'));
```

Dos cosas en el plan de (1): un `Seq Scan` sobre 10.000 filas que tarda milisegundos no es un
problema que resolver; y si el índice existe y **no** aparece en el plan, comprueba que el operador
de la consulta casa con el opclass con el que se construyó — un índice que nadie usa cuesta los
781 MB igual. Que además no son solo disco: si no cabe en memoria deja de ser rápido, y cada
escritura paga su mantenimiento.

Si algún día toca construirlo, la pregunta **no** es "qué `ef_search` pongo" —subirlo es pagar por
recorrer más para descartar más—, sino **cómo entra el filtro dentro del índice**: un índice parcial
por inquilino, o el barrido iterativo que ofrezca la versión de pgvector que uséis, comprobado
contra su doc y no de memoria.

> ⚠️ **El límite, dicho antes de que alguien cite esto como ley:** es **un** proyecto, **una**
> distribución (100k totales / 10k por inquilino) y **una** forma de consulta (filtrada por
> inquilino, top-k pequeño). No dice que HNSW no sirva: dice que **en esa forma** no pagaba. Con un
> inquilino de millones de filas o una búsqueda global se da la vuelta. Lo reutilizable son las tres
> condiciones y el comando, no la conclusión.

## El antipatrón que sustituye

`_fixtures/infractor/apps/facturacion/models.py` — cinco decisiones malas en once líneas:

```python
class Factura(models.Model):
    cliente = models.ForeignKey("clientes.Cliente", on_delete=models.CASCADE)  # sin related_name
    numero = models.CharField(max_length=32, null=True, blank=True)            # dos estados vacíos
    concepto = models.CharField(max_length=200, null=True)
    importe = models.FloatField(max_length=10, default=0.0)     # dinero en float, y max_length
    estado = models.CharField(max_length=16, default="borrador")               # sin choices

    class Meta:
        constraints = [
            models.CheckConstraint(check=Q(importe__gte=0), name="importe_no_negativo"),  # deprecado
        ]
```

**`FloatField(max_length=10)` merece su propia regla**, y es de las pocas con precisión medida del
100%: `max_length` **no significa nada** en un campo numérico — Django lo acepta y lo ignora. Que
esté ahí no es un error de comportamiento, es una **huella**: prueba que esa declaración se copió
de un `CharField` y que nadie la revisó. En el backend de referencia había 30 campos así, 0 falsos
positivos, y los 30 eran bases reguladoras de partes de accidente que se reportan a la autoridad
laboral. La detección cuesta un `grep`; la migración de esos 30 a `DecimalField` es otra
conversación, con migración de datos y plan de vuelta atrás, y **no se hace en bloque**.

Y su migración, irreversible:

```python
operations = [migrations.RunPython(rellenar)]   # sin inversa
```

Esa última línea es la que más caro sale y la que menos se ve en review: **una `RunPython` sin
inversa bloquea el rollback del deploy entero**, no solo el suyo. El día que la release de las 2 de
la madrugada haya que revertirla, `migrate <app> <anterior>` falla con
`IrreversibleError` y hay que improvisar SQL a mano en producción. Si de verdad no hay vuelta atrás
posible, se escribe `migrations.RunPython.noop` **a propósito** — que es una afirmación explícita
("revertir esto no restaura nada, y lo sabemos"), no un olvido.

**Y dos que no caben en ese fixture porque no son un campo, son una decisión:**

- ❌ **Escribir el nombre de una tabla a mano dentro de un `RunSQL`** → el día que no coincide, la
  migración no rompe su app: rompe la construcción de la base de test, y con ella los tests de quien
  pasaba por allí. Ni `manage.py check` ni `makemigrations --check` lo ven.
- ❌ **Crear un índice vectorial "porque hay embeddings"** → sin la distribución por inquilino
  medida, se paga el índice para una ganancia que puede ser 1,0×. Y con la consulta filtrada, encima,
  es el propio índice el que devuelve menos resultados de los pedidos.

## Cómo se comprueba

```bash
python3 .claude/patterns/stack/pattern_check_backend.py --rules be-model-checkconstraint-condition,\
be-model-related-name,be-model-null-en-texto,be-model-dinero-float,be-migracion-reversible

# y el gate que Django trae de casa — que no queden cambios de modelo sin migrar:
python manage.py makemigrations --check --dry-run
python manage.py check
```

⚠️ Esos dos gates leen **modelos en Python**: no miran dentro de un `RunSQL`. Salieron los dos verdes
sobre la migración que tumbó los tests de otra app (§`RunSQL`, arriba). El gate real de ese caso es
aplicar las migraciones sobre una base vacía — o sea, correr los tests.

| Regla | Estado | Qué detecta (AST) |
|---|---|---|
| `be-model-checkconstraint-condition` | activo | `CheckConstraint(check=...)` — deprecado en 5.1, se retira en 6.0 |
| `be-model-related-name` | activo | `ForeignKey`/`OneToOneField`/`ManyToManyField` sin `related_name` |
| `be-model-null-en-texto` | activo | `null=True` en `CharField`/`TextField`/`SlugField`/`EmailField`/`URLField`, salvo si el campo es `unique=True` |
| `be-model-dinero-float` | activo | `FloatField` asignado a un campo cuyo nombre suena a dinero (`importe`, `precio`, `total`, `amount`, `saldo`, y la jerga de nómina: `salario`, `subsidy`, `base_a`/`base_b`, `_br`) |
| `be-model-floatfield-max-length` | activo | `FloatField(max_length=…)` — argumento que el campo ignora; precisión medida del 100% |
| `be-migracion-reversible` | activo | `RunPython` con un solo argumento |
| `be-model-bulk-create-invariante` | activo | `bulk_create()` sobre un modelo cuyo `save()` asigna a `self.<campo>`; solo `bulk_create`, y no en `scripts/`/`management/` |
| `be-model-meta-base-de-casa` | activo | `class Meta:` sin base, en un proyecto que **ya tiene** una base de `Meta` compartida |
| `be-model-base-de-casa` | **débil** | modelo concreto que hereda de `models.Model` pelado, en un proyecto que **ya tiene** un modelo base abstracto compartido |
| `be-model-caducidad-no-comprobada` | **débil** | campo `expiration_date`/`valid_until`/`caduca_en`… declarado y **que no lee ninguna** vista, servicio, task ni middleware |

Las dos "de casa" son **débil/activo por una razón asimétrica**, y conviene entenderla:
`be-model-meta-base-de-casa` es `activo` porque su fallo es **silencioso e irreversible en el
tiempo** (el permiso que no se creó al migrar no aparece solo); `be-model-base-de-casa` es `débil`
porque hay modelos que legítimamente no llevan auditoría —tablas de enlace, catálogos de
referencia— y bloquear ahí marcaría código correcto.

`be-model-caducidad-no-comprobada` es **débil a propósito** y tiene un falso positivo conocido: en
un proyecto nuevo se escribe el modelo antes que la lógica de auth, así que durante un rato el
campo existe y no lo lee nadie *todavía*. Bloquear ahí sería absurdo. Lo que la regla caza es el
caso maduro: el campo lleva meses ahí, la interfaz lo deja editar y la autenticación solo mira
`activo`.

Lo que **no** se comprueba, y por qué: no hay regla que juzgue si `on_delete=CASCADE` es correcto,
ni si falta un índice. Ambas cosas dependen del dominio y de los datos reales; una regla mecánica
ahí generaría más ruido que valor (regla de inversión del README: si marcaría medio repo, la mala
es la regla). Para lo segundo existe la skill `django-orm` (`references/optimization.md`) y la medición con `EXPLAIN` — y el
§de índices vectoriales es el ejemplo caro de por qué ninguna regla mecánica puede decidirlo: allí
la respuesta medida fue **no** crear el índice.

**Y una que se propuso y se descartó, escrita aquí para no volver a proponerla** (2026-08-24):
detectar que un proyecto tiene login propio y **ningún** mecanismo de bloqueo por intentos fallidos.
Es tentadora porque en el backend de referencia habría disparado y habría acertado — no hay límite
de intentos, los fallos solo se registran en un log, y eso no es una regresión sino una funcionalidad
que nunca se construyó. Pero sería una regla que **juzga fuera de su dominio**: el bloqueo no vive en
los modelos, vive en un backend de autenticación, en un middleware, en una dependencia
(`django-axes`), en el proxy inverso, o en el proveedor de identidad cuando hay SSO — que es
precisamente lo que ese proyecto usa. Marcaría como infractor a todo el que lo resuelva bien pero en
otra capa. Su sitio es el checklist de un auditor humano (`code-review-gate`,
`sofia-pentester`): *«¿hay límite de intentos, y dónde vive?»*, donde «lo hace el IdP» es una
respuesta válida y un checker mecánico no puede aceptarla.

## Excepciones legítimas

- **`null=True` en un campo de texto `unique`**: PostgreSQL permite varios `NULL` en una columna
  única pero solo una cadena vacía. Si el campo es opcional y único (un NIF, un código externo),
  `null=True` es lo correcto — el checker ya lo exime automáticamente.
- **`FloatField` para magnitudes que sí son reales**: pesos, coordenadas, porcentajes de medición.
  El checker solo mira nombres de campo con semántica monetaria.
- **Migración genuinamente irreversible** (borrado de datos, colapso de columnas):

```python
# pattern-exempt: be-migracion-reversible — el backfill destruye el valor previo; revertir no lo restaura
migrations.RunPython(fusionar_direcciones, migrations.RunPython.noop)
```

- **Modelo sin auditoría a propósito** (tabla de enlace M2M explícita, catálogo de referencia
  cargado por fixture): `# pattern-exempt: be-model-base-de-casa — catálogo de solo lectura, sin dueño`.
- **`bulk_create` deliberado**: `# no-bulk: <razón>` en la línea anterior. Es un marcador propio de
  esta regla, además del `pattern-exempt` genérico, porque se escribe donde se toma la decisión.

## Related

- `backend-validacion.md` — **qué obligación tiene un escritor que NO es el formulario**: es la
  otra mitad de las constraints de este documento
- `backend-servicios.md` (las reglas de negocio no van en `save()`) ·
  `backend-serializers.md` (la validación de forma) · skills `django-orm` (`references/optimization.md`),
  `migration-integrity-checks` (comprobar que un backfill llegó íntegro)
- Doc oficial: <https://docs.djangoproject.com/en/5.2/ref/models/constraints/> ·
  deprecaciones 5.1: <https://docs.djangoproject.com/en/5.2/internals/deprecation/>

---

_2026-08-24 (T-060) — §"De qué HEREDA un modelo": los conteos pasan a los **medidos** sobre un
snapshot del backend de referencia (316 en la rama CRUD, 300 con historial), **con el comando que
los produjo**, y se añade el ⚠️ del historial asíncrono. Nueva §"Credenciales y caducidad de
cuenta". Queda escrito por qué se descartó la regla de bloqueo por intentos. Medición y veredicto
campo a campo: `_archive/2026-10-19/planes-ajenos/2026-08-24-evo-preven-modelos/VERIFICACION.md`._

_2026-08-25 — dos incidentes de un proyecto real, esta semana: §"El nombre de una tabla no se escribe
a mano" (un trigger en `RunSQL` contra una tabla mal nombrada que tumbó los tests de una app que no
tocaba nada, con `check` y `makemigrations --check` en verde) y §"Índices vectoriales" (781 MB por una
ganancia de 1,0×, con las tres condiciones bajo las que se revisa la decisión). **Ninguno de los dos
añade regla al checker**: el primero se busca con un `grep` y el segundo no es automatizable, y así se
dice en vez de fingir cobertura._
