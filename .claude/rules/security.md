---
paths:
  - "**/docker-compose*.yml"
  - "**/docker-compose*.yaml"
  - "**/compose.yml"
  - "**/compose.yaml"
  - "**/Dockerfile*"
  - "**/*nginx*.conf"
  - "**/nginx/**"
  - "**/settings.py"
  - "**/settings/*.py"
  - "**/wp-config*.php"
  - "**/fail2ban/**"
  - ".mcp.json"
  - ".claude/puertos-publicos-declarados.json"
  - ".claude/scripts/check_puertos_docker.py"
  - ".claude/scripts/wp_indicadores.sh"
---
# Reglas de Seguridad

> **Cuándo aplicar:** al escribir o revisar código de **la aplicación** (queries, auth, secrets,
> input de usuario) y al conectar un servidor **MCP** a la sesión.
>
> **NO aplicar:** para la seguridad del **harness** (permisos, hooks, config entrante, skills,
> workflows, IaC generada por IA) → `agent-security.md`. Para el riesgo de **usar** un asistente de
> IA (código propietario, retención por vendor, copyright) → `ai-assistant-risk.md`.
>
> ⚠️ **Y lo que este fichero NO cubre, aunque su nombre lo prometa: el contrato HTTP de la API.**
> Verbos, 405, endpoints que aceptan varios métodos, credenciales y datos personales en la URL,
> idempotencia y borrados masivos viven en **`rules/api-http-contract.md`**. La autorización a nivel
> de objeto y la pertenencia al tenant, en `patterns/stack/backend-vistas.md` §1.2 y en la skill
> `multi-tenant-context`. Esta rule es, en la práctica, **secretos + exposición de red + cadena de
> suministro de MCP**.
>
> **Relacionado:** `agent-security.md` · `ai-assistant-risk.md` · `governance.md` ·
> agente `sofia-pentester` · skill `code-review-gate` (§Seguridad Django/DRF).

## Nunca hacer
- ❌ Hardcodear credenciales
- ❌ Commit de .env o secrets
- ❌ Exponer IDs internos en URLs públicas
- ❌ SQL raw sin parametrizar
- ❌ Confiar en input del usuario

## Siempre hacer
- ✅ Variables de entorno para secrets
- ✅ Validar y sanitizar inputs
- ✅ Usar ORM para queries
- ✅ HTTPS en producción
- ✅ Tokens con expiración

## Django específico
```python
# ✅ Bien
User.objects.filter(id=user_id)

# ❌ Mal
User.objects.raw(f"SELECT * FROM users WHERE id = {user_id}")
```

## Dependencias vulnerables y secretos — los cuatro comandos que no corría nadie

**El hueco, verificado el 2026-08-26:** `bandit`, `pip-audit` y `safety` **no aparecían en ninguna
rule, skill, patrón ni comando** de este harness, y `gitleaks` solo de pasada. `code-review-gate`
mira el diff y las dependencias alucinadas; **nadie miraba si lo que ya está instalado tiene un
CVE**. Cosechado de `everything-claude-code` (EXT-6), que sí lo tenía.

```bash
pip-audit                          # dependencias con CVE conocido (usa la BD de avisos de PyPA)
safety check --full-report         # segunda opinión, con más contexto por vulnerabilidad
bandit -r <paquete>/ -ll           # patrones inseguros en NUESTRO código (-ll = medio y alto)
gitleaks detect --no-banner        # secretos commiteados, incluido el historial
```

**Cuándo se corren**, y el acotamiento importa para que no se ignoren:

| Momento | Qué | Por qué ese y no otro |
|---|---|---|
| Antes de un release | Los cuatro | Es cuando el coste de un CVE pasa a ser real |
| Al añadir una dependencia | `pip-audit` | Cuesta segundos y es cuando entra el problema |
| Una vez al mes | `pip-audit` + `safety` | Los CVE aparecen **después** de instalar: un repo que no cambia se vuelve vulnerable solo |
| Antes de hacer público un repo | `gitleaks detect` | El historial guarda lo que se borró del working tree |

