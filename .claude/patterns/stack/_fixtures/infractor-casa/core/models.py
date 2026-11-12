"""ANTIPATRÓN A PROPÓSITO — banco de pruebas del checker. No copiar nada de aquí.

Las bases de casa SÍ están bien: tienen que existir para que las reglas «de casa» tengan contra
qué comparar. `be-model-base-de-casa` y `be-model-meta-base-de-casa` solo disparan cuando el
proyecto YA tiene una base compartida — en un proyecto nuevo todavía no hay ninguna, y acusar de
no seguir un patrón que aún no existe sería el peor falso positivo posible.

Lo que sí está mal aquí es `TokenApi`: declara caducidad y no la lee nadie.
"""
from django.conf import settings
from django.db import models


class MetaDeCasa:
    default_permissions = ("add", "change", "delete", "view", "relate")


class CRUDModel(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="%(class)s_en_propiedad",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta(MetaDeCasa):
        abstract = True


class CodigoVisibleMixin(models.Model):
    codigo = models.CharField(max_length=32, unique=True, null=True, blank=True)

    class Meta(MetaDeCasa):
        abstract = True

    def save(self, *args, **kwargs):
        if not self.codigo:
            self.codigo = f"EXP-{self.pk or 'NUEVO'}"
        super().save(*args, **kwargs)


class TokenApi(models.Model):
    """be-model-caducidad-no-comprobada: los tres campos están, la interfaz los deja editar…

    …y ninguna vista, servicio, task ni middleware los lee. La autenticación solo mira `activo`.
    Un token con fecha de caducidad puesta sigue funcionando indefinidamente, y quien la puso se
    quedó tranquilo. Un campo de seguridad que se muestra y no se aplica es peor que no tenerlo.
    """

    nombre = models.CharField(max_length=100)
    token_hash = models.CharField(max_length=64, unique=True)
    activo = models.BooleanField(default=True)
    expiration_date = models.DateTimeField(null=True, blank=True)

    class Meta(MetaDeCasa):
        verbose_name = "token de API"
