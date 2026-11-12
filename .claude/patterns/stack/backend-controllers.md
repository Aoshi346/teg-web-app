# Settings + Controller — el patrón CRUD de un backend Django heredado

> **Cuándo aplicar:** cuando trabajas en un repo Django que tiene su **propio framework CRUD** —una
> clase base que dibuja el listado, el formulario y las pestañas a partir de atributos declarados—
> y hay que añadir o tocar una pantalla. Este documento describe la forma dominante de
> `.docs/resources/coding/` → `evo-preven`, que es donde está medido.
>
> **NO aplicar:** en un proyecto NUEVO. Esto no es Django, no es DRF y no es el patrón de casa: es
> el framework interno de un cliente, 1.792 líneas que ya existen allí y que no se importan a
> ningún sitio. Para un backend nuevo mandan `backend-vistas.md` (DRF) y
> `backend-formularios-django.md` (server-rendered). Tampoco aplica a `ControllerView` /
> `ControllerTemplateView` de ese mismo repo, que son vistas normales y **nunca** llevan `Settings`
> (0 de 82).
>
> **Relacionado:** `backend-formularios-django.md` (el arquetipo server-rendered del template, que
> es el pariente más cercano) · `backend-estructura-apps.md` (dónde vive cada fichero de una app) ·
> `backend-vistas.md` (el arquetipo DRF, el otro extremo) ·
> `rules/refactor-progresivo.md` §3 (los 13 intocables de ESTE mismo repo — y la observación de que
> su validación en el formulario "es coherente con tener **un** framework CRUD"; este documento
> describe ese framework) · `patterns/README.md` (dominancia, regla de inversión, escalones).

---

## 0. La corrección de partida

El encargo venía con dos cifras: *830 clases `*Settings`* y *261 `InlineController`*. Re-medidas con
AST sobre los 1.401 ficheros `.py` del repo (`ast.ClassDef`, no `grep`):

| | Encargo | Medido | Nota |
|---|---:|---:|---|
| Clases `*Settings` | 830 | **298** | 983 es el número de *menciones* de la palabra `Settings`; 830 no reproduce con ningún criterio que haya probado |
| Clases que heredan `InlineController` | 261 | **250** | Diferencia pequeña; el `grep` cuenta además la línea del import y las menciones sueltas |
| Clases `ControllerView`/`ControllerTemplateView` | — | **82** | No son este patrón (§3, §9): comparten la palabra "Controller" y llevan 0 `Settings` |
| Menciones en los 14 `backend-*.md` que ya existían | 0 | **0** | ✅ exacto — este documento es el 15º |

**El comando exacto que produce esas cifras**, pegado aquí para que se recomprueben sin tener que
reconstruirlo. Es la diferencia entre una cifra auditable y una que nadie vuelve a mirar — y es
justo por donde se coló el 830 del encargo:

```python
# python3, desde la raíz del repo de referencia
import ast, pathlib
S = I = M = V = 0
CTRL_VIEW = {"ControllerView", "ControllerTemplateView"}
for f in pathlib.Path('.').rglob('*.py'):
    try: tree = ast.parse(f.read_text(errors='ignore'))
    except SyntaxError: continue
    for n in ast.walk(tree):
        if not isinstance(n, ast.ClassDef): continue
        bases = [b.id if isinstance(b, ast.Name) else
                 b.attr if isinstance(b, ast.Attribute) else '' for b in n.bases]
        if n.name.endswith('Settings'):  S += 1
        if 'InlineController' in bases:  I += 1
        if 'ModelController'  in bases:  M += 1
        if CTRL_VIEW & set(bases):       V += 1
print(S, I, M, V)      # -> 298 250 339 82
```

Re-medido el 2026-08-25 por un segundo frente de forma independiente: **298 · 250 · 339 · 82**. El
`grep` equivalente da 255 en vez de 250 porque cuenta también la línea del import; las cifras de
este documento son las del AST.

