---
paths:
  - "**/views.py"
  - "**/views/*.py"
  - "**/vistas.py"
  - "**/viewsets.py"
  - "**/serializers.py"
  - "**/serializers/*.py"
  - "**/permissions.py"
  - "**/throttling.py"
  - "**/settings_prod*.py"
  - "**/settings/prod*.py"
  - "**/*.tsx"
  - ".claude/scripts/check_django_seguridad.py"
  - ".claude/gate-django.json"
---
# Seguridad del código de la aplicación — Django, DRF y React

> **Cuándo aplicar:** al escribir o revisar una **vista, un serializer, un permiso o un componente
> React**, que es donde se escribe el código que OWASP audita; y antes de un release de un Django
> (§1, el gate G3). Cubre los settings de seguridad de producción, lo que DRF deja abierto por
> defecto y lo que un componente no debe pintar ni abrir sin mirar.
>
> **NO aplicar:** para secretos, exposición de red y MCP → `security.md` (esta rule existe porque
> aquella no se carga al tocar `views.py`, `serializers.py` ni un `.tsx`) · para el contrato HTTP
> —verbos, 405, credenciales en la URL, idempotencia— → `api-http-contract.md` · para **quién ve
> qué fila** (objeto y tenant) → `patterns/stack/backend-vistas.md` §1.2 y `multi-tenant-context` ·
> para la seguridad del harness → `agent-security.md`.
>
> **Relacionado:** `scripts/check_django_seguridad.py` (G3) · `patterns/stack/backend-serializers.md`
> (`fields = "__all__"`) · `patterns/stack/saneado.md` (HTML y esquemas de enlace) ·
> `patterns/stack/frontend-auth.md` (el token fuera de `localStorage`) ·
> `patterns/stack/backend-candado-datos-reales.md` · agentes `sofia-pentester`, `code-review-gate`.

## 1. Antes de un release: G3

```bash
python3 .claude/scripts/check_django_seguridad.py . --settings config.settings.production \
        --python .venv/bin/python --env-file <variables de CI>     # 0 · 1 hallazgos · 2 no medido
```

Corre el check de despliegue de Django (`check --deploy --fail-level WARNING`) con los settings de
**producción** y añade lo que ese check no mira: avisos de seguridad silenciados, la CSP, el permiso
por defecto de DRF, el límite de peticiones de cada vista pública, el límite de intentos de login y
el segundo factor del admin. **El check de Django es necesario, no suficiente** (lo dice su propia
documentación): en 6.0 solo valida que `SECURE_CSP` sea un diccionario, no que exista.

Lo lanza el script —ya no por el `deny` `Bash(*deploy*)`, estrechado en la sub-ola 2.02 (MO-8)—
porque necesita el python del proyecto, el `--env-file` y convertir cada aviso en un hallazgo; el
`check --deploy` suelto sí se puede teclear, y desde el 22-10 también con
`--settings config.settings.production`: el `Bash(*production*)` del deny se estrechó a patrones concretos
(un `manage.py migrate`, `flush` o `loaddata` con esos settings sigue denegado). Un 2 no es un verde: sin settings que importen, sin manage.py o
con un python sin Django, nadie ha mirado nada. Lo que resuelve otra capa (la CSP o el HSTS que pone
nginx) se declara en `.claude/gate-django.json` con su razón, y una excepción que ya no cubre nada
es un fallo. Lo que G3 **no** comprueba está en su cabecera.

## 2. Los settings de producción de casa

