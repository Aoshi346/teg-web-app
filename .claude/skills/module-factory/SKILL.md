---
name: module-factory
description: >-
  Usar para desarrollar VARIOS MÓDULOS A LA VEZ en un repo, un worktree por módulo y una sesión
  padre que mergea: 'reparte los módulos', 'worktrees por módulo', 'fábrica de módulos'. Reparto
  escrito, module_split.py, franjas y guiones padre, hijo y e2e. NO usar para: si conviene
  paralelizar (parallelization.md §0), un frente suelto (launch_front.sh) ni elegir mecanismo (/otto).
user-invocable: true
metadata:
  version: 1.0.0
  author: tech-lead-template
  category: workflow
  updated: 2026-10-31
  origin: skill fabrica-de-modulos de un proyecto Django + React con 8 módulos en paralelo (AN-D6, sub-ola 3.20)
---

# Fábrica de módulos — varios frentes a la vez sin pisarse

Una sola sesión avanza en serie; repartir por módulos es lo obvio y falla por lo que no se ve: **los
ficheros que todos tocan**. En el proyecto de origen, los siete más editados en 120 commits eran
**registros compartidos** (contrato de la API, consultas, tipos, rutas, mocks, CSS); ocho worktrees
contra eso son conflictos de ocho vías. La fábrica son dos cosas, y la segunda es la que importa:

1. el banco de trabajo de cada módulo (worktree + su franja de datos y puertos);
2. **un reparto de ficheros escrito y comprobado** antes de lanzar a nadie.

Antes de nada, el test de independencia (`rules/parallelization.md` §0): si la respuesta de un
módulo cambia según la de otro, no son dos frentes.

## 1. El reparto — la regla dura

> **Cada sesión hija toca SOLO los ficheros de su módulo. Lo de fuera lo pide al padre y sigue con
> otra cosa mientras tanto.**

Se escribe en `.claude/modules.json` (formato en la cabecera del script) y se comprueba:

```bash
python3 .claude/scripts/module_split.py --measure --commits 200   # los calientes, sin reparto
python3 .claude/scripts/module_split.py                           # SOLAPE · SIN DUEÑO → exit 1
```

**Del padre, siempre**: el idioma visual (el CSS del design system), el esqueleto de navegación y
rutas, los tipos compartidos de la API, los handlers de mocks, los ficheros **generados** (se
regeneran, no se editan), las dependencias (`pyproject.toml`, `package.json`: el venv y los
`node_modules` son uno), la config del bundler que reparte puertos y proxy, y `.claude/**`.

**Partir un registro antes de repartir** (`consultas.ts` → `consultas/<módulo>.ts` + `index.ts`;
`urls.py` → una lista por módulo) solo vale si el derivado sale **idéntico** (esquema OpenAPI, tests):
compilar no prueba nada. Y algunos no se pueden partir (nombres declarados dos veces, como esquema y
como tipo; mocks cuyo orden global importa): se quedan del padre con la razón escrita. El detalle y los
casos: `parallelization.md` §«Ya tienes el registro localizado».

⚠️ **En una lista de rutas partida, el orden puede ser contrato**: dos módulos que registran el mismo
`name=` hacen que `reverse()` resuelva al último. Reordenar cambia comportamiento.

## 2. Puertos, bases y Redis — una franja por módulo

Un solo Docker con **una base y un índice de Redis por módulo**, no un stack por worktree. Lo reparte
`scripts/franja.py` (escribe el `.env.franja` de cada checkout y comprueba choques y «local =
producción»). Se llega por túnel SSH, nunca escuchando en `0.0.0.0`. El virtualenv es uno, el de la
raíz: con el cwd en el worktree se ejecuta su código con el intérprete compartido.

## 3. Los tres guiones

### El PADRE — una sola sesión, la que coordina

1. Cierra la **ola 0** antes de repartir: registros partidos, `module_split.py` en verde, franjas probadas.
2. Abre cada módulo con `scripts/launch_front.sh <plan> <módulo>` (las diez guardas) desde `sesiones.json`.
3. Es dueño de los ficheros del padre y aplica lo que le piden los hijos.
4. Hace **todos los merges** a la rama de trabajo. Ningún hijo mergea ni hace push.
5. Borra el worktree cuando su rama está integrada y en verde, con OK (`governance.md` §2).

### El HIJO — uno por módulo

- Lee su sesión SpecKit y marca los checkboxes en vivo; commitea en su rama, a menudo.
- **Rebase sobre la rama de trabajo dos veces al día, y después `manage.py migrate` A SECAS** (no
  `migrate <su-app>`): el rebase trae las migraciones de los demás y su base local se queda corta. Se
  disfraza de tres maneras a la vez: los tests siguen verdes (pytest migra su propia base), la pantalla
  sale en blanco sin mensaje, y el 500 nombra una tabla de OTRO módulo.
- pytest con turno: `scripts/pytest_turn.sh <módulo>` (los turnos son de la máquina, no del repo).
- Antes de darse por hecho: tests de su módulo, el lint de verdad y captura si hay pantalla.

> ⚠️ **`npx tsc --noEmit` puede no comprobar NADA.** Con un `tsconfig.json` de `"files": []` y solo
> referencias, type-chequea cero ficheros y sale 0 siempre; el bueno es `tsc -b --noEmit` (lo que hay
> detrás de `npm run build`). Medido con un import inventado: `--noEmit` → 0, `-b --noEmit` → 2.

### El de EXTREMO A EXTREMO

Arranca cuando el desarrollo está integrado, no antes. **Congela el build y anota su sha** (una ronda
con parches en caliente mide un objeto que no existe, `qa-loop.md` §1b), `/qa-loop` sobre ese sha,
**cada auditor con su cuenta de QA** (un freno de peticiones por usuario vacía las páginas si la
comparten), y no se solapa con las sesiones de desarrollo (el navegador cuenta doble en RAM).

## 4. Cuántas sesiones a la vez

Lo dice la máquina, no un número: `bash .claude/hooks/check-ram.sh --explain`. Los agentes con
navegador tienen su propio tope, que no se deriva.

## Anti-patterns

- ❌ Repartir **sin haber partido antes los registros** ni pasado `module_split.py` → conflicto de N vías.
- ❌ Que un hijo edite un fichero del padre «porque era una línea» → el siguiente rebase lo paga.
- ❌ Que un hijo haga push o merge.
- ❌ Un worktree con su propio Docker, o el virtualenv copiado a cada worktree.
- ❌ Lanzar el extremo a extremo a la vez que las de desarrollo, o auditar con una sola cuenta.
- ❌ Dar por bueno un corte de registro porque compila, sin comparar el derivado.
