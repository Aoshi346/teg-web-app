# Formularios Django — el arquetipo server-rendered · patrón de casa

> **Cuándo aplicar:** en un backend Django que **renderiza plantillas en el servidor**, donde la
> puerta de entrada de los datos es un `Form`/`ModelForm` y no un serializer. Es el otro arquetipo
> del patrón, a la par del de DRF — no una variante menor.
>
> **NO aplicar:** en un backend DRF. Allí manda `backend-serializers.md` y la mitad de API de
> `backend-vistas.md` §1. Los dos arquetipos pueden convivir en un mismo repo: lo que no puede es
> aplicarse el documento equivocado.
>
> **Relacionado:** `backend-vistas.md` §2 (la otra mitad del arquetipo: quién llama a este
> formulario y dónde se acota el queryset) · **`backend-controllers.md`** (el framework CRUD que
> consume estos formularios — §1 de aquí explica por qué eso cambia lo que `Meta` significa) ·
> `backend-modelos.md` · `backend-servicios.md`.

---

## 0. Lo medido — y las tres correcciones de partida

Medido con AST (`ast.ClassDef` con resolución **transitiva** de bases) sobre los **1.401 ficheros
`.py`** de `resources/code-refference/evo-preven-develop.zip` → `evopreven/`, Django 4.2 en
producción, 46 apps. La v1.0 de este documento traía cifras de un informe intermedio; tres no
reproducen, y **una de ellas cambia la regla central**:

| | v1.0 decía | Medido | Consecuencia |
|---|---:|---:|---|
| Clases de formulario | 385 | **401** (384 en `forms.py`) | Ajuste menor: 385 era el conteo de `forms.py`, no del repo |
| `Meta` que **enumeran** `fields` | «358 de 360 · 99,4% de disciplina» | **353 de 363 declaran `fields = []`** — una lista **VACÍA** | 🔴 **§1: la regla medía otra cosa.** `fields = []` no es una lista blanca: es "decide el controlador" |
| Formularios con gancho de validación | implícito: dominante | **35 de 401 · 8,7%** | 🔴 **§4: el formulario aquí NO es donde se valida.** Es donde se DECLARA |
| Formularios **sin ningún método** | — | **326 de 401 · 81,3%** | El formulario típico de este repo es `class X(ModelForm)` + `class Meta` y nada más |

El comando exacto, pegado para que se recompruebe sin reconstruirlo:

```python
# python3, desde la raíz del repo de referencia.
import ast, pathlib, collections
classes, allc = {}, []
def bn(n): return [b.id if isinstance(b, ast.Name) else b.attr if isinstance(b, ast.Attribute) else '' for b in n.bases]
for f in pathlib.Path('.').rglob('*.py'):
    try: t = ast.parse(f.read_text(errors='ignore'))
    except SyntaxError: continue
    for n in ast.walk(t):
        if isinstance(n, ast.ClassDef):
            classes.setdefault(n.name, []).append(bn(n)); allc.append((str(f), n, bn(n)))
ROOTS, memo = {'ModelForm', 'Form', 'DjangoModelForm'}, {}
def isform(name, d=0):
    if d > 12: return False
    if name in memo: return memo[name]
    if name in ROOTS: memo[name] = True; return True
    memo[name] = False
    r = any(isform(b, d + 1) for bs in classes.get(name, []) for b in bs)
    memo[name] = r; return r
forms = [(f, n) for f, n, bs in allc if any(isform(b) for b in bs)]
print('forms:', len(forms))                                              # -> 401
print('sin metodos:', sum(1 for _, n in forms
      if not [x for x in n.body if isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef))]))   # -> 326
c = collections.Counter()
for _, n in forms:
    for meta in [m for m in n.body if isinstance(m, ast.ClassDef) and m.name == 'Meta']:
        for st in meta.body:
            if isinstance(st, ast.Assign) and any(getattr(g, 'id', '') == 'fields' for g in st.targets):
                v = st.value
                c["'__all__'" if isinstance(v, ast.Constant) and v.value == '__all__'
                  else 'lista VACIA []' if isinstance(v, (ast.List, ast.Tuple)) and not v.elts
                  else 'lista con campos' if isinstance(v, (ast.List, ast.Tuple)) else 'otro'] += 1
print(c.most_common())   # -> [('lista VACIA []', 353), ('lista con campos', 9), ("'__all__'", 1)]
```

Reparto completo de las 401, para que se vea la forma:

| Medida | Valor |
|---|---:|
| Heredan (transitivamente) del `ModelForm` **de casa** (`core/forms.py:29`) | **361** |
| Heredan del `ModelForm` de **Django** directamente | **1** |
| Viven en `forms.py` | **384** (95,8%) · 7 en `views.py` · 6 · 3 · 1 en otros |
| `Meta.widgets` declarado | **240** (§6 — la convención que no estaba escrita) |
| `Meta.exclude` | **0** |
| `Meta.required` | 2 |
| `save()` · `clean()` · `__init__` · `clean_<campo>` | 45 · 24 · 20 · **11** |

> ⚠️ **Escalón: `sombra` para todo lo que este documento añade** (`patterns/README.md` §1, GAP-1):
> está medido en **un solo repo**. Las reglas `be-form-*` que ya existen en el catálogo se
> mantienen, pero §6 corrige lo que una de ellas afirma medir.

---

## 1. Por qué este arquetipo tiene documento propio

Un backend server-rendered no es "un DRF sin API". La diferencia no es de tecnología, es de **dónde
está la única puerta con validación**:

| | DRF | Server-rendered (este documento) |
|---|---|---|
| Puerta de entrada | `Serializer` | `ModelForm` |
| Contrato con el cliente | JSON + código HTTP | HTML + redirect |
| Quién pone el dueño de la fila | el servicio / `perform_create` | **el `save()` de la base de formulario** |
| Quién sanea el HTML | el frontend al pintar | **el `clean()` de la base de formulario** |
| Qué pasa si te saltas la puerta | el serializer no se ejecuta | **no se valida NADA** |

Esa última fila es la que manda, y está medida en §5: en el backend de referencia `full_clean()`
aparece **0 veces** y hay **0 constraints** en **431 modelos**, así que las **248** declaraciones de
`choices` las valida **únicamente** el `ModelForm`. Todo lo que entra por `objects.create()` (228
veces), `bulk_create()` (9) o un comando de `manage.py` entra sin verificar. El formulario no es una
capa de presentación aquí: **es la capa de integridad, y es la única**.

> Las cifras de modelos y `choices` que traía la v1.0 (342 y 227) no reproducen; las de arriba son
> AST para los modelos —resolviendo bases transitivamente desde `Model`— y `grep` sobre `models.py`
> para `choices`, que es una declaración de una línea y no necesita AST.

---

## 2. La regla (una frase)

**Todo formulario hereda de la base única del proyecto, y esa base es el sitio donde se sanea el
texto, se asigna el dueño y se aplican los campos de solo lectura** — para que nadie tenga que
acordarse de las tres cosas en cada uno de los 401 formularios. Medido: **361 de 401** heredan de
ella (`core/forms.py:29`), y solo **1** hereda del `ModelForm` de Django directamente.

---

## 3. La corrección grande: `Meta.fields` NO es la lista blanca

La v1.0 escribió aquí un corolario que sonaba bien y que **el código no sostiene**:

> ~~"`Meta.fields` se enumera siempre. Ni `'__all__'` ni `exclude`. Una lista blanca protege lo que~~
> ~~todavía no existe… 358 de 360 enumeran `fields` — un 99,4% de disciplina."~~

Lo que enumeran no son campos. **353 de los 363 `Meta` declaran `fields = []`: una lista vacía.**

```python
# campaigns/forms.py:29 — la forma dominante, 353 veces
class CampaignWorkerForm(ModelForm):
    class Meta:
        model = CampaignWorker
        fields = []
        widgets = {'worker': ModelSelect2AutoWidget(url='/query-autocomplete/workers/', add=False)}
```

Una lista vacía no protege nada ni publica nada: **es la declaración de que los campos los decide
otro.** Y ese otro es el controlador, que **subclasea el formulario en tiempo de ejecución y
sobrescribe su `Meta.fields`** (`controller/controllers.py:106-117`, literal):

```python
form_fields = self.get_form_fields(request, *args, **kwargs)      # = fieldsets - exclude_fields
if self.obj and self.request.method == 'POST':
    form_fields = form_fields - self.readonly_fields              # ← y esto sí es enforcement

class ControllerForm(self.form):
    readonly_fields = self.readonly_fields
    class Meta(self.form.Meta):
        fields = form_fields                                      # ← el Meta del form queda pisado

self.form = ControllerForm
```

Y `get_form_fields()` (`controller/controllers.py:489`) sale de los `fieldsets` del `*Settings`:

```python
def get_form_fields(self, *args, **kwargs):
    return self.get_fields_fieldsets(*args, **kwargs) - self.exclude_fields
```

### Qué cambia esto, en concreto

1. **Para todo formulario consumido por un controlador, `Meta.fields` es código muerto.** Se ejecuta
   al importar y se descarta en la primera petición. Medido: **310 `form = …` en los
   `controller_settings.py` y 98 en los `controllers.py`** — o sea, la vía dominante con diferencia.
2. **La lista blanca existe, pero está en otro fichero y es de otro documento.** Quien decide si un
   campo nuevo del modelo se vuelve editable es **`fieldsets` en el `*Settings`**
   (`backend-controllers.md` §2c). La propiedad de seguridad que la v1.0 atribuía a `Meta.fields`
   **sí se cumple** — `get_fields_fieldsets()` enumera desde `fieldsets`, así que un campo nuevo no
   aparece solo — pero la cumple otro mecanismo, en otro sitio, y con otro dueño.
3. **El único `'__all__'` del repo es INERTE.** Está en `campaigns/forms.py:20` (`CampaignForm`), y
   ese formulario lo consume `campaigns/controller_settings.py:7` (`form = CampaignForm`), registrado
   en `campaigns/controllers.py:6`. El controlador le pisa el `Meta`. Es decir: **el único hallazgo
   que `be-form-fields-enumerado` produce hoy sobre la referencia es un falso positivo** (§6).
4. **El `readonly_fields` sí es enforcement de verdad, y del bueno.** La línea
   `form_fields = form_fields - self.readonly_fields` en POST hace que un campo de solo lectura **no
   exista en el formulario** al guardar, así que no se puede enviar aunque se manipule el HTML. No es
   un `disabled` de adorno: es servidor. Se declara **106 veces** en los `controller_settings.py` (y
   solo 4 en `forms.py`), lo que confirma que la decisión vive en el `*Settings`.

**La regla honesta que sustituye al corolario**, y aplica a los dos casos:

> **Si el formulario lo consume un controlador, no enumeres campos en `Meta`: declara `fields = []` y
> pon la lista en `fieldsets`.** Si el formulario se instancia a mano (§4.2), entonces sí —
> `Meta.fields` es la única lista blanca que hay, y ahí `'__all__'` y `exclude` sí hacen daño.

Precedentes de la forma dominante: `campaigns/forms.py:29` · `websign/forms.py:7` ·
`health/laboratory_test/forms.py:208`. Del mecanismo: `controller/controllers.py:106` y `:489`.

---

## 4. Implementación de referencia

`_fixtures/conforme-plano/core/forms.py` (fichero completo, parseable y verificado en el
`--self-test`). Tres métodos, y ninguno es cosmético:

```python
class ModelForm(forms.ModelForm):
    def __init__(self, request=None, data=None, files=None, *args, **kwargs):
        self.request = request
        super().__init__(data, files, *args, **kwargs)
        self.set_readonly_fields()

    def clean(self):                      # 1. saneado central
        datos = super().clean()
        for nombre, valor in list(datos.items()):
            if isinstance(valor, str):
                datos[nombre] = bleach.clean(valor, tags=TAGS_PERMITIDOS,
                                             attributes=ATRIBUTOS_PERMITIDOS, strip=True)
        return datos

    def save(self, commit=True):          # 2. el dueño
        instancia = super().save(commit=False)
        if self.request is not None:
            if instancia.pk is None:
                instancia.created_by = instancia.owner = self.request.user
            instancia.updated_by = self.request.user
        if commit:
            instancia.save()
        return instancia
```

**1. `clean()` es la defensa XSS de todo el sistema, en un punto.** Pasa `bleach.clean()` con lista
blanca de tags y atributos por los **361** formularios que heredan de la base. Importa el contexto:
ese mismo repo tiene **561 usos de `|safe`** y **242 declaraciones de `RichTextField`**. Sin el saneado en la
entrada, cada uno de esos 561 sitios es una salida sin escapar.

