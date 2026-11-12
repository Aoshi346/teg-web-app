# Agentes — índice de la flota y contrato de portabilidad del bundle visual

> **Este documento tiene dos partes.** La **§0** es el **índice de los agentes** que viven en
> `.claude/agents/` —qué hace cada uno, su `error_cost` y su `autonomy_phase`—, **generado** desde
> el frontmatter por `scripts/gen_agent_index.py`. De la **§1 en adelante** está el contrato de
> portabilidad del **bundle de audit visual** (Vera / Lidia / Ignacio + `shared/`), que es un
> sistema cohesivo y no tres agentes independientes: portarlo exige copiar todo el bundle.
>
> **Para quien esté leyendo esto desde techlead-template** (o cualquier otro mecanismo de
> generación/sincronización de agentes): lo portable en bloque es lo de §1-§10; el índice de §0
> describe la flota de ESTE repo y en un proyecto derivado tendrá menos filas.

---

## 0. Índice de la flota

> **Qué es esta sección y por qué está la primera.** El resto de este README documenta **el bundle
> portable de audit visual** (Vera / Lidia / Ignacio + `shared/`) y sus anexos. Hasta el 2026-08-22
> eso era todo lo que había: los demás agentes existían en disco y **no aparecían en ningún
> índice**, así que para saber si teníamos un auditor de accesibilidad o un ingeniero de retrieval
> había que hacer `ls`. Desde el 2026-10-20 la tabla de abajo **no se escribe a mano**: la regenera
> `python3 .claude/scripts/gen_agent_index.py` desde el frontmatter de cada `agents/*.md`, y
> `--check` sale 1 si un agente está en disco y no en la tabla, o al revés (escrita a mano llegó a
> nombrar 27 de 29 y a dar `—` a 15 agentes que ya declaraban su fase).

> ⚠️ **Cobertura DECLARADA ≠ cobertura REAL. Medido el 2026-08-27:** de los **29 agentes con ficha,
> solo 4 han dejado rastro en disco** — `ignacio`, `lidia`, `pol` y `vera`. Los otros 25 nunca han
> corrido, así que **no cuentan como cobertura**: existen, y eso es distinto de proteger de algo.
>
> ```bash
> # quién ha corrido de verdad (deja informes en .docs/)
> find .docs -path '*feedback*' -name 'REPORT.md' | grep -oE '(lidia|vera|ignacio|pol|rita|sofia|priya|quim|bruno|marco|nadia|aitor|lena|tomas|conrado|elena|rafa|ivan|dario|nora|sara|teo)' | sort | uniq -c
> ```
>
> Es el mismo hueco que `rules/qa-loop.md` §2b ya confiesa para los auditores del bucle visual, aquí
> medido sobre la flota entera. Un agente sale de esa lista **cuando corre y deja evidencia**, no
> cuando se le escribe una ficha mejor. Y antes de que su puntuación cuente para un gate, le toca el
> fixture de errores plantados de `rules/qa-loop.md` §4b, que mide su recall **y sus falsos
> positivos** — sin ese número, su tasa de ruido es literalmente desconocida.
>
> **Todos tienen ya su `memory.md`** (se completó el 2026-08-27: faltaba en `desarrollador-backend`,
> `especialista-seguridad` y `naive-user-tester`, retirados en la 3.01). `rules/agent-autonomy-ladder.md` §7 es explícito:
> *un agente sin memoria está en fase 1*, así que un agente declarado en fase 3 o 4 sin ella era una
> contradicción, no un detalle.

> ⚠️ **Las dos columnas de la derecha vienen del frontmatter, no del cuerpo.** Un agente puede
> tener su calibración escrita en prosa y no en el YAML: para el índice eso cuenta como **no
> declarado**, porque lo que no está en el frontmatter no se puede listar ni auditar. La razón de
> que hagan falta **los dos sitios** —frontmatter para inventariar, cuerpo para que el agente se
> calibre de verdad— está en `rules/agent-autonomy-ladder.md` §6.1.
>
> Y el default para un agente que no la declare (el 2026-10-20 la declaran todos; el recuento vivo
> está en la cabecera de la tabla): **si la fase no está escrita, se asume fase 3
> (sombra: reporta, no tiene efecto)** para agentes nuevos. Eso *no* degrada retroactivamente a los
> que ya operan con efecto —los del `/qa-loop` están de facto en fase 4—; se les anota la fase al
> tocarlos por otra razón, no en una migración masiva.

