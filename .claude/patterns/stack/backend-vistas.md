# Vistas — los DOS arquetipos: DRF y servidor renderizado

> **Cuándo aplicar:** al crear o modificar cualquier vista de backend. Este documento cubre **los
> dos arquetipos que el template declara de primera clase** (`stack/README.md`): la vista **API con
> DRF** (`ViewSet`/`APIView` + `REST_FRAMEWORK` en settings) y la vista **servidor renderizado**
> (Django clásico, que devuelve HTML o JSON sin pasar por DRF). Cada regla lleva escrito **a cuál de
> los dos pertenece**: aplicar la del otro es el error que este documento existe para evitar.
>
> **NO aplicar:** al framework CRUD declarativo `Settings`+`Controller` de `evo-preven` — eso es
> `backend-controllers.md`, y sus 589 clases no se escriben como una vista normal · a la puerta de
> entrada de datos del arquetipo servidor, que es el formulario y vive en
> `backend-formularios-django.md`.
>
> **Relacionado:** `backend-formularios-django.md` (la otra mitad del arquetipo servidor) ·
> `backend-serializers.md` (la otra mitad del arquetipo DRF) · `backend-controllers.md` (el
> framework CRUD, y su §5b decide cuándo NO se escribe una vista) · `backend-servicios.md` (qué NO
> le toca a la vista) · `api-y-errores.md` y `formularios.md` del frontend (el contrato del 400).

---

## 0. Lo medido — y la corrección de partida

El único backend Django de referencia que hay en el repo es
`resources/code-refference/evo-preven-develop.zip` → `evopreven/`: **1.401 ficheros `.py`**, 46 apps,
Django 4.2 en producción. Re-medido con AST (`ast.ClassDef` y resolución **transitiva** de bases, no
`grep`), porque el `grep` cuenta menciones y aquí las menciones mienten mucho:

| | Encargo | Medido | Nota |
|---|---:|---:|---|
| Vistas Django (transitivo) | 131 | **250** | El encargo contaba solo bases directas de Django; 42+40 más heredan de `ControllerView`/`ControllerTemplateView`, que **son** vistas Django transitivamente |
| …de ellas, **CBV genéricas** (`ListView`/`DetailView`/`CreateView`) | — | **4** | 1,6%. **La cifra que cambia el documento**: este backend NO usa las vistas genéricas de Django |
| Serializers DRF | 4 | **2** | Los otros dos son `core/serializers.py:3` (el serializador JSON de Django) y `cacheops/serializers.py:4` (librería vendorizada): se llaman `Serializer` por casualidad |
| `ViewSet` DRF | 1 | **1** | ✅ exacto — y está caracterizado en §3 |
| `APIView` de DRF | — | **0** | La "API" de este backend no usa DRF (§3) |

El comando exacto, pegado para que se recompruebe sin reconstruirlo:

```python
# python3, desde la raíz del repo de referencia. Resuelve bases TRANSITIVAMENTE:
# sin eso, ControllerView (que hereda View) no cuenta como vista y salen 133 en vez de 250.
import ast, pathlib, collections
classes, allc = {}, []
def bn(n): return [b.id if isinstance(b, ast.Name) else b.attr if isinstance(b, ast.Attribute) else '' for b in n.bases]
for f in pathlib.Path('.').rglob('*.py'):
    try: t = ast.parse(f.read_text(errors='ignore'))
    except SyntaxError: continue
    for n in ast.walk(t):
        if isinstance(n, ast.ClassDef):
            classes.setdefault(n.name, []).append(bn(n)); allc.append((str(f), n.name, bn(n)))
DJ = {'View','TemplateView','ListView','DetailView','FormView','CreateView','UpdateView','DeleteView','LoginView','PasswordChangeView'}
DRF = {'APIView','GenericAPIView','ModelViewSet','ViewSet','GenericViewSet','ReadOnlyModelViewSet'}
memo = {}
def kind(name, d=0):
    if d > 12 or name in memo: return memo.get(name, set())
    r = ({'dj'} if name in DJ else set()) | ({'drf'} if name in DRF else set())
    memo[name] = r
    for bs in classes.get(name, []):
        for b in bs: r |= kind(b, d + 1)
    memo[name] = r; return r
dj = [c for c in allc if 'dj'  in set().union(*[kind(b) for b in c[2]] or [set()])]
drf= [c for c in allc if 'drf' in set().union(*[kind(b) for b in c[2]] or [set()])]
print(len(dj), len(drf))       # -> 250 1
c = collections.Counter(b for _, _, bs in dj for b in bs)
print(c.most_common(10))
```

### Los dos arquetipos, y qué regla manda en cada uno