| Setting | Valor | Por qué | Lo mira |
|---|---|---|---|
| `DEBUG` | `False`, leído del entorno con `False` por defecto | Con `True`, cada error enseña settings, rutas y variables | `security.W018` |
| `SECRET_KEY` | 50+ caracteres aleatorios, del entorno | Firma sesiones, CSRF y enlaces de restablecer contraseña | `W009` |
| `SECRET_KEY_FALLBACKS` | Vacío, salvo **durante una rotación** | Rotar sin echar a todos: la nueva en `SECRET_KEY`, la vieja aquí; se quita al caducar lo firmado con ella (sesiones, enlaces) | `W025` |
| `SESSION_COOKIE_SECURE` · `CSRF_COOKIE_SECURE` | `True` | Que la cookie no viaje nunca por HTTP | `W012` · `W016` |
| `SECURE_HSTS_SECONDS` | `31536000` (+ `INCLUDE_SUBDOMAINS`, `PRELOAD` si se pide la precarga) | El navegador no vuelve a intentar HTTP | `W004` · `W005` · `W021` |
| `SECURE_SSL_REDIRECT` | `True`, o la redirección en el proxy **declarada** | Si la hace nginx, `SECURE_PROXY_SSL_HEADER` y excepción con la ruta de su config | `W008` |
| CSP | Django ≥ 6.0: `SECURE_CSP` + `ContentSecurityPolicyMiddleware`. **5.2 LTS** (el stack de casa): django-csp ≥ 4, `CONTENT_SECURITY_POLICY` + `csp.middleware.CSPMiddleware` | Un XSS que entra se ejecuta con todos los permisos de la página; la CSP es lo que lo frena | `G3-CSP-*` |
| Límite de intentos | django-axes: la app, `AxesMiddleware` **al final** y `AxesStandaloneBackend` **el primero** | Un diccionario contra una cuenta no lo frena el límite por IP | `G3-SIN-LIMITE-INTENTOS` · `axes.W002`/`W003` |
| Segundo factor | django-otp (`OTPAdminSite`) o two-factor-auth para staff y admin | Una contraseña filtrada no basta para entrar como staff | `G3-SIN-2FA` |

```python
# settings/production.py — Django 5.2 LTS (con 6.0, SECURE_CSP y su middleware en vez de django-csp)
from csp.constants import NONE, SELF
SECRET_KEY = os.environ["SECRET_KEY"]
SECRET_KEY_FALLBACKS = [k for k in os.environ.get("SECRET_KEY_FALLBACKS", "").split(",") if k]
DEBUG = False
SECURE_HSTS_SECONDS, SECURE_HSTS_INCLUDE_SUBDOMAINS = 31536000, True
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = CSRF_COOKIE_SECURE = True
INSTALLED_APPS += ["axes", "django_otp", "django_otp.plugins.otp_totp", "csp"]
MIDDLEWARE += ["django_otp.middleware.OTPMiddleware", "csp.middleware.CSPMiddleware",
               "axes.middleware.AxesMiddleware"]                     # axes, el último
AUTHENTICATION_BACKENDS = ["axes.backends.AxesStandaloneBackend",    # axes, el primero
                           "django.contrib.auth.backends.ModelBackend"]
CONTENT_SECURITY_POLICY = {"DIRECTIVES": {"default-src": [SELF], "script-src": [SELF],
                                          "frame-ancestors": [NONE]}}
```

La versión completa, medida con G3 en verde sobre un `startproject` recién creado (que da 10
hallazgos tal cual sale), está en el template: `_archive/2026-10-20/medicion-2.29/g3/settings_prod.py`.

## 3. DRF: cerrado por defecto, y lo público con su tasa

- **`DEFAULT_PERMISSION_CLASSES` = `IsAuthenticated`** (o un permiso propio cerrado). El valor por
  defecto de DRF es `AllowAny`: la vista que olvide `permission_classes` queda abierta a internet.
- **Cada `AllowAny` lleva su razón escrita al lado** (`be-view-permisos-por-defecto`) **y su límite
  de peticiones**: `throttle_scope = "<nombre>"` con `ScopedRateThrottle` activo y la tasa en
  `DEFAULT_THROTTLE_RATES`. Vale igual para `@permission_classes([AllowAny])` en una vista de función
  (con `@throttle_classes`) y para `@action(permission_classes=[AllowAny])`.
- **Un `throttle_scope` sin `ScopedRateThrottle` no limita nada**, y sin la tasa DRF lo descubre en
  la primera petición. Es un campo que parece funcionar (`verification.md` §Lo importante no es que
  FALTE algo): G3 lo marca como `G3-THROTTLE-DECORATIVO`.
