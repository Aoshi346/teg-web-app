# G2 · Dependencias, SBOM y cadena de suministro

Plantilla de la sub-ola 2.23 de la revisión integral (items **SE-18**, **SE-34**, **SE-38**, **SE-60**). El gate es
`.claude/scripts/gate_deps.py`; aquí solo vive lo que se copia a un proyecto.

| Fichero | Va a | Para qué |
|---|---|---|
| `deps-gate.yml` | `.github/workflows/deps-gate.yml` | Corre G2 en cada PR, en cada push a `develop`/`main` y cada lunes (los CVE aparecen después de instalar). osv-scanner fijado por versión y SHA-256; las Actions, por SHA de commit; sube el SBOM CycloneDX como artefacto |
| `npmrc` | `.npmrc` (raíz del proyecto npm) | `ignore-scripts=true`: un postinstall de una dependencia no corre con tus credenciales. No hace falta con pnpm ≥ 10.26.0 |
| `deps-excepciones.json` | la carpeta `.claude/` del proyecto | Una vulnerabilidad aceptada: con razón escrita y fecha de caducidad. Caducada, vuelve a contar |

## Qué bloquea y qué avisa

| Código | Qué | Efecto |
|---|---|---|
| D1 | Vulnerabilidad de gravedad ≥ HIGH (CVSS 7,0) **con versión arreglada** | rojo (1) |
| D2 | Manifiesto con dependencias y sin lockfile | rojo (1) |
| D3 | El SBOM pedido sale vacío o no es CycloneDX | no medido (2) |
| D4 | Excepción sin razón, sin fecha o caducada | rojo (1) |
| S1 | `npx`/`uvx`/`bunx`/`pipx run`/`pnpm dlx` sin versión exacta, o `@latest` | aviso (`--estricto`: rojo) |
| S2 | Action sin SHA de 40 caracteres, o `uses: docker://` sin `@sha256:` (los `FROM` y `container:` no se miran) | rojo (1) |
| S3 | Se ejecutan los scripts de instalación de las dependencias npm | rojo (1) |
| S4 | `curl … \| sh` | aviso |

Salida **2** = no se pudo medir (sin motor, sin red, salida ilegible, un lockfile que el motor no leyó: p. ej. dentro de un `.gitignore`, que osv respeta aunque no haya repositorio). **No es un
verde**: en CI también para el job.

## Motor

`osv-scanner` v2 (el único que lee `poetry.lock`) o, sin él, `pip-audit` sobre `requirements*.txt`. Instalación sin
tocar el sistema:

```bash
python3 -m venv /ruta/v && /ruta/v/bin/pip install pip-audit                       # pip-audit en un venv
curl -fsSL -o osv-scanner https://github.com/google/osv-scanner/releases/download/v2.7.0/osv-scanner_linux_amd64
echo "160c6253e2922e9e0a6a9771c5c4c40a4b3c6090b34a3cdd5e80c96cc2e4218b  osv-scanner" | sha256sum -c -   # comprobado el 2026-10-21
chmod +x osv-scanner && python3 .claude/scripts/gate_deps.py . --osv ./osv-scanner
```

## Probar el gate (control negativo)

```bash
python3 .claude/scripts/gate_deps.py --autoprueba          # 99 casos sin red: cada sabotaje cae, cada control pasa
python3 .claude/scripts/gate_deps.py --autoprueba --vivo --osv ./osv-scanner   # +6 contra osv.dev real
```

La autoprueba planta una dependencia con CVE (en una salida de osv sintética y, con `--vivo`, jinja2 2.4.1 y
requests 2.19.0 reales), un `@latest`, una Action por etiqueta y un `ignore-scripts=false`, y exige que el gate caiga;
y los controles equivalentes limpios, que exigen que no.

## Lo que no mira

Los lockfiles, no lo instalado en el servidor ni lo que cargan los plugins de nivel usuario (`~/.claude/plugins`):
un plugin que lanza `@latest` desde su propio `.mcp.json` no se ve desde el repo. La gravedad es la que publica la
base; sin gravedad (y siempre con `pip-audit`) la decisión es `--bloquea-desconocida`. Un verde dice que lo conocido,
grave y con arreglo, no está; no certifica que no haya vulnerabilidades.
