"""Las bases de casa: de qué hereda un modelo en este proyecto.

Es la decisión estructural que `backend-modelos.md` no cubría cuando iba campo a campo. En un
proyecto con cientos de modelos, de qué heredan determina el día a día más que cualquier
`CheckConstraint` — y, sobre todo, determina si el filtrado por dueño es siquiera POSIBLE: el
manager filtra por `owner`, así que un modelo que no traiga ese campo se queda fuera del scoping
sin que nada lo avise.

Medida que respalda el patrón (backend Django real, 360 modelos): 173 usan cinco combinaciones de
mixins y 357 declaran el mismo `Meta`. Una consistencia del 99% no se consigue pidiéndola en una
guía de estilo; se consigue heredándola.
"""
from django.conf import settings
from django.db import models


class MetaDeCasa:
    """Mixin de `Meta` — el registro de metadatos del modelo, en un solo sitio.

    Aquí van los cinco permisos de casa: `relate` es un quinto verbo propio, porque en un dominio
    con muchos M2M «puedo ver X» y «puedo asociarle Y» son permisos distintos y Django solo trae
    cuatro. Y aquí está el detalle que cuesta caro: **Django crea los permisos por defecto AL
    MIGRAR**. Un modelo cuyo `Meta` no herede de esta base no falla, no avisa y no aparece en
    ningún log — simplemente se queda sin su permiso `relate_<modelo>`; y arreglar la herencia más
    tarde NO crea el permiso que faltó, hay que crearlo explícitamente.

    Es un mixin normal, no una metaclase. El backend de referencia hacía que esta clase heredara
    de `ModelBase` y nunca la usaba como `metaclass=`: heredar de la metaclase no aportaba nada y
    confundía a quien leía. Un mixin plano hace exactamente el mismo trabajo.
    """

    default_permissions = ("add", "change", "delete", "view", "relate")


class CRUDModel(models.Model):
    """Auditoría y propiedad. Todo modelo de dominio hereda de aquí."""

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="%(class)s_en_propiedad",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True,
        related_name="%(class)s_creados",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True,
        related_name="%(class)s_actualizados",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta(MetaDeCasa):
        abstract = True


class CodigoVisibleMixin(models.Model):
    """Código que el usuario final ve y dicta por teléfono (`EXP-1423`).

    ⚠️ Este mixin es la razón de ser de `be-model-bulk-create-invariante`: el código se calcula en
    `save()`, y `bulk_create()` NO llama a `save()`. Las filas insertadas en bloque quedan con el
    código a nulo, nadie protesta —el campo admite nulos— y el fallo aparece meses después, cuando
    alguien busca por un código que no existe.
    """

    codigo = models.CharField(max_length=32, unique=True, null=True, blank=True)

    class Meta(MetaDeCasa):
        abstract = True

    def save(self, *args, **kwargs):
        if not self.codigo:
            self.codigo = f"{self._meta.model_name.upper()[:3]}-{self.pk or 'NUEVO'}"
        super().save(*args, **kwargs)


class TokenApi(models.Model):
    """Credencial máquina-a-máquina. La caducidad la aplica `core/permissions.py`.

    Vive en la capa compartida y no en una app de dominio a propósito: es infraestructura, y así
    el decorador que la comprueba no tiene que importar hacia abajo.
    """

    nombre = models.CharField(max_length=100)
    token_hash = models.CharField(max_length=64, unique=True)
    activo = models.BooleanField(default=True)
    expiration_date = models.DateTimeField(null=True, blank=True)

    class Meta(MetaDeCasa):
        verbose_name = "token de API"
