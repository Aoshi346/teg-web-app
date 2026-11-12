# Estructura del proyecto — apps, plantillas, capas y scripts sueltos

> **Cuándo aplicar:** al crear una app, al añadir una plantilla, al mover código entre apps y al
> escribir cualquier `.py` que no encaje en un rol conocido (models, views, forms, tasks…).
>
> **NO aplicar:** para el layout de carpetas. Este documento **no** impone `apps/` ni el split de
> `settings/` — eso son defaults de proyecto nuevo, y el porqué está en `README.md` §"Los cuatro
> defaults que NO son reglas".
>
> **Relacionado:** `backend-servicios.md` (dónde vive la lógica) · `backend-signals.md` ·
> `README.md` §"Qué NO copiar de la referencia".

## La regla (una frase)

**Cada fichero tiene un rol y un dueño: ninguna plantilla la sirven dos apps, la capa compartida no
depende del dominio, y todo `.py` que toque la base de datos dice cómo se ejecuta.**

---

## 1. Dos apps no sirven la misma ruta de plantilla

**Es el bug más caro de diagnosticar de todo el catálogo, porque no falla.**

Django resuelve las plantillas de app por orden de `INSTALLED_APPS`: si dos apps tienen un fichero
con la **misma ruta relativa** dentro de su `templates/`, gana la primera y la otra queda muerta.
No hay error, no hay warning, no hay log. Editas el fichero, guardas, recargas… y no pasa nada.

Medido en el backend de referencia: **3 rutas duplicadas, 2 con contenido distinto**. La peor son
34 líneas de un widget que **no se renderizan jamás**. Otra era un fichero huérfano que además
llevaba datos personales escritos a mano, así que borrarlo fue un arreglo de seguridad gratis.

```
❌  risks_management/templates/widgets/dichotomic_widget.html   ← 34 líneas muertas
    health/concepts/templates/widgets/dichotomic_widget.html    ← esta es la que se ve

✅  core/templates/core/base.html
    expedientes/templates/expedientes/detalle.html
```

**La prevención cuesta un directorio:** dentro de `templates/`, un subdirectorio con el nombre de
la app. Es la convención que documenta el propio Django y existe exactamente por esto. Con ella la
colisión es imposible por construcción.

Si el override entre apps es **deliberado** (extender una plantilla de una app de terceros
vendorizada, por ejemplo), se declara donde se hace:

```html
<!-- pattern-exempt: be-tpl-ruta-duplicada — override deliberado del widget de `concepts` -->
```

## 2. La capa compartida no importa hacia el dominio (en sombra)

Un proyecto Django mediano acaba con una capa de infraestructura propia —`core`, `common`,
`shared`— de la que cuelgan las apps de dominio. La dependencia tiene un sentido: **dominio →
compartido**. Cuando se invierte, aparece un ciclo de imports, y el ciclo se parchea metiendo
imports dentro de las funciones.

Medido en la referencia: **38 de 46 apps en un único componente fuertemente conexo**, y **430 de
1.690 imports entre apps (25%) diferidos dentro de funciones** para romper ciclos, sin un comentario
que lo explique. Consecuencia mecánica que importa más que la estética: **no existe ninguna unidad
importable en aislamiento — por eso no hay tests.**

Cómo se declara la capa compartida: con el marcador que ya existe, en el `apps.py` de la app.

```python
"""Capa compartida del proyecto.
# pattern-layer: shared
"""
```

**No hay ningún YAML que mantener**, y es deliberado: la lista de apps compartidas cambia con el
proyecto, y un fichero de configuración aparte se desincroniza. El día que `core` deje de ser
infraestructura, se borra esa línea.

> **Esta regla arranca en SOMBRA: mide, no bloquea.** Y así se queda hasta que alguien decida lo
> contrario **con el número delante**. El motivo es honesto: en un proyecto existente, el coste no
> es el checker (40 líneas) sino la **lista inicial de excepciones** — en la referencia serían 126
> entradas, veinte veces la única lista viva que tenemos. En sombra la fricción es cero y la
> pregunta que responde ya vale ("¿el enredo crece?"). Promoverla a bloqueante exige un criterio
> duro escrito de antemano, no un "ya veremos".
>
> **Alternativa razonable si no quieres mantener checker propio:** `import-linter` con un contrato
> `forbidden` hace lo mismo, a cambio de una dependencia más y de salirse de nuestro vocabulario
> `sombra`/`débil`/`activo`.

**Lo que la regla NO mira:** los imports diferidos dentro de funciones. Son la señal del ciclo,
pero marcarlos sería castigar a quien ya apagó el fuego. Se mide el acoplamiento real —el import a
nivel de módulo—, no el parche.

## 3. Un monkeypatch a Django es un efecto global

```python
# ❌ core/managers.py
from django.db.models import Manager
Manager.for_user = for_user          # ← para TODO el proceso
```

Inyectar un método en una clase de Django afecta a `contrib.auth`, al admin y a cualquier librería
de terceros que se cargue después. Tres daños concretos, los tres medidos en la referencia:

1. Desde `Expediente.objects.for_user(...)` **no hay forma de llegar a la definición** con "ir a
   definición". El método no aparece en ninguna búsqueda de texto útil.
2. Un choque de nombre con otra librería es **silencioso y depende del orden de importación**.
3. Cuando el parche es **seguridad** —el otro caso real era sustituir
   `FileField.default_validators` por una lista negra de extensiones— la protección depende de que
   ese módulo se importe antes de que se declare cualquier `FileField`. Funciona por posición en
   `INSTALLED_APPS`, no por diseño. Y una lista **negra** de extensiones no cubre `.svg`, `.html`,
   las dobles extensiones ni el contenido real del fichero.