La tercera fila es la que motivaba el encargo y es correcta: **el patrón dominante del CRUD de ese
backend no está escrito en ninguna parte**. Las otras dos no cambian la conclusión, pero sí cambian
qué se puede afirmar en un informe, así que van corregidas aquí y no en una nota al pie.

**Dónde está el código.** No en `.docs/resources/coding/` —ahí están `elvion` y `proxera_musa`, y en
los dos el patrón aparece **cero veces**— sino en `resources/code-refference/evo-preven-develop.zip`.
Medir sobre el repo equivocado da 0 y parece que el patrón no existe.

---

## 1. La regla (una frase)

**Lo que se DECLARA (formulario, columnas, `fieldsets`, filtros, inlines) vive en una clase
`XSettings` sin base; lo que se COMPORTA vive en el controlador, que la hereda —`class
XController(XSettings, ModelController)`— con el `Settings` SIEMPRE primero.**

El porqué no es estético y se puede medir: **de las 298 clases `Settings`, 193 (65%) alimentan a la
vez una pantalla completa y un inline embebido dentro de la pantalla de otro modelo.** Sin la
separación, ese layout se escribiría dos veces y divergiría en la segunda edición.

---

## 2. Implementación de referencia

Tres ficheros de la misma app, y el orden en que hay que leerlos.

**(a) La declaración** — `evopreven/campaigns/controller_settings.py:54`. Clase suelta, sin heredar
de nada: es un saco de atributos.

```python
class CampaignWorkerSettings:
    form = CampaignWorkerForm
    filterset = CampaignWorkerFilter
    search_worker = True
    list_display = ['worker', 'visual_status', 'consultation', 'vaccine_dose', 'get_sex', 'get_age']
    inlines = []
```

**(b) La pantalla completa** — `evopreven/campaigns/controllers.py:11`. El cuerpo es literalmente
`...`: todo lo que esta pantalla es, lo pone el `Settings`.

```python
@register(CampaignWorkerForm.Meta.model._meta.slug)
class CampaignWorkerController(CampaignWorkerSettings, ModelController):
    ...
```

**(c) El mismo modelo, embebido en la pantalla de una campaña** —
`evopreven/campaigns/inlines.py:5`. Reusa la declaración y añade **solo** lo que cambia por estar
dentro de otro objeto:

```python
class CampaignWorkerInline(CampaignWorkerSettings, InlineController):
    add_slug = 'workers'
    inline_list_template = 'campaigns/sideform_campaign_worker_list_template.html'
    disable_state_save = True

    def get_table_buttons(self):
        buttons = super().get_table_buttons()
        buttons.remove('delete_relation')
        ...
```

Ese trío —declaración compartida, página vacía, inline con la conducta— es la forma. Se repite en
193 modelos.

**Precedentes adicionales** (≥2 por afirmación, como pide `patterns/README.md`):

| Afirmación | Precedentes |
|---|---|
| `Settings` sin base, solo declaración | `campaigns/controller_settings.py:54` · `blueprints/controller_settings.py:9` |
| Mismo `Settings` en página + inline | `blueprints/controller_settings.py:192` → `controllers.py:47` y `inlines.py:11` · `campaigns/controller_settings.py:79` → `controllers.py:15` y `inlines.py:30` |
| `Settings` que hereda de otro `Settings` | `blueprints/controller_settings.py:46` y `:88` (los dos de `BaseBlueprintSettings`, `:21`) |
| Las bases del framework | `controller/controllers.py:725` (`InlineController`) · `controller/controllers.py:880` (`ModelController`) |

---

## 2b. Cómo se PUBLICA una pantalla: registrar es publicar

El decorador `@register` no es azúcar sintáctico: es el mecanismo entero de publicación
(`module/module.py:16`).

```python
def register(table):
    def _register(model_controller):
        assert issubclass(model_controller, ModelController)
        module.register(table, model_controller=model_controller)
        return model_controller
    return _register
```

