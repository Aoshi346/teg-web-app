# Validación fuera del formulario — qué debe un escritor que NO es la puerta buena

> **Cuándo aplicar:** siempre que se escriba en la base de datos **sin pasar por el formulario ni
> por el serializer**: un `objects.create()` en un servicio, un `bulk_create`, un comando de
> gestión, un import masivo, una migración de datos, un `manage.py shell`.
>
> **NO aplicar:** para decidir cómo valida el formulario (`backend-formularios-django.md`) ni el
> serializer (`backend-serializers.md`). Esas puertas ya están cubiertas — este documento es sobre
> **las otras**.
>
> **Relacionado:** `backend-modelos.md` (§constraints y §de qué hereda un modelo — es la otra mitad
> de esta página) · `backend-servicios.md` · `backend-tests.md`.

## El hueco, dicho con la medida delante

En el backend Django de referencia el formulario base de casa es **excelente**: sanea el HTML de
todo campo de texto, aplica los campos de solo lectura del perfil y asigna el dueño de la fila. 346
de 385 clases de formulario heredan de él. Es el elemento más sano del proyecto.

Y es **la única puerta con validación**. En 342 modelos hay:

| Medida | Valor |
|---|---:|
| Constraints de base de datos (`CheckConstraint`/`UniqueConstraint`) | **0** |
| Llamadas a `full_clean()` en todo el repositorio | **0** |
| Campos con `choices=` que solo valida el formulario | 227 |
| `objects.create(` | 227 |
| `.update(` | 428 |
| Comandos de gestión | 64 |

Todo lo que entra por `create`, `update`, `bulk_create`, un comando o el `shell` entra **sin
verificar nada**.

## La regla (una frase)

**La invariante que nunca debe romperse vive en la base de datos; y todo escritor que no sea el
formulario valida explícitamente antes de guardar.**

### ⚠️ Dónde NO poner el arreglo

La tentación, en cuanto se ve la tabla de arriba, es **mover la validación del formulario al
modelo** — un `Model.clean()` gordo, por simetría. Eso rompería el elemento más sano del proyecto
a cambio de una coherencia teórica: el formulario seguiría siendo necesario (sanea HTML, aplica
perfiles, pone el dueño), y ahora habría dos sitios donde buscar por qué un dato se rechazó.

**Lo que falta no es cambiar la puerta buena: es poner cerradura en las otras.** Dos cerraduras
distintas, para dos problemas distintos:

| Cerradura | Qué protege | Quién la aplica |
|---|---|---|
| **Constraint en la base de datos** | La invariante que **nunca** puede romperse, venga el dato de donde venga | PostgreSQL. También al `manage.py shell` de dentro de seis meses, y también a la migración de datos |
| **`full_clean()` en el escritor** | Lo que depende de la lógica de Python: `choices`, `max_length`, validadores del campo, `clean()` del modelo | El código que escribe. Da un error legible, campo a campo |

No se sustituyen. La constraint te salva del descuido que nadie previó; el `full_clean()` te da el
mensaje que le puedes enseñar a una persona.

## Implementación de referencia

**(1) La invariante, en la base** — `_fixtures/conforme-casa/expedientes/models.py`:

```python
class Meta(MetaDeCasa):
    constraints = [
        # La misma regla que `choices`, pero en la puerta por la que entra TODO.
        models.CheckConstraint(condition=Q(estado__in=Estado.values),
                               name="expediente_estado_valido"),
        models.CheckConstraint(condition=Q(importe__gte=0),
                               name="expediente_importe_no_negativo"),
    ]
```

> El enum va **a nivel de módulo**, no anidado en el modelo: el cuerpo de `class Meta` no ve el
> espacio de nombres de la clase que lo contiene, así que un `Estado` anidado es inalcanzable desde
> la constraint. Con el enum fuera, la lista de valores válidos se escribe una vez y la usan el
> campo y la constraint.

**(2) El escritor que no es el formulario** —
`_fixtures/conforme-casa/expedientes/management/commands/importar_expedientes.py`:

```python
for numero, fila in enumerate(csv.DictReader(fichero), start=2):
    expediente = Expediente(referencia=fila["referencia"], estado=fila.get("estado", ...),
                            owner_id=opciones["owner_id"])
    try:
        expediente.full_clean()
    except ValidationError as exc:
        rechazadas += 1
        self.stderr.write(f"fila {numero}: {exc.message_dict}")
        continue
    expediente.save()
```

Fíjate en lo que hace con el error: **no aborta el import entero, dice qué fila y por qué**. Un
comando que revienta en la fila 4.000 sin decir cuál es un comando que nadie vuelve a usar.

**(3) El dueño de la fila, explícito** — `_fixtures/conforme-casa/expedientes/services.py`:

```python
expediente = Expediente.objects.create(
    referencia=referencia, ..., owner=usuario, created_by=usuario,
)
```

## Por qué el dueño merece su propia regla

`owner` no es un campo de auditoría más: **es por el que filtra el scoping por usuario**. Una fila
creada sin él existe en la base de datos y **no aparece en la pantalla de nadie** que no tenga
permiso de organización. No hay error, no hay log, no hay excepción — solo un registro invisible. El
síntoma que llega a soporte es *"se ha perdido lo que metí"*, que es el peor de todos porque no
apunta a ninguna causa.

