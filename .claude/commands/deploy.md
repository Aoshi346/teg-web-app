# /deploy - Deploy a producción/staging

> **Cuándo aplicar:** publicar cambios en un servidor que ya está montado — el ciclo
> pull → deps → migrar → construir → recargar → verificar, y qué mirar cuando devuelve 502 o 500.
>
> **NO aplicar:** levantar un servidor **desde cero** (eso es un bootstrap del proyecto: unidades
> systemd, nginx, certificados, datos iniciales; en un derivado suele ser su propia skill) ·
> decidir si una migración es destructiva (`rules/governance.md` §2) · auditar la seguridad de la
> app (`rules/security.md`, `sofia-pentester`).
>
> **Relacionado:** `rules/governance.md` §2 (el gate de aprobación del Paso 0) ·
> `rules/agent-security.md` §7 (IaC) · `rules/verification.md` §Ciclo de producción (qué se prueba
> antes) y §Smoke testing (dónde se guarda la evidencia).

---

## 🛑 Paso 0 — El deploy a producción NO es autónomo

**Antes de tocar el servidor**, y antes que ningún comando de aquí abajo:

> **Deploy a producción requiere aprobación** — `rules/governance.md` §2, lista "Requieren
> APROBACIÓN del Supervisor". No la relaja la urgencia ni la hora.

Se pide **en la conversación**, con lo que se va a publicar delante:

```bash
git log --oneline origin/main..HEAD          # qué entra exactamente en este deploy
git diff --name-only origin/main..HEAD | grep -c migrations/   # ¿lleva migraciones?
```

- [ ] El Usuario/Supervisor ha aprobado **este** deploy, con esa lista de commits a la vista
- [ ] Si lleva migraciones: se han **leído** y ninguna es destructiva (`DROP`, `ALTER … DROP`,
      `DELETE` masivo). Si lo es → es otro gate, y otro día
- [ ] Hay backup o snapshot si toca datos

> ⚠️ **Por qué este paso abre el comando y no lo cierra.** Este procedimiento vivió durante meses
> en un **subagente** (`especialista-devops`, archivado el 2026-08-22), y un subagente no puede
> recabar la aprobación del Usuario: trabaja en su propio contexto y devuelve un informe. El
> runbook estaba bien y le faltaba justo la única parte no negociable. Aquí está arriba del todo
> a propósito.

## 🛑 Paso 0b — Gate de IaC (solo si el deploy toca infraestructura)

Si el deploy incluye Terraform / OpenTofu / CloudFormation / Pulumi **generado o modificado por IA**,
no se aplica sin pasar estos dos checks. Son dos fallos silenciosos y caros: no se ven en el diff,
se ven en la factura o en la auditoría GDPR. Detalle y ejemplos: `rules/agent-security.md` §7.

```bash
# 1) REGIÓN explícita — nunca implícita, nunca heredada del entorno
rg -n 'region|location|availability_zone' *.tf \
  || echo "❌ sin región explícita → NO aplicar (riesgo GDPR: se crea todo en US)"

# 2) SIZING explícito — revisar A MANO cada match: familia y tamaño
rg -n 'instance_type|machine_type|node_type|disk_size|sku|max_size' *.tf

# 3) El PLAN es la evidencia, no el diff del HCL
terraform plan -out=tfplan && terraform show -no-color tfplan | rg -n '\+ resource|instance_type|region'
```

- [ ] Región declarada en el fichero y **coherente con la jurisdicción del producto**
- [ ] Tamaño/familia de instancia explícitos y con coste estimado (una EC2 mal dimensionada puede
      irse a **109 USD/hora**)
- [ ] Cotas y límites donde existan (`max_size`, retención, `disk_size`)
- [ ] Protección de borrado en lo que tenga estado (`prevent_destroy`, `deletion_protection`, backups)
- [ ] **El sizing es gasto externo → requiere aprobación** (`rules/governance.md`)

