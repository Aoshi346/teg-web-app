"""be-script-sin-runner: toca el ORM y no dice quién lo lanza.

¿Cron? ¿El CI? ¿Alguien a mano una vez en 2024? ¿Ya nadie? No hay forma de saberlo sin preguntar
a quien lo escribió, y ese es justo el conocimiento que se pierde. La regla no prohíbe que exista
—`manage.py shell < script.py` funciona, la doc de Django lo documenta— solo pide una línea que
diga cómo se ejecuta.
"""
from expedientes.models import Expediente

Expediente.objects.filter(estado="borrador").delete()
