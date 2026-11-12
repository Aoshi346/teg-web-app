# Smoke: worktree — ¿el contenedor de una franja funciona de verdad?

> **Gate:** al adoptar worktrees en un proyecto (y tras tocar `settings.json`, `.worktreeinclude` o
> `.gitignore`). **Coste:** ~10 min, un subagente, sin pytest y sin navegador.
> **Contexto:** `rules/parallelization.md` §Aislar FICHEROS no es aislar DATOS (la franja: base y puerto
> propios por frente) · `rules/parallelization.md` §3 y, en el template, `claude-code-referencia` §4 (el
> mecanismo) · `rules/parallelization.md` §0, test de independencia (la pregunta: ¿hacen falta dos frentes?).

Un mecanismo que nadie ha probado no es un mecanismo. Este drill existe porque el modo de fallo real
no es «no sé el comando»: es que **el worktree nace sin el proyecto dentro y parece que funciona**.

**Por qué hace falta fabricar un testigo.** `.worktreeinclude` solo copia lo que además está
gitignorado. Si lista `.env` y `.env` **no existe**, no copia nada y el drill sale verde sin haber
probado nada. Y sin **control negativo** —un fichero gitignorado que NO está en la lista— no se
distingue «selecciona bien» de «copia todo lo ignorado».

---

## Procedimiento

### 0. Foto previa (es el criterio de cierre)
```bash
bash .claude/hooks/check-ram.sh --explain     # ¿cabe? si el tope es 1, el drill va solo
git worktree list ; git status --porcelain    # guarda esta salida: al final debe ser idéntica
python3 -c "import json;print(json.load(open('.claude/settings.json')).get('worktree'))"
```

### 1. Testigo + control negativo
```bash
TOK="drill-$(date +%s)-$RANDOM"
printf 'DRILL_TOKEN=%s\n' "$TOK" > .env                 # SÍ está en .worktreeinclude
printf 'CONTROL_NEGATIVO=%s\n' "$TOK" > drill-control.bak # gitignorado, NO está en la lista
git check-ignore -v .env drill-control.bak              # los dos deben casar, o ABORTA
git status --porcelain                                  # ninguno puede aparecer aquí
```

### 2. Lanzar el drill dentro de un worktree
Un subagente con `isolation: worktree` (o `claude --worktree drill-franja`) que **solo observe y
reporte**, sin arreglar nada. Las seis comprobaciones: dónde está · ¿llegó el testigo? · ¿llegó el
control negativo (no debe)? · ¿bloquea el aislamiento por las tres vías? · ¿de dónde nace la rama? ·
¿ve el proyecto?

### 3. Limpieza y gate
Borrar testigo y control. `git worktree list` y `git status --porcelain` **idénticos a la foto del
paso 0**. Esa identidad es la prueba, igual que el diff vacío prueba que un registro se partió bien.
⚠️ Retirar un worktree requiere aprobación (`governance.md` §2): **decláralo desechable al crearlo**,
no al borrarlo.

---

## Resultados — ejecución del 2026-09-12 (tech-lead-template, v2.1.269)

| # | Qué se probaba | Observado | ¿Esperado? |
|---|---|---|:--:|
| 1 | Se crea en la ruta nativa y no ensucia | `.claude/worktrees/agent-…`, rama propia, `locked`; principal limpio | ✅ |
| 2 | `.worktreeinclude` copia el testigo | `.env` presente, **35 B — mismo tamaño** que el original | ✅ |
| 3 | **Control negativo** | `drill-control.bak` **NO** está en el worktree | ✅ selecciona, no copia todo |
| 4a | Aislamiento — tool `Write` | **bloqueado**: *"This agent is isolated in the worktree … Edit the worktree copy"* | ✅ |
| 4b | Aislamiento — `echo x > /ruta/absoluta` | 🔴 **ESCRIBIÓ el fichero en el checkout principal** | ❌ |
| 4c | Aislamiento — `git -C <principal>` | **bloqueado**: *"…redirects git to the shared checkout via -C. Refusing to run it"* | ✅ |
| 5 | De dónde nace la rama | `HEAD` = `origin/main` = **Initial commit, 1 fichero**; `develop` **447 commits** por delante | 🔴 |
| 6 | ¿Ve el proyecto? | `git ls-files` = **1**. No hay `.claude/`, ni rules, ni código | 🔴 |

### Los dos hallazgos

**🔴 1 — El worktree nacía VACÍO.** No «447 commits por detrás»: **sin el proyecto**. `origin/HEAD`
apunta a `main`, y aquí `main` es un *Initial commit* de un solo fichero. Con el default
`baseRef: "fresh"` un subagente aislado no tenía nada con lo que trabajar. **Arreglado el 2026-09-12**
con `"worktree": { "baseRef": "head" }` en `settings.json` (aprobado por el Usuario).
→ **En cada proyecto derivado hay que comprobarlo**, no heredarlo por fe.

**🔴 2 — El aislamiento no es un sandbox.** Bloquea las tools de edición y la redirección de git;
**no** bloquea una escritura de Bash a ruta absoluta, ni la lectura del checkout principal. Es
coherente con la doc —el check de Bash es sobre el **cwd**, no sobre el destino— pero se lee como si
protegiera el filesystem. Escrito como límite honesto en `claude-code-referencia` §4.6 (antes en
`boris-worktrees` §6, retirada el 2026-10-20).

### Lo que este drill NO demuestra
- **No demuestra paralelismo real**: el tope de sesiones ese día era **1**.
- **No verificó el CONTENIDO del testigo**: el sistema de permisos denegó todo comando que nombrara
  `.env`. Se comprobó por tamaño (35 B ambos), que es consistente pero no es leerlo.
- No prueba `baseRef: "head"`: se configuró **después** del drill. **Pendiente de repetir.**
