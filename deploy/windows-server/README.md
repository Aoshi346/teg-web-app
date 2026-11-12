# TesisFar en un PC con Windows — guía de instalación

El PC con Windows 10 sirve TesisFar a internet en `https://tesisfar.<tu-red>.ts.net` y **se
actualiza solo**: cada vez que fusionas algo en `master` y los tests de GitHub salen en verde, en
menos de 5 minutos está publicado. Si una actualización falla, vuelve sola a la versión anterior.

```
Tú: push a master ──▶ GitHub Actions (tests) ──▶ ✓ verde
                                                   │  cada 5 min el PC pregunta: «¿hay algo nuevo con ✓?»
PC Windows 10 ─ WSL2 Ubuntu ───────────────────────┘
   copia de la BD → compila → migra → cambia de versión → comprueba
   ├─ bien  → aviso «Publicado abc1234»
   └─ falla → vuelve a la versión anterior + restaura la BD → aviso «Falló…»

Internet ──HTTPS──▶ Tailscale Funnel ──▶ Caddy 127.0.0.1:8080 ─┬─ /api, /admin → Django 127.0.0.1:8000
                                                               ├─ /media, /django-static → disco
                                                               └─ resto → Next.js 127.0.0.1:3000
```

No se abre ningún puerto del router y nada escucha fuera de `127.0.0.1`: la única entrada es Funnel.

---

## Ya hecho

- [x] WSL2 + Ubuntu con tu usuario de Linux
- [x] Cuenta de Tailscale
- [x] Suspensión desactivada

## Paso 1 — Que el kit esté en `master`

El servidor instala y vigila la rama `master`. Antes de instalar, fusiona en `master` la rama
`chore/despliegue-windows` (por `development`, como siempre) y espera a que GitHub Actions salga en
verde en la pestaña **Actions** del repositorio.

## Paso 2 — Instalar (dentro de Ubuntu)

Abre **Ubuntu** desde el menú Inicio y pega:

```bash
curl -fsSLo instalar.sh https://raw.githubusercontent.com/Aoshi346/teg-web-app/master/deploy/windows-server/install.sh
bash instalar.sh
```

Lo que pasará:

1. **La primera vez se para** y te dice que reinicies Ubuntu (activa systemd). Haz lo que indica:
   cierra Ubuntu, en PowerShell `wsl --shutdown`, abre Ubuntu y vuelve a ejecutar `bash instalar.sh`.
2. Te pide **tu contraseña de Ubuntu** (la que creaste con el usuario de Linux).
3. Muestra un **enlace de Tailscale**: ábrelo en el navegador de Windows e inicia sesión.
4. Compila la app (5-15 minutos la primera vez).
5. Te pide los datos de la **cuenta de Administrador** (correo, nombre, contraseña). Es la cuenta con
   la que entrarás a la web; la base de datos empieza vacía, sin usuarios de prueba.
6. Puede mostrar **otro enlace de Tailscale para activar Funnel**: ábrelo, pulsa activar y vuelve.
7. Al final te dice la dirección pública: `https://tesisfar.<tu-red>.ts.net`.

## Paso 3 — Arranque automático (PowerShell como administrador)

```powershell
powershell -ExecutionPolicy Bypass -File C:\TesisFar\install-windows.ps1
```

Desactiva la hibernación y crea una tarea que, al iniciar sesión en Windows, arranca Ubuntu en
segundo plano (y con él TesisFar) y bloquea la pantalla al minuto.

## Paso 4 — Inicio de sesión automático

Para que tras un reinicio (Windows Update, un apagón) TesisFar vuelva sin que nadie toque el PC:

1. `Win + R` → escribe `netplwiz` → Enter.
2. Desmarca **«Los usuarios deben escribir su nombre de usuario y contraseña para usar el equipo»**.
   Si esa casilla no aparece: Configuración → Cuentas → Opciones de inicio de sesión → desactiva
   «Requerir el inicio de sesión con Windows Hello» y vuelve a abrir `netplwiz`.
3. Aceptar → escribe la contraseña de Windows dos veces.
4. Reinicia el PC y comprueba que, sin tocar nada, la web vuelve a responder (tarda 1-2 minutos).

El paso 3 bloquea la pantalla al minuto de entrar, así que el escritorio no queda abierto.

## Paso 5 (opcional) — Avisos por correo

Cuando tengas la contraseña de aplicación de Gmail (https://myaccount.google.com/apppasswords):

```bash
bash ~/tesisfar/bin/configure-email.sh
```

Manda un correo de prueba. Hasta entonces los avisos quedan en `~/tesisfar/logs/avisos.log`.

---

## Día a día

No hay que hacer nada: push a `master` → en menos de 5 minutos, publicado (si los tests pasan).

| Quiero… | Comando (dentro de Ubuntu) |
|---|---|
| Ver si todo está en marcha | `systemctl status tesisfar-backend tesisfar-frontend tesisfar-proxy` |
| Ver los avisos | `cat ~/tesisfar/logs/avisos.log` |
| Ver el registro de despliegues | `tail -50 ~/tesisfar/logs/deploy.log` |
| Buscar actualización ya, sin esperar 5 min | `sudo systemctl start tesisfar-update` |
| Saber qué versión está publicada | `readlink ~/tesisfar/current` |
| Reintentar un commit que falló | `rm ~/tesisfar/state/failed-sha && sudo systemctl start tesisfar-update` |
| Ver la dirección pública | `sudo tailscale funnel status` |

**Copias de seguridad:** cada día a las 03:30, de la base de datos y de los ficheros subidos, en
`~/tesisfar/backups/daily` **y** en `C:\TesisFar\backups` (sobreviven aunque Ubuntu se rompa). Se
guardan 14 días. Antes de cada actualización se hace además una copia de la base de datos
(`~/tesisfar/backups/pre-deploy-*`).

**Restaurar una copia a mano** (solo si hace falta):

```bash
sudo systemctl stop tesisfar-backend
cp ~/tesisfar/backups/daily/db-AAAAMMDD-HHMM.sqlite3 ~/tesisfar/data/db.sqlite3
rm -f ~/tesisfar/data/db.sqlite3-wal ~/tesisfar/data/db.sqlite3-shm
sudo systemctl start tesisfar-backend
```

## Lo que conviene saber

- **El PC tiene que estar encendido y con internet.** Si se apaga, la web no responde hasta que vuelva.
- **Memoria (PC de 8 GB):** WSL queda limitado a 4 GB más 4 GB de swap, y la compilación de cada
  actualización a ~1,5 GB. Con Windows ya usando 5 GB, conviene cerrar lo que no haga falta
  (navegadores con muchas pestañas, programas que arrancan solos) para que las actualizaciones no vayan lentas.
- **Tailscale Funnel tiene un límite de ancho de banda** que Tailscale no publica. Para formularios y
  PDFs sobra; si un día va lento con mucha gente, el plan B es comprar un dominio y cambiar Funnel
  por Cloudflare Tunnel (solo cambia esa pieza).
- **Windows 10 ya no recibe parches de seguridad** (desde octubre de 2025). Desde internet solo se ve
  la app, no el PC, pero conviene pasar a Windows 11 cuando se pueda.
- **Los ficheros subidos (`/media/`) se sirven sin comprobar sesión**, igual que antes en local:
  quien tenga el enlace exacto de un PDF puede abrirlo. Pendiente de decidir si se protege.
- Si cambian los ficheros de `templates/` (servicios o Caddyfile), hay que volver a ejecutar
  `bash ~/tesisfar/bin/install.sh` una vez; el actualizador automático solo
  cambia el código de la app.