**Todos los `.md` de la carpeta son agentes.** Lo fueron desde el 2026-08-22: hasta entonces
`security-qa-bundle.md` vivía aquí sin `name:` en el frontmatter —o sea, sin que el harness lo
cargara nunca— y era documentación del par Sofía + Marco. Su contenido operativo ya estaba dentro de
las dos fichas (que es el único texto que recibe un subagente); lo que quedaba está en el anexo de
abajo. Archivado con la medición en `_archive/2026-08-22/`.

<!-- AGENT-INDEX:BEGIN — generado por .claude/scripts/gen_agent_index.py; no editar a mano -->

### La tabla (generada)

**12 agentes** en `.claude/agents/*.md` con `name:` en el frontmatter · **12** declaran `error_cost` y `autonomy_phase` · **0** no declaran alguno de los dos.

`ec` = `error_cost` · `fase` = `autonomy_phase` · `—` = no declarado en el frontmatter. «Qué hace» es la primera frase de la `description`, que es lo que lee el harness para decidir cuándo lanzar el agente.

| Agente | Familia | Qué hace | ec | fase |
|---|---|---|:--:|:--:|
| `aitor-a11y-auditor` | auditor-persona | auditor de accesibilidad WCAG 2.2 AA: contraste, teclado y foco, ARIA, target size, alternativa al arrastre, errores de formulario, encabezados | false-negative | 3 |
| `desarrollador-backend` | stack backend | Desarrollador backend senior en Django 5.2 LTS + DRF + PostgreSQL + Celery/Redis: modelos, serializers, ViewSets, migraciones, lógica de negocio y ORM | symmetric | 4 |
| `desarrollador-frontend` | stack frontend | Constructor de pantallas React con nueva-pantalla, disenar-pantalla y escribir-tests precargadas, en su worktree y con pattern_check_frontend.py al parar | symmetric | 2 |
| `ignacio-roig` | bundle visual | crítico visual adversarial: baseline 3.0, ≥10 hallazgos en 6 tipos (UGLY/AMATEUR/CLICKBAIT/INCONSISTENT/AI-SLOP/PLACEHOLDER), 8 tests y nota ≥1.0 bajo la de Vera | false-negative | 4 |
| `lector-web` | tipo de workflow | Lector en cuarentena de los workflows de research: busca y lee la web y el repo, sin escribir, ejecutar ni usar MCP | false-positive | 3 |
| `lidia-naive-tester` | bundle visual | tester no técnica con atención <2s: si no entiende rápido, se va. Tres modos: su persona, una persona pasada al lanzarla y primer uso (onboarding, empty states, time-to-value) | false-negative | 4 |
| `marco-qa-breaker` | bundle sec+QA | QA destructivo de la lógica de negocio, contra la API: estados ilegales, carreras en acciones únicas, idempotencia, límites, bordes temporales, estados zombi | false-negative | 3 |
| `pol-product-advisor` | producto | asesor de producto y requisitos: propone qué mejorar, añadir o quitar, por valor×esfuerzo, y revisa planes y diseños antes de ejecutarlos | symmetric | 4 |
| `priya-privacy-auditor` | cumplimiento | auditora de privacidad (RGPD) y trust-&-safety: base legal, derechos del interesado, PII en logs y embeddings, LLMs de terceros, LSSI y Lista Robinson | false-negative | 3 |
| `rita-pattern-keeper` | patrones | guardiana del patrón de código del proyecto: juzga los candidatos de `pattern-check.sh` con ≥2 precedentes del repo, en modo sombra y sin bloquear | false-positive | 3 |
| `sofia-pentester` | bundle sec+QA | pentester ética (OWASP Top 10, WSTG, API Security): IDOR, auth y sesión, subida de ficheros, webhooks, inyección, secrets | false-negative | 3 |
| `vera-art-director` | bundle visual | crítica visual experta (estándar Awwwards/SiteInspire): tipografía, tokens de color, jerarquía, micro-interacciones y design system | false-positive | 3 |