> ⚠️ **`bandit` no es un gate, es un mapa.** Marca patrones —`subprocess` con `shell=True`, `assert`
> en producción, un `random` donde debería haber `secrets`— y muchos son deliberados. Se corre con
> `-ll` y se lee buscando el **Intent** (`verdict-contract.md`): código defensivo y `# nosec` con
> razón escrita son respuestas válidas. Un `bandit` bloqueante en un repo existente marcaría
> decenas de sitios y se aprendería a saltar (regla de inversión, `patterns/README.md` §2).

**Ninguno está instalado en esta máquina** (2026-08-26): son dependencias de sistema o de proyecto,
y eso lo decide el Usuario (`governance.md` §2). Aquí queda el qué y el cuándo; el `pip install` no
lo hace un agente por su cuenta.

### G2 — el gate que los junta (sub-ola 2.23, SE-18/34/38/60)

`python3 .claude/scripts/gate_deps.py <proyecto>` es la forma ejecutable de la tabla de arriba, y sale con
0 (bien) · 1 (hallazgos) · 2 (no se pudo medir: sin motor, sin red, manifiestos que nadie lee). Dos mitades:

- **Vulnerabilidades** — `osv-scanner scan source -r` (lee `poetry.lock`, `package-lock`, `pnpm-lock`, `uv.lock`;
  `pip-audit` no lee `poetry.lock`) o, sin él, `pip-audit -r` sobre los `requirements*.txt`. **Rojo** con una
  vulnerabilidad de gravedad ≥ HIGH (CVSS 7,0) **que ya tiene versión arreglada**; el resto va al informe.
  Un manifiesto sin lock es rojo (no hay versión que medir). Una excepción vive en
  `deps-excepciones.json` (en el `.claude/` del proyecto) con razón y **fecha de caducidad**: caducada, vuelve a contar.
  `--sbom F` escribe el SBOM CycloneDX (el artefacto de release que pide el CRA).
- **Cadena de suministro** — una GitHub Action por etiqueta y no por SHA de 40 caracteres es **rojo** (tj-actions,
  CVE-2025-30066); un proyecto npm que ejecuta los scripts de instalación de sus dependencias es **rojo**
  (s1ngularity: un postinstall robó credenciales lanzando los CLI de IA locales con los flags de bypass; este servidor
  corre como root con Claude Code instalado). La política es `ignore-scripts=true` en `.npmrc`
  (plantilla: `templates/seguridad-deps/npmrc`) **o** pnpm ≥ 10.26.0 (la 10.0-10.25 se saltaba con una dependencia
  de un repositorio git, CVE-2025-69264). Un `npx`/`uvx` sin versión exacta o con `@latest` es **aviso**
  (`--estricto` lo hace rojo).

Instalación sin tocar el sistema (decisión del 20-10): `pip-audit` en un venv (`python3 -m venv v && v/bin/pip install
pip-audit`) y `osv-scanner` como binario descargado de las releases de `google/osv-scanner` **comprobando el
SHA-256** de `osv-scanner_SHA256SUMS`; se pasa con `--osv RUTA` o `$GATE_DEPS_OSV`. En CI: `templates/seguridad-deps/deps-gate.yml`.
Con `ignore-scripts=true`, los paquetes que compilan algo (esbuild, sharp, husky) piden un `npm rebuild <paquete>`
explícito: es el precio, y está bien que se vea.

## Archivos sensibles (no commit)
- .env
- *.pem
- *.key
- secrets.*
- credentials.*

---

## 🌐 Servir HTML para verificar — SIEMPRE `--bind 127.0.0.1`

**`python3 -m http.server` escucha en TODAS las interfaces por defecto.** En un servidor con IP
pública, eso publica en internet el directorio desde el que lo lanzaste — sin auth y sin avisar.

```bash
python3 -m http.server 8899 --bind 127.0.0.1     # ✅ solo local
python3 -m http.server 8899                      # ❌ 0.0.0.0 — el directorio queda expuesto
```

**No es teórico:** el 2026-08-21 se encontraron dos `http.server` de meses en `0.0.0.0` en este
servidor, uno con material de un cliente, respondiendo 200 desde la IP pública; los había lanzado el
propio flujo de verificación visual, que el template recomendaba sin `--bind` (el caso, en
`knowledge/wordpress/seguridad.md` del template, §Historia).

**Para llegar desde fuera se usa un túnel SSH, nunca `0.0.0.0`:**

```bash
ssh -N -L <puerto>:127.0.0.1:<puerto> <usuario>@<servidor>
```

