---
description: >-
  ¿Qué toca ahora y cómo está el proyecto? Da el estado del repo (rama, cambios, commits, RAM,
  disco) y en cuál de los 13 pasos del proceso está, con qué teclear. Usar cuando: /siguiente, 'qué
  toca ahora', 'qué hago ahora', 'siguiente paso', 'cómo está el repo', '/status'. NO usar para:
  cómo abordar una tarea o repartir varios frentes (/otto).
---

# /siguiente — qué toca ahora, explicado

Dos cosas, en este orden: **el estado del repo** (§0, antes el comando `/status`) y **el paso del
proceso** (§1-6). Si solo se pide el estado («cómo está el repo», `/siguiente estado`), basta el §0.

## Cuándo se activa (detalle)

Disparadores: /siguiente, 'qué toca ahora', 'qué hago ahora', 'por dónde vamos', 'siguiente paso',
'no sé qué comando', 'what next', 'what should we do next', 'estado del proyecto', 'cómo está el
repo', '/status'.

Alcance: para quien no conoce los comandos. Da el estado del repo (rama, cambios, últimos commits,
RAM, disco; antes el comando /status, que chocaba con el /status de Claude Code) y mide en qué paso
del proceso (13 estados: definir → diseñar → construir → verificar) está el proyecto y dice, en
lenguaje llano, qué hay que teclear.

## 0. El estado del repo (antes `/status`)

> El comando `/status` se retiró el 2026-10-19 (LI-25): su nombre es el del `/status` **integrado de
> Claude Code** (versión, modelo, cuenta, conectividad), y con dos piezas del mismo nombre lo que se
> ejecuta depende de la precedencia. Su contenido es este apartado.

### /status - Ver estado del proyecto

Ejecuta estos comandos y muestra resumen:

```bash
# Git status
git status --short

# Rama actual
git branch --show-current

# Últimos 3 commits
git log --oneline -3

# Servicios (si aplica)
systemctl status [servicio] 2>/dev/null || echo "No systemd service"

# RAM disponible
free -h | grep Mem

# Disco
df -h / | tail -1
```

Mostrar resumen en formato:
- Branch: [rama]
- Cambios: [N archivos]
- RAM libre: [XGB]
- Estado: [OK/Warning]

> **Sin gastar turno (sub-ola 2.11, CL-25):** el mod `tl-visibilidad` (`.claude/mods/tl-visibilidad/`,
> se carga con `claude --plugin-dir`) trae `/estado` (este apartado: rama, cambios, RAM, PROGRESS.json y
> wave) y `/paso` (el paso del proceso de §1-6) como comandos que responden sin turno del modelo, incluso
> con Claude ocupado. Con el mod cargado, `/paso` es la forma gratis de este comando; `/siguiente` sigue
> siendo la skill (razona y explica). El nombre `/siguiente` no se registra en el mod a propósito: dos
> piezas con el mismo nombre se resuelven por precedencia, no por intención.

### Salida HTML (opcional)

Si el usuario pide `/siguiente html` (antes `/status html`; o un status "visual"/"para compartir"), genera el resumen como
artefacto HTML Tier-1 con la skill `html-suelto` (`/html-suelto status`) en vez de texto:
métricas + tabla shipped/slipped + chart + timeline, autocontenido en `.claude/docs/html/`.
Ver `.claude/rules/html-output.md`.

## 1-6. El paso del proceso

Ejecuta:

```bash
python3 .claude/scripts/siguiente_paso.py
```

y **explica el resultado a alguien que no conoce ni el proceso ni la jerga**:

1. Di en qué paso estamos (N de 13), **qué significa ese paso** en una o dos frases sin siglas, y
   **por qué va antes que el siguiente** (una razón, no tres).
2. Enseña **el comando exacto** que hay que escribir, tal cual sale del script, y qué va a pasar al
   escribirlo: si va a hacer preguntas, cuántas tandas y de qué; si va a generar ficheros, cuáles.
3. Si el script dice que hay material «sin verificar», explícalo: existe algo, pero ningún gate lo
   ha dado por bueno todavía — no es un error, es que falta comprobarlo.
4. Si el paso actual está en `no_cumple`, corre `python3 .claude/scripts/gate_arranque.py . --explica`
   y traduce **qué falta y cómo se arregla**, en llano.
5. Ofrece el tablero (`proceso.html`, servido con `abrir_panel.py`) y el manual
   (`.docs/core/manual.html`) como «dónde verlo con más calma».
6. Cierra con una sola pregunta: **«¿Lo lanzo?»**. Si el Usuario dice sí / adelante / vale, ejecuta
   el comando indicado. Si dice que no sabe algo que el paso va a preguntar, recuérdale que
   «no lo sé» es una respuesta válida: se marca `desconocido` y no se inventa.

## Lo que NO haces

- No das por sabido ningún comando, ruta ni sigla (PRD, ADR, gate, wave, MSW…): la primera vez que
  aparece, se explica en media línea. El glosario está en `manual.html`.
- No te saltas un paso porque «ya se sabe la respuesta»: el orden es el proceso, y el gate
  `gate-arranque.sh` bloquea el código de producto hasta cerrar los 7 pasos de arranque.
- No lanzas nada sin la pregunta del punto 6.