Regenerar: `python3 .claude/scripts/gen_agent_index.py` · comprobar: `--check` (exit 1 si un agente está en disco y no aquí, o al revés).

<!-- AGENT-INDEX:END -->

### Cómo se mantiene al día

Ya no hace falta comprobarlo a mano: `gen_agent_index.py --check` lista lo que está en disco y no en
el índice, y al revés, y falla también si un agente no tiene **familia** (la columna que no sale del
disco: `family:` en su frontmatter o la tabla `FAMILIAS` del script). Al crear un agente nuevo se
regenera en el mismo commit que el `.md`, igual que se le escriben su `error_cost` y su
`autonomy_phase`, que son parte del checklist de `rules/agent-autonomy-ladder.md` §7.

## 0b. Cuándo delegar y en qué orden

*Antes en el `AGENTS.md` de `.claude/`, retirado el 2026-10-20 (LI-32): era un segundo índice de agentes
escrito a mano. Lo que tenía de criterio está aquí; lo que tenía de inventario, en la tabla de §0.*

| Complejidad | Acción |
|-------------|--------|
| Tarea única, simple (<30 LOC) | Ejecución directa |
| Tarea compleja (>3 archivos) | Planificar con EnterPlanMode |
| Investigación / búsqueda amplia | `Explore` agent |
| Decisión arquitectónica | `Plan` agent |
| Tarea específica de dominio | El agente de la tabla de §0 cuya `description` casa con la tarea |

Cada agente de la tabla es su propio `subagent_type` (el harness los lista por su `name:`); no hace
falta lanzarlos como `general-purpose` con «actúa como…». Qué **capa** usar —subagente, workflow,
agent-teams o pizarra— lo decide `rules/layer-decision.md` §5, y si conviene repartir, el test de
independencia de `rules/parallelization.md` §0.

**Personalizar al instalar en un proyecto:** el stack de los agentes de backend, y los nombres y la
persona de los que la traen (`vera-art-director`, `lidia-naive-tester`, `ignacio-roig`, y los
`[PERSONALIZAR]` de `marco-qa-breaker` y `sofia-pentester`); el detalle del bundle visual, en §4.

**Flujo de trabajo recomendado** (las piezas que ya no son agentes van como skill o patrón):

```
Contenido/Copy → skill /escribir-copy (escribir) + conrado-cro-auditor (auditar)
      ↓
Diseño/UI → skill /disenar-pantalla (decidir la forma con el Usuario)
      ↓
Lógica/Forms/CRM → skill /integrar-crm (la integración con el tercero)
         (el patrón de formulario: patterns/stack/formularios.md
          la clave del tercero NUNCA en el bundle: patterns/stack/api-y-errores.md)
      ↓
Frontend → nueva-pantalla (skill)
         (el movimiento y su apagado: patterns/stack/accesibilidad.md)
      ↓
Backend → desarrollador-backend
         (el diseño de la API: patterns/stack/backend-vistas.md + skill django-orm)
         (queries lentas e índices: skill django-orm, optimization.md / advanced-queries.md)
      ↓
QA Pre-release (paralelo):
  - lidia-naive-tester → ¿una persona no-técnica lo entiende?
  - vera-art-director  → ¿está tier-1 visualmente?
  - ignacio-roig       → ¿qué hay de feo?
      ↓
Cross-check Vera/Ignacio (delta ≥1.0)
      ↓
DONE → screenshot evidencia + push
```