> ⚠️ **Dos divergencias entre el fixture y el original — leídas, no supuestas.** El fixture de arriba
> es el que verifica el `--self-test` y enseña la forma; el código real (`core/forms.py:83-93` y
> `:100-106`) difiere en dos puntos que hay que conocer antes de copiar cualquiera de los dos:
>
> | | Fixture (arriba) | Original (`core/forms.py`) |
> |---|---|---|
> | Alcance del saneado | **todos** los campos de `cleaned_data` | **solo `self.changed_data`** (`:88`) — lo que no cambió en esta petición no se re-sanea |
> | Guarda de `request` en `save()` | `if self.request is not None:` | **no la tiene** (`:100-104`): `self.request.user` directo ⇒ `AttributeError` si se instancia sin `request` |
>
> La primera es defendible (no reescribe lo que el usuario no tocó, y ahorra trabajo) y a la vez es
> el sitio por donde entraría contenido guardado **antes** de que existiera el saneado: `bleach` solo
> pasa por lo que se edita. La segunda convierte "olvidé pasar el `request`" en una excepción
> ruidosa en lugar de en una fila sin dueño — es decir, **falla mejor que el fixture**, aunque el
> fixture parezca más prudente.
>
> Y la reversión de entidades de `:91` —`.replace('&amp;', '&').replace('&gt;', '>').replace('&lt;', '<')`
> justo después de sanear— es la que §8.2 marcaba como *"no se ha podido descartar leyendo código"*.
> **Ahora está localizada** (`core/forms.py:91`) y sigue **sin verificar en vivo**: qué hace ese `<`
> crudo al llegar a una plantilla con `|safe` no se decide leyendo, se decide ejecutando.

**2. `save()` es el único sitio del sistema donde se pobla `owner`.** Y `owner` es el campo por el
que el filtrado por usuario decide qué ve cada uno. La consecuencia es literal: una fila creada
fuera del formulario queda con `owner = NULL` y **el usuario que la creó no la ve nunca**. El
registro existe, es correcto, y es invisible. Re-medido: **228 `objects.create()`** y 9
`bulk_create()` en el repo, ninguno de los cuales pasa por este `save()`.

Y el campo que hace que eso importe es el mismo del que habla `backend-vistas.md` §2.3: `owner` es
por donde filtra `core/managers.py:9` (`for_user`). Los dos documentos describen los dos extremos del
mismo hilo — **este lo escribe, aquel lo lee** — y por eso una fila creada fuera del formulario no la
ve nadie.

**3. `set_readonly_fields()`** materializa los campos de solo lectura del perfil en el propio
formulario. En el original (`core/forms.py:44-81`) incluye una rama explícita para M2M que vuelve a
filtrar por usuario los valores relacionados —`value.for_request(self.request)`, `core/forms.py:75`—
así que el scoping no se detiene en la fila: llega a los desplegables.

Dos detalles del original que no estaban escritos y que se notan al tocar código:

- **Solo corre en `GET`** (`core/forms.py:37`: `if self.request and self.request.method == 'GET'`).
  Lo que impide enviar un campo de solo lectura en POST **no es esto**: es el controlador restando
  `readonly_fields` de `Meta.fields` (§3, punto 4). El formulario por sí solo no lo defiende.
- **`Meta.required` fuerza campos obligatorios** (`core/forms.py:40-42`): un `required = ['campo']`
  en el `Meta` los marca como requeridos aunque el modelo permita nulo. Es convención de casa y
  **apenas se usa — 2 de 401** — así que no es patrón; se documenta para que quien la encuentre sepa
  qué mira.

### 4.1 El detalle que hay que saber antes de tocar nada: `request` va PRIMERO

```python
def __init__(self, request=None, data=None, files=None, ...)
```

`MiForm(request.POST)` pasa el `QueryDict` como `request`. El formulario queda **unbound**,
`is_valid()` devuelve `False` **siempre**, y **no salta ningún error**: la página se recarga en
blanco y nadie sabe por qué.

**Re-verificado uno a uno, y la conclusión de la v1.0 aguanta con otro número**: hay **8** —no 6—
instanciaciones con los datos en primera posición, y **las 8 son `forms.Form` de Django**, que no
lleva `request` en su firma, así que ninguna es un fallo:

| Sitio | Clase | Base |
|---|---|---|
| `risks_management/views.py:851` · `:2199` · `:2240` | `NewEvaluationForm` · `ChangeRiskMeasuresManagerForm` · `TransferRiskMeasuresForm` | `forms.Form` |
| `questionnaires/views.py:499` · `:517` | `DataMinningForm` | `forms.Form` |
| `import_export_data/views.py:81` · `campaigns/views.py:190` · `health/consultation/views.py:1948` | `ConfirmImportForm` · `CampaignWorkerSideForm` · `ConsultationApparatusForm` | `forms.Form` |