| | **API — DRF** (§1) | **Servidor renderizado** (§2) |
|---|---|---|
| En la referencia | **1** clase, 2 serializers | **250** clases |
| Puerta de entrada de datos | `Serializer` (`backend-serializers.md`) | `ModelForm` (`backend-formularios-django.md`) |
| Quién acota las filas | `get_queryset()` de la vista, o una base de casa | un **manager** (`for_user`), llamado desde la vista |
| Contrato de error | `{"errors": {…}}` vía `EXCEPTION_HANDLER` (§1.3) | `form.errors` re-renderizado, o `PermissionDenied` |
| Salida | JSON serializado | HTML (`template_name`, 117 usos) o `JsonResponse` (310 usos) |

**Un repo puede tener los dos, y este los tiene.** Lo que no puede es aplicarse el documento
equivocado: pedirle `EXCEPTION_HANDLER` a una vista que devuelve HTML, o `bleach` en el `clean()` a
un `ViewSet`, son las dos formas de que este canon estorbe en vez de ayudar.

> ⚠️ **Escalón de todo lo que se mide aquí: `sombra`, por GAP-1** (`patterns/README.md` §1). Está
> medido en **un solo repo**. Un repo no es dominancia del ecosistema: es cómo escribe un equipo.
> Las reglas DRF de §1 ya estaban en `activo`/`debil` **por otra vía** —los fixtures del template— y
> ahí siguen; lo que nace en `sombra` es lo que este documento añade del arquetipo servidor (§4).

---

## 1. Arquetipo **API — DRF**

### 1.1 La regla (una frase)

**La vista traduce HTTP ↔ dominio y nada más: resuelve el queryset del usuario que pregunta,
delega en el serializer y en el servicio, y convierte la excepción de dominio en un código de
estado.**

Por qué el énfasis en "del usuario que pregunta": la vista es el único sitio donde existe la
identidad de quien llama. Es, por tanto, **el único sitio donde se puede filtrar por dueño** — y
el sitio donde ese filtro se olvida.

### 1.2 Implementación de referencia

`_fixtures/conforme/apps/facturacion/views.py`:

```python
class FacturaViewSet(viewsets.ModelViewSet):
    serializer_class = FacturaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # El filtro por dueño va aquí y no en la vista de lista: así lo heredan detail, update
        # y delete, y no hay forma de olvidarlo en uno de los cuatro.
        return Factura.objects.filter(cliente__usuario=self.request.user).select_related("cliente")

    def perform_create(self, serializer):
        serializer.save(cliente=self.request.user.cliente)

    @action(detail=True, methods=["post"])
    def emitir(self, request, pk=None):
        try:
            factura = emitir_factura(factura_id=pk, emitido_por_id=str(request.user.pk))
        except FacturaNoEmitible as exc:
            raise ValidationError(str(exc)) from exc
        return Response(FacturaSerializer(factura).data, status=status.HTTP_200_OK)
```

Con los defaults cerrados en settings (`_fixtures/conforme/config/settings/base.py:22`):

```python
REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 50,
}
```

Ese bloque es la pieza más rentable de todo el fichero: **hace que el olvido sea seguro**. El
default de DRF es `AllowAny`; con él, un ViewSet nuevo al que se le olvide `permission_classes`
queda abierto a internet y nada avisa. Con el default cerrado, el mismo olvido produce un 403 que
se ve en el primer test. La diferencia entre las dos configuraciones es la diferencia entre un
descuido caro y un descuido barato — y en trabajo autónomo los descuidos se acumulan sin testigo.

Lo mismo con la paginación: sin `DEFAULT_PAGINATION_CLASS`, el primer `GET /facturas/` sobre una
tabla que ha crecido serializa la tabla entera en memoria. No falla en desarrollo con 20 filas;
falla en producción con 200.000.

**`get_queryset()` y no `queryset =`**: el atributo de clase se evalúa una vez, al importar el
módulo, y no tiene acceso a `self.request`. El método se evalúa en cada petición y sí lo tiene.
Por eso el filtro por dueño solo puede vivir en el método.

#### Mejor todavía: UN punto de filtrado, no uno por vista (REF-2)

Todo lo de arriba es correcto y tiene un agujero que este documento **reconocía sin resolver**:
decía que el filtro *"es el sitio donde se olvida"* y luego pedía escribirlo en cada `ViewSet`. Con
N vistas hay N oportunidades de olvidarlo, y el olvido aquí no es un bug de listado: es que un
cliente ve las filas de otro.

La respuesta viene de un backend Django real, y es mejor que la nuestra: **el filtro vive en una
base de la que heredan todas las vistas**. Allí, `controller/controllers.py:467` es el ÚNICO sitio
donde se filtra el CRUD de **356 tablas** — de 356 oportunidades de olvido se pasa a una. Y el
único punto del sistema donde el scoping fila-a-fila no se aplicaba era, exactamente, el único
`ViewSet` que no pasaba por esa base.

