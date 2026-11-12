from rest_framework.throttling import SimpleRateThrottle


class LoginAccountThrottle(SimpleRateThrottle):
    """Limita los intentos de login por cuenta, venga de la IP que venga.

    Es la defensa principal contra adivinar contraseñas: detrás de Tailscale Funnel y Caddy no hay
    garantía de que la IP del cliente llegue intacta, así que el límite por IP solo es un respaldo.
    """

    scope = "login_account"

    def get_cache_key(self, request, view):
        email = str(request.data.get("email", "")).strip().lower()
        if not email:
            return None
        return self.cache_format % {"scope": self.scope, "ident": email}


class LoginIPThrottle(SimpleRateThrottle):
    scope = "login_ip"

    def get_cache_key(self, request, view):
        return self.cache_format % {"scope": self.scope, "ident": self.get_ident(request)}