Es invisible para quien no lo sepa, y **es exactamente el error que comete un agente escribiendo de
noche**. Por eso `be-form-request-primero` es una regla de regresión pura: hoy da 0 hallazgos sobre
la base de casa y su coste de adopción es cero. **Y por eso la regla tiene que distinguir la
familia**: si marcase toda llamada `*Form(request.POST, …)` produciría estos 8 falsos positivos.

---

---

## 5. Dónde vive la validación de verdad — y por qué no es `clean_<campo>`

La hipótesis razonable al abrir un repo con 401 formularios es que `clean()` y `clean_<campo>` sean
el gancho dominante. **Medido, no lo son ni de lejos:**

| Gancho | Veces | Sobre 401 |
|---|---:|---:|
| `clean()` | 24 | 6,0% |
| `clean_<campo>` | **11** | **2,7%** — y son **11 campos distintos, uno cada uno** |
| `save()` | 45 | 11,2% |
| `__init__` | 20 | 5,0% |
| **Ningún método** | **326** | **81,3%** |

Cuatro de cada cinco formularios de este backend son `class X(ModelForm)` + `class Meta` y **nada
más**. Ejemplos de los 11 `clean_<campo>`, para que se vea que son casos puntuales y no un patrón:
`core/forms.py:127` (`clean_analytical_tests`: tope de 10 pruebas) y `:133` (`clean_serologies`,
idéntico). No hay un idioma de validación por campo que copiar; hay once excepciones.

### 5.1 Entonces, ¿quién valida?

La respuesta honesta, con lo que se puede medir:

| Capa | En este repo | Medido |
|---|---|---|
| **Definición del campo en el modelo** (`max_length`, `choices`, `null`, FK) | **La única capa que valida sistemáticamente**, y la aplica el `ModelForm` al construir sus campos | — |
| Reglas entre campos, en el formulario | 35 ganchos | 8,7% de los formularios |
| **`full_clean()` en el modelo** | **0** | `grep -rn "full_clean()" → 0` |
| **Constraints de base de datos** (`CheckConstraint`, `UniqueConstraint`) | **0** | `grep -rn "CheckConstraint\|UniqueConstraint" → 0` |
| Excepciones de validación lanzadas a mano | 46 `raise ValidationError` | 9 en `forms.py` · 8 en `models.py` · 7 en `views.py` |

**La consecuencia, dicha sin adornos: en este backend la integridad de los datos depende de que se
pase por el formulario, y no hay ninguna red por debajo.** Sin `full_clean()` y sin constraints, los
**228 `objects.create()`** y los **9 `bulk_create()`** del repo escriben sin verificar nada — ni los
`choices`, ni las reglas entre campos, ni el dueño (§4, punto 2). No es una crítica al equipo que lo
escribió: es la propiedad estructural que hay que conocer **antes** de escribir el 403.

Y su corolario operativo, que es la regla accionable de esta sección:

> **En el arquetipo servidor, todo escritor que no sea el formulario es una vía sin validar.** Si
> escribes un comando de `manage.py`, una tarea de Celery o un import masivo, o llamas al formulario,
> o replicas su validación a mano — y lo segundo no lo comprueba nadie.

### 5.2 Lo que esto NO permite concluir

- **No he comprobado si la validación falta en algún sitio concreto** ni he buscado datos corruptos
  en producción. Lo medido es la ausencia de mecanismos (`full_clean`, constraints), no la presencia
  de un daño.
- **`choices` sin constraint no es exclusivo de este repo**: es el default de Django, que valida
  `choices` en `full_clean()` y no en `save()`. Lo llamativo aquí es la combinación con 228
  `objects.create()`, no el hecho aislado.
- **Los 46 `raise ValidationError` no están clasificados** por si son de dominio o de formulario. No
  lo he mirado uno a uno y no lo afirmo.

---

## 6. La convención que faltaba: el formulario es una DECLARACIÓN, y se lee con su `Settings`

Si el 81% no tiene métodos y el `Meta.fields` lo pisa el controlador, la pregunta legítima es qué
queda en un `forms.py`. Queda esto, y es más de lo que parece:

```python
# campaigns/forms.py:16 — un forms.py típico, entero
from core.forms import ModelForm
from module.module import dependent_fields

dependent_fields['campaigns'] = {                       # 3. dependencias entre desplegables
    'consultation_reasons': {'consultation_type': 'consultation_types'},
}

class CampaignForm(ModelForm):                          # 1. hereda de la base de casa
    class Meta:
        model = Campaign                                # 2. el modelo — lo ÚNICO obligatorio
        fields = '__all__'                              #    (inerte: lo pisa el controlador, §3)
        widgets = {                                     # 4. los widgets: la parte con contenido
            'consultation_reason': ModelSelect2AutoWidget(
                url='/active-query-autocomplete/consultation_reasons/campaigns/',
                forward=['consultation_type'], add=False),
            'companies': ModelSelect2MultipleAutoWidget(
                url='/active-query-autocomplete/companies/', add=False),
        }
```