El diseño de endpoints (lo que hacía el retirado `arquitecto-apis`) vive en
`patterns/stack/backend-vistas.md` y `backend-serializers.md`, con comprobador; el CRUD, en la skill
`django-orm` (`references/crud.md`).

**En paralelo, sin pisarse:** `/escribir-copy` + `/seo-on-page` (copy y meta tags) ·
`disenar-pantalla` + `/escribir-copy` (la forma y los textos que van dentro) · la tríada
`lidia-naive-tester` + `vera-art-director` + `ignacio-roig`. **No en paralelo:** el formulario y su
integración con el CRM (uno depende del otro), diseño e implementación (se implementa lo aprobado),
y el esquema del backend con el frontend que lo consume.

---

## 1. Qué son estos 3 agentes

Sistema de audit visual de 3 agentes que trabajan complementariamente:

| Agente | Rol | Scoring |
|--------|-----|---------|
| **vera-art-director** | Art Director senior, evalúa ejecución visual técnica contra estándar Awwwards/SiteInspire | Numérico 0-10, baseline 5.0, 10 ejes |
| **lidia-naive-tester** | Usuaria no-técnica que llega desde Instagram Reel, atención <2s | Híbrido: 8 dimensiones numéricas + gate categórico (Claro/Algo Claro/Confuso/Muy Confuso) |
| **ignacio-roig** | Crítico adversarial ex-Creative Director de estudio boutique, busca fallos | Numérico 0-10, baseline 3.0, ≥1.0 debe estar por debajo de Vera. 8 tests adversariales + 6 categorías de findings |

**Cross-check**: si Vera da 8.0 e Ignacio 7.5 (delta < 1.0), Ignacio no fue
suficientemente adversarial. Si delta > 3.0, flag para revisión humana. Esto
previene el score inflation sistémico de LLMs.

---

## 2. Estructura portable

```
.claude/agents/
├── README.md                        ← este archivo
├── vera-art-director.md             ← agente 1 (definición)
├── vera-art-director/
│   └── memory.md                    ← historial cross-versión
├── lidia-naive-tester.md            ← agente 2 (definición)
├── lidia-naive-tester/
│   └── memory.md
├── ignacio-roig.md                  ← agente 3 (definición)
├── ignacio-roig/
│   └── memory.md
└── shared/                          ← UTILIDADES COMPARTIDAS (CRÍTICO)
    ├── README.md                    ← documenta el bundle
    ├── calibration-v2.md            ← fuente única de umbrales y protocolos
    ├── red-flags.sh                 ← grep patterns ejecutables (10 patterns)
    └── multi-modal-checklist.md     ← 8 checks Playwright obligatorios
```

**Al portar**: copia TODO este árbol preservando rutas relativas. Los 3 agentes
referencian `./shared/calibration-v2.md`, `./shared/red-flags.sh` y
`./shared/multi-modal-checklist.md` por ruta relativa.

---

## 3. Version contract

Cada agente declara en su frontmatter YAML:

```yaml
shared_utils_version: "2026-04-22.1"
```

**Regla**: si `shared/calibration-v2.md` cambia (nuevos umbrales, penalizaciones,
reglas), hay que:

1. Actualizar `calibration-v2.md` y bumpear su header (`_Last updated: ..._`)
2. Bumpear `shared_utils_version` en los 3 agentes `.md`
3. Bumpear `shared/README.md` con la nueva fecha
4. Agregar entrada en el changelog (sección 5 abajo)

Si un agente tiene `shared_utils_version` distinto al de `calibration-v2.md` →
**mismatch warning**. El agente puede seguir funcionando pero las reglas
pueden estar desactualizadas.

---

## 4. Integración con techlead-template

Si el techlead-template sincroniza agentes a proyectos nuevos:

### Pre-flight

```bash
# Verificar que el proyecto destino tiene la estructura base
test -d "$TARGET_PROJECT/.claude/agents" || mkdir -p "$TARGET_PROJECT/.claude/agents"
```

### Sincronización

