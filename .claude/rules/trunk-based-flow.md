---
paths:
  - ".claude/rules/trunk-based-flow.md"
  - ".github/pull_request_template.md"
  - ".claude/scripts/pr_video.py"
  - "**/feature_flags.py"
---
# Trunk-based — ramas cortas, rebase 2×/día y feature flags

> **Cuándo aplicar:** siempre que se abra una rama de trabajo en un repo con más de una persona (o
> más de un agente) tocándolo. Define **cómo se integra**: cada cuánto se rebasa, cómo se mergea
> algo a medias sin romper a nadie, cómo se parte un PR grande, y qué evidencia lleva un PR con
> interfaz.
>
> **NO aplicar:** repo de una sola persona con una sola rama viva (no hay de quién alejarse) ·
> commits directos a la rama de trabajo dentro de una misma sesión (eso ya lo cubre
> `governance.md` §2 como acción autónoma) · el reparto de **quién toca qué fichero** cuando hay
> varios frentes en paralelo — eso es `parallelization.md` §file claims, y esta rule **no lo
> duplica**: aquí se dice cada cuánto te reconcilias con el tronco, allí quién reclama cada ruta.
>
> **Relacionado:** `parallelization.md` (§file claims y el protocolo de worktrees — el compañero
> natural de esta rule) · `governance.md` (§2 qué merges necesitan aprobación · §3.1 autonomía por
> tipo de tarea) · `code-style.md` (§Branches, la nomenclatura) · `verification.md` (el checklist
> pre-DONE que el PR trae ya cumplido) · `recovery-patterns.md` (cuando el rebase sale mal) ·
> skill `verification-loops` (§Después del merge) (quien verifica **después** del merge).

---

## 0b. ⚠️ ACTUALIZACIÓN 2026-08-27 — aquí NO se abre rama por feature

> **Decisión del Usuario:** *«Hazlo todo en develop siempre. No crees ramas. Solo estamos
> desarrollando nosotros. Si acaso para separar y hacerlo todo más paralelo y separable, usa
> worktrees siempre y si acaso en esos worktrees le asignas ramas. Pero siempre debemos tener como
> principal develop.»*

**Esta rule sigue valiendo entera, pero su premisa cambia.** Estaba escrita para el caso de varias
personas que se pisan, y por eso su §1 dice «rebasa tu rama dos veces al día». Aquí no hay varias
personas: **se commitea directamente en `develop`**, así que no hay rama de la que alejarse y el
rebase deja de aplicar en el caso normal.

**Qué se conserva, y por qué sigue siendo lo importante de este documento:**

| Sección | Sigue valiendo |
|---|---|
| §1 rebase 2×/día | **Solo dentro de un worktree.** Sin rama, no hay nada que rebasar |
| §2 feature flags | **Entero, y ahora más:** trabajar en `develop` obliga a que lo que está a medias no se vea. El flag deja de ser una opción y pasa a ser la forma de meter algo sin terminar |
| §3 slice pattern | **Entero.** Partir por capas sigue siendo lo que hace que un cambio grande entre sin romper el tronco |
| §4 evidencia del PR | **Entero**, aunque no haya PR: la captura, el vídeo del flujo y la salida de los tests van igual en el commit o en el informe |
| §5 targets de salud | La «edad de la rama» deja de medirse; los demás siguen |

**Cuándo se abre rama, y es el único caso:** dos frentes simultáneos sobre los mismos ficheros. La
respuesta entonces es **un worktree** con su rama (`parallelization.md` §3 y §file
claims), no una rama a secas. Y ahí sí vuelve a aplicar el §1 completo.

**O cuando el proyecto lo declara** (MO-16, sub-ola 2.14): «todo en develop» es el default, no una
imposición. Un proyecto con `git_branching: rama-por-issue` en su `CONFIGURACION.yaml` (EvoPreven: rama
`EVO-XXXX-slug` + worktree por issue) trabaja así y esta rule le aplica entera, §1 incluido; quién
commitea y quién mergea, también ahí (`git_commit`, `git_merge`).