**Los widgets son la carga útil, y son el dato que más sorprende: 240 de 363 `Meta` los declaran
(66%).** Reparto de los usados:

| Widget | Usos en `forms.py` |
|---|---:|
| `ModelSelect2AutoWidget` | **539** |
| `ModelSelect2MultipleAutoWidget` | 102 |
| `HiddenInput` | 101 |
| `Select` · `ImageCropWidget` · `NumberInput` · `Textarea` · `ReadonlyWidget` | 43 · 14 · 10 · 5 · 5 |

Es decir: **el trabajo de un `forms.py` en este repo es decir de dónde saca sus opciones cada campo
relacionado**, no validar. Cada `ModelSelect2AutoWidget` declara una URL de autocompletado y, con
`forward=[...]`, de qué otro campo depende. Y el acotado por usuario vuelve a aparecer aquí: el
controlador reescribe esas URLs y sus permisos de alta en `get_form()`
(`controller/controllers.py:512-544`).

`dependent_fields` (20 de los `forms.py` lo declaran) es un **registro a nivel de módulo**: se
importa el diccionario y se le añade una entrada al importar el fichero. Renombrar una clave no lo
detecta ningún IDE — la misma contrapartida que `backend-controllers.md` §5 describe para los
inlines referenciados por cadena de texto.

### 6.1 El formulario NO es un detalle de la vista: es la declaración central

Es la consecuencia que cambia cómo hay que leer un `forms.py`, y viene de `backend-controllers.md`
§2c: **`form` es el único atributo obligatorio** de los 42 que declara `BaseController`, y el modelo
de la pantalla se deriva de él:

```python
# controller/controllers.py:213-214 — no hay atributo `model` en ninguna parte
@classmethod
def get_model(cls):
    return cls.form._meta.model
```

De ahí sale el modelo, y del modelo el nombre visible, el icono y el slug de la URL. Medido:
**310 `form = …` en los `controller_settings.py`** y 98 en los `controllers.py`; y el registro de la
pantalla se escribe `@register(XForm.Meta.model._meta.slug)` (`campaigns/controllers.py:6`), es decir
**derivando la clave de la URL del formulario**.

Consecuencias al tocar código:

1. **Cambiar `Meta.model` en un `forms.py` cambia la URL, el icono y el título de una pantalla.** No
   es un cambio local al formulario.
2. **Un formulario sin controlador y un formulario con controlador se leen distinto.** Con
   controlador, `Meta.fields` es decorativo y la verdad está en `fieldsets`. Sin él —los que se
   instancian a mano, medidos por sus **40 `.is_valid()`**— `Meta.fields` **es** la lista blanca, y un
   `fields = []` heredado por copia-pega produciría un formulario sin campos.
3. **Para entender un formulario hay que abrir su `controller_settings.py`.** Es la misma factura que
   `backend-controllers.md` §8 declara para las pantallas, un fichero más arriba.

---

## 7. El antipatrón que sustituye

`_fixtures/infractor-plano/expedientes/forms.py`:

```python
from django.forms import ModelForm

class ExpedienteForm(ModelForm):        # ← el ModelForm de Django, no el del proyecto
    class Meta:
        model = Expediente
        fields = "__all__"
```

Qué duele exactamente, y no en abstracto:

1. **El texto entra sin sanear.** Este formulario no pasa por el `bleach.clean()` de la base; el
   HTML que escriba el usuario se guarda crudo y sale por cualquiera de las plantillas con `|safe`.
2. **La fila nace sin dueño.** No se asigna `owner`, así que el filtrado por usuario no la
   devuelve: el usuario rellena el formulario, ve el mensaje de éxito y el registro desaparece.
3. **`fields = "__all__"` publica lo que todavía no existe.** El día que alguien añada
   `aprobado_por` al modelo, se vuelve editable en este formulario sin que nadie lo decida. Con
   `exclude` pasa lo mismo y además con apariencia de estar controlado.
4. **Los campos de solo lectura del perfil no se aplican**, porque quien los aplica es la base.