**Higiene de puertos.** Estos servidores no mueren solos: sobreviven a la sesión que los lanzó. Un
puerto por informe, y al terminar se cierran. Para ver qué hay abierto:

```bash
ss -tlnp | grep -E ':(88|89)[0-9][0-9]'          # qué escucha, y en qué interfaz
ss -tlnp | grep '0.0.0.0'                        # ⚠️ lo que está EXPUESTO
```


## 🚫 NINGÚN puerto se expone. Nunca. Solo hay dos formas de llegar

> **Decisión del Usuario, 2026-08-28**, tras el incidente del 27: *«nunca se debe exponer ningún
> puerto. Siempre accedemos al localhost por túnel SSH, o se accede a una URL pública con dominio y
> HTTPS».*

No es una recomendación ni un objetivo: es la política. **Todo servicio escucha en `127.0.0.1`.** Y
para llegar a él solo existen dos caminos, los dos con nombre:

| Camino | Cuándo | Qué escucha en público |
|---|---|---|
| **Túnel SSH** | Paneles, bases de datos, informes, herramientas internas, cualquier cosa de trabajo | **Nada.** El servicio está en `127.0.0.1` y el túnel lo trae a tu máquina |
| **URL pública con dominio y HTTPS** | Lo que de verdad tiene que ver un usuario final | **Solo el proxy inverso** (nginx/Traefik), en 80 y 443, con su certificado. La aplicación sigue en `127.0.0.1` detrás |

```bash
python3 -m http.server 8899 --bind 127.0.0.1        # y desde fuera:
ssh -N -L 8899:127.0.0.1:8899 <usuario>@<servidor>
```

**No hay una tercera forma.** «Lo abro un momento para probar» y «es solo el entorno de desarrollo»
son las dos frases que preceden a un incidente: el puerto se queda abierto porque nadie lo apunta, y
los bots barren internet entera cada pocas horas.

### Y con Docker, el firewall NO te protege — esto es lo que casi nadie sabe

```yaml
services:
  panel:
    ports: ["8081:80"]        # ❌ 0.0.0.0 — internet entera, aunque ufw diga DENY
    ports: ["127.0.0.1:8081:80"]   # ✅ solo local
```

Literal de `docs.docker.com/engine/network/packet-filtering-firewalls/`:

> *«Docker and ufw use firewall rules in ways that make them incompatible with each other. When you
> publish a container's ports using Docker, traffic to and from that container gets diverted before
> it goes through the ufw firewall settings. […] Packets are routed before the firewall rules can be
> applied, **effectively ignoring your firewall configuration**.»*

Y de `docs.docker.com/engine/network/port-publishing/`: *«**Publishing container ports is insecure
by default.**»* Lo mismo dice OWASP en su Docker Security Cheat Sheet, RULE #5a.

Dos consecuencias que hay que tener delante:

1. **`ufw status` no es evidencia de nada** para un contenedor. Puede decir `DENY` con el puerto
   abierto de par en par. Lo que sí lo dice: `sudo iptables -t nat -L DOCKER -n`.
2. **Omitir la dirección NO es «por defecto local»: es `0.0.0.0`.** Literal de la referencia de
   Compose: *«If you do not specify a host IP (such as 127.0.0.1), Docker binds to all interfaces
   (0.0.0.0)»*. El caso peligroso es justo el que no lleva ninguna IP escrita.

**Medido, no supuesto** (incidente de este servidor del 2026-09-11, detalle en el
template, `knowledge/wordpress/seguridad.md`): `ufw` permitía solo 22, 80 y 443 y un contenedor tenía
`0.0.0.0:18800` abierto a internet. El tráfico de un puerto publicado por Docker entra por
`FORWARD`/DNAT y las reglas de ufw viven en `INPUT`: nunca se evalúan.

| | Qué protege | Qué NO protege |
|---|---|---|
| **Firewall de HOST** (`ufw`, `iptables -L INPUT`) | Lo que escucha el propio host | **Nada publicado por Docker** — lo esquiva por DNAT |
| **Firewall del PROVEEDOR** (Hetzner Cloud Firewall y equivalentes) | Está **aguas arriba** de la máquina: Docker **no lo puede saltar** | Al atacante que entra **por el puerto web legítimo con credenciales válidas** |

