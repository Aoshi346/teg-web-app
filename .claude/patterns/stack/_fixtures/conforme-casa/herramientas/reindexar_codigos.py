"""Recalcula el código visible de los expedientes que se quedaron sin él.
# runner: manual, con `python manage.py shell < herramientas/reindexar_codigos.py`
#         tras una importación masiva. NO está en cron.

Esa cabecera es toda la regla `be-script-sin-runner`. No prohíbe que existan scripts sueltos —la
doc de Django documenta `manage.py shell < script.py`, así que el script funciona— y no obliga a
promoverlos a comandos: solo pide que digan cómo se ejecutan, para que dentro de seis meses nadie
tenga que adivinar si esto lo lanza un cron, el CI, alguien a mano, o ya nadie.
"""
from expedientes.models import Expediente

for expediente in Expediente.objects.filter(codigo__isnull=True).iterator(chunk_size=500):
    expediente.save(update_fields=["codigo"])