`_fixtures/conforme-casa/core/api.py`:

```python
class BaseViewSet(viewsets.ModelViewSet):
    """Base de casa. Una vista que herede de aquí no puede olvidar el filtro."""

    permission_classes = [IsAuthenticated]
    modelo = None

    def get_queryset(self):
        return self.modelo.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user, created_by=self.request.user)
```

```python
# expedientes/views.py — la vista de app se queda en declarar
class ExpedienteViewSet(BaseViewSet):
    modelo = Expediente
    serializer_class = ExpedienteSerializer
```

Dos cosas que hacen que esto funcione y no sea solo herencia por herencia:

- **La ruta del scoping se declara junto al modelo, no se repite en la vista.** Aquí es
  `owner=self.request.user` porque el modelo trae `owner` de la base
  (`backend-modelos.md` §"de qué hereda un modelo"). En un dominio multi-empresa, la base puede
  leer del `Meta` del modelo por dónde alcanzar la organización. En los dos casos el dato de "cómo
  se acota este modelo" vive **una vez**.
- **Heredar no impide acotar más.** Una vista que necesite otro queryset hereda igual y refina
  dentro de su `get_queryset()` llamando a `super()`. Lo que no debe hacer es empezar de cero desde
  `objects.all()`.

**La regla es `débil`, y está gateada por descubrimiento**: solo dispara si el proyecto **ya tiene**
una vista base compartida (una clase en `core/`, `common/`, `shared/`… que hereda de DRF y define
`get_queryset`). En un proyecto nuevo no existe, y el checker no la inventa. Es débil porque hay
vistas que legítimamente no van por la base —un catálogo público, un webhook— y bloquear ahí
marcaría código correcto.

### 1.3 El contrato del error 400 — la frontera con el frontend

Es el único punto donde este documento y los del frontend tienen que decir **exactamente** lo
mismo. La forma acordada con `api-y-errores.md` y `formularios.md`:

```
400  {"errors": {"campo": ["mensaje"], "non_field_errors": ["mensaje de formulario"]}}
```

**Esa forma no es la de DRF por defecto, y conseguirla cuesta una línea de settings.** Verificado
en la doc oficial: DRF devuelve las validaciones con *el nombre del campo como clave a nivel raíz*
(`{"importe": ["..."]}`, y `non_field_errors` para las generales) pero los errores de auth,
permisos, 404 y throttling como `{"detail": "..."}`. Son **dos formas distintas**, y un cliente que
lea solo una se come la otra sin enterarse — el front no muestra nada y el usuario ve un formulario
que no reacciona.

La unificación se hace en un `EXCEPTION_HANDLER` de casa
(`_fixtures/conforme/config/exceptions.py`), registrado en settings:

```python
REST_FRAMEWORK = {
    ...
    "EXCEPTION_HANDLER": "config.exceptions.api_exception_handler",
}
```

Con él, las tres rutas acaban en la misma forma:

| Origen | DRF por defecto | Con el handler |
|---|---|---|
| `validate_importe` del serializer | `{"importe": ["..."]}` | `{"errors": {"importe": ["..."]}}` |
| `raise ValidationError(str(exc))` en la vista | `["..."]` (lista suelta) | `{"errors": {"non_field_errors": ["..."]}}` |
| 401 / 403 / 404 / 429 | `{"detail": "..."}` | `{"errors": {"non_field_errors": ["..."]}}` |

La clave `non_field_errors` no es inventada: es el valor por defecto de `NON_FIELD_ERRORS_KEY` en
DRF, así que el handler la lee de `api_settings` en vez de escribirla a mano.

**El agujero del handler: un error se LANZA, no se devuelve.** La doc de DRF lo dice explícitamente:

> *"the exception handler is only invoked for exceptions raised during request processing. It does
> not apply to responses generated directly by views."*

Es decir, `return Response({"error": "..."}, status=400)` escrito a mano **esquiva el handler
aunque esté perfectamente configurado**: sale sin el sobre y el frontend no pinta nada. Tener el
`EXCEPTION_HANDLER` no basta si las vistas construyen errores por su cuenta, así que las dos reglas
van en pareja:

```python
# ❌ esquiva el handler — sale {"error": "ya emitida"}, sin sobre
return Response({"error": "ya emitida"}, status=400)

# ✅ lo atraviesa — sale {"errors": {"non_field_errors": ["ya emitida"]}}
raise ValidationError("ya emitida")
```

El frontend mantiene además una segunda capa defensiva (`normalizeErrors` en su cliente) que tolera
las tres formas. Es correcto que exista —hay endpoints de terceros y legacy fuera del alcance de
este handler— pero **no sustituye a estas dos reglas**: la tolerancia del cliente evita la pantalla
en blanco, no que la API tenga dos contratos.