Y un puerto publicado **además** del proxy es un punto ciego de auditoría: lo que entra por él no
pasa por nginx y no queda en ningún log.

### El gate, porque esto no se sostiene con disciplina

```bash
python3 .claude/scripts/check_puertos_docker.py <proyecto>   # exit 1 si algo sale fuera
```

**Lee `docker compose config`, nunca el YAML a pelo**, y ahí está lo importante: `config` interpola
las variables. Medido — con `ports: ["${BIND}:5432:5432"]` y `BIND=0.0.0.0` en el `.env`, un
`grep 0.0.0.0` da **cero coincidencias** y el puerto está abierto a internet. Un gate hecho con grep
habría dado luz verde.

Con varios entornos compose en la misma máquina, cada uno se opera por su envoltorio
(`templates/compose-wrapper/`): con la misma lectura de `config` se niega a tocar un nombre que no
es del entorno o un contenedor de otro proyecto (`commands/deploy.md` §Montar el proyecto en un servidor NUEVO).

Permite 80 y 443 (son la segunda vía: el proxy inverso) y marca todo lo demás. Si algo **debe** ser
público de verdad, se declara en `.claude/puertos-publicos-declarados.json` con su razón — una razón
vacía no cuenta como declaración. La escotilla existe a propósito: sin ella, lo que se comenta es el
check entero.

> **Por qué esta sección existe y llegó tarde:** la lección se pagó tres veces en este servidor
> —dos `http.server` en `0.0.0.0` (21-ago), un phpMyAdmin publicado por `docker-compose` con intrusión
> (27-ago) y un minero en un WordPress archivado con sus contenedores vivos (11-sep)— porque se
> escribió para una herramienta y no se generalizó. La historia, en el template: `knowledge/wordpress/seguridad.md`.

## 🔐 Autenticación web y WordPress — el vector real no es una CVE, son credenciales

En un WordPress de producción, la puerta que no audita nadie es **la contraseña de administrador**:
`sofia-pentester` mira la aplicación, `code-review-gate` el diff y `check_puertos_docker.py` la red.
Lo que hay que tener, por eficacia contra *credential stuffing* distribuido (cientos de IPs, por
debajo de cualquier umbral por IP):

1. **2FA en todas las cuentas admin** — la única que lo corta en seco.
2. **Límite de intentos + bloqueo de cuenta** con desbloqueo por correo.
3. **fail2ban** sobre los `POST` a `wp-login.php` (mitiga; comprueba antes qué jails hay de verdad:
   `fail2ban-client status`, y pasa el filtro por `fail2ban-regex` con control negativo).
4. **`xmlrpc.php` bloqueado en nginx** — casi nadie lo usa y es por donde entra buena parte del ataque.
5. **`limit_req` de nginx** sobre `wp-login.php`.

Un plugin de **gestión de ficheros** en producción es una webshell con soporte oficial aunque esté al
día: **`DISALLOW_FILE_MODS`** (no solo `DISALLOW_FILE_EDIT`) cierra esa vía. Tocar nginx o fail2ban en
una máquina con webs vivas es acción del Usuario (`governance.md` §2); un agente sí puede comprobar y
reportar, y no publicar nunca un WordPress en `0.0.0.0` ni desplegarlo sin 2FA planificado.

**El caso que lo ancla** —el minero de 17 días en un WordPress de este servidor, las tablas de
intentos, el filtro de fail2ban medido y las cinco medidas con lo que habría hecho cada una— está
entero en **`knowledge/wordpress/seguridad.md`** del template (el módulo de WordPress, pack `ops-web`:
solo llega a un proyecto que lo pida).

## ♻️ Ciclo de vida: archivar un proyecto es PARAR Y ELIMINAR sus contenedores

**Archivar el código no apaga nada.** Un proyecto archivado cuyos contenedores siguen corriendo,
publicados y sin mantener es superficie de ataque que nadie va a parchear, porque nadie recuerda que
está ahí (fue la causa raíz del incidente del 2026-09-11: en el template, `knowledge/wordpress/seguridad.md`).

**La regla:** dar de baja o archivar un proyecto **incluye** parar y eliminar sus contenedores
(volúmenes aparte — esos se conservan o se respaldan a propósito). Un contenedor cuyo proyecto ya no
existe es **superficie de ataque sin mantenimiento**: nadie va a parchearlo porque nadie recuerda
que está ahí.

