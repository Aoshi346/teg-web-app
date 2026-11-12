# docker-compose y variables de entorno — patrón de casa

> **Cuándo aplicar:** al tocar `docker-compose*.yml`, `settings/*.py` o cualquier fichero que lea
> configuración del entorno.

## La regla (una frase)

**Ningún secreto en un fichero versionado, ninguna imagen sin versión fija, y toda variable que el
código lee está documentada en `.env.example`.**

Las tres van juntas porque las tres responden a la misma pregunta: *¿puede otra persona —o el
mismo agente mañana— levantar esto y obtener exactamente lo mismo?* Si la respuesta es no, cada
sesión empieza depurando el entorno en vez de trabajar.

## Implementación de referencia

`_fixtures/conforme/docker-compose.yml`:

```yaml
services:
  db:
    image: postgres:16.3-alpine
    environment:
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?falta POSTGRES_PASSWORD en .env}
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $${POSTGRES_USER} -d $${POSTGRES_DB}"]
      interval: 5s
      timeout: 3s
      retries: 10

  backend:
    build: ./backend
    env_file:
      - .env
    depends_on:
      db:
        condition: service_healthy
      cache:
        condition: service_healthy
      broker:
        condition: service_healthy
```

Y en settings (`_fixtures/conforme/config/settings/base.py:11`):

```python
env = environ.Env()

SECRET_KEY = env("DJANGO_SECRET_KEY")            # sin default: si falta, no arranca
DEBUG = env.bool("DJANGO_DEBUG", default=False)  # el default seguro es el restrictivo
```

Cuatro decisiones:

- **`${POSTGRES_PASSWORD:?mensaje}`** falla al levantar, con un mensaje que dice qué falta. La
  alternativa (`${POSTGRES_PASSWORD:-postgres}`) arranca con una contraseña por defecto y nadie se
  entera hasta que esa contraseña está en producción.
- **`SECRET_KEY` sin default.** Un default hace que el sistema arranque mal configurado, que es
  peor que no arrancar: el fallo se descubre tarde y en otro sitio.
- **`condition: service_healthy`** con un `healthcheck` real. La forma corta (`depends_on: [db]`)
  solo espera a que el **contenedor** exista, no a que Postgres acepte conexiones — así que el
  backend arranca, no conecta y muere. Es el fallo típico de "la primera vez nunca levanta, dale
  otra vez", que además hace irreproducible cualquier arranque automatizado.
- **Versiones exactas** (`postgres:16.3-alpine`). Con `:latest`, el mismo compose levanta cosas
  distintas en semanas distintas y un fallo deja de ser reproducible.

`.env.example` es documentación ejecutable: se versiona, lista **todas** las claves (aunque sea
vacías) y `.env` va al `.gitignore`.

## El antipatrón que sustituye

`_fixtures/infractor/docker-compose.yml` y `config/settings/base.py`:

```yaml
services:
  db:
    image: postgres:latest
    environment:
      POSTGRES_PASSWORD: supersecreto123      # en git, para siempre
  cache:
    image: redis                              # sin tag: hoy 7.x, mañana lo que salga
  backend:
    depends_on:
      - db                                    # no espera a que Postgres esté listo
      - cache
```

```python
SECRET_KEY = "django-insecure-4f9a2b7c1d8e3f6a"
DEBUG = True
STRIPE_API_KEY = "sk_live_51H8xQ2eZvKYlo2C"    # una clave LIVE en el repositorio
SENTRY_DSN = os.environ.get("SENTRY_DSN", "")  # se lee, pero no está en .env.example
```

El daño del secreto literal es peor de lo que parece: **borrarlo en el commit siguiente no lo
elimina**. Queda en el historial de git y en cada clon, cada fork y cada copia de CI. El único
arreglo real es rotar la credencial, no editar el fichero. Por eso esta regla es de las pocas que
merecen bloquear antes de que el commit exista.

Y `SENTRY_DSN` sin documentar es el fallo aburrido que más tiempo consume: el proyecto arranca,
parece funcionar, y falta media configuración que nadie sabe que existe hasta que algo la necesita.

## Cómo se comprueba

```bash
python3 .claude/patterns/stack/pattern_check_backend.py --rules be-env-secreto-literal,\
be-env-documentado,be-compose-healthcheck,be-compose-tag-latest
```

| Regla | Estado | Qué detecta |
|---|---|---|
| `be-env-secreto-literal` | activo | clave que contiene `PASSWORD/SECRET/TOKEN/API_KEY/PRIVATE_KEY/ACCESS_KEY/DSN` con valor literal en compose o settings. Ignora `${VAR}`, `env(...)`, `os.environ`, y rellenos evidentes (`<...>`, `CHANGEME`, `your-`, `example`) |
| `be-env-documentado` | activo | cruce settings ↔ `.env.example`: variable leída con `env(...)`, `env.bool(...)`, `os.environ[...]` o `os.getenv(...)` que no aparece documentada |
| `be-compose-healthcheck` | débil | `depends_on` en forma corta (lista) sin `condition: service_healthy` |
| `be-compose-tag-latest` | activo | `image:` con `:latest` o sin tag |

Dos límites conocidos: `be-env-secreto-literal` es **detección por nombre de clave**, así que un
secreto guardado en una variable llamada `AJUSTE_7` se le escapa (para el barrido genérico está
`gitleaks`/`trufflehog`, fuera de este catálogo); y `be-compose-healthcheck` comprueba la *forma*
del `depends_on`, no que el `healthcheck` del servicio dependido sea correcto.

## Excepciones legítimas

- **Credenciales de juguete en un compose exclusivo de test/CI** que nunca toca datos reales:

```yaml
# pattern-exempt: be-env-secreto-literal — compose de CI: base efímera, se destruye al acabar
POSTGRES_PASSWORD: test
```

- **Imagen construida en el propio repo** (`build:` sin `image:`): no hay tag que fijar y el
  checker no la mira.
- **Servicio sin healthcheck posible** (un sidecar que no expone nada comprobable): usa
  `condition: service_started` explícito, que al menos declara la intención.

## Related

- `backend-celery.md` (el servicio `worker` y `--max-tasks-per-child`) ·
  `backend-cache-redis.md` (`maxmemory-policy` del contenedor) · `rules/security.md`
- `rules/governance.md` — tocar configuración de producción exige aprobación explícita