Mete el controlador en un diccionario (`module/module.py:9`, `active_tables`), y **una sola ruta
genérica sirve todas las tablas** (`module/urls.py:67`):

```python
path('frame/<str:table>/', views.ListView.as_view(), name='list_view'),
```

La vista busca el controlador por el slug de la URL (`module/views.py:50`) y, si no está
registrado, devuelve `PermissionDenied`. Tres consecuencias prácticas:

1. **Registrar es publicar.** Una tabla sin `@register` no tiene URL. Quitarle el decorador la
   retira del sistema entero sin tocar `urls.py`, y añadir una tabla nueva tampoco toca rutas.
2. **La clave del slug se deriva, no se teclea:** `@register(XForm.Meta.model._meta.slug)`
   (`structure/controllers.py:31`), así que no puede desincronizarse del modelo.
3. **El `assert issubclass(..., ModelController)` (`module/module.py:18`) impide registrar un
   `*Settings` suelto**, y falla al importar el módulo, no en runtime — aunque con un
   `AssertionError` sin mensaje, que cuesta leer.

Precedentes: `module/module.py:16` · `structure/controllers.py:31` · `module/urls.py:67` ·
`module/views.py:50`.

---

## 2c. Qué declara un `Settings` y qué hace el framework con ello

**No hay atributo `model`.** El modelo se deduce del formulario, y por eso `form` está en todos los
`Settings` de §2 (`controller/controllers.py:213-214`):

```python
@classmethod
def get_model(cls):
    return cls.form._meta.model
```

Del modelo salen además el nombre visible, el icono y el slug, leídos de su `Meta`
(`core/models.py:51`, `get_cls_slug()`). Es decir: **`form` es el único atributo obligatorio** de
los 42 que `BaseController` declara con valor por defecto (`controller/controllers.py:25-68`:
`list_display = []`, `page_length = 10`, `orderable = False`, `base_buttons = [...]`…).

Por eso un controlador entero puede ser una línea, y es forma frecuente en el repo:

```python
@register(EmergencyPlanForm.Meta.model._meta.slug)
class EmergencyPlanController(EmergencyPlanSettings, ModelController): ...   # structure/controllers.py:32
```

**Corolario al escribir uno nuevo: declara solo lo que se aparta del default.** Copiar el bloque de
`fieldsets` de otro `Settings` y ajustarlo produce configuración muerta que nadie se atreve luego a
tocar, porque no sabe qué parte está viva.

El formato de `fieldsets` **no es el de Django admin** aunque se le parezca: cada tupla interior es
una **fila**, y un campo puede llevar sus anchos responsive — `('int_code', (3, 6, 6))`. Lo procesa
`process_fields_columns()` (`controller/utils.py:24`), que además agrupa en filas los campos que se
declaran sueltos.

Precedentes: `controller/controllers.py:213` · `structure/controller_settings.py:36` (declaración
mínima) · `structure/controller_settings.py:162` (declaración completa con `fieldsets` responsive).

---

## 3. Lo medido — y qué escalón le corresponde

Universo: toda clase que hereda de un controlador CRUD de la casa (`ModelController` o
`InlineController`). `ControllerView`/`ControllerTemplateView` quedan **fuera a propósito**: son
vistas normales, no CRUD declarativo, y meterlas hundía la dominancia al 75,9% midiendo otra cosa.

| Base | Clases | Con `Settings` | Dominancia |
|---|---:|---:|---:|
| `InlineController` | 250 | 248 | **99%** |
| `ModelController` | 339 | 263 | **78%** |
| **CRUD (las dos)** | **589** | **511** | **86,8%** |
| `ControllerView` + `ControllerTemplateView` | 82 | 0 | 0% (otra familia) |

86,8% cruza el ≥85% que `patterns/README.md` §1 pide para `activo`. **Y aun así todas las
candidatas de §6 van en `sombra`**, por la razón que esa misma regla declara en GAP-1: esto está
medido en **un solo repo**. Un repo no es dominancia del ecosistema; es la manera de escribir de un
equipo. Sube de escalón cuando se mida en un segundo repo con el mismo framework, no antes.