```bash
# Contenedores ZOMBI: su proyecto de compose ya no existe en disco.
docker ps -a --format '{{.Names}}' | while read -r c; do
  wd=$(docker inspect -f '{{index .Config.Labels "com.docker.compose.project.working_dir"}}' "$c" 2>/dev/null)
  [ -n "$wd" ] && [ ! -d "$wd" ] && echo "ZOMBI $c → $wd"
done
```

Parado es tolerable (no escucha); corriendo no. Lo que convierte a un zombi en incidente es
**`RUNNING` + puerto publicado**, y eso se cruza con `check_puertos_docker.py`. Un barrido **diario**
lo caza en 24 horas: es el trabajo de `hugo-vigilancia-diaria` (sus indicadores, en su `memory.md`),
y el valor está en el delta contra la medición de ayer, no en la foto de hoy.

## Un `deny` no se aplica siempre — lo que falla caro va en un hook (TPL-2, cosecha de Xera)

Medido el 18-ago-2026 en un sistema de agentes en producción: una sesión real leyó
`secrets/telegram.env` con `Read(secrets/**)` en `deny`. Se explicó como «sin el diálogo de confianza,
Claude Code IGNORA las entradas de permisos y los hooks sí corren». **Esa frase estaba mal generalizada**
(SE-30, re-medida el 22-oct-2026 en 2.1.307) y la premisa correcta tiene tres partes, según el modo:

| Caso | Hooks del repo | `allow` del repo | `deny` / `ask` |
|---|---|---|---|
| **`claude -p` / SDK**, carpeta sin confianza | **Corren** (medido: un `PreToolUse` escribió su log) | **Se ignoran**, con aviso en stderr: *«Ignoring 1 permissions.allow entry … this workspace has not been trusted»* (medido) | **Se aplican** (medido: `Read` de `.env` con `deny Read(**/.env*)` → *«File is in a directory that is denied by your permission settings»*) |
| **Interactivo**, sin aceptar el diálogo | Se **retienen** hasta aceptar la confianza (doc `hooks`/`permissions`; **no medible desde `-p`**) | Se retienen | **No se ven afectados** (doc `permissions` §Project allow rules and workspace trust) |
| **`.mcp.json`** en `-p` | — | — | Los servidores del proyecto se conectan **sin preguntar** (§MCP más abajo) |

Consecuencias: (1) **un `deny` nunca se ignora por falta de confianza**: la fuga de Xera se explica mejor
por el gotcha de abajo (un `deny Read()` no para un `cat` si `Bash(cat*)` está en `allow`, y en `-p` ese
`allow` del repo ni siquiera se aplicaría) que por «los permisos se ignoran»; (2) **un hook sirve en `-p`,
pero no es «lo único que funciona»**: en interactivo, antes de la confianza, ni corre; (3) para un job
`claude -p` **sobre un repo ajeno**, no se confía en el `.claude/` de ese repo: `--bare`, `--setting-sources
user` o `--settings` con `disableAllHooks` (receta en `harness-gotchas.md` §`claude -p` desatendido).

Y el segundo agujero, medido el 2026-09-05 en `/home/agents`: `deny: Read(/home/agents/secrets/**)`
con `allow: Bash(cat*) Bash(head*) Bash(grep*) Bash(curl*)`. **Las reglas `Read()` no se evalúan
contra Bash** — solo `Edit(ruta)` y `Read(ruta)` miran ficheros; `Write()`, `Glob()`, `Grep()` se
ignoran con aviso. `cat secrets/integraciones.env` casaba con `Bash(cat*)` y estaba **permitido**,
con `curl` en la misma sesión como vía de salida. En modo yolo desaparece hasta el `deny`.

> ⚠️ **Matiz del 2026-10-20** (sin probar en vivo): la doc de hoy dice que sin confianza se retienen los
> `allow` del repo, no los `deny`, y que un `deny` `Read(ruta)` cubre también `cat`, `head`, `tail`, `sed`
> y `tee` en Bash, aunque no un script que lee por su cuenta (`code.claude.com/docs/en/permissions`; en el
> template, `claude-code-referencia` §8.4-8.5). Lo de arriba se midió en agosto y septiembre con otras
> versiones. La consecuencia de abajo sigue en pie; el repaso, con MO-71.