### 1.4 La URL y el código de estado — el resto del contrato, medido

El error ya tiene forma acordada (arriba). La **URL** y el **código de estado** también son contrato
con quien consume la API, y hasta ahora vivían fuera de este canon: en el agente `arquitecto-apis`,
que los declaraba de memoria y sin comprobar (retirado el 2026-08-22; archivado en `_archive/2026-10-19/agents/`). Aquí están medidos
sobre los dos backends Django reales que hay en el repo —`.docs/resources/coding/elvion` y
`.../proxera_musa`—, que es lo único medible: el template no tiene código Django propio.

```bash
cd .docs/resources/coding                       # los dos backends reales
REG='router\.register\((r?.)[a-z0-9_-]+'
grep -rhoE "$REG" --include='*.py' . | sed -E "s/.*['\"(]//" > /tmp/recursos.txt
wc -l  < /tmp/recursos.txt                      # 39 recursos registrados
grep -cv 's$' /tmp/recursos.txt                 # 6 que no acaban en plural
grep -c  '_'  /tmp/recursos.txt                 # 0 con guion bajo
grep -rhE "path\(\s*['\"]api/"    --include='urls.py' . | wc -l   # 24 montajes bajo /api/
grep -rhE "path\(\s*['\"]api/v[0-9]" --include='urls.py' . | wc -l   # 1 con versión en la URL
grep -rhoE 'status\.HTTP_[0-9]{3}_[A-Z_]+' --include='*.py' . | sort | uniq -c | sort -rn
```

| Convención | Medida | Lectura |
|---|---|---|
| Recurso en **plural** (`/leads/`, `/expedientes/`) | **33 / 39 · 85%** | Es el patrón. Las 6 excepciones —`faq`, `rag`, `knowledge`, `abandoned`, `daily`, `crosssell`— son acrónimos, incontables o adjetivos: ahí el plural no existe o suena peor |
| Multipalabra con **guion**, nunca `_` | **4 / 4 · 100%** (`service-deposits`, `optimizer-models`, `rag-configs`, `sync-status`) | Unánime, aunque la muestra sea de cuatro |
| Montado bajo **`/api/…`** | **24 / 24** | Todo lo que es API cuelga de `/api/`, y el segundo tramo es la app Django (`api/leads/`, `api/returns/`, `api/campaigns/`); cuatro montan el router en la raíz `api/` |
| Versión en la URL (**`/api/v1/`**) | **1 / 24** (`evo_lumi/urls.py:151`) | ⚠️ **Lo que el agente predicaba, el código lo contradice.** No versionamos por URL, y ninguno de los dos proyectos ha tenido que romper un contrato todavía. Lo honesto es escribir lo que hacemos, no una convención que nadie sigue: el día que haya que romper un contrato, esa decisión es un **ADR** (`rules/adr.md`), no un prefijo puesto por si acaso |

**El código de estado que escribes es el del `@action`, no el del CRUD.** `ModelViewSet` ya devuelve
201 al crear y 204 al borrar sin que nadie lo teclee; por eso la cuenta medida sale tan escorada:
**246 `HTTP_200_OK` frente a 30 `HTTP_201_CREATED` y 10 `HTTP_204_NO_CONTENT`**. Los 67
`HTTP_400_BAD_REQUEST` son el otro punto a mirar: cada uno construido a mano es un candidato a
`be-view-error-sin-excepcion` — un 400 que sale sin el sobre `{"errors": …}` y que el frontend no
pinta (§ anterior).

**Rate limiting: global generoso, y estrecho donde da a la calle.** Solo uno de los dos proyectos lo
configura (`proxera_musa/backend/config/settings/base.py:196`), y su forma es mejor que el
"anon 1000/h · user 10000/h" que decía el agente: esos dos son solo el **fallback** —pensados para
que el panel de administración no se estrangule solo— y encima van scopes por endpoint público
(`ScopedRateThrottle` + `throttle_scope`) en lo único expuesto sin sesión: el widget a 60/min y el
webhook entrante a 120/min. La regla que se deduce: **el límite global no protege nada; protege el
scope del endpoint que cualquiera puede llamar sin autenticarse.**

> **Por qué esto no lleva comprobador, y no es pereza.** La regla obvia —"el recurso acaba en s"—
> marcaría 6 de 39 registros (**15%**) que están **bien**. El README de `patterns/` exige FPR
> < 5-10% antes de activar nada (§Reglas duras 3), así que una regla así se cae por su propio
> criterio. Queda como convención escrita, que es su sitio: la decide una persona al nombrar el
> recurso, una sola vez, y un acrónimo mal pluralizado no le cuesta un incidente a nadie.

