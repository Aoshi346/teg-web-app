---
paths:
  - ".claude/settings.json"
  - ".claude/settings.local.json"
  - ".claude/commands/**"
  - ".claude/hooks/**"
  - ".claude/skills/**"
  - "CLAUDE.md"
  - ".claude/CLAUDE.md"
  - "documentation/settings-examples/**"
  - ".claude/scripts/settings_profile.py"
  - ".claude/templates/adoption-playbook.md"
  - "**/managed-settings*.json"
---
# Las 5 capas por ROL HUMANO — quién construye y quién solo usa

> **Cuándo aplicar:** al montar o tocar la configuración para personas que **no programan**
> (marketing, ventas, operaciones): permisos de un rol no técnico, un comando nuevo para ellos, o
> decidir quién edita `CLAUDE.md`, skills, hooks o lo programado. Era `governance.md` §6; vive aquí
> bajo `paths:` porque solo importa cuando se toca esa configuración.
>
> **NO aplicar:** para repartir autonomía **entre agentes** (eso es `governance.md` §2-§3) ni para
> promocionar agentes (`agent-autonomy-ladder.md`).

`governance.md` reparte autonomía **entre agentes**. Esta rule reparte responsabilidad **entre personas**: en una instalación con varios departamentos (marketing, ventas, operaciones) hay que dejar escrito quién construye la configuración y quién solo la consume. Sin esto, termina alguien de marketing editando `settings.json`.

| Capa | Qué es | Quién la toca | Quién NO |
|---|---|---|---|
| **1 · `CLAUDE.md`** | Contexto de toda la organización: qué hacemos, tono de marca, líneas rojas | El rol técnico (CTO / dueño del harness), con **input** de negocio | Nadie más lo edita. Además, una edición a mitad de sesión no se aplica hasta `/clear`, `/compact` o reiniciar (`harness-gotchas.md` §Caché) |
| **2 · Skills** | El know-how empaquetado (`.claude/skills/`) — cómo se hace bien cada cosa | El rol técnico. Cada skill necesita **owner**: los skills son código y se pudren sin dueño | El rol no técnico |
| **3 · Slash commands** | `.claude/commands/` — **la ÚNICA capa que toca el rol no técnico**: escribe `/comando <argumento>` y obtiene resultado | Los construye el rol técnico; **los ejecuta cualquiera** | — |
| **4 · Hooks** | `.claude/hooks/` + `settings.json` — el enforcement determinista (RAM, formato, permisos) | **Solo** el rol técnico. Tocar `settings.json` requiere además aprobación explícita (`governance.md` §2) | Todos los demás |
| **5 · Programado / headless** | Cron, `claude -p … --max-turns N`, agentes en background, informes recurrentes | **Solo** el rol técnico (gasta dinero sin nadie mirando) | Todos los demás |

**La frase que resume el reparto** (fuente: *"5 Marketing Workflows con Claude Code"*, Rezvani 2026): *"El CTO construye la infraestructura […] El equipo de marketing corre los workflows. Tipean `/competitor-report` y obtienen resultados. **NO abren archivos de configuración. NO escriben prompts. Corren comandos.**"*

Consecuencias prácticas:

1. **Si un rol no técnico necesita algo nuevo, el entregable es un comando**, no un instructivo para editar ficheros. Si te encuentras explicando dónde está `settings.json`, el diseño falló.
2. **Permisos al revés para roles no técnicos**: el default de dev es *allow amplio, deny estrecho*; para un rol no técnico se empieza **denegando todo** y se abre solo el directorio de su trabajo. Ver `rules/security.md` y `documentation/settings-examples/`.
3. **La capa 3 es la superficie de contrato**: si cambias lo que hace un comando, cambias el trabajo de otra persona — avísalo como cambio de interfaz, no como refactor interno.
4. **Esto no sustituye a `governance.md` §2**: un comando ejecutado por un rol no técnico sigue estando sujeto a los approval gates (no puede deployar por el hecho de estar en la capa 3).

## Anti-patterns

- ❌ Pedirle a un rol no técnico que edite un fichero de configuración → si hace falta, es que falta un comando

---

_Rule version: 1.0 · 2026-10-28 — sale de `governance.md` §6 (v1.1, ND-4) a una rule con `paths:` (MO-46)._