**Consecuencia para todos los proyectos:** el `deny` es la **segunda** capa. Para un secreto, la
primera es un `PreToolUse` sobre `Bash|Read|Grep` (`Glob` solo lista nombres) que bloquee **la ruta y un verbo lector a la
vez** — `cat`, `head`, `tail`, `less`, `grep`, `python3 -c open(...)`, `base64` — y deje pasar
`test -s`, `stat`, `ls`: un hook que estorba se acaba quitando. Con su límite escrito en el propio
hook: *es una lista de verbos y las listas de verbos se pueden rodear; no es defensa contra alguien
que ya tiene root*. La implementación es
**`hooks/guard-secretos.sh`** — desde el 2026-10-22 (SE-23) vive en `hooks/`, está registrado en el
`settings.json` del template (`PreToolUse`, `Bash|Read|Grep`) y se propaga. Antes era un ejemplo en
`examples/` que solo llevaban a mano dos proyectos. Lo genérico (`.env`, `secrets/`, `creds/`, `*.pem`,
`*.key`, `~/.ssh`, `~/.aws`, `.netrc`…) protege a cualquiera; **las rutas de TU proyecto van en
`RUTAS_PROPIAS`** (`bash .claude/hooks/guard-secretos.sh --autocomprobar` dice si lo está, y
`check_harness_seguridad.py` H4 lo vigila). **Qué cubre que los `deny` no**: `grep`, `awk`, `base64`,
`cp`, `curl -d @…` y `python -c` sobre la ruta, la herramienta `Grep`, y rutas fuera del patrón del
`deny`; lo que los `deny` de `Read()` ya cubren (`Read`, `Edit` y `cat`/`head`/`tail`/`sed`/`tee`) no se
repite aquí con otro mensaje: el hook solo añade lo que falta.

> **La ruta se escribe entera a propósito.** Hasta el 2026-09-11 esta frase decía «va en
> `examples/`» sin nombrar el fichero — y el fichero **no estaba**, llevaba meses siendo una
> promesa incumplida que `check_mechanisms.py` no podía cazar porque una promesa sin ruta no le
> da nada que comprobar. Consecuencia observada: **los proyectos se lo copiaban entre ellos**
> (`ppos` heredó el de `eva` sin adaptar, con los efectos del §3 de abajo). Ahora que la cita es
> una ruta, si alguien borra el fichero el comprobador lo dice solo. Es el patrón general: **una
> promesa que cita su ruta se vigila sola; una que no, la caza alguien de paso o no la caza
> nadie.**

### Las tres formas en que un guard de secretos falla (medidas, 2026-09-11)

Ninguna es un fallo del diseño del hook: las tres son de cómo se usa, se copia y se rodea. Van
aquí porque las tres se descubrieron el mismo día y se explican mal por separado.

**1 · Se rodea, y el rodeo llega disfrazado de pragmatismo.** El guard corta por **cadena + verbo
lector** sobre el comando que se teclea. Partir la cadena lo desactiva:

```bash
_envf=".../backend/.${_e:-env}"      # ❌ compone ".env" en dos trozos: el guard no lo ve
_envf=".../backend/.env"             # ✅
```

Apareció en un script que **no hacía nada malo** —cargaba credenciales sin imprimirlas— con el
motivo escrito en un comentario, camino de entrar en `examples/`. Ahí está el daño real: un ejemplo
del template se replica a N proyectos, así que publicarlo es **distribuir la receta**.
`agent-security.md` §10 ya admite que los hooks son *pattern-matchers* y se pueden rodear; admitir
el límite y repartir el método no son lo mismo.

Y el rodeo traía dentro un bug: **`${_e:-env}` usa una variable sin declarar como mecanismo**. Si
alguien la tiene exportada, la ruta cambia en silencio y el script carga otro fichero.

> **Regla:** si el guard bloquea una línea legítima, la salida es **una excepción con su razón
> escrita**, o arreglar el guard. Nunca partir la cadena. Y un rodeo **no se publica** aunque sea
> inofensivo donde nació.