Otras dos medidas que hacen falta para escribir comprobaciones:

- **Orden del MRO: 511 de 511 ponen el `Settings` primero. Cero excepciones.**
- **Ubicación: 294 de 298 `Settings` viven en `controller_settings.py`.** Las 4 restantes: 2 en
  `inlines.py`, 1 en `controllers.py`, 1 en `cacheops/conf.py:32` que **no es este patrón** (es la
  config de una librería y se llama `Settings` por casualidad).

---

## 4. Por qué el `Settings` va PRIMERO

`class X(XSettings, ModelController)` y `class X(ModelController, XSettings)` son las dos válidas
para Python y hacen cosas distintas. El MRO recorre de izquierda a derecha, así que en la primera
gana `XSettings` y en la segunda ganan los valores por defecto del controlador.

Puesto al revés, el `list_display` que acabas de escribir **no se aplica** y la pantalla sale con las
columnas por defecto. No hay error, no hay traza: sale una pantalla plausible y equivocada. Es el
modo de fallo silencioso que justifica que esto sea una comprobación mecánica y no una convención
que se recuerda.

Que los 511 lo tengan bien es exactamente lo que hace la comprobación barata: **hoy no marcaría
nada**, así que no hay deuda que congelar, y la primera vez que dispare será sobre código nuevo.

---

### La otra mitad: el mismo `Settings`, dos comportamientos

Lo de arriba es el lado de los **atributos**. El lado de los **métodos** es el que explica por qué
el patrón paga, y no es simetría del anterior.

`get_table_buttons()` **no existe en `BaseController`**. Solo está en `InlineController`
(`controller/controllers.py:802`) y en `ModelController` (`:882`), y devuelven cosas distintas:
crear/editar/borrar/importar en una página, relacionar/desrelacionar en un inline.

Así que cuando un `Settings` sobrescribe ese método y encadena
(`structure/controller_settings.py:198`):

```python
def get_table_buttons(self):
    if self.request.GET.get('action') == 'copy_risks':
        return self.base_buttons + ['copy_risks', ]
    return super().get_table_buttons()
```

…ese `super()` resuelve **a una implementación distinta según con qué controlador se mezcle**:

| Mezcla | `super().get_table_buttons()` resuelve a | Botones que salen |
|---|---|---|
| `EquipmentUnitController(EquipmentUnitSettings, ModelController)` (`structure/controllers.py:162`) | `ModelController` (`:882`) | crear · editar · borrar · importar · histórico |
| `EquipmentUnitInline(EquipmentUnitSettings, InlineController)` (`structure/inlines.py:94`) | `InlineController` (`:802`) | añadir relación · crear y añadir · quitar relación |

Una sola clase de configuración, dos pantallas con el comportamiento correcto en cada contexto, y
sin un solo `if` que pregunte dónde estamos. **Y prueba que el `*Settings` es abstracto por
construcción:** ese `super()` no tiene a dónde ir si no hay un controlador detrás.

Es lo que sostiene el 65% de reutilización que mide §1. Sin este mecanismo, ese 65% exigiría un
`if self.related_obj` repartido por cada método.

La contrapartida va en §8: la cadena cooperativa **se rompe en silencio** si alguien sobrescribe un
método y no llama a `super()`. En los 30 `controller_settings.py` hay **220 llamadas a `super()`**
que dependen de que nadie corte la cadena, y los MRO llegan a siete niveles —
`EquipmentUnitInline` → `EquipmentUnitSettings` → `WithRisksTabSettings` → `TDSubstancesTabs` →
`InlineController` → `BaseController` → `object`.

---

## 5. Las tres convenciones que lo acompañan

**Los inlines se referencian por STRING, no por símbolo** — 238 de 270 (88%):

```python
inlines = ['campaigns.inlines.CampaignWorkerInline', 'filiation.inlines.WorkerInline']
```