```bash
# Copiar bundle completo
cp -r .claude/agents/README.md                      $TARGET_PROJECT/.claude/agents/
cp -r .claude/agents/vera-art-director.md           $TARGET_PROJECT/.claude/agents/
cp -r .claude/agents/vera-art-director/             $TARGET_PROJECT/.claude/agents/
cp -r .claude/agents/lidia-naive-tester.md          $TARGET_PROJECT/.claude/agents/
cp -r .claude/agents/lidia-naive-tester/            $TARGET_PROJECT/.claude/agents/
cp -r .claude/agents/ignacio-roig.md                $TARGET_PROJECT/.claude/agents/
cp -r .claude/agents/ignacio-roig/                  $TARGET_PROJECT/.claude/agents/
cp -r .claude/agents/shared/                        $TARGET_PROJECT/.claude/agents/

# Asegurar permisos ejecutables en red-flags.sh
chmod +x $TARGET_PROJECT/.claude/agents/shared/red-flags.sh
```

### Post-install

**Las memorias deben reiniciarse en proyecto nuevo** (no portar historial
cross-versión que sería inconsistente con el nuevo proyecto):

```bash
# Limpiar memorias históricas (mantener estructura pero vaciar versiones)
cat > $TARGET_PROJECT/.claude/agents/vera-art-director/memory.md << 'EOF'
# Vera Art Director — Memory (cross-version)

> Reiniciada al incorporar Vera al proyecto. Historial pre-existente no aplica.

## Versiones auditadas

| Versión | Fecha | Promedio | Gate | Link findings |
|---------|-------|----------|------|---------------|
| _(aún no ha habido ronda)_ | — | — | — | — |
EOF
```

(Análogo para lidia y ignacio.)

### Project-specific customization

Las memorias personales del proyecto (`vera-art-director/memory.md` etc.)
NO son portables — son historial del proyecto. Lo que SÍ es portable:

- Definiciones de agentes (`.md`)
- Persona (frozen, no cambiar)
- Rúbricas y umbrales (calibration-v2.md)
- Grep patterns (red-flags.sh)
- Multi-modal checklist

Lo que cada proyecto adapta:

- Colores/tokens del design system en `calibration-v2.md` (sección 3 penalties
  referencia los colores reales del proyecto)
- URLs target en memorias (sustituir por la URL del proyecto)
- Referencias específicas de sector / audiencia (cada proyecto tiene la suya)

---

## 5. Changelog

| Versión | Fecha | Cambio principal |
|---------|-------|------------------|
| `2026-04-22.1` | 2026-04-22 | Calibración v2 desde deep research (2374 líneas). Baselines Vera 5.0 / Ignacio 3.0. 26 penalizaciones numéricas. Nielsen adversarial. Reference comparison obligatoria >7.0. Multi-agent cross-check Ignacio ≥1.0 bajo Vera. Lidia híbrido: 8 dim + categorical gate |
| `2026-04-22.0` | 2026-04-22 | Versión inicial: R-A..R-G en Vera, L-A..L-H en Lidia, creación Ignacio con 6 categorías |

---

## 6. Source of truth

La calibración v2 deriva de deep research ejecutado 2026-04-22:

- **Documento**: `AI Design Audit Agent Calibration — Professional Visual Critique Methodology & Score Inflation Mitigation.md`
- **Tamaño**: 2374 líneas, 58 fuentes
- **Ubicación original**: SpecKit session de un proyecto cliente (research no incluido en el template — se mantiene como deuda externa)

Si quieres re-ejecutar la research para tu proyecto, redacta un prompt
específico de tu sector y déjalo en `.specify/sessions/[ID]/deep-research-prompt.md`.

Principales insights del research aplicados:

1. **LLM inflation bias**: partir scoring bajo (5.0 Vera, 3.0 Ignacio), no alto
2. **Blind evaluation**: ignorar "mejoras previas" en prompts
3. **Render verification**: computed styles > DOM inspection (detecta bugs
   como Tailwind JIT no generando opacity `/85`)