Un `BaseManager`/`BaseQuerySet` explícito del que hereden los modelos da lo mismo sin el efecto
global. La regla es **débil**: desmontar un monkeypatch que ya toca cientos de ficheros no es una
tarde, y lo que pide de entrada es que sea **visible y esté comentado**, no que desaparezca hoy.

## 4. Todo `.py` que toque el ORM dice cómo se ejecuta

Esta regla es **lo que sobrevivió** de una propuesta mayor que se cayó al verificarla. Merece
contarse, porque el descarte enseña más que la regla:

> **✘ Descartada:** *"el código operacional vive en `management/commands/`; un `.py` fuera de una
> app que importe modelos es un hallazgo"*.
>
> **Por qué se cayó** (`README.md` §"Descartes" tiene la refutación completa): su premisa central
> era falsa y comprobable — se afirmaba que sin `django.setup()` un script no puede tocar el ORM, y
> la doc de Django documenta `manage.py shell < script.py`. El "74 ficheros inejecutables" no medía
> ficheros muertos: medía *"ficheros que no contienen la cadena `django.setup()`"*. Y el remedio
> era peor: promover a comandos oficiales unos scripts reconocidamente basura los haría aparecer en
> `manage.py help` —incluido uno que vacía una cola republicando mensajes—, que es convertir un
> cable pelado en un botón rojo sin tapa.

Lo que sí aguanta es mucho más modesto, y por eso entra:

```python
"""Recalcula el código visible de los expedientes que se quedaron sin él.
# runner: manual, con `python manage.py shell < herramientas/reindexar_codigos.py`
#         tras una importación masiva. NO está en cron.
"""
```

Una línea. No prohíbe `scripts/`, no obliga a mover nada y no presupone ningún layout: solo pide
que el fichero diga si lo lanza un cron, el CI, alguien a mano — o si ya no lo lanza nadie. Ese es
justo el conocimiento que se pierde y que después nadie se atreve a borrar.

Vale también `django.setup()` explícito, o estar bajo `management/commands/`.

## 5. Nada de MongoDB en el stack canónico

El stack de casa es **PostgreSQL puro**, y la exclusión es una decisión, no un olvido. Los tres
usos reales que justificaban Mongo en la referencia los cubre PostgreSQL:

| Uso | Sustituto |
|---|---|
| Auditoría automática de ~200 modelos | `django-simple-history` sobre tablas normales |
| Catálogo grande de solo lectura (CIE/ICD) | tabla con índice **GIN** |
| Formularios dinámicos guardados como documento | `JSONField` — es exactamente su caso |

El detalle de qué cambia al quitarlo (y qué **sí** se traslada) está en `README.md` §"Quitar
Mongo". La regla es **débil**: si un proyecto usa Mongo de verdad, se exime con su razón.

## Cómo se comprueba

```bash
python3 .claude/patterns/stack/pattern_check_backend.py --rules be-tpl-ruta-duplicada,\
be-capa-compartida-importa-dominio,be-script-sin-runner,be-py-monkeypatch-django,be-no-mongo
```

| Regla | Estado | Qué detecta |
|---|---|---|
| `be-tpl-ruta-duplicada` | activo | dos directorios de app (con `apps.py`/`models.py`) que sirven la misma ruta bajo `templates/` |
| `be-capa-compartida-importa-dominio` | **sombra** | import **a nivel de módulo** de una app de dominio desde una app marcada `# pattern-layer: shared` |
| `be-script-sin-runner` | débil | `.py` con rol desconocido que toca el ORM y no declara `# runner:` ni `django.setup()` |
| `be-py-monkeypatch-django` | débil | asignación a nivel de módulo sobre un atributo de algo importado de `django.*` |
| `be-no-mongo` | débil | import de `pymongo`/`bson`/`djongo`, o `"ENGINE": "djongo"` |

**Límites conocidos, sin adornos:**

- `be-tpl-ruta-duplicada` es una regla de **proyecto**: se calcula sobre todo el repo, no sobre el
  diff. Desde dos ficheros cambiados no se puede afirmar que dos apps colisionan.
- `be-script-sin-runner` decide "rol desconocido" contra una lista de nombres de fichero
  deliberadamente **generosa** (`models`, `views`, `utils`, `helpers`, `reports`, `controllers`…).
  Su falso positivo es acusar de "script" a un módulo normal, y eso quema la regla en dos días. La
  contrapartida es que un script llamado `utils.py` se le escapa.
- `be-py-monkeypatch-django` solo mira **asignaciones a nivel de módulo**. Un parche aplicado
  dentro de una función `ready()` no lo ve.

## Excepciones legítimas

- **Override de plantilla deliberado** → comentario `pattern-exempt` dentro del propio `.html`.
- **Import compartido→dominio inevitable** (un registro central que necesita conocer los modelos):
  `# pattern-exempt: be-capa-compartida-importa-dominio — el registro de tablas necesita el modelo`.
- **Script de exploración que no toca producción**: sigue necesitando su `# runner:`, aunque diga
  `# runner: nadie; se quedó de una investigación de 2026-03, candidato a borrar`. Esa frase es
  información valiosa.
- **Proyecto que usa Mongo de verdad**: `# pattern-exempt: be-no-mongo — el catálogo CIE vive en
  Mongo por <razón>`.

## Related

- `README.md` §"Los cuatro defaults que NO son reglas" (por qué esto NO impone `apps/`) ·
  §"Qué NO copiar de la referencia" · §"Quitar Mongo"
- `backend-signals.md` (registro de receivers en `AppConfig.ready()`) ·
  `backend-servicios.md` (el nombre del fichero es un default, la sustancia es la regla)