### 1.5 El antipatrón que sustituye

`_fixtures/infractor/apps/facturacion/views.py`:

```python
class FacturaViewSet(viewsets.ModelViewSet):
    queryset = Factura.objects.all()        # todas las filas, de todos los usuarios
    serializer_class = FacturaSerializer
    permission_classes = [AllowAny]         # y sin login

    @action(detail=True, methods=["post"])
    def emitir(self, request, pk=None):
        factura = self.get_object()
        if factura.estado != "borrador":            # regla de negocio en la vista
            return Response({"error": "ya emitida"}, status=400)
        with transaction.atomic():
            factura.estado = "emitida"
            factura.save()
            enviar_factura_por_email.delay(str(factura.pk))
        return Response(FacturaSerializer(factura).data)
```

`queryset = Factura.objects.all()` sin `get_queryset()` no es un descuido estético: es que
`GET /facturas/1234/` devuelve la factura de otro cliente. Y como `ModelViewSet` deriva **todas**
las operaciones del mismo queryset, también permite editarla y borrarla. Un solo atributo mal
puesto abre lectura, escritura y borrado cruzados entre clientes.

Lo demás (lógica en la vista, `.delay()` dentro de `atomic`) está diseccionado en
`backend-servicios.md` y `backend-celery.md`.

---

## 2. Arquetipo **SERVIDOR RENDERIZADO** — las 250 vistas que nadie había descrito

Esta es la mitad que faltaba. El documento anterior mencionaba "plantillas" una vez y describía
solo DRF; en el backend de referencia, DRF es **1 clase de 251** y todo lo demás es esto.

### 2.1 La regla (una frase)

**La vista de servidor resuelve permiso y queryset acotado, construye el contexto y delega el
render; la escritura entra por un `ModelForm`, no por la vista** — y el acotado por usuario **no lo
escribe la vista**: lo pide a un manager que ya sabe hacerlo (§2.3).

### 2.2 Qué se usa de verdad, y qué no

Reparto de las **250** por su base directa (una clase puede tener varias, por eso suma más):

| Base directa | Clases | Para qué |
|---|---:|---|
| `View` | **93** | El caballo de batalla: `get`/`post` escritos a mano. Autocompletados, modales, exportaciones, endpoints que devuelven JSON |
| `ControllerView` · `ControllerTemplateView` | 42 · 40 | El framework CRUD → **`backend-controllers.md`**, no este documento |
| `TemplateView` · `ModuleTemplateView` · `DashboardTemplateView` | 34 · 23 · 7 | Páginas con contexto. `ModuleTemplateView` (`module/views.py:31`) es la base de casa que añade el menú |
| `APIPortalView` | 4 | La "API" real (§3) |
| **CBV genéricas** (`ListView`, `DetailView`, `CreateView`) | **4** | **1,6% — prácticamente no se usan** |

**La conclusión que hay que llevarse, y es contraintuitiva:** este backend **no usa las vistas
genéricas de Django**. No hay `ListView` con `paginate_by`, ni `CreateView` con `form_class` y
`success_url`. Hay `View` con un `get` y un `post` escritos, y hay `TemplateView` con
`get_context_data`. Los métodos medidos lo confirman: **`get` 78 · `post` 60 ·
`get_context_data` 26**, y **cero** `form_valid` / `get_success_url` / `get_queryset` en las 250.

El motivo no es descuido: **el CRUD —que es justo lo que las CBV genéricas resuelven— ya lo resuelve
el framework de `backend-controllers.md`**. Lo que queda fuera del framework es precisamente lo que
no encaja en una CBV genérica. §5b de aquel documento ya escribió esa frontera y **esta sección no
la reabre**: si es "una tabla de un modelo con su formulario", va por el framework; si no, es una de
estas 250.

Precedentes: `module/views.py:44` (`ControllerView(View)`) · `module/views.py:31`
(`ModuleTemplateView(TemplateView)`) · `dashboard/views.py:1319` (`DashboardTemplateView`).

### 2.3 Dónde vive el acotado por usuario — un manager, no la vista