No es descuido: `controller_settings.py` no puede importar `inlines.py`, porque `inlines.py` hace
`from .controller_settings import *`. La cadena de texto rompe el ciclo. El precio es que el
renombrado de una clase de inline **no lo ve ningún IDE ni ningún `grep` de símbolos**, y falla en
tiempo de ejecución al abrir esa pantalla. Es la contrapartida y conviene tenerla escrita.

**Un `controller_settings.py` por app** — 30 ficheros, y el registro `@register(...)` (351 usos)
cuelga el controlador de un slug del modelo.

**El `Settings` que vive en el framework.** `FileInlineSettings` (`controller/controllers.py:939`)
es la excepción que confirma "un `*Settings` no hereda de nada del framework": vive **dentro** de él
y define un **contrato**, no configuración — aporta plantillas y deja `create_files()` como
`raise NotImplementedError` (`:963`) para que cada app lo implemente
(`structure/controller_settings.py:80` y `:141`).

**El `import *` es deliberado**, no deuda: `rules/refactor-progresivo.md` §3 ya lo midió en este
mismo repo —384 `from X import *`, y solo **4 símbolos** realmente pisados— y lo clasificó como
*load-bearing*. No lo "arregles" de paso.

---

## 5b. Cuándo NO se escribe un controlador

§9 acota fuera `ControllerView`/`ControllerTemplateView`. Esta es la frontera accionable para quien
tiene que decidir hoy qué escribe. En el mismo backend conviven **325 vistas Django normales** con
las clases del framework:

```bash
grep -rnE "^class [A-Za-z_]+\(.*(TemplateView|ListView|DetailView|APIView|ViewSet|FormView|View)\)" \
     --include=*.py . | wc -l    # 325
```

El framework nunca pretendió comérselo todo. Mirando sus nombres, lo que tienen en común es que
**ninguna es "una tabla de un modelo con su formulario"**: `ActiveWorkerAutocompleteView`,
`AddRiskInstanceModalView`, `CenterRiskGraphsView`, `AgendaView`, `APIPortalView`, `ChangePassword`
— autocompletados, modales, gráficas, calendarios, API, exportaciones y autenticación.

| Va por el framework | Va como vista normal |
|---|---|
| Un modelo, su listado, su formulario y sus relacionados | Cualquier cosa sin una tabla detrás |
| La pantalla tiene tabla con filtros, columnas y botones | Devuelve JSON a un widget o a un `<select>` |
| Se quiere reutilizar como inline en la ficha de otro modelo | Es una gráfica, un calendario, un asistente |
| Los permisos son los del modelo (`add`/`change`/`view`/`delete`/`relate`) | Los permisos son de otra naturaleza |

**Por qué esto también es coste (§8):** salirse del framework es todo o nada. El `__init__`
(`controller/controllers.py:70`) encadena una veintena de llamadas —permisos, `fieldsets`, inlines,
formulario construido al vuelo— antes de que el objeto exista. Una pantalla que necesite la mitad
de eso no puede coger la mitad: o entra en el molde, o se escribe desde cero como vista normal. Esa
rigidez es lo que explica las 325.

---

## 6. Candidatas a comprobación — las tres, en `sombra`

Cada una con su recuento de infractores actuales, que es lo que decide si la regla es viable o si
la mala es la regla (`patterns/README.md` §2: >20-30 sitios ⇒ la regla está mal).

| id | Enunciado | Infractores hoy | Veredicto |
|---|---|---:|---|
| `be-ctrl-settings-primero` | En `class X(Settings, Controller)` el `*Settings` va antes que el `*Controller`: al revés, sus atributos no se aplican y la pantalla sale con los valores por defecto, sin error | **0** / 511 | ✅ viable — no marca nada hoy; caza la primera regresión |
| `be-ctrl-settings-en-su-fichero` | Las clases `*Settings` viven en `controller_settings.py` de su app | **3** / 298 (+1 falso positivo conocido: `cacheops/conf.py:32`) | ✅ viable — 3 sitios, muy por debajo del umbral |
| `be-ctrl-inline-con-settings` | Una clase que hereda `InlineController` declara su layout en un `*Settings`, no dentro del propio inline | **2** / 250 | ✅ viable, **acotada a `InlineController`** |