**2 · Su falso positivo tiene una forma concreta, y conviene reconocerla en dos segundos.** No es
que marque cualquier mención de la ruta —el diseño es bueno y deja pasar `test -s`, `stat` y `ls` a
propósito—. Salta cuando **`.env` viaja como PATRÓN DE BÚSQUEDA y no como ruta**:

```bash
grep -nE '\.env' config.py      # ❌ bloqueado: el guard ve «.env» + grep, y el fichero es inocente
```

Distinguir «mención como patrón» de «mención como ruta» exigiría parsear la línea de comandos de
verdad, así que **no se arregla: se esquiva bien**. La salida buena es leer con `Read` en vez de
`grep`, que además deja rastro de qué se leyó.

**3 · Se copia entre proyectos sin adaptar, y entonces protege por casualidad.** El caso medido:
el guard de `ppos` es el de `eva` copiado tal cual.

| Qué | Efecto |
|---|---|
| `HQ="${EVA_HQ:-/home/agents}"` se asigna y **no se usa** (el patrón lleva la ruta literal) | Código muerto que **engaña**: quien lo lee cree que el hook se adapta solo |
| `LOG="${EVA_SECRETOS_LOG:-/var/log/eva/secretos.log}"` **sí se usa** | Los bloqueos de un proyecto se escriben **en el log de otro**. Quien audite los bloqueos de `ppos` no los encuentra donde mira |
| El patrón lista rutas que en el destino **no existen** (`departments/_shared/creds/`, `gmail-*.json`…) | Media regla apuntando al vacío. Lo que salva es la parte genérica (`\.env`, `secrets/`, `/root/.ssh`) — o sea, **protege por casualidad** |

**Al copiar un guard entre proyectos**, tres comprobaciones y ninguna cuesta un minuto: ¿la variable
de raíz **se usa** o es decorativa? · ¿a qué fichero escribe el log, y es de este proyecto? · ¿cuántas
rutas del patrón existen aquí? Si la respuesta a la tercera es «pocas», no estás protegido: estás
protegido por la parte genérica, y eso hay que saberlo.

## 🔌 Cero MCP sin revisión de código

**Anthropic NO audita los servidores MCP.** "Estándar abierto" no es "seguro por defecto": cada
servidor que conectas es superficie de ataque y puede exfiltrar datos mientras aparenta devolver
lo que se le pidió. La propia doc oficial lo dice:

> "Verify you trust each server before connecting it. Servers that fetch external content can
> expose you to prompt injection risk."

**La regla:** un servidor MCP no se conecta sin que alguien haya **leído su código o lo haya
verificado**. Para agentes delegados a perfiles no técnicos, la regla es más dura: **cero MCP**
salvo revisión previa de ingeniería. Cómo se configuran (scopes, tool search, el agujero de `-p`):
`code.claude.com/docs/en/mcp` y, en el template, `claude-code-referencia` §2; esta rule dice *cuándo NO*.

### Default-deny que SÍ funciona (y la trampa que hay que evitar)

⚠️ **`deny: ["mcp__*"]` junto a un `allow` de servidores concretos NO es "default-deny con
allowlist": es un apagón total de MCP.** Verificado en la doc de permisos: las reglas se evalúan
`deny` → `ask` → `allow`, gana el primer match y **la especificidad no cambia el orden**, así que
*"un `deny` no puede llevar excepciones"*. Además, un `allow` con glob sin anclar (`mcp__*`) *"se
ignora con un warning"*: los `allow` solo admiten glob **después** de un `mcp__<servidor>__`
literal.

El default-deny real se hace en **admisión de servidores**, no en reglas de tool:

| Quiero… | Clave | Dónde |
|---|---|---|
| Que el `.mcp.json` de un repo **no se auto-apruebe** | `enableAllProjectMcpServers: false` | settings de usuario/proyecto |
| Allowlist explícita de los servidores del repo que sí | `enabledMcpjsonServers: ["<nombre>"]` | idem |
| Bloqueo duro de un servidor **en todos los modos** | `disabledMcpjsonServers: ["<nombre>"]` | idem |
| Lockdown total (perfil sin ningún MCP) | `permissions.deny: ["mcp__*"]` | idem — **sin excepciones posibles** |
| Allowlist a nivel de tool de un servidor revisado | `permissions.allow: ["mcp__<servidor>__*"]` | idem |
| Política de organización (no sobrescribible) | `allowedMcpServers` / `deniedMcpServers` | **solo managed settings** |

