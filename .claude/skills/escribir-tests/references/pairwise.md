# pairwise-test-data — cobertura combinatoria sin explosión de casos

> Referencia de la skill `escribir-tests` (§Combinatoria). Era la skill `pairwise-test-data`,
> fusionada el 2026-10-19 (LI-10, `_archive/2026-10-19/README.md` §Sub-ola 1.04). El script está al
> lado: `.claude/skills/escribir-tests/pairwise.py`.

## Principio

Con 5 variables de 3-4 valores cada una tienes cientos o miles de combinaciones: probarlas todas es
inviable y probar cuatro "a ojo" deja agujeros que nadie puede nombrar. **Pairwise (all-pairs)**
resuelve el punto medio: genera el conjunto mínimo de casos en el que **cada par de valores de cada
par de variables aparece al menos una vez**. La base empírica es que la gran mayoría de los defectos
combinatorios se disparan por la interacción de **dos** factores, no de cinco a la vez.

Lo importante para nosotros no es solo generar: es que la cobertura sea **verificable**. El script
de esta skill devuelve los casos **y** los pares sin cubrir (debe ser 0, y sale con exit≠0 si no).

## Cuándo activar

- Una feature depende de ≥3 variables independientes y alguien pregunta *"¿qué combinaciones
  probamos?"*.
- Matriz de compatibilidad: navegador × dispositivo × idioma × rol × plan.
- Feature flags: 6 flags booleanos son 64 combinaciones; pairwise las reduce a un puñado.
- Un endpoint con varios parámetros opcionales que se combinan entre sí.
- El punto 5 de la rúbrica de `code-review-gate` ("casos límite") pide combinatoria y no la hay.

**NO la actives** cuando: hay ≤2 variables (prueba el cartesiano entero, es barato); las variables
no interactúan entre sí (pruébalas por separado); o lo que buscas es romper la lógica de negocio
(eso es `marco-qa-breaker`).

## Procedimiento

### 1. Declara las variables y sus valores en JSON

Un valor por clase de equivalencia, no por dato. `edad: [17, 18, 65, 66]` (los bordes) en vez de
veinte edades. Los bordes exactos y los valores tóxicos (`null`, `""`, negativo) son **valores** más
de la variable — así entran en la combinatoria en vez de vivir en tests sueltos.

```json
{
  "navegador":  ["chrome", "firefox", "safari"],
  "rol":        ["admin", "editor", "lector"],
  "plan":       ["free", "pro"],
  "idioma":     ["es", "en"],
  "dispositivo": ["desktop", "movil"]
}
```

### 2. Genera y verifica

```bash
python3 .claude/skills/escribir-tests/pairwise.py variables.json
python3 .claude/skills/escribir-tests/pairwise.py variables.json --csv > casos.csv
# exit 0 = todos los pares cubiertos · exit 1 = faltan pares (no uses la salida)
```

Salida real del ejemplo de arriba (verificada al escribir esta skill):

```
  1  navegador=chrome   rol=lector  plan=free  idioma=es  dispositivo=desktop
  2  navegador=chrome   rol=editor  plan=pro   idioma=en  dispositivo=movil
  3  navegador=firefox  rol=admin   plan=pro   idioma=es  dispositivo=desktop
  4  navegador=safari   rol=admin   plan=free  idioma=en  dispositivo=movil
  5  navegador=firefox  rol=editor  plan=free  idioma=en  dispositivo=desktop
  6  navegador=safari   rol=lector  plan=pro   idioma=es  dispositivo=movil
  7  navegador=firefox  rol=lector  plan=free  idioma=en  dispositivo=movil
  8  navegador=safari   rol=editor  plan=free  idioma=es  dispositivo=desktop
  9  navegador=chrome   rol=admin   plan=free  idioma=es  dispositivo=desktop

# casos pairwise: 9  ·  producto cartesiano: 72  ·  pares sin cubrir: 0
```

Nueve casos en lugar de setenta y dos, y ni un par de valores sin visitar. Otro caso medido:
5 variables de 4 valores → **22 casos** frente a 1024 del cartesiano, 0 pares sin cubrir.

El generador es determinista (`seed=0`): dos ejecuciones dan el mismo conjunto, así que el diff de
tus tests no cambia sin motivo.

### 3. Vuélcalo a tests parametrizados