Y el reverso, en `views.py`: `CierreExpedienteForm(request.POST)` — la instanciación invertida de
arriba. Hereda bien de la base, y aun así no funciona nunca.

---

## 8. Cómo se comprueba

```bash
python3 .claude/patterns/stack/pattern_check_backend.py            # ficheros cambiados
python3 .claude/patterns/stack/pattern_check_backend.py --rules be-form-fields-enumerado,be-form-base-de-casa
```

| Regla | Estado | Qué detecta (AST) | Medido en el repo de referencia |
|---|---|---|---|
| `be-form-fields-enumerado` | activo | `Meta.fields = '__all__'` o presencia de `Meta.exclude` en una clase de formulario | **1 hit de 363** — y ese hit es un **falso positivo**, ver 8.1 |
| `be-form-base-de-casa` | activo | Una clase de formulario hereda del `ModelForm` **de Django** existiendo ya una base compartida en el proyecto (`core/`, `common/`, `shared/`…). Resuelve alias de import; exime al fichero donde se define la base | **1 hit de 401** — re-medido: 361 heredan de la base, 1 de Django directo |
| `be-form-request-primero` | activo | Llamada a una clase de la familia de la base cuyo **primer posicional** es `request.POST`/`GET`/`FILES`/`data`, cuando la base declara `request` primero | **0 hits** — regresión pura |
| `be-form-clase-fuera-de-forms` | débil | `ClassDef` `*Form` en un `.py` que no es `forms.py` | **24 hits** por el criterio del checker (nombre) · **17** por herencia real → `debil` + baseline |

**`be-form-base-de-casa` no dispara en un proyecto nuevo hasta que la base existe**, y eso es
deliberado: el primer formulario del proyecto tiene que poder heredar de Django sin que un gate lo
bloquee. La base se **descubre** (una subclase de `ModelForm` en un módulo compartido), no se
declara en ningún fichero de configuración.

### 8.1 `be-form-fields-enumerado` mide un campo inerte — qué hacer con eso

§3 lo demuestra: donde hay controlador, `Meta.fields` lo pisa `controller/controllers.py:106-117`. De
ahí salen dos hechos incómodos, y los dos son de la regla, no del código:

1. **Su dominancia del 99,4% no mide disciplina, mide un idioma.** 353 de 363 declaran `fields = []`
   porque el controlador decide; la regla los cuenta como "enumerados" y no lo están.
2. **Su único hallazgo sobre la referencia es un falso positivo.** `campaigns/forms.py:20` usa
   `'__all__'`, y su controlador (`campaigns/controller_settings.py:7` → `controllers.py:6`) le
   sobrescribe el `Meta`. Marcarlo es pedir un cambio que no cambia nada. Sobre 1 hallazgo eso es un
   **FPR del 100%**, muy por encima del <5-10% que `patterns/README.md` §3 exige para `activo`.

**Qué NO hay que hacer: retirarla.** En el otro caso —el formulario que se instancia a mano, los 40
`.is_valid()` del repo— `Meta.fields` **sí** es la única lista blanca, y ahí `'__all__'` publica de
verdad lo que todavía no existe. La regla es correcta para ese caso y equivocada para el dominante.

**Lo que hace falta es acotarla**, y por eso va como candidata y no como parche (el comprobador es de
otro frente y este documento no lo toca):

| id | Enunciado propuesto | Estado |
|---|---|---|
| `be-form-fields-enumerado` (acotar) | Marcar `'__all__'`/`exclude` **solo** si el formulario NO es consumido por un controlador — o sea, si ninguna clase del proyecto lo declara como `form = <esa clase>` | propuesta |
| `be-form-fieldsets-es-la-lista-blanca` | Donde hay controlador, la lista blanca es `fieldsets` en el `*Settings`: un campo del modelo que no esté en `fieldsets` no es editable | `sombra` — y su dueño natural es **`backend-controllers.md`**, no este documento |

Mientras no se acote, lo honesto es lo que dice esta sección: **la regla está en `activo` y su único
hallazgo actual no es accionable.** No se apaga a espaldas de nadie; se deja escrito para que quien
la vea disparar sepa qué mirar antes de "arreglarlo".

### 8.2 Lo que este documento NO comprueba (límites, no descuidos)

- **Que el dueño se asigne fuera del formulario.** Es la regla de mayor valor de este arquetipo y
  la que **no entra en el catálogo**, porque marcaría del orden de **200 de los 228 `objects.create()`** del repo de
  referencia: por la regla de inversión, con ese volumen la mala sería la regla. Necesita baseline
  y alcance de solo-código-nuevo antes de existir. Hasta entonces es criterio, y va escrito aquí
  para que se lea, no disfrazado de check.