**La cuarta, la que NO se propone, y por qué.** El enunciado natural sería *"todo controlador CRUD
se empareja con un `Settings`"*. Aplicado a `ModelController` marca **76 sitios**. Eso es entre dos
y tres veces el umbral de la regla de inversión: no es que haya 76 ficheros mal escritos, es que
**el enunciado no describe lo que hace el repo**. Por eso la fila de arriba se acota a
`InlineController` (2 infractores) y `ModelController` se queda fuera de toda comprobación.

Qué son esos 76, para que nadie los "arregle" sin mirar: controladores de catálogo pequeños que
declaran sus tres o cuatro atributos en el propio cuerpo —`generals/controllers.py:8` (`CNAEController`),
`:21`, `:34`, `:47`— cuando esa declaración **no la comparte nadie más**. Con un solo consumidor, la
clase `Settings` aparte no compra nada: es un fichero más que abrir. La forma colapsada es
razonable ahí, y por eso no se marca.

Entradas para `catalog.yaml` (mismo formato que `_catalog-entries-backend.yaml`):

```yaml
  - id: be-ctrl-settings-primero
    enunciado: "En class X(Settings, Controller) el *Settings va ANTES: al revés sus atributos no se aplican y la pantalla sale con los valores por defecto, sin error"
    eje: 1-estructura
    mecanismo: ast
    ambito: "**/controllers.py, **/inlines.py"
    dominancia: "511/511 = 100% (evo-preven, UN repo — por eso sombra, GAP-1)"
    estado: sombra
    baseline: null
    precedentes:
      - "resources/code-refference/evo-preven-develop.zip → evopreven/campaigns/controllers.py:11"
      - "resources/code-refference/evo-preven-develop.zip → evopreven/campaigns/inlines.py:5"
    source: ".claude/patterns/stack/backend-controllers.md"
    doc: stack/backend-controllers.md

  - id: be-ctrl-settings-en-su-fichero
    enunciado: "Las clases *Settings viven en controller_settings.py de su app"
    eje: 1-estructura
    mecanismo: ast
    ambito: "**/*.py"
    dominancia: "294/298 = 99% (evo-preven, UN repo)"
    estado: sombra
    baseline: null
    precedentes:
      - "…→ evopreven/campaigns/controller_settings.py:54"
      - "…→ evopreven/blueprints/controller_settings.py:21"
    source: ".claude/patterns/stack/backend-controllers.md"
    doc: stack/backend-controllers.md

  - id: be-ctrl-inline-con-settings
    enunciado: "Una clase que hereda InlineController declara su layout en un *Settings, no en el propio inline"
    eje: 1-estructura
    mecanismo: ast
    ambito: "**/inlines.py"
    dominancia: "248/250 = 99% (evo-preven, UN repo)"
    estado: sombra
    baseline: null           # 2 infractores: health/consultation/inlines.py:71 · health/laboratory_test/inlines.py:195
    precedentes:
      - "…→ evopreven/campaigns/inlines.py:5"
      - "…→ evopreven/blueprints/inlines.py:11"
    source: ".claude/patterns/stack/backend-controllers.md"
    doc: stack/backend-controllers.md
```

---

## 7. El antipatrón

`evopreven/generals/controllers.py:8` — la forma colapsada, con el `controller_settings.py` de esa
misma app existiendo al lado y vacío de estas clases:

```python
@register(CNAEForm.Meta.model._meta.slug)
class CNAEController(ModelController):          # sin Settings
    resource_class = CNAEResource
    form = CNAEForm                              # ← declaración dentro del controlador
    list_display = ['int_code', 'name', 'parent', 'year']
    fieldsets = ((_("Información"), {'fields': ('int_code', 'name', 'parent', 'year')}),)
```