> `terraform apply` está en la lista `ask` de `settings.json` y `terraform destroy` en `deny`.
> No los saltes: el incidente de DataTalks.Club (AI Incident DB #1424) fue exactamente un
> `destroy` con auto-approve sobre un state obsoleto.

## 🛑 Paso 0c — Gate de datos de salud (solo si el producto los toca)

Aplica cuando el sistema vaya a tratar **datos de salud reales** — pacientes, citas de una clínica,
cualquier cosa que caiga en el art. 9 del RGPD. No aplica a datos sintéticos ni a una demo con un
catálogo ficticio, y ahí está la clave: **este gate es exactamente la frontera entre las dos.**

```bash
python3 .claude/scripts/gate_datos_salud.py .     # exit 1 si falta cualquiera de las 8
```

Las ocho, y el orden es el de ejecución: contrato de encargo firmado (art. 28) · subencargados
identificados con su ubicación · EIPD revisada por el DPD · aviso de privacidad **y** aviso de IA
(son dos obligaciones distintas) · derivación humana probada · pruebas superadas con datos
sintéticos · simulacro de borrado e incidente · registro de accesos (usuario nominal, lecturas
incluidas, plazo escrito y firmado, extracción por paciente). El procedimiento entero para llegar hasta aquí es la
skill `cumplimiento-salud`.

> ⚠️ **Lo que este gate NO dice.** Comprueba que cada pieza **existe, está fechada y está firmada
> por alguien con nombre**, y que el documento no conserva huecos sin rellenar. **No juzga si el
> contenido es correcto**: que exista un contrato no dice que sus cláusulas sirvan, y que exista una
> EIPD no dice que su análisis sea bueno. Eso lo valida un DPD o un abogado, y este script no los
> sustituye ni los imita. Lo que sí impide es el fallo que ocurre de verdad: llegar al día del
> lanzamiento y descubrir que el contrato nunca se firmó.

## 🛑 Paso 0c-bis — G2: dependencias y cadena de suministro (todo proyecto con manifiestos)

```bash
python3 .claude/scripts/gate_deps.py . --osv <osv-scanner> --sbom sbom.cdx.json
# 1 = vulnerabilidad HIGH+ con arreglo, lockfile ausente, Action sin SHA, scripts de instalación activos · 2 = no medido: tampoco se despliega
```

Rojo si una dependencia tiene una vulnerabilidad de gravedad ≥ HIGH **con versión arreglada**, si falta un lockfile,
si una GitHub Action va por etiqueta en vez de por SHA, o si el proyecto npm ejecuta los scripts de instalación de sus
dependencias. Los `@latest` salen como aviso. Un 2 (sin motor, sin red) **no es un verde**. El SBOM CycloneDX sale como
artefacto del release (lo pide el CRA). Las excepciones llevan razón y fecha de caducidad
(`deps-excepciones.json`, en el `.claude/` del proyecto). Detalle y plantilla de CI: `templates/seguridad-deps/`; criterio: `rules/security.md` §G2.

## 🛑 Paso 0d — Gates de bots y multi-tenant (G5, G6 y G4, si aplican)

**G6, si el proyecto es un bot** (LangGraph o LangChain en sus dependencias; el script lo detecta y
sale 0 si no lo es). Viene con el pack conversacional: si el script no está, el proyecto no tiene ese
pack y no es un bot de casa.

```bash
python3 .claude/scripts/gate_doble_obediente.py . --correr --python <python del proyecto>
# 1 = no se despliega · 2 = no medido (tampoco)
```

Exige la suite «doble obediente» (`templates/seguridad-bot/`) instalada, el adaptador relleno y la
suite en verde y **entera**: el gate lee el junit, así que un `-k` en los addopts, un conftest que
salta pruebas o un `xfail` también son un 1. Aunque el modelo obedezca una inyección, no puede hacer
daño. Lo que no mira —lo que el redactor escribe en el mensaje— está en el README de la plantilla.

**G5, si el bot tiene tools** (la superficie: tool abierta, `tenant_id` en la firma, efecto sin
`interrupt()`; tabla de seguridad coherente con el inventario). Acotado por rutas: nunca sobre el proyecto
entero (`pattern_check_agente.py` provocó un OOM así).

```bash
python3 .claude/scripts/gate_agente_superficie.py . --rutas <carpeta del agente> --exigir-tabla
# 1 = hallazgos · 2 = no medido (ninguna tool, demasiados ficheros)
```

**Hoy G5 es INFORMATIVO** (decisión G5-DEPLOY del Usuario, 22-10): se corre y sus hallazgos van al informe
del despliegue, pero un 1 o un 2 **no** lo paran. Pasará a exigirse cuando se haya medido en un bot real
de casa (cuántos falsos positivos da sobre un grafo de verdad); hasta entonces solo bloquean G6 y G4.

**G4, si el producto es multi-tenant con una columna `tenant_id`**, contra la base de CI o de staging
(nunca producción: la sonda cuenta tablas enteras, e intenta escribir —siempre con rollback—):

```bash
GATE_TENANT_DSN=<rol de la app> GATE_TENANT_DSN_ADMIN=<rol que ve todo> \
  python3 .claude/scripts/gate_tenant.py --exigir-sonda --sonda-escritura --exigir-escritura
# 1 = fuga o defensa ausente · 2 = no medido
```

Un 2 no es un verde: sin la sonda nadie ha visto filtrar a las políticas (la lectura estática es
léxica). La de escritura prueba, desde el tenant A, a insertar en B, a mover filas a B y a borrar más
de lo suyo: es lo que una política `FOR DELETE USING (true)` deja abierto aunque la lectura esté
cerrada. Con FK inmediatas (no Django), esa prueba de borrado solo se mide si el DSN de admin es
superusuario; si no, sale 2. La suite del ORM (`templates/seguridad-tenant/`) va en el CI del
proyecto, no aquí.

**Campañas, si el cambio toca lo que arma o envía una campaña** (la consulta de la audiencia, la plantilla, el
control). Con la audiencia resuelta por un `--dry-run` del propio proyecto:

```bash
python3 .claude/scripts/gate_campana.py .
# 1 = la campaña no sale (sin base legal registrada, bajas en la lista, sin control…) · 2 = no medido: tampoco
```

Es la puerta C1-C10 de `rules/campanas-salida.md`: base legal del comercio registrada y cumplida por cada
destinatario, excluidos, control por hash, variables resueltas, simulación marcada. Un verde no certifica
cumplimiento y no sustituye a Priya.

## 🛑 Paso 0e — Gates de Django y del candado de datos reales (G3, si es un Django)

**G3**, con los settings de **producción** y las variables que piden (sus valores no se imprimen):

```bash
python3 .claude/scripts/check_django_seguridad.py . --settings <módulo de producción> \
        --python <python del proyecto> --env-file <variables de CI>
# 1 = no se despliega · 2 = no medido (tampoco)
```

Corre el check de despliegue de Django y lo que ese check no mira: avisos de seguridad silenciados,
la CSP, el permiso por defecto de DRF, el límite de peticiones de cada vista pública, el límite de
intentos de login y el 2FA del admin. Lo que resuelve el proxy se declara en `.claude/gate-django.json`
con su razón. Detalle: `rules/backend-seguridad.md`.

**Si el proyecto trata datos reales de terceros con candado** (`patterns/stack/backend-candado-datos-reales.md`):

```bash
python3 .claude/scripts/gate_datos_reales.py . --demostrar --python <python del proyecto>
```

En producción el estado no existe y manda el entorno; lo que se mira aquí es que el candado **bloquea
de verdad** (arrancar con una integración en real y la variable a 0 tiene que negarse) antes de
publicar el código que lo lleva.

---

## Paso 1 — Antes de tocar el servidor

Esto se comprueba **en local o en la rama**, no en producción:

```bash
git branch --show-current      # la rama que toca (main o develop según el proyecto)
git status                     # sin cambios sin commitear
bash .claude/hooks/check-ram.sh   # y solo entonces, tests por módulo
```

- [ ] Tests del módulo afectado en verde (`rules/ram-pytest.md`: por módulo, nunca la suite entera)
- [ ] La construcción del frontend pasa sin errores
- [ ] Si se publica HTML estático (una web, una landing): sin notas internas visibles en lo
      construido — `python3 .claude/scripts/check_internal_notes.py <dist>/` en 0
- [ ] Migraciones preparadas y revisadas (Paso 0)
- [ ] Variables de entorno nuevas **ya puestas en el servidor** — es el olvido más común, y no
      falla al desplegar: falla en la primera petición que las usa

---

## Paso 2 — Publicar

**Lee la unidad systemd antes de teclear nada.** Los nombres de servicio, el directorio de trabajo
y las rutas de log **las declara la unidad**, no una convención:

```bash
systemctl list-units --type=service | grep -i <proyecto>   # cómo se llaman de verdad
systemctl cat <servicio>                                   # WorkingDirectory, EnvironmentFile, logs
```

> ⚠️ **No hay una ruta de proyecto universal.** De los dos proyectos del corpus, uno tiene el
> backend en `backend/` y el otro tiene `manage.py`, `apps/` y `core/` **en la raíz**. Cualquier
> `cd backend` escrito de antemano acierta en la mitad de los casos.

```bash
git pull origin <rama>

# Backend — el gestor de dependencias es el del proyecto (poetry / pip / uv)
poetry install --no-dev            # o: pip install -r requirements.txt · uv sync
python manage.py migrate
python manage.py collectstatic --noinput

# Frontend
npm ci && npm run build            # nginx sirve el resultado; no hay que reiniciarlo por esto

# Servicios de aplicación: por nombre de unidad, uno por uno
sudo systemctl restart <unidad-gunicorn>
sudo systemctl restart <unidad-celery-worker> <unidad-celery-beat>

# nginx: RECARGA, y solo si cambió su configuración — probándola antes
sudo nginx -t && sudo systemctl reload nginx
```

**Las dos correcciones de este bloque están medidas, no son preferencia:**

| Lo que se hace | Medida sobre los dos proyectos del corpus |
|---|---|
| `reload` de nginx, no `restart` | **14 usos de `systemctl reload nginx`, 0 de `restart`.** `reload` recoge la configuración nueva sin cortar las conexiones en vuelo; `restart` las tira sin ganar nada |
| `nginx -t` antes de recargar | **5 de esos 14** lo encadenan. Una configuración con un error tipográfico deja nginx caído; probarla cuesta un segundo |
| `restart` (no reload) del servidor de aplicación | **0 de las 10 unidades systemd del corpus declara `ExecReload`.** Sin `ExecReload`, `systemctl reload` no tiene qué ejecutar. Si quieres recarga sin corte, el trabajo es **declararla en la unidad**, no buscar el PID a mano |

> **Sobre `kill -HUP <PID>`:** era el consejo estrella del runbook viejo, y **no aparece ni una vez
> en el corpus** (0 usos, frente a 26 de `systemctl`). Con los servicios bajo systemd, encontrar el
> PID maestro con `ps aux | grep` para mandarle una señal es dar un rodeo alrededor del gestor que
> ya los supervisa — y lo que ve `systemctl status` después deja de coincidir con la realidad.

---

## Paso 3 — Verificar (no se cierra sin esto)

```bash
# 1) Los servicios están arriba y no en bucle de reinicio
systemctl is-active <unidad-gunicorn> <unidad-celery-worker>
systemctl show <unidad-gunicorn> -p NRestarts      # ¿está reiniciándose solo?

# 2) Sin errores nuevos desde el deploy — journalctl acota por tiempo, tail no
sudo journalctl -u <unidad-gunicorn> --since "5 min ago" -p err

# 3) La app responde de verdad: el código, no solo "no da error de conexión"
curl -s -o /dev/null -w "%{http_code} %{time_total}s\n" https://<dominio>/
curl -s -o /dev/null -w "%{http_code}\n" https://<dominio>/api/<endpoint-de-salud>/

# 4) Un flujo real, no la portada (rules/verification.md §Smoke testing, requests reales)
```

- [ ] Códigos HTTP esperados en portada y API (un 200 en `/` con la API caída es lo normal:
      nginx sirve el frontend construido aunque el backend no arranque)
- [ ] Sin errores nuevos en el log **desde** el deploy
- [ ] Los workers de Celery aparecen activos si el proyecto los usa
- [ ] Evidencia guardada en `.claude/smoke/` (`rules/verification.md` §Smoke testing) — pegarla en el chat no
      cuenta como smoke

---

## Paso 4 — Rollback (decidido ANTES, no improvisado)

La pregunta se responde antes de publicar: **si esto sale mal, ¿cómo vuelvo?**

```bash
git log --oneline -5              # anota el sha ANTERIOR al deploy, antes de empezar
git checkout <sha-anterior> && <reinstalar deps> && <reconstruir> \
  && sudo systemctl restart <unidad-gunicorn>
```

> ⚠️ **El código vuelve atrás; la base de datos no.** Una migración ya aplicada sigue aplicada, y
> el código viejo puede no saber leer el esquema nuevo. Por eso las migraciones **aditivas**
> (añadir columna que admite nulos, y borrar la vieja en un despliegue posterior) hacen el rollback
> posible y las destructivas lo hacen imposible. Deshacer datos es una acción de aprobación
> (`governance.md` §2), no un paso de este comando.

---

## Troubleshooting

| Síntoma | Qué mirar, en este orden |
|---|---|
| **502 Bad Gateway** | nginx está vivo y su *upstream* no. `systemctl is-active <unidad>` → si está caído, `journalctl -u <unidad> -n 50` dice por qué (casi siempre: falta una variable de entorno, un import roto, o el puerto/socket del `proxy_pass` no coincide con el `--bind` de la unidad) |
| **500 Internal Server Error** | La app arrancó y falla al servir. `journalctl -u <unidad> --since "10 min ago" -p err` → traza. Sospechosos: migración sin aplicar, `collectstatic` sin correr, credencial de un servicio externo |
| **Va lento tras el deploy** | ¿Redis y la base responden? ¿Celery está consumiendo o la cola crece? ¿Alguna query nueva sin índice (`django-orm`, `references/optimization.md`)? Antes de culpar al servidor, mide |
| **Funciona en `curl` local y no desde fuera** | Es nginx o el certificado, no la app: `nginx -t`, y el `server_name` y el `proxy_pass` de ese sitio |

### Montar el proyecto en un servidor NUEVO — lo genérico que costó una tarde cada uno

El bootstrap entero (unidades, nginx, datos iniciales) es de cada proyecto y va en su propia skill.
Lo que se repite en cualquiera, cosechado del bootstrap de elvion (AN-25, sub-ola 3.20):

- **`git clone` a secas puede darte código de hace meses**: si la rama por defecto del remoto no es
  la de trabajo, clona con `-b <rama>`. No da error; monta un servidor donde no funciona casi nada.
- **Los puertos de casa no son los de fábrica**: sácalos de la rule de topología medida
  (`templates/rule-topology.md`, `check_topology.py`), nunca de la documentación del servicio.
- **Verifica contando, no por el código de salida**: un indexado o un restore puede terminar en 0
  habiendo fallado; se cuentan filas o `points_count` en el destino.
- **Un smoke verde con la función principal caída**: servicios activos, `/health` 200 y tests verdes
  no prueban que el bot (o la pantalla clave) responda; el smoke habla con ella de verdad.
- **Dos servidores no comparten un canal externo** (una sesión de WhatsApp, un webhook): el segundo
  arranca con ese canal APAGADO hasta tener el suyo.
- **DNS antes que el certificado**, y `docker compose -p <nombre>` cuando hay dos instancias del mismo
  compose: sin `-p`, la segunda reutiliza el proyecto y pisa los volúmenes de la primera.
- **Con varios entornos compose en la misma máquina, un envoltorio por entorno** (`./stage`,
  `./langfuse`): `templates/compose-wrapper/compose-wrapper.sh` fija `--env-file`, `-p` y los `-f`, y se
  niega si `docker compose config` da un nombre sin el prefijo del entorno o de un contenedor de otro
  proyecto. El `-p` correcto solo no basta: sin `--env-file`, `${PREFIJO:-prod}` cae al de producción.

---

## Lo que NO se hace

- ❌ Desplegar sin la aprobación del Paso 0 porque "es un cambio pequeño".
- ❌ `git reset --hard` en el servidor sin backup.
- ❌ Aplicar migraciones sin haberlas leído.
- ❌ `restart` de nginx donde basta `reload`, o recargarlo sin `nginx -t` antes.
- ❌ Buscar el PID con `ps aux | grep` para mandar señales a un servicio que gestiona systemd.
- ❌ Hardcodear rutas (`backend/logs/…`) en vez de leer la unidad: en la mitad del corpus no existe
  ese directorio.
- ❌ Exponer al exterior el puerto de la base de datos o del servidor de aplicación (`--bind
  127.0.0.1` y nginx delante — `rules/security.md`).
- ❌ Commitear `.env` o cualquier fichero con credenciales.
- ❌ Dar el deploy por bueno porque los comandos no dieron error: eso es el Paso 3.

---

_Comando v2.0 · 2026-08-22 · CAP-ESP-DEVOPS. Absorbe el runbook del agente `especialista-devops`
(archivado: `_archive/2026-08-22/README.md`), corregido contra los dos proyectos del corpus —
14 `reload nginx` frente a 0 `restart`, 0 de 10 unidades con `ExecReload`, 0 usos de `kill -HUP`.
El Paso 0 y el Paso 4 no venían de ningún lado: faltaban en las dos piezas._