Medida en la referencia: **199 de 227 `objects.create()` no asignan `owner`**, y el dueño se pobla
en **un solo sitio**: el `save()` del formulario base.

> **Y por eso esta regla es `débil` y está limitada a lo nuevo.** Con 199 de 227, activarla en
> bloque marcaría el 88% de las creaciones del proyecto, nadie miraría los avisos y la regla
> moriría en tres días. Es el caso de libro de la **regla de inversión** del README — con un
> matiz: aquí el hallazgo **sí** es cierto, lo que no era vivible era la regla. Por eso:
>
> - el checker corre por defecto **sobre los ficheros cambiados**, así que en el día a día solo ve
>   código nuevo, que es el alcance aprobado;
> - en un proyecto existente se siembra en `sombra`, se mide con `--all --json`, y lo preexistente
>   se congela como baseline (README §"Declarado, no medido");
> - la regla solo dispara si el proyecto **tiene** una base de modelo con campo de dueño. En un
>   proyecto nuevo sin esa base, no existe.

## El antipatrón que sustituye

`_fixtures/infractor-casa/`:

```python
# services.py — la fila nace huérfana e invisible
return Expediente.objects.create(referencia=referencia, titulo=titulo,
                                 responsable_id=responsable_id)

# management/commands/importar.py — sin full_clean, y el modelo sin constraints
for fila in csv.DictReader(fichero):
    Expediente.objects.create(referencia=fila["referencia"], estado=fila["estado"])
```

Ese `estado=fila["estado"]` acepta `"inventado"`, `""` o el nombre de la columna si el CSV venía
con cabecera duplicada. El campo tiene `choices`, y `choices` **no valida nada** en la base de
datos: es metadata para el formulario y el admin. Sin `full_clean()` y sin `CheckConstraint`, la
fila entra.

## Cómo se comprueba

```bash
python3 .claude/patterns/stack/pattern_check_backend.py --rules be-val-escritura-sin-full-clean,\
be-model-choices-sin-constraint,be-owner-create-sin-dueno
```

| Regla | Estado | Qué detecta (AST) |
|---|---|---|
| `be-val-escritura-sin-full-clean` | **débil** | fichero bajo `management/commands/` que llama a `save`/`create`/`bulk_create` y **no menciona `full_clean` en ningún sitio** |
| `be-model-choices-sin-constraint` | **sombra** | campo con `choices=` cuyo `Meta.constraints` no tiene ninguna `CheckConstraint` que lo nombre |
| `be-owner-create-sin-dueno` | **débil** | `Modelo.objects.create(...)` sin el kwarg del dueño, sobre un modelo que hereda la base de casa, fuera de `forms.py`/`serializers.py` |

**Los tres estados están elegidos, no puestos por defecto:**

- `be-model-choices-sin-constraint` es **sombra** —solo mide, no se imprime salvo con `--all`—
  porque en cualquier proyecto existente marcaría los cientos de campos con `choices` que ya hay.
  En sombra responde a la pregunta útil ("¿cuántas invariantes viven solo en el formulario?") sin
  fricción. Promoverla a `activo` es una decisión que se toma **con el número delante**, y en
  proyecto nuevo, donde el coste es cero.
- `be-val-escritura-sin-full-clean` está acotada a **comandos de gestión** a propósito. Es la
  población pequeña y bien definida de "escritores que no son la puerta buena". Extenderla a
  servicios y tasks marcaría medio backend y no distinguiría el `create()` de un objeto ya
  validado del que viene de un CSV.
- La comprobación de `full_clean` es **por fichero, no por llamada**: si el comando lo menciona una
  vez, la regla calla. Es un proxy tosco y deliberado —igual que el de idempotencia en
  `backend-celery.md`—: fuerza a que alguien haya *pensado* la validación de ese comando. Un proxy
  honesto vale más que una regla exacta que nadie puede ejecutar.

**Lo que NO se comprueba:** que la constraint sea *la correcta*, ni que el `full_clean()` esté en
la rama que de verdad guarda. Eso es criterio, y es el trabajo de Rita con los precedentes de este
documento.

## Excepciones legítimas

- **Comando que solo lee** (informes, exportaciones, comprobaciones): no escribe, la regla no lo
  mira.
- **Comando que escribe objetos ya validados** río arriba (los creó un servicio que sí validó):
  `# pattern-exempt: be-val-escritura-sin-full-clean — los objetos vienen validados de crear_lote()`.
- **Modelo sin dueño por diseño** (catálogo global, tabla de enlace): no hereda la base con `owner`,
  así que la regla no le aplica. Si hereda y aun así no procede:
  `# pattern-exempt: be-owner-create-sin-dueno — fila de sistema, sin usuario propietario`.
- **`choices` puramente presentacional** (un campo que la BD no debe restringir porque los valores
  cambian con el negocio y hay filas históricas con valores retirados): es un caso real, y por eso
  la regla vive en sombra.

## Related

- `backend-modelos.md` §"de qué hereda un modelo" y §constraints — la otra mitad exacta de esto
- `backend-formularios-django.md` (la puerta buena, y por qué NO se toca) ·
  `backend-serializers.md` (`read_only_fields`: el equivalente para la API)
- `backend-tests.md` (el test que demuestra que la constraint aplica aunque no pases por el form)
- skill `migration-integrity-checks` — comprobar que un backfill llegó íntegro