**No está mal por sí solo** (§6 explica por qué no se marca). Se convierte en problema el día que
alguien necesita ese mismo modelo como inline: entonces copia los cuatro atributos al inline, y a
partir de ahí hay dos layouts del mismo modelo que nadie vuelve a sincronizar. El antipatrón real
no es la clase colapsada: es **colapsarla y luego duplicarla**.

---

## 8. El coste, declarado

Ningún patrón es gratis y este tiene una factura concreta:

- **Dos ficheros por pantalla, mínimo.** Para entender una pantalla hay que abrir
  `controller_settings.py` *y* `controllers.py`, y si es un inline, tres. Con el cuerpo del
  controlador en `...`, el fichero que lleva su nombre no dice nada de él.
- **Los ficheros de declaración se hacen enormes.** 30 `controller_settings.py` suman **11.451
  líneas**; el mayor, `risks_management/controller_settings.py`, tiene **2.683** — cuatro veces el
  techo de 600 que marca `be-techo-lineas`. Son declaraciones, no lógica, pero se leen igual de mal.
- **El renombrado deja de ser seguro** por la referencia a inlines en cadena de texto (§5).
- **27% de los `Settings` (81 de 298) tienen un solo consumidor**: ahí la separación es ceremonia y
  no compra la reutilización que la justifica.
- **La cadena cooperativa se rompe en silencio.** Las 220 llamadas a `super()` de los 30
  `controller_settings.py` dependen de que nadie sobrescriba un método sin encadenar; quien lo haga
  se lleva por delante lo que aportaban los mixins de más arriba, sin error y sin traza (§4, *La
  otra mitad*). Y los MRO llegan a siete niveles, así que "qué hace este método aquí" no se responde
  leyendo un fichero.
- **El framework hay que mantenerlo**: 963 líneas en `controller/controllers.py` más 829 en
  `module/views.py` que nadie fuera del proyecto revisa ni actualiza.

---

## 9. Lo que este documento NO dice

- **No recomienda adoptar esto.** Describe lo que hay para que quien toque ese repo escriba como el
  repo, que es el eje de Rita. En un proyecto nuevo, este patrón sería construir un framework CRUD
  propio: una decisión de arquitectura que iría por `rules/plan-gates.md` Gate C (buy vs build) y
  Gate D (ADR), y que casi siempre pierde contra Django admin o DRF.
- **No está medido fuera de `evo-preven`.** Un repo. Por eso las tres candidatas van en `sombra` y
  por eso ninguna debe promoverse con lo que hay hoy.
- **No hay comprobador escrito.** Las tres candidatas de §6 son enunciados con su recuento y su
  ámbito; falta implementarlas en `pattern_check_backend.py` y pasarles el `--self-test` (FPR <5-10%
  sobre ficheros conformes, `patterns/README.md` §3). Sin eso son texto, no gate.
- **No cubre `ControllerView`/`ControllerTemplateView`** (82 clases, 0% con `Settings`): comparten
  la palabra "Controller" y no son este patrón.

---

## Related

- `backend-formularios-django.md` (el arquetipo server-rendered del template) ·
  `backend-estructura-apps.md` (qué fichero va en cada app) ·
  `backend-vistas.md` (DRF, el otro extremo) ·
  `rules/refactor-progresivo.md` §3 (los 13 intocables de este mismo repo: el `import *`, la clave
  primaria visible y la validación en el formulario ya están juzgados allí — no los re-abras) ·
  `patterns/README.md` (dominancia, regla de inversión, GAP-1) · agente `rita-pattern-keeper`.

---

_Pattern doc v1.0 · 2026-08-25 · Medido con AST sobre los 1.401 ficheros `.py` de
`resources/code-refference/evo-preven-develop.zip`. Las cifras del encargo (830/261) no
reproducen; las reales están en §0. Las tres candidatas nacen en `sombra` por GAP-1: un solo repo._