> **La regla de oro que NO cambia:** `governance.md` §2 sigue mandando. Commitear en `develop` no
> da permiso para `push`, ni para merge a `main`, ni para nada de la lista de aprobación.

---

## 0. El problema, en una frase

Una rama que lleva cinco días abierta ya no se está desarrollando: se está **alejando**. Cuando por
fin se mergea, el diff es tan grande que nadie lo revisa de verdad — se aprueba por cansancio — y
los conflictos que aparecen ya no son de dos líneas, son de arquitectura.

**Trunk-based** es el nombre del flujo contrario: existe **un tronco** (aquí, `develop`) que es la
verdad, y todo lo demás son ramas que viven **horas o un día**, no semanas.

> ⚠️ **No confundir con "sin ramas".** Trunk-based no significa commitear directo al tronco. Las
> ramas siguen existiendo y los PRs también; lo que cambia es **cuánto viven** y **cada cuánto se
> reconcilian** con el tronco.

**Qué es el tronco aquí.** Este template usa `main` (producción) y `develop` (desarrollo), con
`feature/*` y `fix/*` colgando (`code-style.md` §Branches). **El tronco es `develop`**, y esta rule
no cambia esa nomenclatura: cambia la vida media de las ramas que salen de él.

---

## 1. Rebase 2 veces al día (la pieza no negociable)

**Qué es un rebase, sin jerga.** Tu rama salió del tronco en un punto concreto. Mientras trabajabas,
otros han metido cosas en el tronco. Rebasar es **recoger tu trabajo, mover la base de tu rama al
estado más reciente del tronco, y volver a aplicar tus commits encima** — como si hubieras empezado
hoy en vez de anteayer. El resultado: tu código se prueba siempre contra lo último, no contra una
foto vieja.

**La diferencia con `merge`, con un ejemplo.** Si tú y otra persona tocáis el mismo fichero:
- **Rebasando 2×/día**: el segundo día te sale un conflicto de tres líneas, lo resuelves en dos
  minutos y sigues.
- **Mergeando al final**: el viernes te sale el mismo conflicto multiplicado por cinco días de
  cambios de ambos, y ya nadie recuerda por qué se escribió cada trozo.

Es el mismo conflicto. Lo único que cambia es **cuándo lo descubres y cuánto cuesta**.

### El procedimiento

```bash
# Dos veces al día — al empezar y después de comer. Cuesta ~2 minutos si no hay conflicto.
git fetch origin
git rebase origin/develop

# Si hay conflicto: resuelves, y sigues el rebase (NO haces commit)
#   git add <ficheros resueltos> && git rebase --continue
# Si te lías y quieres volver al punto de partida, siempre:
#   git rebase --abort

# Subir la rama ya rebasada
git push --force-with-lease
```

**`--force-with-lease`, y por qué NUNCA `--force` a secas.** Rebasar reescribe la historia de tu
rama, así que el push normal se rechaza y hay que forzarlo. La diferencia:

| Comando | Qué hace si alguien subió algo a tu rama mientras rebasabas |
|---|---|
| `git push --force` | **Lo borra sin avisar.** El trabajo del otro desaparece |
| `git push --force-with-lease` | **Se aborta y te avisa.** Solo pisa si el remoto está donde tú creías |

`--force-with-lease` no es una versión "suave" del force: es la única forma segura de subir una rama
rebasada. Trátalo como el default y `--force` como algo que no se teclea.

> ⚠️ **La regla de oro del rebase:** se rebasa **tu propia rama de trabajo**. Nunca se rebasa una
> rama de la que cuelga el trabajo de otra persona, ni el tronco. Reescribir historia compartida es
> una acción que requiere aprobación (`governance.md` §2) y suele acabar en
> `recovery-patterns.md`.
>
> **Corolario para agentes en worktrees:** el `git push --force-with-lease` de un TL solo aplica a
> **su** rama de worktree. Si dos frentes comparten rama, no son dos frentes — es uno mal repartido
> (`parallelization.md` §0).