```python
# tests/test_permisos.py — un caso pairwise por fila
import csv, pytest

with open("tests/data/casos.csv") as f:
    CASOS = [tuple(r.values()) for r in csv.DictReader(f)]

@pytest.mark.parametrize("navegador,rol,plan,idioma,dispositivo", CASOS)
def test_panel_visible_segun_rol(navegador, rol, plan, idioma, dispositivo):
    ...
    assert visible is esperado, f"combinación {rol}/{plan}/{idioma} en {navegador}/{dispositivo}"
```

Versiona el CSV junto a los tests: es la evidencia de qué se cubrió y con qué criterio.

### 4. Restricciones (combinaciones imposibles)

Pairwise no sabe que *"safari + movil"* significa iOS, ni que *"rol=lector + plan=free"* no existe
en tu producto. Dos formas de tratarlo, en este orden:

1. **Filtra después de generar** y **vuelve a verificar**: si al quitar los casos inválidos quedan
   pares sin cubrir, el script lo dice y añades casos a mano para taparlos.
2. **Modela la restricción como variable**: en vez de `so` y `navegador` sueltos, una variable
   `plataforma: ["ios-safari", "android-chrome", "win-chrome", "win-firefox"]` que ya excluye lo
   imposible por construcción. Suele ser la solución más limpia.

```python
# 1) filtrar y re-verificar (nunca lo primero sin lo segundo)
from pairwise import verify
validos = [c for c in casos if not (c["plan"] == "free" and c["rol"] == "admin")]
faltan = verify(variables, validos)
assert not faltan, f"tras filtrar quedan {len(faltan)} pares sin cubrir: {sorted(faltan)[:5]}"
```

### 5. Añade a mano lo que pairwise no cubre por diseño

Pairwise garantiza **pares**, no tríos. Si sabes de una interacción de tres factores que ya te ha
mordido (o que el negocio considera crítica), **añádela como caso fijo** además del conjunto
generado, y documenta por qué está ahí.

## Anti-patterns

- ❌ Usar la salida sin mirar la línea de verificación (`pares sin cubrir` debe ser 0).
- ❌ Filtrar combinaciones inválidas y **no** re-verificar la cobertura → agujeros invisibles.
- ❌ Meter 30 valores por variable: pairwise no arregla una mala elección de clases de equivalencia,
  solo la combina. Primero reduce a bordes y representantes.
- ❌ Aplicarlo a variables que no interactúan → casos que no aportan información.
- ❌ Confundir "todos los pares cubiertos" con "sin bugs": los defectos de 3+ factores siguen ahí
  (por eso existe el paso 5).
- ❌ Pedirle al modelo que "genere combinaciones pairwise" a mano en el chat: la combinatoria es
  aritmética, y aquí un script la hace exacta, determinista y verificable.

## Ejemplos

### User: "hay que probar el panel con 3 navegadores, 3 roles, 2 planes, 2 idiomas y móvil/desktop, pero son demasiadas"
TL: escribe `variables.json`, corre `pairwise.py`, obtiene 9 casos con 0 pares sin cubrir, los
vuelca a `tests/data/casos.csv` y parametriza el test. Reporta: "9 casos cubren todos los pares
frente a los 72 del cartesiano".

### User: "tenemos 6 feature flags nuevos y no sabemos qué combinaciones testear"
TL: 6 variables booleanas (64 combinaciones). Genera el conjunto pairwise, verifica cobertura, y
**además** añade a mano el caso "todos ON" y "todos OFF" (los dos extremos que el negocio garantiza)
documentando que son fijos, no generados.

## Related

- `code-review-gate` — la rúbrica de 7 puntos exige casos límite y parametrización; esta skill los
  produce (puntos 3 y 5)
- `marco-qa-breaker` (agente) — **complementario, no solapado**: él ataca la lógica ya implementada
  (transiciones ilegales, race conditions, idempotencia, valores tóxicos); esta skill decide *qué
  combinaciones de entradas válidas* se prueban. Flujo natural: pairwise define la matriz → Marco
  intenta romper lo que quede fuera de ella
- `rules/verification.md` §Estabilidad E2E — si los casos se ejecutan como E2E, cada uno necesita datos únicos
- `escribir-tests` (`SKILL.md`, la skill que contiene esta referencia) — escribe los tests
  parametrizados a partir del CSV