- **Que exista validación en las vías que no son el formulario.** `full_clean()` = 0 y constraints
  = 0 en el repo medido. Lo que el patrón de casa exige decir en voz alta es **qué hace un escritor
  que no es el formulario** — y hoy la respuesta honesta en ese backend es "nada".
- **Que una vista Django (no DRF) no escriba en la BD.** `be-svc-escritura-en-vista` solo mira
  clases `*ViewSet`/`*APIView`: en una CBV de Django clásico no dispara. El principio sigue siendo
  el de `backend-servicios.md` —la lógica va en la capa de servicio, se llame como se llame— pero
  aquí no hay comprobación mecánica que lo respalde. Dicho, no escondido.
- **Si el saneado deshace parte de su propio trabajo.** Localizado en `core/forms.py:91`: tras
  `bleach.clean()` se revierten `&amp;`, `&gt;` y `&lt;`. Con `strip=True` el caso obvio queda
  cubierto; devolver `<` crudo al almacén con 561 `|safe` en las plantillas **sigue sin poder
  descartarse leyendo código**. Es un hallazgo a verificar en vivo, **no una vulnerabilidad
  confirmada** — y localizarlo no lo confirma, solo dice dónde mirar.
- **Que el saneado alcance lo que ya estaba guardado.** El `clean()` real solo recorre
  `self.changed_data` (`core/forms.py:88`), así que el contenido escrito antes de que existiera el
  saneado no pasa por `bleach` hasta que alguien edite ese campo. **No he medido cuánto contenido
  está en esa situación** y no lo estimo.

---

## 9. Excepciones legítimas

- **`forms.Form` de Django (sin modelo)** para búsquedas, filtros y confirmaciones: no hay fila que
  guardar, así que no hay dueño que asignar. `be-form-base-de-casa` solo mira `ModelForm`.
- **Bases intermedias de dominio.** En el repo medido hay 16 formularios que heredan de bases
  intermedias (`AntecedentBaseForm` y similares) en vez de directamente de la de casa. Es correcto y
  el checker lo respeta: resuelve la familia de forma transitiva.
- **Un formulario definido fuera de `forms.py`** con razón escrita (un wizard de un solo uso, un
  formulario de una migración de datos):

```python
# pattern-exempt: be-form-clase-fuera-de-forms — formulario de un solo uso del asistente de alta
class PasoConfirmacionForm(forms.Form):
    ...
```

---

## Related

- **`backend-vistas.md` §2** — la otra mitad de este arquetipo: quién instancia este formulario, y
  dónde se acota el queryset (`for_user`, el manager que lee el `owner` que escribe §4)
- **`backend-controllers.md`** — quien consume estos formularios: §2c (`form` es el único atributo
  obligatorio y de él sale el modelo) y §2 (`fieldsets`, la lista blanca de verdad, §3 de aquí)
- `backend-servicios.md` — la lógica de negocio, y por qué el nombre del fichero es un default
- `backend-modelos.md` — el otro extremo del hueco: lo que el formulario no puede garantizar (§5:
  0 `full_clean()`, 0 constraints)
- `backend-serializers.md`, `backend-vistas.md` §1 — **el arquetipo DRF; no aplican aquí**
- `README.md` §"Los cuatro defaults que NO son reglas" — por qué este documento existe
- `rita-pattern-keeper` — juzga los candidatos que emite el checker; nunca busca ella (regla R-1)

---

_Pattern doc v2.0 · 2026-08-25 · Re-medido con AST sobre los 1.401 ficheros `.py` de
`resources/code-refference/evo-preven-develop.zip`. v1.0 acertaba en la base de casa, en
`request` primero y en el saneado central; fallaba en su corolario comprobable — §3: `Meta.fields`
no es la lista blanca de este repo, porque el controlador la sobrescribe en runtime
(`controller/controllers.py:106-117`), y las 353 listas vacías que la regla contaba como
"disciplina" son un idioma, no una defensa. Nuevo y medido: §5 (la validación NO vive en `clean_`:
35 ganchos en 401 formularios, 0 `full_clean()`, 0 constraints) y §6 (240 `Meta.widgets` — el
trabajo real de un `forms.py`). Todo lo añadido nace en `sombra` (GAP-1: un solo repo)._
