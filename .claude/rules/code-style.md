# Reglas de Estilo de Código

## Python/Django
- PEP 8 siempre
- Type hints en funciones públicas
- Docstrings en clases y funciones complejas
- Max 100 caracteres por línea
- Imports ordenados: stdlib, third-party, local

## TypeScript/React
- ESLint + Prettier
- Componentes funcionales (no clases)
- Props con interfaces, no types
- Hooks para lógica reutilizable
- Evitar any, usar unknown si necesario

## Idioma — el código en inglés; comentarios, docstrings y pantalla en castellano
- **Identificadores en inglés**: ficheros, carpetas, clases, funciones, variables, campos, claves
  JSON y rutas de API. **En castellano**: comentarios, docstrings, mensajes y todo texto que lee una
  persona. Los nombres de test pueden ir en castellano (son frases que se leen en la salida).
- Decisión del Usuario (06-09-2026, «prohibido, prohibido, prohibido»): se incumplió dos veces con la
  regla en memoria, así que la regla trae su gate: `python3 .claude/scripts/gate_idioma.py --staged`
  (exit 1 con un nombre nuevo en castellano). Lo heredado no se renombra en caliente: se congela
  una vez con `--congelar` y lo que se toque después se juzga línea a línea (`refactor-progresivo.md` §4).

## Comentarios — escuetos, y la cita `<fichero>:<línea>` va fuera del código (MO-59)
- Un comentario dice el porqué del código que tiene al lado, en una línea si cabe. Sin historia
  («antes hacía…», «el Usuario pidió…») ni procedencia: eso va al commit, a la respuesta o al informe.
- **«Cita el patrón con archivo:línea»** (`code-reuse`, Rita, revisiones) se cumple en la respuesta y
  en el informe, **nunca en un comentario**: el número de línea caduca con la siguiente edición y queda
  como ruido permanente. Caso EVO-2876: ~600 líneas de comentario, 66 con historia y 27 con cita.
  Lo marca `code-review-gate` (§Comentarios con cita en el diff).

## Commits
```
tipo(scope): descripción corta

Tipos: feat, fix, docs, style, refactor, test, chore
Ejemplo: feat(clients): add portal public view
```

## Branches — se trabaja EN `develop`, no en una rama por feature

> **Decisión del Usuario, 2026-08-27**, y aplica a casi cualquier proyecto de la casa:
> *«Hazlo todo en develop siempre. No crees ramas. Solo estamos desarrollando nosotros. Si acaso
> para separar y hacerlo todo más paralelo y separable, usa worktrees siempre y si acaso en esos
> worktrees le asignas ramas. Pero siempre debemos tener como principal develop.»*

| Rama | Para qué |
|---|---|
| `main` | Producción |
| **`develop`** | **Donde se trabaja.** Es el default: se commitea aquí directamente |
| `feature/*` · `fix/*` | **Solo dentro de un worktree**, cuando hay dos frentes de verdad a la vez |

**Por qué así, y por qué no es lo que dice el manual.** El flujo de rama-por-feature existe para
coordinar a varias personas que se pisan. Aquí no hay varias personas: hay un equipo pequeño y
agentes que trabajan de uno en uno sobre el mismo repo. La rama entonces no coordina nada — solo
añade un merge que hacer, un sitio donde olvidarse el trabajo, y un estado más que recordar.

**Cuándo SÍ se abre rama, y es el único caso:** cuando hay **dos frentes simultáneos** que tocarían
los mismos ficheros. Entonces la respuesta no es «una rama», es **un worktree** (`rules/parallelization.md`
§3 y §file claims), y a ese worktree se le asigna su rama. La rama es una
consecuencia del worktree, no un paso previo a trabajar.

**Para quien crea o actualiza proyectos** (`project-setup`, `create-agent`, `update-agent`): un
proyecto nuevo **no nace proponiendo rama por feature**. Nace trabajando en `develop`, y el
asistente propone worktree cuando de verdad haya dos frentes.

**Es el default, no una imposición** (MO-16): un proyecto que decidió otra cosa —EvoPreven: rama
`EVO-XXXX-slug` y worktree por issue, commits solo del Usuario— lo declara en su `CONFIGURACION.yaml`
(`git_commit`, `git_merge`, `git_branching`) y eso manda; los hooks lo leen (`session-stop.sh`).

> ⚠️ **Esto no relaja `governance.md` §2.** Trabajar en `develop` sigue sin dar permiso para
> `push`, para merge a `main` ni para nada de la lista de aprobación. Lo que cambia es dónde se
> commitea, no qué se puede hacer sin preguntar.