Es la diferencia estructural más importante con DRF y la que hace que §1.2 (*"el filtro por dueño
solo puede vivir en `get_queryset()`"*) **no se aplique literalmente aquí**.

`core/managers.py:42-43` engancha dos métodos a **todos** los managers del proyecto:

```python
# core/managers.py:42-43 — se le añaden a la clase Manager de Django, así que los tiene TODO modelo
Manager.for_user = for_user
Manager.for_request = for_request
```

Y `for_user` (`core/managers.py:9`) es donde está la lógica de quién ve qué:

```python
def for_user(self, user):
    base_qs = self.get_queryset()
    if issubclass(self.model, CRUDModel):
        ...
        if user.is_superuser or shared_records_conf.check_organization_perms(...):
            return base_qs
        qs = base_qs.filter(Q(owner=user) | Q(shared_property=user))     # las suyas
        ...                                                              # + las compartidas
        return qs.distinct()
    return base_qs
```

Consecuencias, y las tres importan al escribir una vista nueva:

1. **El acotado es opt-in por llamada.** `Modelo.objects.all()` NO está acotado;
   `Modelo.objects.for_user(request.user)` sí. No hay manager por defecto que lo haga solo, así que
   **`.all()` en una vista es una decisión, aunque casi nunca sea una decisión consciente**.
2. **El framework CRUD lo llama UNA vez para las 356 tablas** — `controller/controllers.py:467`:
   `def get_queryset(self): return self.manager.for_user(self.request.user)`. De ahí la afirmación
   de §1.2: de 356 oportunidades de olvido se pasa a una.
3. **Fuera del framework hay que acordarse.** Medido: **390 usos de `for_request` y 25 de
   `for_user`** en el repo. Es la vía normal, y está bien usada — pero es disciplina, no mecanismo.

Precedentes: `core/managers.py:9` y `:42` · `controller/controllers.py:467` ·
`core/forms.py:75` (`value.for_request(self.request)` — el acotado llega hasta los desplegables).

### 2.4 Los permisos, en el `dispatch()`

Sin DRF no hay `permission_classes`, así que el permiso se comprueba a mano y el sitio dominante es
`dispatch()`, antes de que corra nada. Medido: **101 apariciones** de
`PermissionDenied` / `login_required` / `LoginRequiredMixin` en los `views.py`.

```python
# api_portal/views.py:49 — el patrón: se valida ANTES de super().dispatch(), y se LANZA
class APIPortalView(View):
    def dispatch(self, request, *args, **kwargs):
        from rest_framework_simplejwt.authentication import JWTAuthentication
        if JWTAuthentication().authenticate(self.request):
            return super().dispatch(request, *args, **kwargs)
        raise PermissionDenied()
```

Lo mismo hace el framework CRUD cuando la tabla no está registrada (`module/views.py:50`:
`raise PermissionDenied`). **Lanzar y no devolver** es la misma regla que §1.3 pide en DRF, por otra
razón: un `return HttpResponse(status=403)` se salta el `handler403` del proyecto.

⚠️ **Lo que NO se puede afirmar:** que esas 101 cubran las 250 vistas. No lo he comprobado vista por
vista y el conteo es de apariciones, no de clases protegidas. Lo que sí está medido es que **no hay
un default cerrado equivalente al `DEFAULT_PERMISSION_CLASSES` de DRF**: en el arquetipo servidor, una
vista nueva a la que se le olvide el permiso queda abierta y **nada avisa**. Es el mismo agujero que
§1.2 describe para el queryset, un piso más arriba, y aquí no tiene red.

---

## 3. El único `ViewSet` — qué se hizo con él, y qué enseña

Con **1 `ViewSet` en 1.401 ficheros**, ese caso acota el arquetipo API mejor que cualquier regla
escrita: **DRF entró solo para el portal del trabajador**, un cliente externo que consume JSON con
token; todo lo demás del producto es HTML servido.

```python
# api_portal/views.py:56 — la clase entera, literal
class WorkerViewSet(viewsets.ModelViewSet):
    queryset = Worker.objects.all()
    serializer_class = WorkerSerializer
    lookup_field = 'encrypted_personal_data__identif_document'
```

Enrutado en `module/urls.py:15` (`router.register(r'api_portal', api_views.WorkerViewSet)`) y con
los defaults de `evopreven/settings.py:873`:

```python
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': ['api_portal.permissions.IsPortalUser'],
    'DEFAULT_AUTHENTICATION_CLASSES': ('rest_framework_simplejwt.authentication.JWTAuthentication',),
}
```

Contrastado contra las reglas de §1, y el resultado es útil justo porque no sale limpio:

| Regla de §1 | Este `ViewSet` | Lectura |
|---|---|---|
| `be-view-permisos-por-defecto` | ✅ **cumple** | Hay `DEFAULT_PERMISSION_CLASSES` y es cerrado: `IsPortalUser` exige `is_authenticated and is_portal` (`api_portal/permissions.py:7`) |
| `be-view-paginacion` | ❌ falta | No hay `DEFAULT_PAGINATION_CLASS` |
| `be-api-exception-handler` | ❌ falta | No hay `EXCEPTION_HANDLER`, así que el sobre `{"errors": …}` de §1.3 no existe en este backend |
| `be-view-queryset-sin-filtrar` | ❌ **es el caso de libro** | `queryset = Worker.objects.all()`, sin `get_queryset()` |

**La última fila es la que vale el apartado.** §1.2 ya afirmaba —sin poder citarlo— que *"el único
punto del sistema donde el scoping fila-a-fila no se aplicaba era, exactamente, el único `ViewSet`
que no pasaba por esa base"*. Ahora está localizado: `api_portal/views.py:58`. Es literalmente la
única vista del backend que no llama a `for_user`/`for_request` ni pasa por
`controller/controllers.py:467`, y su `lookup_field` es el **documento de identidad** del trabajador.

⚠️ **Lo que afirmo y lo que no.** He leído esas cuatro líneas, el permiso y la ruta: `IsPortalUser`
comprueba **rol**, no **pertenencia**, y el queryset no está acotado. Lo que **no** he hecho es
ejecutar una petición, así que **no afirmo que sea explotable**: puede haber middleware, una
comprobación en el serializer o una restricción de red que no he visto, y el repo es material de
cliente. Se reporta como **lo observado en el código**, no como vulnerabilidad confirmada — y como
la mejor razón que hay para que `be-view-queryset-sin-filtrar` exista.

---

## 4. Cómo se comprueba — y a qué arquetipo aplica cada regla

```bash
python3 .claude/patterns/stack/pattern_check_backend.py --rules be-view-queryset-sin-filtrar,\
be-view-permisos-por-defecto,be-view-paginacion,be-svc-escritura-en-vista
```

| Regla | **Arquetipo** | Estado | Qué detecta |
|---|---|---|---|
| `be-view-queryset-sin-filtrar` | **API-DRF** | **débil** | AST: clase de vista con `queryset = X.objects.all()` y sin `get_queryset()` |
| `be-view-permisos-por-defecto` | **API-DRF** | activo | settings sin `DEFAULT_PERMISSION_CLASSES`, o `permission_classes = [AllowAny]` sin un comentario que lo justifique al lado |
| `be-view-paginacion` | **API-DRF** | activo | settings sin `DEFAULT_PAGINATION_CLASS` |
| `be-api-exception-handler` | **API-DRF** | activo | settings sin `EXCEPTION_HANDLER` (el sobre `{"errors": …}` del contrato con el frontend) |
| `be-view-error-sin-excepcion` | **API-DRF** | activo | AST: `return Response(..., status=4xx/5xx)` dentro de una clase de vista — esquiva el handler |
| `be-view-base-de-casa` | **API-DRF** | **débil** | vista que hereda de DRF directamente en un proyecto que **ya tiene** una vista base compartida con `get_queryset()` |

> ⚠️ **Las seis miran solo DRF, y hasta hoy eso no estaba escrito en ninguna parte.** Cuatro de ellas
> leen el bloque `REST_FRAMEWORK` de settings y las otras dos hacen AST sobre clases `*ViewSet` /
> `*APIView`. En un backend del arquetipo servidor **no disparan nunca** — ni deben. El riesgo real
> no es el falso positivo: es leer el catálogo en verde y concluir que las vistas están cubiertas
> cuando el 99,6% de ellas no las mira nadie. Las candidatas que cerrarían ese hueco están en §4.1,
> y **todas en `sombra`**.

### 4.1 Candidatas del arquetipo SERVIDOR — propuestas, en `sombra`

No implementadas: `pattern_check_backend.py` es de otro frente y **este documento no lo toca**.
Cada una con su recuento sobre las 250 vistas de la referencia, que es lo que decide si la regla es
viable o si la mala es la regla (`patterns/README.md` §2: >20-30 sitios ⇒ regla mal enunciada).

| id | Enunciado | Infractores hoy | Veredicto |
|---|---|---:|---|
| `be-view-servidor-en-su-fichero` | Las clases de vista viven en el `views.py` de su app | **0** / 250 | ✅ viable — 100% de disciplina, caza la primera regresión |
| `be-view-servidor-objects-all` | Una vista de servidor que consulta `Modelo.objects.all()`/`.filter()` directamente en vez de `.for_user(...)` / `.for_request(...)`, existiendo ya un manager con esos métodos en el proyecto | **sin medir** (ver aviso) | ⚠️ **NO proponer todavía** |
| `be-view-servidor-permiso-en-dispatch` | Una vista de servidor que no comprueba permiso ni hereda de una base que lo haga | **sin medir** | ⚠️ **NO proponer todavía** |

**Por qué dos de las tres se quedan sin número, y no es pereza.** Las dos exigen decidir *por vista*
si su acceso está acotado, y eso no se resuelve con un `ClassDef`: hay que seguir de dónde sale cada
queryset y qué hace la base de la que hereda. Publicar un recuento estimado aquí sería exactamente el
error que §0 corrige — así que se declaran como enunciado y **se marcan sin medir**. Una regla sin
recuento no puede promoverse: `patterns/README.md` §2 y §3 lo piden antes de activar nada.

Entrada para `catalog.yaml` de la única medida (mismo formato que `_catalog-entries-backend.yaml`):

```yaml
  - id: be-view-servidor-en-su-fichero
    enunciado: "Las clases de vista de servidor viven en el views.py de su app"
    eje: 1-estructura
    mecanismo: ast
    ambito: "**/*.py"
    dominancia: "250/250 = 100% (evo-preven, UN repo — por eso sombra, GAP-1)"
    estado: sombra
    baseline: null
    precedentes:
      - "resources/code-refference/evo-preven-develop.zip → evopreven/module/views.py:44"
      - "resources/code-refference/evo-preven-develop.zip → evopreven/api_portal/views.py:49"
    source: ".claude/patterns/stack/backend-vistas.md"
    doc: stack/backend-vistas.md
```

`be-view-queryset-sin-filtrar` es **débil a propósito** (avisa, no bloquea): hay catálogos que sí
son globales y legítimos, y una regla que bloquee ahí marcaría código correcto. Su daño es alto
pero su tasa de falsos positivos también, así que avisa y deja decidir. Es la aplicación literal
de la regla de inversión del README: cuando una regla marcaría muchos sitios buenos, la que está
mal es la regla.

## 5. Excepciones legítimas

- **Recurso público de solo lectura.** La razón se escribe al lado; el checker acepta un
  comentario en la línea:

```python
permission_classes = [AllowAny]  # público: tarifas de la web, sin ningún dato de cliente
```

- **Catálogo global de verdad** (países, tipos de IVA), donde `objects.all()` es la respuesta
  correcta: `# pattern-exempt: be-view-queryset-sin-filtrar — catálogo global, sin dueño`.
- **Endpoint que devuelve un objeto único** (`/me/`, un healthcheck): no hay lista que paginar.
- **Vista que no debe pasar por la base de casa** (catálogo público, receptor de webhook, endpoint
  de salud): `# pattern-exempt: be-view-base-de-casa — endpoint público sin dueño que filtrar`.

## 6. Lo que este documento NO dice

- **No recomienda un arquetipo sobre el otro.** Los dos son de primera clase (`stack/README.md`).
  Lo que sí dice es que un backend nuevo **elige uno** y que mezclarlos sin decidirlo produce
  exactamente lo de §3: un `ViewSet` suelto que no pasa por el acotado del resto del sistema.
- **El arquetipo servidor está medido en un solo repo** (GAP-1). Sus candidatas van en `sombra` y
  ninguna debe promoverse con lo que hay hoy.
- **No hay comprobador nuevo escrito.** §4.1 son enunciados con su ámbito; falta implementarlos y
  pasarles el `--self-test` (FPR <5-10%). Sin eso son texto, no gate.
- **No se ha ejecutado nada del backend de referencia**, solo leído. Todo lo de §3 es lectura de
  código: dónde acaba en producción no lo sé.
- **No cubre `Settings`+`Controller`** (589 clases): es `backend-controllers.md`.

## Related

- `backend-formularios-django.md` — **la otra mitad del arquetipo servidor**: la puerta por donde
  entran los datos que estas 250 vistas no validan
- `backend-controllers.md` — el framework CRUD (82 de las 250 vistas cuelgan de él) y su §5b, la
  frontera de cuándo NO se escribe una vista
- `backend-modelos.md` §"de qué hereda un modelo" — la base que trae el campo por el que se filtra;
  sin ella, el filtrado por dueño de esta página no puede existir
- `backend-servicios.md` (qué NO le toca a la vista) · `backend-serializers.md` (`read_only_fields`)
- skill `code-review-gate` (§Seguridad Django/DRF) (permisos, IDOR) · skill `multi-tenant-context` si el proyecto
  aísla por tenant · skill `django-orm` (`references/crud.md` y `assets/crud-template.py`: la plantilla del CRUD y sus filtros)
- `_archive/2026-10-19/agents/_deprecated-README.md` — de dónde salió §"La URL y el código de estado" y qué se retiró

---

_Pattern doc v2.0 · 2026-08-25 · v1.0 describía SOLO el arquetipo DRF y no lo decía, así que sus
seis reglas parecían cubrir "las vistas" cuando miran 1 clase de 251 en el backend de referencia.
v2.0 no borra nada de DRF: lo **etiqueta** (§1, §4) y añade el arquetipo servidor que faltaba (§2),
medido con AST sobre los 1.401 ficheros `.py` de
`resources/code-refference/evo-preven-develop.zip`. Las cifras del encargo (131 vistas, 4
serializers) no reproducen; las reales y su comando están en §0. Todo lo nuevo nace en `sombra`
(GAP-1: un solo repo), y dos de las tres candidatas van **sin medir** a propósito._