4. **Mandatory reference comparison**: Stripe/Linear/Vercel parity antes de >7.0
5. **26 numeric penalty categories**: typography, color, animation, shadow,
   CTA, spacing, AI-slop, rendering, template
6. **Adversarial framing**: Ignacio debe encontrar ≥10 findings + 8 tests
7. **Multi-agent cross-check**: delta obligatorio entre evaluadores
8. **Awwwards benchmark**: Design 40% + Usability 30% + Creativity 20% + Content 10%

---

## 7. Troubleshooting

### "El agente da scores altos igualmente"

Causa probable: el prompt que lanza el agente incluye "lista de cambios
recientes" o "mejoras implementadas". Esto sesga la evaluación.

**Fix**: eliminar contexto de iteraciones del prompt. Pasar solo URL +
audiencia + objetivos + constraints. Los agentes tienen blind evaluation
protocol pero solo funciona si el prompt lo respeta.

### "Ignacio y Vera dan scores similares"

Ignacio está siendo blando. Volver a ejecutar con recordatorio explícito:
"Tu score DEBE estar ≥1.0 bajo Vera. Si no lo está, re-evalúa aplicando
estrictamente los 8 tests adversariales."

### "red-flags.sh da error de permisos"

```bash
chmod +x .claude/agents/shared/red-flags.sh
```

### "Los agentes no encuentran shared/calibration-v2.md"

Verificar que la estructura de directorios está intacta:

```bash
ls -la .claude/agents/shared/
# Deben aparecer: README.md, calibration-v2.md, red-flags.sh, multi-modal-checklist.md
```

---

## 8. Versionado en el techlead-template

Si techlead-template mantiene múltiples versiones del bundle:

```
templates/
└── audit-agents-bundle/
    ├── v2026-04-22.1/              ← current
    │   ├── README.md
    │   ├── vera-art-director.md
    │   ├── lidia-naive-tester.md
    │   ├── ignacio-roig.md
    │   └── shared/
    └── v2026-04-22.0/              ← previous (keep for rollback)
        └── ...
```

Recomendación: mantener últimas 2 versiones para rollback.

---

## 9. Feedback al bundle

Si el uso en proyectos reales revela fallos de los agentes (ej: Vera infla
scores aun así, Ignacio no encuentra 10 findings, red-flags.sh tiene falsos
positivos), documentar en:

- El memory.md del agente en el proyecto afectado (fix local)
- Issue en techlead-template para fix global (si aplica a todos los proyectos)

Los fixes globales deben:
1. Actualizar `calibration-v2.md`
2. Bumpear versión en los 3 agentes
3. Añadir entrada en changelog
4. Distribuir a proyectos usando techlead-template

---

## 9b. Pol — asesor de producto (fuera del bundle de QA, convive con él)

`pol-product-advisor` (+ `pol-product-advisor/{memory.md,trend.json}`) NO es un auditor de calidad:
es **dirección de producto** — mejorar/añadir/quitar/gaps, valor×esfuerzo, anclado a personas.
Incluye modo pre-ejecución ("revisa este plan/diseño"). No usa la calibración numérica de
`shared/` (no puntúa ejes): su métrica es el address-rate de sus sugerencias por ronda.
Importado de proxera_boquera y generalizado (TPL-1 W2). Al instalarlo en un proyecto, rellenar
las "Notas de dominio" de su memory.md (personas reales + líneas rojas) — sin eso, es genérico.

## 10. Origen

Bundle promovido al `tech-lead-template` desde un proyecto piloto (2026-04-22).
La calibración v2 se forjó tras un fallo real: un audit dio 7.80/10 a una
web con bugs evidentes (navbar invisible al scroll, CTA clickbait, logo
amateur). De ahí los baselines bajos (5.0/3.0), los 8 tests adversariales
y la verificación de render computado.

---

_Este README es parte del bundle portable. Incluirlo siempre al sincronizar._

---

## Anexo: Lidia, persona al vuelo y multipersona

Además del bundle de 3 agentes calibrados (Vera / Lidia / Ignacio), el template incluye:

- **Lidia en modo persona al vuelo** — recibe la persona como input del prompt (en lugar de la fija). Hasta la 3.01 era un agente aparte, `naive-user-tester` (0 usos observados, EQ-30); su protocolo es `skills/naive-user-playthrough/references/dynamic-persona.md`, que Lidia precarga. Útil para proyectos con múltiples arquetipos de usuario.
- **`personas/`** — estructura para multipersona testing con memoria + trend acumulados por ronda. Cada persona vive en `personas/<slug>/` con `memory.md`, `trend.json` y `reports/round-N.md`. Ver `personas/README.md` para el patrón completo.

**Cuándo usar cuál:**

| Caso | Agente |
|------|--------|
| Una sola persona dominante en el proyecto (ej. peluquera, contable) | `lidia-naive-tester` con persona FIJA personalizada al instalar |
| Múltiples arquetipos (ej. SaaS B2B: CPO + dev + sales testers) | `lidia-naive-tester` en modo persona al vuelo + `personas/<slug>/` por cada uno |
| Persona ocasional one-shot | `lidia-naive-tester` en modo persona al vuelo, sin carpeta `personas/` (test efímero) |
| Onboarding, empty states, time-to-value | `lidia-naive-tester` en modo primer uso (era `tomas-onboarding-tester`, EQ-D21) |

Los modos conviven en el mismo proyecto: es el mismo agente.

---

## Anexo: Security + QA bundle (sofia-pentester + marco-qa-breaker)

Además del trío visual, el template incluye un **par adversarial de security + QA** que ataca el
backend (no la UI). Son dos agentes complementarios: mismo proyecto, dos ángulos.

| Agente | Qué es | Cuándo usarlo |
|--------|--------|---------------|
| **sofia-pentester** | Pentester ética (OSCP). Ataca seguridad: OWASP Top 10, WSTG, file upload, webhook spoofing, IDOR, injection, secrets. NO arregla — demuestra con PoC. | Gate pre-merge de waves de auth/pagos/ficheros/datos sensibles: "pentest", "OWASP", "hackea esto" |
| **marco-qa-breaker** | QA destructivo de lógica de negocio: transiciones ilegales, race conditions, idempotencia, límites, lógica temporal. NO arregla — reproduce. | Gate pre-merge de waves con máquina de estado / acciones únicas / pagos: "rompe el sistema", "edge cases" |

Se diferencian de la revisión defensiva del diff (`code-review-gate` §Seguridad Django/DRF; era el agente `especialista-seguridad` hasta la 3.01) en que Sofia
y Marco son **adversariales y dinámicos** (atacan la app corriendo, sin `Edit`).

Siguen la **misma convención que el trío** Vera/Lidia/Ignacio: carpeta `<agente>/` con `memory.md`
+ `trend.json`, session dir en `.docs/feedback/<agente>/<timestamp>/`, frontmatter
`shared_utils_version`. Añaden además tres piezas de protocolo: **production-scope guard**,
**finding-closure state machine** y **cross-referencia** entre ambos vía el campo `related` en
`findings.json`.

### El protocolo compartido vive DENTRO de cada ficha, no al lado

Las tres piezas están escritas enteras en `sofia-pentester.md` y en `marco-qa-breaker.md`, como una
sección `##` cada una. **Es duplicación a propósito:** un subagente solo recibe el cuerpo de su
propio fichero, así que un protocolo guardado aparte —por muy enlazado que esté— es advisory y puede
no llegarle nunca. Aquí eso no es un matiz de estilo: la pieza que no puede fallar es el
production-scope guard, y lo que cuesta que se lo salte es atacar producción.

Eso deja el problema del otro lado: **dos copias que se pueden separar sin que nadie se entere.**
Por eso el guard no se vigila con una advertencia escrita sino con un comprobador —el bloque va
entre marcadores `<!-- SHARED:BEGIN security-qa-guard -->` / `<!-- SHARED:END -->` en las dos
fichas, y son byte a byte iguales:

```bash
python3 .claude/scripts/check_shared_block.py    # exit 1 si el guard diverge entre Sofía y Marco
```

Si cambias el guard, cámbialo en las dos y sube `shared_utils_version` en los dos frontmatter. El
comprobador caza la primera mitad de ese olvido; la segunda sigue siendo disciplina.

Personalización (el `[Nombre]`, el dominio de producción a vetar, la máquina de estados del
proyecto): `sofia-pentester/_EXAMPLE-PERSONALIZATION.md` +
`marco-qa-breaker/_EXAMPLE-PERSONALIZATION.md`. Para **llevarlos a otro proyecto** no hay checklist
propia: es el trabajo genérico de `update-agent` / `scripts/template_diff.py`, que ya copia
`agents/<x>.md` + su carpeta y **preserva** `memory.md`/`trend.json` del destino.

---

## Anexo: Auditores-persona (research-aware)

8 auditores-persona adicionales que cubren huecos que los anteriores NO cubren. Misma familia y
convención (carpeta `<agente>/` con `memory.md` + `trend.json`, `shared_utils_version`, frontmatter
`name/description/tools/model`, **NO arreglan** — detectan, puntúan y reportan). Dos rasgos propios:

- **Research-aware**: todos llevan `WebSearch` + `WebFetch` en `tools` y una sección "Mantenerse
  actualizado" — antes de auditar refrescan su estándar (su umbral puede haber cambiado) y citan la
  fuente. Para decisiones que cruzan fuentes pueden proponer `/deep-research`. Los umbrales numéricos
  de sus rúbricas son **"verify before fixing"**.
- **Verificación**: los auditores de UI usan el **MCP de Playwright**
  (`mcp__playwright__browser_navigate` / `browser_take_screenshot` / `browser_snapshot`) con fallback
  a `.claude/scripts/screenshot.py`; los de backend conducen API/curl o la vector DB vía Bash.
- **Output multi-ronda**: escriben en `.docs/feedback/<persona>/iter-<N>/` (REPORT.md + findings.json
  + screenshots), actualizan `<persona>/trend.json` y el `RESULT.md` del plan. Cada re-run = un
  `iter-N` nuevo (ver `.docs/plans/.../STRUCTURE.md` regla 9).

| Agente | Persona | Foco | Verificación |
|--------|---------|------|--------------|
| `aitor-a11y-auditor` | **Aitor** | Accesibilidad WCAG 2.2 AA (contraste, teclado, ARIA, target ≥24px) | Playwright MCP (a11y tree) + axe |
| `nadia-chatbot-evaluator` | **Nadia** | Calidad conversacional de chatbots (resolution/hallucination, tono, coste) | API/curl + golden set |
| `conrado-cro-auditor` | **Conrado** | CRO/conversión (7 Levels de Morys, LIFT, Hormozi/Cialdini) | Playwright MCP (above-the-fold + funnel) |
| `priya-privacy-auditor` | **Priya** | Privacidad/GDPR & trust-&-safety (derechos, PII en embeddings, consentimiento) | Código (Grep) + Playwright MCP + vector DB |
| `bruno-perf-cop` | **Bruno** | Rendimiento y operabilidad: web (CWV, budgets, Lighthouse), bot (p95, coste por turno, traza completa) y reposo (gasto con cero usuarios) | Bash (Lighthouse, trazas, `pg_stat_activity`) + Playwright MCP (CWV runtime) |
| `lena-i18n-auditor` | **Lena** | i18n/localización & brand voice (strings hardcoded, locale, tono) | Código (Grep) + Playwright MCP (por idioma) |

Las personas están **fijadas** (Aitor, Nadia, …); Tomás y Quim se retiraron en la 3.01 (modo primer uso de Lidia; integridad del índice, de Rafa); lo PROJECT-specific (persona objetivo, URL, golden
set, locales) queda como `[PERSONALIZAR: ...]` en cada `.md` y `memory.md`. Cierran como gate
pre-merge de su dominio: un CRITICAL/HIGH abierto bloquea el merge de su wave.