**El agujero que nos aplica:** `claude -p`, las sesiones del Agent SDK y las de cloud **no pueden
mostrar el diálogo de aprobación, así que cargan los servidores del proyecto sin preguntar.** Como
usamos `/loop`, headless y workflows, el prompt interactivo no nos protege ahí: lo único que
bloquea en todos los modos es `disabledMcpjsonServers` (o excluir los settings del proyecto con
`--setting-sources`).

**Y la restricción de autenticación que va con ese agujero (SE-29, 2026-10-22).** Todo **producto** que
corra Claude por dentro, y todo uso **headless** (`claude -p`, Agent SDK, cloud) que no sea una persona
delante de su propia sesión, **autentica con API key (o credenciales de cloud) a nombre del operador**, y
**nunca con el OAuth de un plan de suscripción** (Pro/Max) ni intermediando las credenciales de otra
persona. Fuente: `r2-ciberseguridad.md` §3.1 (conclusión A: *«incluso aquí, `claude -p`/Agent SDK
headless deben autenticar por API key, no por OAuth de plan»*) y §4 punto 2. La verificación
independiente matiza: la restricción es literal para el SDK, y es **menos estricta para el binario de
Claude Code sin modificar** usado por una persona con su propia suscripción. Por eso esta rule fija lo
que sostiene la fuente (producto y headless de servicio → API key) y **no** da por buenos los
desatendidos propios de esta casa (`harness-gotchas.md` §`claude -p`), que hoy corren por suscripción:
si eso encaja o hay que pasarlos a API key es **decisión pendiente del Usuario** (se anota en
`decisiones_pendientes.json` al cerrar la sub-ola 2.28). Como la API se paga por token, el presupuesto va en la
cuenta del operador y se topa (`--max-budget-usd`, límite de la cuenta).

Desde v2.1.196 un repo clonado **no puede auto-aprobar sus propios servidores**: el
`enableAllProjectMcpServers` commiteado en el `.claude/settings.json` del repo se ignora en una
carpeta no confiada. Es una mitigación de Anthropic, no una excusa para no mirar.

### Checklist antes de conectar un servidor MCP

```bash
claude mcp list                      # ¿qué hay conectado AHORA y de qué scope?
claude mcp get <nombre>              # comando, args, origen
claude mcp reset-project-choices     # olvidar aprobaciones previas del proyecto
```

1. ¿De quién es el código y lo puedo leer? Si no → no se conecta.
2. ¿Qué datos ve y hacia dónde sale? (`agent-security.md` §6, lethal trifecta)
3. ¿Está pinneado a una versión, o es un `npx -y paquete@latest` que cambia bajo mis pies? (`gate_deps.py --solo cadena` lo avisa)
4. ¿Necesita credenciales? Que sean de ámbito mínimo y propias del agente, no las mías.
5. Al añadirlo: `allow` explícito de `mcp__<servidor>__*`, nunca un glob sin anclar.

El hook `audit-incoming-config.sh` avisa cuando un repo trae `.mcp.json` o
`enableAllProjectMcpServers`; el juicio sigue siendo humano.

---

## Anti-patterns

- ❌ **Dar por segura una red porque `ufw status` dice `DENY`** con contenedores publicando puertos →
  el tráfico de Docker entra por `FORWARD`/DNAT y no pasa por `INPUT`.
- ❌ Un WordPress de producción sin 2FA, con `xmlrpc.php` abierto o con un gestor de ficheros
  instalado → el detalle, en el template: `knowledge/wordpress/seguridad.md` §Anti-patterns.
- ❌ Publicar un contenedor en `0.0.0.0` «además» de ponerlo detrás de nginx → no solo es superficie
  de ataque: **el proxy no ve ese tráfico y el ataque no queda en ningún log**.
- ❌ **Archivar un proyecto y dejar sus contenedores corriendo** → archivar el código no apaga nada.

---

_2026-10-21 (sub-ola 2.15, MO-78): el caso del WordPress de este servidor —el minero, sus mediciones
y los anti-patterns de WordPress— se movió entero a `knowledge/wordpress/seguridad.md`; aquí queda la
regla general. Antes, 31,9 KB._
