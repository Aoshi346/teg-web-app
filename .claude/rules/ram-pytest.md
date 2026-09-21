# RAM y pytest — límites duros del servidor

> **Cuándo aplicar:** SIEMPRE antes de correr cualquier test, lanzar agentes paralelos o abrir
> navegadores headless. Consolidada aquí desde CLAUDE.md (poda TPL-1, 2026-08-07) — el CLAUDE.md
> lleva el resumen; esta rule es el detalle; el **enforcement determinista es el hook
> `check-ram.sh`** (PreToolUse), no la prosa.

## Límites del servidor — la fuente es el hook, no esta prosa

⚠️ **Los números vivían en SEIS sitios hasta el 2026-09-11**: aquí, en `parallelization.md`,
`agent-teams.md`, `speckit-workflow.md`, `blackboard.md`, `loop-workflow.md`, `qa-loop.md` y
`CLAUDE.md`. Cambiar el umbral obligaba a tocarlos todos, y el que se olvidara dejaba escrita una
norma que ya no era cierta — que es el modo de fallo de `verification.md` §"una norma escrita no es
una norma aplicada". **Ahora la fuente única es `.claude/hooks/check-ram.sh`**, que los calcula para
la máquina en la que estés y los sabe decir:

```bash
bash .claude/hooks/check-ram.sh --explain    # los límites de ESTA máquina, ahora mismo
```

Esta rule conserva **el criterio y el porqué**; el resto del harness la cita a ella o al hook, y no
vuelve a escribir cifras.

| Recurso | Valor | ¿Quién lo decide? |
|---|---|---|
| RAM total | se lee de la máquina (`free -g`) | la máquina — **nunca se asume** |
| Reserva del sistema (umbral) | **`max(10% del total, 3 GB)`** | el hook lo calcula |
| RAM por worktree / Tech Lead | **4 GB** | criterio |
| Instancias simultáneas **en un repo** | **derivado**: `(libre − umbral) ÷ 4 GB`, mínimo 1 | el hook lo calcula |
| Workers pytest | **máx 2** | criterio |
| Agentes con navegador (Playwright/Chrome) | cuentan **~doble** — **máx 3**, y NUNCA solapados con pytest | criterio: **esto NO se deriva** |

### El umbral (decisión del Usuario, 2026-09-11)

**`max(10% de la RAM total, 3 GB)`.** Sustituye a `max(20%, 5 GB)` (2026-08-08), que en este
servidor de 62 GB apartaba **12,4 GB que no usaba nadie** y bloqueaba trabajo en paralelo legítimo.
El porcentaje escala con el hardware; el suelo de 3 GB evita que en una máquina de 8 GB el 10%
(0,8 GB) deje al sistema sin aire.

### El tope de instancias ya no es «3» (misma decisión)

Aquel **3 fijo venía de una máquina más pequeña, no de una medición**. Ahora sale de la RAM que
queda por encima del umbral, a 4 GB por sesión. En este servidor con 42 GB libres son **9**, no 3.

Dos cosas que hay que entender antes de "arreglar" la fórmula:

1. **Es auto-correctiva.** `free` *available* ya descuenta lo que consumen las sesiones vivas, así
   que el tope se estrecha solo conforme se llena la máquina. Por eso **no se le suman** las
   sesiones actuales: si se hiciera, el tope sería siempre mayor que la cuenta y no bloquearía nunca.
2. **El navegador sigue topado en 3 a mano.** El hook no puede saber qué sesión abre Chrome, así que
   esa parte es criterio humano y no se deriva de nada.

> **Se ha visto fallar.** Los dos checks se probaron saboteándolos a propósito el 2026-09-11 (umbral
> imposible → bloquea por RAM; 5 sesiones con tope 2 → bloquea por concurrencia). Un gate que nunca
> has visto en rojo no es un gate (`verification.md`).

## Antes de CUALQUIER pytest (PASO 1, siempre)

```bash
bash .claude/hooks/check-ram.sh && echo "vía libre"   # el gate real, con el umbral ya calculado
```

⚠️ **No cuentes instancias con `grep -c claude`**: engloba el daemon, los `bg-pty-host`/`bg-spare`,
los `tmux new … claude` y hasta shells cuyo path contiene `/root/.claude/`. Daba 13 "instancias"
donde había 3 y bloqueaba `pytest` siempre — un falso positivo que invita a saltarse el gate. El
hook cuenta procesos de Claude Code con **>200 MB RSS**, y **solo los de este repo**: bloquear por
lo que hace otro proyecto era el mismo falso positivo una capa más abajo (arreglado 2026-08-26).

## Pytest SIEMPRE en chunks

```bash
# ❌ PROHIBIDO — mata el servidor:
pytest                    # todo el proyecto
pytest tests/             # directorio completo
pytest -n auto            # auto workers
pytest --cov              # coverage = +RAM

# ✅ OBLIGATORIO:
pytest apps/MODULE/ -v --maxfail=3     # por módulo
pytest -k "test_name" -v               # test específico
pytest tests/file.py -v -x             # un archivo, para al primer fallo
pytest -n 2 tests/unit/algo/ -v        # máximo 2 workers
```

Muchos tests → chunks de ~20 con verificación de RAM entre cada uno:

```bash
pytest tests/unit/models/ -v --maxfail=3 && free -h | awk '/Mem:/{print $7}'
pytest tests/unit/views/ -v --maxfail=3
```

## Si ocurre OOM

1. Es **FALLO CRÍTICO** del Tech Lead — documentarlo en PROGRESS.log.
2. Reducir el scope de tests, esperar a que se libere RAM, reintentar con chunk más pequeño.

## Anti-patterns

- ❌ Correr pytest sin el `free -h` previo — la verificación de RAM es el paso 1, no opcional.
- ❌ Lanzar QA visual (3 personas con Chrome) en paralelo con pytest — revienta el límite.
- ❌ Confiar en que esta rule se leerá: el hook `check-ram.sh` es quien bloquea de verdad.