### Cuándo NO rebasar y mergear en su lugar

- La rama ya está **en revisión** y el revisor ha dejado comentarios anclados a commits: rebasar se
  los descoloca. Termina la revisión, luego rebasa antes de mergear.
- Estás a **minutos** de mergear y el tronco no se ha movido: `git fetch` y comprueba; si no hay
  nada nuevo, el rebase es una operación vacía.

---

## 2. Feature flags — cómo mergear algo a medias sin que se vea

El rebase diario solo funciona si además **puedes mergear pronto**. Y no puedes mergear pronto si el
código está a medias… salvo que lo escondas detrás de un interruptor.

**Qué es un feature flag, sin jerga.** Una variable de entorno que decide si una funcionalidad se
ve o no. El código está en el tronco, mergeado y compilando junto a todo lo demás, pero el usuario
no lo alcanza porque el interruptor está apagado.

```python
# Django — el patrón mínimo. Un helper, no una librería.
import os

def flag(name: str, default: bool = False) -> bool:
    """Lee un feature flag del entorno. FEATURE_<NAME>=1 lo enciende."""
    raw = os.environ.get(f"FEATURE_{name.upper()}")
    return default if raw is None else raw.strip().lower() in {"1", "true", "yes", "on"}
```

```python
# En la vista / el router: la mitad nueva solo existe si el flag está encendido
if flag("NUEVO_CHECKOUT"):
    return nuevo_checkout(request)
return checkout_actual(request)
```

```tsx
// Frontend — el flag entra por la variable de build, no por un if suelto en cada componente
const NUEVO_CHECKOUT = import.meta.env.VITE_FEATURE_NUEVO_CHECKOUT === "1";
```

**Lo que compras con esto:**

| Sin flag | Con flag |
|---|---|
| El código a medias vive en una rama que se aleja 5 días | El código a medias vive en el tronco, integrado desde el día 1 |
| Rollback = revertir un merge grande y rezar | Rollback = **cambiar una variable de entorno y reiniciar** |
| Se prueba en producción el día del despliegue | Se puede encender solo para ti, o solo en staging |

**Lo que cuesta, dicho claro:**

1. **El código muerto se acumula.** Cada flag deja dos caminos vivos en el repo. Un flag que lleva
   seis meses encendido al 100% ya no es un flag: es ruido que hace el código más difícil de leer.
2. **La combinatoria explota.** Tres flags son ocho estados posibles y nadie los prueba todos.
3. **Hay que acordarse de limpiarlo**, y nadie se acuerda solo.

**Las tres reglas que hacen que el coste no se dispare:**

- **Todo flag nace con fecha de caducidad**, escrita en el mismo commit que lo crea:
  `# flag: NUEVO_CHECKOUT · retirar tras el despliegue del 2026-09-15 · dueño: <quién>`.
- **Máximo ~3 flags vivos a la vez** en un proyecto. Si necesitas el cuarto, retira uno antes.
- **Retirar el flag es una tarea del plan**, con su casilla en `tasks.md` — no "cuando haya un
  rato". Se borra el `if`, se borra el camino viejo, y se comprueba que los tests siguen verdes.

> **Cuándo NO usar flag:** un cambio pequeño y completo que cabe en un PR de un día no necesita
> interruptor — necesita mergearse. El flag es para lo que **tarda más de un día en estar
> presentable**, no para todo.

---

## 3. Slice pattern — partir el PR de 5 días en 4 de un día

Con el flag puesto, un trabajo grande deja de ser un PR gigante y pasa a ser una **serie de PRs
pequeños que ya están integrados**. La forma de cortarlo, en orden:

| # | El corte | Qué contiene | Se puede mergear porque… |
|---|---|---|---|
| 1 | **Andamiaje** | El flag (apagado), migraciones vacías o aditivas, el esqueleto de módulo | No cambia ningún comportamiento visible |
| 2 | **Backend detrás del flag** | Modelos, lógica, endpoints — con sus tests | Nadie lo alcanza con el flag apagado |
| 3 | **Frontend detrás del flag** | Pantallas y componentes | Idem |
| 4 | **Encendido + limpieza** | Flag a `1`, retirada del camino viejo | Ya está todo probado y revisado |

La regla que decide si un corte es válido: **¿este PR, solo, deja el tronco sano?** Si la respuesta
es sí (compila, los tests pasan, nada visible cambió), se mergea aunque la funcionalidad no esté
terminada. Si es no, el corte está mal hecho.

**Corte por capas, no por "mitad del trabajo".** El error habitual es partir por volumen ("los
primeros 25 ficheros"), y eso produce dos PRs que solo funcionan juntos. Se corta por **capa** o por
**caso de uso completo pero pequeño**.

---

## 4. Evidencia de un PR — y el vídeo cuando hay interfaz

Un PR pequeño se revisa rápido solo si trae su evidencia dentro. Lo mínimo ya está en
`verification.md` (código corre · tests del módulo · sin errores de consola); esta rule añade **qué
se adjunta** según lo que toque el PR:

| El PR toca… | Evidencia obligatoria en la descripción |
|---|---|
| Solo backend / config | Salida de los tests del módulo, pegada |
| Un endpoint nuevo o modificado | Además, la llamada real (`rules/verification.md` §Smoke testing, requests reales) |
| **Interfaz** (cualquier cambio visible) | Además, **captura** del estado final |
| **Interfaz con un flujo de varios pasos** | Además, **vídeo** del recorrido (§4.1) |
| Ficheros que otro frente también toca | El claim declarado (`parallelization.md`) |

### 4.1 Vídeo — solo cuando hay flujo, no en todo PR

**El acotamiento es deliberado.** Un vídeo por cada PR que mueva un margen de 8px es peso muerto:
engorda el repo, nadie lo abre, y al mes se ignoran todos — la misma fatiga que describe
`agent-security.md` (ASI09). El vídeo se exige donde la captura **no puede** demostrar lo que hay
que demostrar:

| Lleva vídeo | No lleva vídeo (basta captura) |
|---|---|
| Un flujo de varios pasos (alta, checkout, wizard, login→acción→resultado) | Cambio de estilo, copy, color, espaciado |
| Una transición o animación que es parte de la feature | Una pantalla nueva estática |
| Un estado intermedio que solo existe un segundo (spinner, toast, validación en vivo) | Un componente aislado |
| El cierre de una wave con UI (junto al `/qa-loop`) | Un fix de un solo campo |

**Cómo se graba.** Playwright ya graba vídeo de forma nativa; el helper del template lo expone:

```bash
# Graba el recorrido y deja el .webm listo para adjuntar
python3 .claude/scripts/pr_video.py "http://127.0.0.1:8000/" /tmp/pr-<n>.webm \
    --steps '[{"click":"[data-testid=\"login-submit\"]"},{"wait_for":"[data-testid=\"dashboard\"]"}]'
```

**Dónde vive el fichero — la respuesta es "fuera del repo".** Un vídeo por PR commiteado hace que
el repo crezca para siempre, y git no sabe borrar el pasado. Por orden de preferencia:

1. **Adjunto en el PR** (GitHub acepta `.webm`/`.mp4` arrastrándolo al comentario y lo hospeda él).
   Es el default: queda junto a la revisión y no toca el repo.
2. Si no hay plataforma de PR, en el directorio de evidencias del plan
   (`.docs/plans/<plan>/feedback/…`) **con el `.gitignore` ya puesto** para binarios, y se enlaza.
3. **Nunca** commiteado en el árbol de código.

`.gitignore` recomendado (mismo criterio que las capturas del `qa-loop`):

```gitignore
*.webm
*.mp4
```

---

## 5. Targets de salud — números para mirar, no para castigar

Estos son los indicadores de que el flujo funciona. **Son orientativos y solo sirven si alguien los
mira**; puestos en un panel que nadie abre son decoración.

| Indicador | Objetivo | Qué significa pasarse |
|---|---|---|
| Edad de la rama al mergear | **< 2 días** | Estás volviendo a ramas largas; parte el trabajo (§3) |
| Tiempo desde "listo" hasta mergeado | **< 4 horas** | El cuello de botella es la revisión, no el desarrollo |
| PRs por persona (o por TL) y día | **3-5** | Menos = PRs demasiado grandes. Mucho más = PRs sin contenido |
| Conflictos por semana | **< 5** | Se está rebasando poco, o dos frentes comparten ficheros (`parallelization.md`) |

**Cómo se miden, sin montar nada:**

```bash
# Edad de las ramas locales que no son el tronco
for b in $(git for-each-ref --format='%(refname:short)' refs/heads/ | grep -v -E '^(main|develop)$'); do
  base=$(git merge-base "$b" develop 2>/dev/null) || continue
  printf '%-40s %s\n' "$b" "$(git log -1 --format=%cr "$base")"
done

# PRs mergeados en los últimos 7 días (necesita gh)
gh pr list --state merged --limit 100 \
   --json number,mergedAt,additions,deletions --jq \
   '[.[] | select(.mergedAt > (now - 7*86400 | todate))] | length'
```

> **Límite honesto: esto es disciplina, no mecanismo.** Nada impide dejar una rama dos semanas
> abierta. No hay hook que lo bloquee ni lo va a haber: el tamaño correcto de un PR depende del
> criterio, y un gate que lo forzara produciría PRs troceados para engañar al contador. Lo que sí
> se puede automatizar —y va aparte— es **avisar** de las ramas que superan los 2 días.
>
> **Si solo vas a adoptar una cosa de esta rule, que sea el §1 (rebase 2×/día).** Los flags, el
> slice pattern y los targets suman sobre eso; sin rebase diario, no arreglan nada.

---

## Anti-patterns

- ❌ `git push --force` a secas → borra en silencio el trabajo de quien subió mientras rebasabas.
  Siempre `--force-with-lease`.
- ❌ Rebasar una rama compartida o el tronco → reescribe historia de otros; es acción de aprobación.
- ❌ Rebasar "cuando toque" en vez de 2×/día → el conflicto de tres líneas se convierte en el de
  trescientas, que es exactamente lo que esta rule existe para evitar.
- ❌ Rama de una semana "porque la feature es grande" → la feature grande se parte (§3); el tamaño
  de la feature no obliga al tamaño de la rama.
- ❌ Feature flag sin fecha de retirada ni dueño → código muerto permanente con dos caminos vivos.
- ❌ Más de ~3 flags vivos a la vez → la combinatoria deja de estar probada.
- ❌ Partir un PR por volumen de ficheros en vez de por capa → dos PRs que solo funcionan juntos, o
  sea, uno disfrazado de dos.
- ❌ Mergear un corte que deja el tronco roto "porque el siguiente PR lo arregla".
- ❌ Vídeo en **todos** los PRs → se ignoran todos, y el que importaba también.
- ❌ Commitear el `.webm`/`.mp4` en el árbol de código → el repo engorda para siempre.
- ❌ Publicar los targets de §5 como objetivo de rendimiento de una persona → se optimiza el número
  (PRs vacíos) y se pierde la señal.

---

_Rule version: 1.0 · EQ-1 + EQ-5, aprobados 2026-08-08. El rebase diario ya se mencionaba de pasada
en `parallelization.md` §file claims; aquí está el procedimiento, y allí sigue el reparto de
ficheros — no se duplica._