- El throttle global (`AnonRateThrottle` para todo) no basta: el login, el alta y el «olvidé mi
  contraseña» necesitan una tasa propia, mucho más baja que la del resto de la API.
- Quién ve **qué fila** no lo decide el permiso de clase: `get_queryset()` filtrado por dueño o
  tenant y `has_object_permission` (`backend-vistas.md` §1.2).

## 4. Serializers: lo que entra y lo que sale

- **Lista blanca de campos**, nunca `fields = "__all__"` (`backend-serializers.md`, `be-ser-fields-all`):
  publica hoy lo que alguien añada al modelo mañana.
- **El dueño, el tenant y los permisos no entran por el payload**: `read_only_fields` y se ponen en
  `perform_create`/`save(owner=request.user)`. Un `is_staff`, un `tenant_id` o un `owner` escribibles
  son una escalada de privilegios con un `PATCH`.
- Un fichero subido se valida por **contenido y tamaño**, no por la extensión ni el `Content-Type`
  que manda el cliente (lo ataca `sofia-pentester`, File Upload Cheat Sheet).

## 5. React (`.tsx`): lista blanca de dominios para todo lo que sale

El esquema (`http`/`https`, nunca `javascript:`) lo valida `saneado.md` al entrar el dato. Falta la
otra mitad: **a qué dominio** se manda al usuario o se pide un recurso cuando la URL viene de datos
—un enlace de un perfil, el `?next=` de después del login, la imagen de un proveedor, un
`window.open`—. Sin lista blanca, es una redirección abierta: el enlace del correo dice tu dominio y
acaba en otro.

```ts
// src/lib/urlSegura.ts — un único sitio decide adónde se puede ir
const DOMINIOS_PERMITIDOS = new Set(['app.ejemplo.es', 'ayuda.ejemplo.es']);

export function urlSegura(valor: string, base = window.location.origin): string | null {
  try {
    const u = new URL(valor, base);                       // relativa → del propio origen
    if (!['http:', 'https:'].includes(u.protocol)) return null;
    if (u.origin === new URL(base).origin) return u.toString();
    return DOMINIOS_PERMITIDOS.has(u.hostname) ? u.toString() : null;
  } catch {
    return null;
  }
}
// const destino = urlSegura(params.get('next') ?? '/') ?? '/';
```

- El HTML que no has escrito tú, solo saneado (`saneado.md`, `fe-html-saneado`).
- `target="_blank"` hacia fuera, con `rel="noopener noreferrer"`.
- Nada de scripts en línea ni `eval`: la CSP del §2 los bloquea, y un componente que los necesita
  obliga a debilitarla para toda la página.
- El token de sesión, fuera de `localStorage` (`frontend-auth.md`, `fe-token-no-en-localstorage`).

## Anti-patterns

- ❌ Dar por seguro un Django porque `check --deploy` sale limpio: no mira la CSP, ni DRF, ni el login.
- ❌ Silenciar `security.W018` (o cualquier `security.*`) en `SILENCED_SYSTEM_CHECKS` para que el
  check pase: G3 lo marca como `G3-CHECK-SILENCIADO`.
- ❌ CSP solo en `Report-Only` «de momento», durante meses: avisa y no bloquea nada.
- ❌ `SECURE_CSP` en un Django 5.2: ese setting no existe antes de 6.0 y no se envía ninguna cabecera.
- ❌ Un `AllowAny` sin `throttle_scope`, o un `throttle_scope` sin `ScopedRateThrottle`.
- ❌ Correr G3 con los settings de desarrollo y llamarlo verde: el script los imprime en la cabecera.
- ❌ Construir un `href` o un `navigate()` con una URL de datos sin pasar por la lista blanca.

---

_Rule version: 1.0 · 2026-10-21 · sub-ola 2.29 de la revisión integral (SE-54, con G3 de SE-48).
Medido: `_archive/2026-10-20/medicion-2.29/`._
