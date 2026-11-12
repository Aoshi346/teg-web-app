#!/usr/bin/env python3
"""pattern_check_backend.py — la capa determinista del patrón de casa (backend).

Ejecuta las reglas de `.claude/patterns/stack/backend-*.md` sobre los ficheros CAMBIADOS.
0 tokens, sin dependencias fuera de la stdlib. Es el Tier 0 de Rita para el stack Django:
lo que salga de aquí son los CANDIDATOS que ella juzga (nunca busca ella — regla R-1).

    python3 .claude/patterns/stack/pattern_check_backend.py            # ficheros cambiados
    python3 .claude/patterns/stack/pattern_check_backend.py --all      # repo entero (inventario)
    python3 .claude/patterns/stack/pattern_check_backend.py ruta/a/app # rutas concretas
    python3 .claude/patterns/stack/pattern_check_backend.py --list     # tabla de reglas
    python3 .claude/patterns/stack/pattern_check_backend.py --json     # salida para otro agente
    python3 .claude/patterns/stack/pattern_check_backend.py --self-test  # FPR sobre _fixtures/

Política (idéntica a `.claude/hooks/pattern-check.sh`):
    activo  → violación nueva = exit 1
    debil   → avisa, nunca bloquea
    sombra  → solo mide (no se imprime salvo --all/--json)
    excepción → `# pattern-exempt: <id> — razón` en la línea, la anterior, o en cualquier
                parte del fichero. Se respeta SIEMPRE (auditable, permanente).
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import re
import subprocess
import sys
import warnings
from dataclasses import dataclass, field
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
# Registro de reglas — el enunciado corto vive aquí; el porqué, en el .md
# ─────────────────────────────────────────────────────────────────────────────

RULES: dict[str, dict] = {
    # -- servicios (capa 4) --------------------------------------------------
    "be-svc-sin-drf": dict(estado="activo", capa="servicios", doc="backend-servicios.md",
        enunciado="La capa de servicio no importa DRF/HTTP ni recibe `request`: la lógica se llama desde un test, una task o un comando"),
    "be-svc-escritura-en-vista": dict(estado="activo", capa="vistas", doc="backend-servicios.md",
        enunciado="Las vistas no escriben en la BD: delegan en un servicio (salvo serializer.save y hooks perform_* triviales)"),
    # -- modelos (capa 1) ----------------------------------------------------
    "be-model-checkconstraint-condition": dict(estado="activo", capa="modelos", doc="backend-modelos.md",
        enunciado="CheckConstraint usa `condition=` — `check=` está DEPRECADO desde Django 5.1 y se retira en 6.0"),
    "be-model-related-name": dict(estado="activo", capa="modelos", doc="backend-modelos.md",
        enunciado="Toda FK/O2O/M2M declara related_name explícito"),
    "be-model-null-en-texto": dict(estado="activo", capa="modelos", doc="backend-modelos.md",
        enunciado="Campos de texto no usan null=True (dos estados vacíos); excepción documentada: unique=True"),
    "be-model-dinero-float": dict(estado="activo", capa="modelos", doc="backend-modelos.md",
        enunciado="El dinero nunca es FloatField — DecimalField con max_digits/decimal_places"),
    "be-model-floatfield-max-length": dict(estado="activo", capa="modelos", doc="backend-modelos.md",
        enunciado="FloatField no tiene max_length: que esté ahí prueba que nadie revisó esa declaración"),
    "be-migracion-reversible": dict(estado="activo", capa="modelos", doc="backend-modelos.md",
        enunciado="RunPython declara siempre la función inversa (o RunPython.noop explícito)"),
    "be-model-bulk-create-invariante": dict(estado="activo", capa="modelos", doc="backend-modelos.md",
        enunciado="bulk_create() no llama a save(): prohibido sobre un modelo cuyo save() calcula invariantes"),
    "be-model-base-de-casa": dict(estado="debil", capa="modelos", doc="backend-modelos.md",
        enunciado="Si el proyecto tiene un modelo base abstracto compartido (auditoría/dueño), los modelos de app heredan de él"),
    "be-model-meta-base-de-casa": dict(estado="activo", capa="modelos", doc="backend-modelos.md",
        enunciado="Si el proyecto tiene una base de `Meta` compartida, todo `class Meta` la hereda (si no, pierde sus permisos en silencio)"),
    "be-model-caducidad-no-comprobada": dict(estado="debil", capa="modelos", doc="backend-modelos.md",
        enunciado="Un campo de caducidad que no lee nadie es una promesa falsa: quien lo configura cree que protege"),
    # -- serializers (capa 2) ------------------------------------------------
    "be-ser-fields-all": dict(estado="activo", capa="serializers", doc="backend-serializers.md",
        enunciado="Serializers declaran fields explícito, nunca '__all__'"),
    "be-ser-campo-servidor-escribible": dict(estado="activo", capa="serializers", doc="backend-serializers.md",
        enunciado="Campos que decide el servidor (user/owner/created_by/tenant) van en read_only_fields"),
    "be-ser-sin-efectos": dict(estado="activo", capa="serializers", doc="backend-serializers.md",
        enunciado="Los serializers validan y transforman: no lanzan tasks, correos ni llamadas HTTP"),
    # -- formularios Django (capa 2b — arquetipo server-rendered) -------------
    "be-form-fields-enumerado": dict(estado="activo", capa="formularios", doc="backend-formularios-django.md",
        enunciado="Meta.fields enumerado en un ModelForm: nunca '__all__' ni exclude (un campo nuevo no se vuelve editable solo)"),
    "be-form-base-de-casa": dict(estado="activo", capa="formularios", doc="backend-formularios-django.md",
        enunciado="Si el proyecto tiene un ModelForm base compartido, los formularios de app heredan de él y no de django.forms directamente"),
    "be-form-request-primero": dict(estado="activo", capa="formularios", doc="backend-formularios-django.md",
        enunciado="Una base cuya firma empieza por `request` no se instancia con los datos en primera posición: el formulario queda unbound y is_valid() es False sin error"),
    "be-form-clase-fuera-de-forms": dict(estado="debil", capa="formularios", doc="backend-formularios-django.md",
        enunciado="Una clase *Form vive en forms.py — fuera de él nadie la encuentra y se duplica"),
    # -- vistas (capa 3) -----------------------------------------------------
    "be-view-queryset-sin-filtrar": dict(estado="debil", capa="vistas", doc="backend-vistas.md",
        enunciado="ViewSet con queryset=...objects.all() y sin get_queryset() expone todas las filas"),
    "be-view-permisos-por-defecto": dict(estado="activo", capa="vistas", doc="backend-vistas.md",
        enunciado="settings define DEFAULT_PERMISSION_CLASSES; AllowAny explícito exige razón escrita"),
    "be-view-paginacion": dict(estado="activo", capa="vistas", doc="backend-vistas.md",
        enunciado="settings define DEFAULT_PAGINATION_CLASS + PAGE_SIZE (una lista sin paginar tumba el proceso)"),
    "be-api-exception-handler": dict(estado="activo", capa="vistas", doc="backend-vistas.md",
        enunciado="settings define EXCEPTION_HANDLER: una sola forma de error 400 {\"errors\": {campo: [msg]}} — contrato con el frontend"),
    "be-view-error-sin-excepcion": dict(estado="activo", capa="vistas", doc="backend-vistas.md",
        enunciado="Un error se LANZA (raise ValidationError), no se devuelve: `return Response(..., status=4xx)` esquiva el EXCEPTION_HANDLER y rompe el contrato"),
    "be-view-base-de-casa": dict(estado="debil", capa="vistas", doc="backend-vistas.md",
        enunciado="Si el proyecto tiene una vista base con el filtrado por dueño, las vistas de app heredan de ella y no de DRF directamente"),
    # -- contrato HTTP (rules/api-http-contract.md) ---------------------------
    "be-api-secreto-en-query": dict(estado="sombra", capa="vistas", doc="../../rules/api-http-contract.md",
        enunciado="Una credencial o un identificador fuerte no se lee de la query: la URL se escribe entera en el log de acceso, el historial y el Referer"),
    "be-view-action-multiverbo": dict(estado="sombra", capa="vistas", doc="../../rules/api-http-contract.md",
        enunciado="Un @action no mezcla un verbo de lectura con uno de escritura: son dos intenciones y por tanto dos endpoints"),
    # -- celery (capa 5) -----------------------------------------------------
    "be-celery-delay-en-transaccion": dict(estado="activo", capa="celery", doc="backend-celery.md",
        enunciado="No se encola dentro de transaction.atomic() sin on_commit: el worker corre antes del COMMIT"),
    "be-celery-serializer-json": dict(estado="activo", capa="celery", doc="backend-celery.md",
        enunciado="task_serializer='json' + accept_content=['json']: hace imposible pasar objetos y cierra el RCE de pickle"),
    "be-celery-timeouts": dict(estado="activo", capa="celery", doc="backend-celery.md",
        enunciado="settings define task_soft_time_limit y task_time_limit (sin ellos una task cuelga un worker para siempre)"),
    "be-celery-retry-io": dict(estado="activo", capa="celery", doc="backend-celery.md",
        enunciado="Task que hace I/O de red declara autoretry_for + retry_backoff"),
    "be-celery-ackslate-idempotente": dict(estado="debil", capa="celery", doc="backend-celery.md",
        enunciado="Task con acks_late=True exige un test de idempotencia que la nombre"),
    "be-http-timeout": dict(estado="activo", capa="celery", doc="backend-celery.md",
        enunciado="Toda llamada HTTP saliente lleva timeout=: sin él, una conexión colgada aparca el worker para siempre"),
    # -- cache redis (capa 6) ------------------------------------------------
    "be-cache-ttl-infinito": dict(estado="activo", capa="cache", doc="backend-cache-redis.md",
        enunciado="cache.set(..., timeout=None) guarda para siempre: TTL explícito o razón escrita"),
    "be-cache-key-prefix": dict(estado="activo", capa="cache", doc="backend-cache-redis.md",
        enunciado="CACHES define KEY_PREFIX (varios proyectos comparten Redis y las claves colisionan)"),
    "be-cache-key-helper": dict(estado="debil", capa="cache", doc="backend-cache-redis.md",
        enunciado="La clave de caché se construye en un helper, no con una f-string suelta en el punto de uso"),
    "be-cache-sin-invalidacion": dict(estado="sombra", capa="cache", doc="backend-cache-redis.md",
        enunciado="Helper de clave usado en cache.set y nunca en cache.delete: nadie sabe invalidarlo"),
    # -- rabbitmq (capa 7) ---------------------------------------------------
    "be-mq-dlx": dict(estado="debil", capa="rabbitmq", doc="backend-mensajeria-rabbitmq.md",
        enunciado="Toda Queue declarada a mano lleva x-dead-letter-exchange Y x-delivery-limit (sin los dos, el mensaje venenoso gira eternamente o se borra en silencio)"),
    # -- docker / entorno (capa 8) -------------------------------------------
    "be-env-secreto-literal": dict(estado="activo", capa="docker-env", doc="backend-docker-env.md",
        enunciado="Ningún secreto literal en compose/settings: siempre ${VAR} o env(...)"),
    "be-env-documentado": dict(estado="activo", capa="docker-env", doc="backend-docker-env.md",
        enunciado="Toda variable que settings lee está documentada en .env.example"),
    "be-compose-healthcheck": dict(estado="debil", capa="docker-env", doc="backend-docker-env.md",
        enunciado="depends_on usa condition: service_healthy (si no, Django arranca antes que Postgres)"),
    "be-compose-tag-latest": dict(estado="activo", capa="docker-env", doc="backend-docker-env.md",
        enunciado="Las imágenes se fijan a una versión: nunca :latest ni tag ausente"),
    # -- señales (capa 2c — el arquetipo server-rendered las usa como control de flujo) --------
    "be-sig-efecto-sin-on-commit": dict(estado="activo", capa="signals", doc="backend-signals.md",
        enunciado="Un receiver corre DENTRO de la transacción de quien guardó: todo efecto hacia fuera va en transaction.on_commit()"),
    "be-sig-logica-de-negocio": dict(estado="debil", capa="signals", doc="backend-signals.md",
        enunciado="En signals.py solo hay receivers: una función de negocio definida ahí es inalcanzable fuera del post_save"),
    # -- estructura del proyecto (capa 0) ------------------------------------
    "be-tpl-ruta-duplicada": dict(estado="activo", capa="estructura", doc="backend-estructura-apps.md",
        enunciado="Dos apps no sirven la misma ruta de plantilla: gana la primera de INSTALLED_APPS y la otra no se renderiza JAMÁS"),
    "be-capa-compartida-importa-dominio": dict(estado="sombra", capa="estructura", doc="backend-estructura-apps.md",
        enunciado="Una app de la capa compartida no importa una app de dominio a nivel de módulo (mide el enredo; no bloquea)"),
    "be-script-sin-runner": dict(estado="debil", capa="estructura", doc="backend-estructura-apps.md",
        enunciado="Todo fichero suelto que toque el ORM declara cómo se ejecuta (comando, django.setup() o cabecera `# runner:`)"),
    "be-py-monkeypatch-django": dict(estado="debil", capa="estructura", doc="backend-estructura-apps.md",
        enunciado="No se asignan atributos a clases de django.* a nivel de módulo: el efecto es global y depende del orden de import"),
    "be-no-mongo": dict(estado="debil", capa="estructura", doc="backend-estructura-apps.md",
        enunciado="El stack canónico es PostgreSQL puro: pymongo/bson/djongo fuera (los campos JSON ya cubren ese caso)"),
    "be-techo-lineas": dict(estado="sombra", capa="estructura", doc="backend-estructura-apps.md",
        enunciado="Un módulo de dominio cabe en la cabeza de alguien: por encima del techo nadie lo tiene entero y los bugs se esconden dentro"),
    # -- validación fuera del formulario (capa 2d) ---------------------------
    "be-val-escritura-sin-full-clean": dict(estado="debil", capa="validacion", doc="backend-validacion.md",
        enunciado="Un comando de gestión que escribe llama a full_clean(): es una puerta sin la validación del formulario"),
    "be-model-choices-sin-constraint": dict(estado="sombra", capa="validacion", doc="backend-validacion.md",
        enunciado="Un campo con choices= sin CheckConstraint solo lo valida el formulario: create/update/import escriben lo que quieran"),
    "be-owner-create-sin-dueno": dict(estado="debil", capa="validacion", doc="backend-validacion.md",
        enunciado="Un create() fuera del formulario asigna owner= explícito: sin dueño la fila existe y es invisible"),
    # -- tests (capa 9) ------------------------------------------------------
    "be-test-stub-vacio": dict(estado="activo", capa="tests", doc="backend-tests.md",
        enunciado="Ningún tests.py vacío de `startapp`: cuenta como app testeada en cualquier informe y no prueba nada"),
    "be-test-descubrible": dict(estado="activo", capa="tests", doc="backend-tests.md",
        enunciado="Un fichero con `def test_` que el descubridor no encuentra es un test que no se ejecuta nunca"),
    "be-test-db-alias-sin-engine": dict(estado="activo", capa="tests", doc="backend-tests.md",
        enunciado="Todo alias de DATABASES declara ENGINE: sin él, `manage.py test` no puede crear su base y la suite ni arranca"),
    # -- observabilidad (capa 10) --------------------------------------------
    "be-obs-logging": dict(estado="activo", capa="observabilidad", doc="backend-observabilidad.md",
        enunciado="settings define LOGGING: sin él, el fallo de las 4 de la mañana no deja rastro en ningún sitio"),
    "be-obs-healthcheck": dict(estado="debil", capa="observabilidad", doc="backend-observabilidad.md",
        enunciado="El proyecto expone un endpoint de salud: sin él nadie sabe si el proceso está vivo salvo mirándolo"),
}

BLOCKING = {"activo"}
QUIET = {"sombra"}


@dataclass
class Finding:
    rule: str
    path: str
    line: int
    msg: str
    fix: str = ""

    @property
    def estado(self) -> str:
        return RULES[self.rule]["estado"]

    def render(self) -> str:
        mark = {"activo": "✗ [ACTIVO]", "debil": "⚠ [débil]", "sombra": "· [sombra]"}[self.estado]
        out = f"{mark} {self.path}:{self.line} — {self.msg} ({self.rule})"
        if self.fix:
            out += f"\n   fix: {self.fix}"
        return out


@dataclass
class Ctx:
    """Estado compartido entre reglas (cross-file: settings, .env.example, tests)."""
    root: Path
    findings: list[Finding] = field(default_factory=list)
    settings_src: str = ""
    settings_path: str = ""
    env_example_keys: set[str] = field(default_factory=set)
    env_example_found: bool = False
    tests_src: str = ""
    # ¿el proyecto usa DRF? Las reglas de settings de DRF NO se le exigen a un backend
    # Django server-rendered: allí no hay REST_FRAMEWORK que configurar (EVO-4).
    uses_drf: bool = False
    # Bases de formulario compartidas del proyecto: {nombre_de_clase: fichero donde se define}.
    # Se descubren, no se declaran: en un proyecto nuevo todavía no existe ninguna.
    form_bases: dict[str, str] = field(default_factory=dict)
    form_classes: dict[str, list[str]] = field(default_factory=dict)
    # Formularios que consume un framework CRUD declarativo vía `form = <Clase>`. Su `Meta.fields`
    # NO es la lista blanca efectiva: el controlador subclasea el form en runtime y la sobrescribe
    # con los `fieldsets` de su `*Settings`. Medido en el backend de referencia: 353 de 359 forms
    # declaran `fields = []` (VACÍA) justo por eso. Ver patterns/stack/backend-controllers.md.
    forms_de_controller: set[str] = field(default_factory=set)
    form_family: set[str] = field(default_factory=set)
    form_base_request_first: bool = False
    cache_set_helpers: dict[str, tuple[str, int]] = field(default_factory=dict)
    cache_del_helpers: set[str] = field(default_factory=set)
    # Directorios que parecen una app Django (tienen apps.py o models.py). Se descubren; es lo
    # que permite hablar de "dos APPS con la misma plantilla" sin presuponer layout (EVO-4).
    app_dirs: set[str] = field(default_factory=set)
    shared_apps: set[str] = field(default_factory=set)
    # ruta de plantilla relativa a templates/ → [(app, fichero)]
    templates: dict[str, list[tuple[str, str]]] = field(default_factory=dict)
    # Bases compartidas descubiertas, igual que `form_bases`: {clase: fichero}
    model_bases: dict[str, str] = field(default_factory=dict)
    meta_bases: dict[str, str] = field(default_factory=dict)
    view_bases: dict[str, str] = field(default_factory=dict)
    # modelo → fichero donde se define · y su cierre transitivo sobre las bases de casa
    model_files: dict[str, str] = field(default_factory=dict)
    model_parents: dict[str, list[str]] = field(default_factory=dict)
    model_family: set[str] = field(default_factory=set)
    meta_base_uses: set[str] = field(default_factory=set)
    shared_classes: dict[str, str] = field(default_factory=dict)
    owner_field: str = ""
    # modelos cuyo save() calcula invariantes (el que `bulk_create` se salta)
    models_save_invariante: dict[str, str] = field(default_factory=dict)
    # campos de caducidad declarados: campo → (modelo, fichero, línea)
    expiry_fields: dict[str, tuple[str, str, int]] = field(default_factory=dict)
    # texto de las capas que CONSUMEN el modelo (vistas, servicios, tasks, middleware…)
    consumer_src: str = ""
    urls_files: list[tuple[str, str]] = field(default_factory=list)

    def add(self, rule: str, path: Path, line: int, msg: str, fix: str = "") -> None:
        rel = os.path.relpath(path, self.root) if isinstance(path, Path) else str(path)
        self.findings.append(Finding(rule, rel, line, msg, fix))


# ─────────────────────────────────────────────────────────────────────────────
# Utilidades
# ─────────────────────────────────────────────────────────────────────────────

EXEMPT_RE = re.compile(r"pattern-exempt:\s*([\w\-]+)")


def exempt(lines: list[str], lineno: int, rule: str) -> bool:
    """Excepción en la propia línea, la anterior, o declarada para todo el fichero."""
    for idx in (lineno - 1, lineno - 2):
        if 0 <= idx < len(lines):
            for m in EXEMPT_RE.finditer(lines[idx]):
                if m.group(1) == rule:
                    return True
    head = "\n".join(lines[:15])
    return any(m.group(1) == rule for m in EXEMPT_RE.finditer(head))


def call_name(node: ast.AST) -> str:
    """Nombre punteado de un Call/Attribute/Name: `models.ForeignKey`, `cache.set`…"""
    if isinstance(node, ast.Call):
        return call_name(node.func)
    if isinstance(node, ast.Attribute):
        base = call_name(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    if isinstance(node, ast.Name):
        return node.id
    return ""


def kw(node: ast.Call, name: str):
    for k in node.keywords:
        if k.arg == name:
            return k.value
    return None


def is_true(node) -> bool:
    return isinstance(node, ast.Constant) and node.value is True


def is_none(node) -> bool:
    return isinstance(node, ast.Constant) and node.value is None


def str_const(node) -> str | None:
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else None


def bases_of(cls: ast.ClassDef) -> list[str]:
    return [call_name(b) for b in cls.bases]


def is_drf_view(cls: ast.ClassDef) -> bool:
    return any(re.search(r"(ViewSet|APIView|GenericAPIView|ListAPIView|RetrieveAPIView|"
                         r"CreateAPIView|UpdateAPIView|DestroyAPIView)$", b) for b in bases_of(cls))


def is_serializer(cls: ast.ClassDef) -> bool:
    return any(re.search(r"Serializer$", b) for b in bases_of(cls))


def is_model(cls: ast.ClassDef) -> bool:
    return any(re.search(r"(^|\.)Model$|Model$", b) for b in bases_of(cls))


def task_decorators(fn: ast.FunctionDef) -> list[ast.Call | ast.Attribute | ast.Name]:
    out = []
    for d in fn.decorator_list:
        n = call_name(d)
        if re.search(r"(^|\.)(shared_task|task)$", n):
            out.append(d)
    return out


def descendants(node: ast.AST):
    yield from ast.walk(node)


# ─────────────────────────────────────────────────────────────────────────────
# Clasificación de ficheros
# ─────────────────────────────────────────────────────────────────────────────

LAYER_RE = re.compile(r"pattern-layer:\s*([\w\-]+)")


def declared_layers(src: str) -> set[str]:
    """`# pattern-layer: services` en la cabecera → este fichero ES esa capa, se llame como se llame.

    Los nombres de fichero (`services.py`, `forms.py`) son el DEFAULT de proyecto nuevo, no la
    regla. Un backend que ya tiene su capa de servicio en `utils.py` la declara aquí y el checker
    le aplica la parte comprobable —no importar HTTP, no recibir `request`— sin renombrar nada.
    """
    return {m.group(1) for m in LAYER_RE.finditer("\n".join(src.splitlines()[:15]))}


def classify(p: Path) -> set[str]:
    # solo los 3 últimos segmentos: el resto es la ruta de instalación y no dice nada del rol
    # del fichero (un repo clonado en /srv/views/ no convierte todo en vistas).
    parts = [x.lower() for x in p.parts[-3:]]
    name = p.name.lower()
    stem = p.stem.lower()
    kinds: set[str] = set()
    if "migrations" in parts and p.suffix == ".py" and not name.startswith("__"):
        kinds.add("migration")
    if p.suffix == ".py":
        if stem == "models" or "models" in parts:
            kinds.add("models")
        if stem == "serializers" or "serializers" in parts:
            kinds.add("serializers")
        if stem in ("views", "viewsets") or "views" in parts:
            kinds.add("views")
        if stem in ("services", "service", "use_cases", "selectors") or "services" in parts:
            kinds.add("services")
        if stem == "forms" or "forms" in parts:
            kinds.add("forms")
        if stem == "tasks" or "tasks" in parts:
            kinds.add("tasks")
        if stem == "signals" or "signals" in parts:
            kinds.add("signals")
        if "settings" in parts or stem in ("settings", "base", "production", "prod", "dev", "local"):
            if "settings" in parts or stem == "settings":
                kinds.add("settings")
        if stem.startswith("test_") or stem.endswith("_test") or "tests" in parts:
            kinds.add("tests")
        if "commands" in parts and not name.startswith("__"):
            kinds.add("command")
        kinds.add("python")
    if name.startswith("docker-compose") and p.suffix in (".yml", ".yaml"):
        kinds.add("compose")
    if name in (".env.example", ".env.sample", "env.example", ".env.template"):
        kinds.add("env-example")
    return kinds


# ─────────────────────────────────────────────────────────────────────────────
# Reglas — modelos y migraciones
# ─────────────────────────────────────────────────────────────────────────────

TEXT_FIELDS = {"CharField", "TextField", "SlugField", "EmailField", "URLField", "FilePathField"}
# Vocabulario monetario. La segunda línea es jerga de NÓMINA, añadida tras medir el recall sobre
# un backend real: `be-model-dinero-float` cazaba `estimated_cost` y `monthly_salary` pero se le
# escapaban `base_a`, `base_b` y `subsidy_ammount` — bases reguladoras de un parte de accidente que
# se reportan a la autoridad laboral. `total_br` ya entraba por `total`.
MONEY_RE = re.compile(r"(price|amount|ammount|total|cost|coste|precio|importe|saldo|balance|fee|"
                      r"subtotal|tax|iva|discount|descuento)|"
                      r"(salary|salario|subsidy|subsidio|nomina|payroll|retribucion|cuota|prima|"
                      r"reguladora|^base_[ab]$|_br$|^br_)", re.I)
REL_FIELDS = {"ForeignKey", "OneToOneField", "ManyToManyField"}


def rule_models(tree: ast.AST, lines: list[str], p: Path, ctx: Ctx) -> None:
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        fname = call_name(node).split(".")[-1]

        # be-model-related-name
        if fname in REL_FIELDS and kw(node, "related_name") is None:
            if not exempt(lines, node.lineno, "be-model-related-name"):
                ctx.add("be-model-related-name", p, node.lineno,
                        f"{fname} sin related_name — el accessor inverso queda como `<modelo>_set` y "
                        "renombrar el modelo rompe queries silenciosamente",
                        f"{fname}(..., related_name=\"<plural_en_snake>\")")

        # be-model-null-en-texto
        if fname in TEXT_FIELDS and is_true(kw(node, "null")):
            if not is_true(kw(node, "unique")) and not exempt(lines, node.lineno, "be-model-null-en-texto"):
                ctx.add("be-model-null-en-texto", p, node.lineno,
                        f"{fname}(null=True) — deja dos estados vacíos ('' y NULL) y toda query "
                        "necesita comprobar los dos",
                        "usa blank=True y default=\"\"; null=True solo si el campo es unique")

        # be-model-dinero-float
        if fname == "FloatField":
            target = _assign_target(tree, node)
            if target and MONEY_RE.search(target) and not exempt(lines, node.lineno, "be-model-dinero-float"):
                ctx.add("be-model-dinero-float", p, node.lineno,
                        f"`{target}` es FloatField — el binario flotante no representa 0.10 y los "
                        "totales se desvían céntimo a céntimo",
                        "DecimalField(max_digits=12, decimal_places=2)")

        # be-model-floatfield-max-length — `max_length` no significa NADA en un campo numérico.
        # Precisión 100% (30 aciertos, 0 falsos positivos sobre el backend de referencia): que esté
        # ahí es la prueba de que nadie revisó esa declaración, y en la medida las 30 eran dinero.
        if fname == "FloatField" and kw(node, "max_length") is not None:
            if not exempt(lines, node.lineno, "be-model-floatfield-max-length"):
                target = _assign_target(tree, node) or "el campo"
                ctx.add("be-model-floatfield-max-length", p, node.lineno,
                        f"`{target}` es FloatField(max_length=…) y `max_length` no hace nada en un "
                        "campo numérico — la declaración no la revisó nadie, y en la medida de "
                        "referencia los 30 casos así eran importes de dinero",
                        "DecimalField(max_digits=12, decimal_places=2) si es dinero; "
                        "quita max_length si de verdad es una magnitud real")

        # be-model-checkconstraint-condition
        if fname == "CheckConstraint" and kw(node, "check") is not None:
            if not exempt(lines, node.lineno, "be-model-checkconstraint-condition"):
                ctx.add("be-model-checkconstraint-condition", p, node.lineno,
                        "CheckConstraint(check=...) — `check` está DEPRECADO desde Django 5.1 "
                        "(warning) y la doc de deprecaciones lo retira en 6.0",
                        "renómbralo a condition=Q(...)")

    _rule_model_clases(tree, lines, p, ctx)


def _meta_of(cls: ast.ClassDef) -> ast.ClassDef | None:
    return next((n for n in cls.body if isinstance(n, ast.ClassDef) and n.name == "Meta"), None)


def _choices_fields(cls: ast.ClassDef) -> list[tuple[str, int]]:
    """Campos del modelo declarados con `choices=` — los que solo valida el formulario."""
    out = []
    for n in cls.body:
        if isinstance(n, ast.Assign) and isinstance(n.value, ast.Call) and kw(n.value, "choices"):
            for t in n.targets:
                if isinstance(t, ast.Name):
                    out.append((t.id, n.lineno))
    return out


def _hay_check_del_campo(constraints, campo: str) -> bool:
    """¿Alguna CheckConstraint de este Meta nombra el campo? (la UniqueConstraint no cuenta:
    protege unicidad, no el conjunto de valores válidos)."""
    if constraints is None:
        return False
    for n in ast.walk(constraints):
        if isinstance(n, ast.Call) and call_name(n).split(".")[-1] == "CheckConstraint":
            # `estado__in=` es una referencia al campo `estado`, y `\b` no sirve para verlo: el
            # guion bajo es carácter de palabra, así que `\bestado\b` NO casa en `estado__in`.
            if re.search(rf"\b{re.escape(campo)}(__|\b)", ast.dump(n)):
                return True
    return False


def _rule_model_clases(tree: ast.AST, lines: list[str], p: Path, ctx: Ctx) -> None:
    """Reglas que miran la CLASE del modelo, no cada campo suelto."""
    rel = os.path.relpath(p, ctx.root).replace(os.sep, "/")
    define_base_aqui = rel in set(ctx.model_bases.values()) or rel in set(ctx.meta_bases.values())

    for cls in [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]:
        if not is_model(cls):
            continue
        meta = _meta_of(cls)
        abstracto = bool(meta and any(
            isinstance(n, ast.Assign) and is_true(n.value)
            and any(isinstance(t, ast.Name) and t.id == "abstract" for t in n.targets)
            for n in meta.body))

        # be-model-base-de-casa — solo si el proyecto YA tiene un modelo base compartido
        if ctx.model_bases and not define_base_aqui and not abstracto:
            if all(b.split(".")[-1] not in ctx.model_family for b in bases_of(cls)):
                if not exempt(lines, cls.lineno, "be-model-base-de-casa"):
                    donde = ", ".join(f"{n} ({f})" for n, f in sorted(ctx.model_bases.items()))
                    ctx.add("be-model-base-de-casa", p, cls.lineno,
                            f"{cls.name} hereda de `models.Model` pelado y no de la base del "
                            f"proyecto [{donde}] — se queda sin los campos de auditoría y sin el "
                            "campo de dueño por el que filtra el scoping por usuario",
                            f"class {cls.name}({sorted(ctx.model_bases)[0]}): …")

        # be-model-meta-base-de-casa — el Meta sin la base pierde permisos EN SILENCIO
        if ctx.meta_bases and meta is not None and not meta.bases and not define_base_aqui:
            if not exempt(lines, meta.lineno, "be-model-meta-base-de-casa"):
                base = sorted(ctx.meta_bases)[0]
                ctx.add("be-model-meta-base-de-casa", p, meta.lineno,
                        f"{cls.name}.Meta no hereda de `{base}` ({ctx.meta_bases[base]}) — nada "
                        "falla y nada avisa: simplemente los permisos que esa base añade no se "
                        "crean para este modelo. ⚠️ Django crea los permisos por defecto AL "
                        "MIGRAR, así que arreglar la herencia después NO crea los que faltaron",
                        f"class Meta({base}): …  + `manage.py createpermissions` (o una migración "
                        "de datos) para los que ya se perdieron")

        # be-model-choices-sin-constraint (sombra) — la invariante que solo vive en el formulario
        cons = _class_attr(meta, "constraints") if meta is not None else None
        for campo, ln in _choices_fields(cls):
            if _hay_check_del_campo(cons, campo):
                continue
            if exempt(lines, ln, "be-model-choices-sin-constraint"):
                continue
            ctx.add("be-model-choices-sin-constraint", p, ln,
                    f"`{cls.name}.{campo}` tiene choices= y ninguna CheckConstraint que lo "
                    "respalde — la lista de valores válidos solo la aplica el formulario; un "
                    "create(), un import o un `manage.py shell` escriben cualquier cosa",
                    f'CheckConstraint(condition=Q({campo}__in=<Enum>.values), name="…")')


def _assign_target(tree: ast.AST, call: ast.Call) -> str | None:
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and node.value is call:
            t = node.targets[0]
            if isinstance(t, ast.Name):
                return t.id
        if isinstance(node, ast.AnnAssign) and node.value is call:
            if isinstance(node.target, ast.Name):
                return node.target.id
    return None


def rule_migration(tree: ast.AST, lines: list[str], p: Path, ctx: Ctx) -> None:
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and call_name(node).split(".")[-1] == "RunPython":
            has_reverse = len(node.args) >= 2 or kw(node, "reverse_code") is not None
            if not has_reverse and not exempt(lines, node.lineno, "be-migracion-reversible"):
                ctx.add("be-migracion-reversible", p, node.lineno,
                        "RunPython sin función inversa — esta migración no se puede revertir y "
                        "bloquea el rollback de un deploy entero",
                        "RunPython(forward, reverse) o RunPython(forward, migrations.RunPython.noop)")


# ─────────────────────────────────────────────────────────────────────────────
# Reglas — serializers
# ─────────────────────────────────────────────────────────────────────────────

# Campos cuyo valor lo decide el servidor a partir de la sesión, nunca el payload. En castellano
# también: el repo documenta en español y `cliente`/`usuario` son el `owner` de media casa.
SERVER_OWNED = {"user", "owner", "created_by", "author", "tenant", "organization", "account",
                "company", "usuario", "cliente", "propietario", "creado_por", "empresa", "autor"}
SIDE_EFFECT_RE = re.compile(r"\.(delay|apply_async)$|send_mail$|(^|\.)requests\.(get|post|put|patch|delete)$|"
                            r"(^|\.)httpx\.(get|post|put|patch|delete)$")


def rule_serializers(tree: ast.AST, lines: list[str], p: Path, ctx: Ctx) -> None:
    for cls in [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]:
        if not is_serializer(cls):
            continue
        meta = next((n for n in cls.body if isinstance(n, ast.ClassDef) and n.name == "Meta"), None)
        if meta:
            fields_node = _class_attr(meta, "fields")
            ro_node = _class_attr(meta, "read_only_fields")
            if str_const(fields_node) == "__all__":
                if not exempt(lines, fields_node.lineno, "be-ser-fields-all"):
                    ctx.add("be-ser-fields-all", p, fields_node.lineno,
                            f"{cls.name}.Meta.fields = '__all__' — cualquier campo que se añada al "
                            "modelo mañana se publica en la API sin que nadie lo decida",
                            "enumera los campos: fields = [\"id\", \"...\"]")
            declared = _str_list(fields_node)
            readonly = set(_str_list(ro_node)) | _declared_read_only(cls)
            for f in declared:
                if f in SERVER_OWNED and f not in readonly:
                    ln = fields_node.lineno
                    if not exempt(lines, ln, "be-ser-campo-servidor-escribible"):
                        ctx.add("be-ser-campo-servidor-escribible", p, ln,
                                f"{cls.name} expone '{f}' como escribible — el cliente puede mandar "
                                f"'{f}' en el payload y crear recursos a nombre de otro",
                                f"read_only_fields = [\"{f}\", ...] y asígnalo en el servicio")
        for node in ast.walk(cls):
            if isinstance(node, ast.Call) and SIDE_EFFECT_RE.search(call_name(node)):
                if not exempt(lines, node.lineno, "be-ser-sin-efectos"):
                    ctx.add("be-ser-sin-efectos", p, node.lineno,
                            f"efecto lateral (`{call_name(node)}`) dentro de {cls.name} — los "
                            "serializers se ejecutan también al validar, y un 400 ya habría "
                            "mandado el correo",
                            "muévelo al servicio que orquesta la operación")


def _class_attr(cls: ast.ClassDef, name: str):
    for n in cls.body:
        if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in n.targets):
            return n.value
    return None


def _str_list(node) -> list[str]:
    if isinstance(node, (ast.List, ast.Tuple)):
        return [v for v in (str_const(e) for e in node.elts) if v]
    return []


def _declared_read_only(cls: ast.ClassDef) -> set[str]:
    """Campos declarados en el cuerpo con read_only=True."""
    out = set()
    for n in cls.body:
        if isinstance(n, ast.Assign) and isinstance(n.value, ast.Call):
            if is_true(kw(n.value, "read_only")):
                for t in n.targets:
                    if isinstance(t, ast.Name):
                        out.add(t.id)
    return out


# ─────────────────────────────────────────────────────────────────────────────
# Reglas — vistas y servicios
# ─────────────────────────────────────────────────────────────────────────────

WRITE_METHODS = {"save", "delete", "create", "update", "bulk_create", "bulk_update",
                 "get_or_create", "update_or_create"}
DRF_HOOKS = {"perform_create", "perform_update", "perform_destroy"}


DRF_DIRECTO_RE = re.compile(r"^(viewsets|generics|mixins)\.|^(ModelViewSet|ReadOnlyModelViewSet|"
                            r"GenericViewSet|ViewSet|APIView|GenericAPIView)$")


def rule_views(tree: ast.AST, lines: list[str], p: Path, ctx: Ctx) -> None:
    rel = os.path.relpath(p, ctx.root).replace(os.sep, "/")
    define_base_aqui = rel in set(ctx.view_bases.values())

    for cls in [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]:
        if not is_drf_view(cls):
            continue

        # be-view-base-de-casa — el filtrado por dueño en UN punto, no repetido en N vistas
        if ctx.view_bases and not define_base_aqui:
            bases = bases_of(cls)
            if not any(b.split(".")[-1] in ctx.view_bases for b in bases):
                if any(DRF_DIRECTO_RE.match(b) for b in bases) and \
                        not exempt(lines, cls.lineno, "be-view-base-de-casa"):
                    base = sorted(ctx.view_bases)[0]
                    ctx.add("be-view-base-de-casa", p, cls.lineno,
                            f"{cls.name} hereda de DRF directamente y no de `{base}` "
                            f"({ctx.view_bases[base]}), que es donde este proyecto resuelve el "
                            "filtrado por dueño — cada vista que se salta la base es una "
                            "oportunidad más de olvidar el filtro, y el olvido aquí es que un "
                            "cliente vea las filas de otro",
                            f"class {cls.name}({base}): … — y si esta vista necesita otro "
                            "queryset, hereda igual y acota dentro de get_queryset()")

        # be-view-queryset-sin-filtrar
        qs = _class_attr(cls, "queryset")
        has_get_qs = any(isinstance(n, ast.FunctionDef) and n.name == "get_queryset" for n in cls.body)
        if qs is not None and not has_get_qs and call_name(qs).endswith("objects.all"):
            if not exempt(lines, qs.lineno, "be-view-queryset-sin-filtrar"):
                ctx.add("be-view-queryset-sin-filtrar", p, qs.lineno,
                        f"{cls.name} sirve `objects.all()` sin get_queryset() — cualquier usuario "
                        "autenticado lista las filas de todos los demás",
                        "def get_queryset(self): return Model.objects.filter(user=self.request.user)")

        # be-view-permisos-por-defecto (AllowAny explícito sin razón)
        perms = _class_attr(cls, "permission_classes")
        if perms is not None and "AllowAny" in ast.dump(perms):
            ln = perms.lineno
            justified = exempt(lines, ln, "be-view-permisos-por-defecto") or _has_comment(lines, ln)
            if not justified:
                ctx.add("be-view-permisos-por-defecto", p, ln,
                        f"{cls.name} abre el endpoint con AllowAny y sin una razón escrita al lado",
                        "# público: <por qué>  — o pattern-exempt: be-view-permisos-por-defecto — <razón>")

        # be-view-error-sin-excepcion — el error devuelto a mano esquiva el EXCEPTION_HANDLER
        for node in ast.walk(cls):
            if not isinstance(node, ast.Return) or not isinstance(node.value, ast.Call):
                continue
            if not call_name(node.value).endswith("Response"):
                continue
            st = kw(node.value, "status")
            if st is None or not _es_status_error(st):
                continue
            if exempt(lines, node.lineno, "be-view-error-sin-excepcion"):
                continue
            ctx.add("be-view-error-sin-excepcion", p, node.lineno,
                    f"{cls.name} devuelve un error con `return Response(..., status=4xx)` — la doc "
                    "de DRF avisa de que el EXCEPTION_HANDLER solo corre para excepciones LANZADAS, "
                    "así que esta respuesta sale sin el sobre {\"errors\": …} y el frontend no la pinta",
                    "raise ValidationError({...}) / PermissionDenied(...) — deja que el handler le dé forma")

        # be-svc-escritura-en-vista
        for fn in [n for n in ast.walk(cls) if isinstance(n, ast.FunctionDef)]:
            if fn.name in DRF_HOOKS and len(fn.body) <= 1:
                continue  # passthrough idiomático de DRF
            for node in ast.walk(fn):
                if not isinstance(node, ast.Call):
                    continue
                dotted = call_name(node)
                meth = dotted.split(".")[-1]
                if meth not in WRITE_METHODS:
                    continue
                receiver = ".".join(dotted.split(".")[:-1])
                if receiver.startswith("serializer") or receiver.endswith("serializer"):
                    continue  # serializer.save() es la vía sancionada por DRF
                if not receiver:
                    continue
                if exempt(lines, node.lineno, "be-svc-escritura-en-vista"):
                    continue
                ctx.add("be-svc-escritura-en-vista", p, node.lineno,
                        f"{cls.name}.{fn.name} escribe en la BD (`{dotted}`) — esa regla de negocio "
                        "solo se puede ejecutar por HTTP: ni la task nocturna ni el test la alcanzan",
                        "mueve la operación a services.py y llama al servicio desde la vista")


STATUS_ERROR_RE = re.compile(r"HTTP_[45]\d\d")


def _es_status_error(node) -> bool:
    """`status=400` o `status=status.HTTP_400_BAD_REQUEST` (4xx/5xx)."""
    if isinstance(node, ast.Constant) and isinstance(node.value, int):
        return node.value >= 400
    return bool(STATUS_ERROR_RE.search(call_name(node) or ""))


def _has_comment(lines: list[str], lineno: int) -> bool:
    for idx in (lineno - 1, lineno - 2):
        if 0 <= idx < len(lines) and "#" in lines[idx]:
            return True
    return False


FORBIDDEN_SVC_IMPORTS = ("rest_framework", "django.http", "django.shortcuts")


# ─────────────────────────────────────────────────────────────────────────────
# Reglas — contrato HTTP (rules/api-http-contract.md)
# ─────────────────────────────────────────────────────────────────────────────

# Credenciales e identificadores FUERTES. `email` y `telefono` se dejan FUERA a propósito: son
# filtros de búsqueda legítimos en medio repo (`?email=` en un buscador de admin), así que meterlos
# dispararía en decenas de sitios correctos y la regla moriría de ruido — que es justo lo que la
# regla de inversión de `patterns/README.md` §2 manda evitar. Que un email no deba viajar en la
# query de un endpoint público sigue siendo cierto; es criterio (§4 de la rule), no mecanismo.
SECRETO_EN_QUERY_RE = re.compile(
    r"^(token|api_?key|secret|password|passwd|pwd|access_token|refresh_token|auth|authorization|"
    r"session|session_id|sessionid|dni|nif|nie|iban|tarjeta|card|cvv)$", re.I)

VERBOS_LECTURA = {"get", "head", "options"}
VERBOS_ESCRITURA = {"post", "put", "patch", "delete"}


def rule_http_contract(tree: ast.AST, lines: list[str], p: Path, ctx: Ctx) -> None:
    """be-api-secreto-en-query · be-view-action-multiverbo — `rules/api-http-contract.md` §2 y §4."""
    for node in ast.walk(tree):

        # be-api-secreto-en-query — request.query_params.get("token") y sus variantes
        nombre = None
        if isinstance(node, ast.Call):
            fn_name = call_name(node)
            if fn_name.endswith(("query_params.get", "query_params.getlist",
                                 "GET.get", "GET.getlist")) and node.args:
                nombre = str_const(node.args[0])
        elif isinstance(node, ast.Subscript):
            base = call_name(node.value)
            if base.endswith(("query_params", "GET")):
                nombre = str_const(node.slice)
        if nombre and SECRETO_EN_QUERY_RE.match(nombre.strip()):
            if not exempt(lines, node.lineno, "be-api-secreto-en-query"):
                ctx.add("be-api-secreto-en-query", p, node.lineno,
                        f"lee `{nombre}` de la query — una URL se escribe entera en el log de "
                        "acceso, en el historial del navegador y en el Referer al salir a otro "
                        "dominio, así que ese valor acaba en cinco sitios que no controlas",
                        "la credencial va en la cabecera Authorization y el dato en el body; si el "
                        "proveedor SOLO acepta una URL (webhook), aplica las 3 condiciones de "
                        "skills/webhook-multi-tenant-validation y marca "
                        "`pattern-exempt: be-api-secreto-en-query — <razón>`")

        # be-view-action-multiverbo — un @action que sirve a la vez para leer y para escribir
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for dec in node.decorator_list:
                if not isinstance(dec, ast.Call) or not call_name(dec).endswith("action"):
                    continue
                m = kw(dec, "methods")
                verbos = {v.lower() for v in _str_list(m)}
                if not (verbos & VERBOS_LECTURA and verbos & VERBOS_ESCRITURA):
                    continue
                if exempt(lines, dec.lineno, "be-view-action-multiverbo"):
                    continue
                ctx.add("be-view-action-multiverbo", p, dec.lineno,
                        f"`{node.name}` acepta {sorted(verbos)} en el mismo endpoint — mezcla una "
                        "consulta con una escritura, así que el CSRF aplica a una rama y no a la "
                        "otra, la caché puede guardar lo que no debía y el log de acceso deja de "
                        "distinguir leer de escribir",
                        "pártelo en dos @action, uno por intención: "
                        "methods=[\"get\"] para consultar y methods=[\"post\"] para actuar")


def rule_services(tree: ast.AST, lines: list[str], p: Path, ctx: Ctx) -> None:
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            if any(node.module == m or node.module.startswith(m + ".") for m in FORBIDDEN_SVC_IMPORTS):
                if not exempt(lines, node.lineno, "be-svc-sin-drf"):
                    ctx.add("be-svc-sin-drf", p, node.lineno,
                            f"la capa de servicio importa `{node.module}` — al atarla al ciclo "
                            "HTTP deja de ser invocable desde una task, un comando o un test",
                            "devuelve datos/objetos o lanza excepciones de dominio; que la vista traduzca a HTTP")
        if isinstance(node, ast.Import):
            for a in node.names:
                if any(a.name == m or a.name.startswith(m + ".") for m in FORBIDDEN_SVC_IMPORTS):
                    if not exempt(lines, node.lineno, "be-svc-sin-drf"):
                        ctx.add("be-svc-sin-drf", p, node.lineno,
                                f"la capa de servicio importa `{a.name}` (ver arriba)",
                                "saca la dependencia HTTP del servicio")
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = [a.arg for a in node.args.args] + [a.arg for a in node.args.kwonlyargs]
            if "request" in args and not exempt(lines, node.lineno, "be-svc-sin-drf"):
                ctx.add("be-svc-sin-drf", p, node.lineno,
                        f"el servicio `{node.name}()` recibe `request` — arrastra la petición HTTP "
                        "hasta el dominio y obliga a fabricar un request falso para testearlo",
                        "pásale los datos que necesita (user, ids, valores), no el request")


# ─────────────────────────────────────────────────────────────────────────────
# Reglas — formularios Django (arquetipo server-rendered, `backend-formularios-django.md`)
# ─────────────────────────────────────────────────────────────────────────────

FORM_BASE_RE = re.compile(r"(^|\.)(ModelForm|Form)$")
MODELFORM_RE = re.compile(r"(^|\.)ModelForm$")
DJANGO_MODELFORM = {"forms.ModelForm", "django.forms.ModelForm"}
SHARED_DIR_RE = re.compile(r"(^|/)(core|common|shared|comun|compartido)(/|$)")
DATA_FIRST_RE = re.compile(r"^(self\.)?request\.(POST|GET|FILES|data)$")


def _import_aliases(tree: ast.AST) -> dict[str, str]:
    """`from core.forms import ModelForm as ModelFormDeCasa` → {ModelFormDeCasa: ModelForm}.

    Sin esto, renombrar la base al importarla la volvía invisible para todas las reglas de
    formulario: ni se reconocía la clase como formulario, ni entraba en la familia de la base.
    """
    out: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for a in node.names:
                if a.asname:
                    out[a.asname] = a.name
    return out


def is_form(cls: ast.ClassDef, aliases: dict[str, str] | None = None) -> bool:
    aliases = aliases or {}
    return any(FORM_BASE_RE.search(aliases.get(b, b)) for b in bases_of(cls))


def _django_modelform_names(tree: ast.AST) -> set[str]:
    """Cómo se llama EN ESTE FICHERO el ModelForm de Django (que puede no ser el de casa)."""
    names = set(DJANGO_MODELFORM)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and (node.module or "").startswith("django.forms"):
            for a in node.names:
                if a.name == "ModelForm":
                    names.add(a.asname or a.name)
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.name == "django.forms" and a.asname:
                    names.add(f"{a.asname}.ModelForm")
    return names


def _collect_forms_de_controller(src: str, ctx: Ctx) -> None:
    """Cualquier `form = <Nombre>` a nivel de clase declara que ese form lo gobierna un controller."""
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return
    for cls in [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]:
        for stmt in cls.body:
            if not isinstance(stmt, ast.Assign):
                continue
            for tg in stmt.targets:
                if getattr(tg, "id", None) == "form" and isinstance(stmt.value, ast.Name):
                    ctx.forms_de_controller.add(stmt.value.id)


def _collect_form_bases(p: Path, src: str, ctx: Ctx) -> None:
    """Descubre el árbol de formularios del proyecto y cuáles son las bases COMPARTIDAS.

    No se declara en ningún sitio: se mira dónde vive la clase. Una base de formulario en un
    módulo compartido (`core/`, `common/`, `shared/`…) es la base de casa. En un proyecto nuevo
    todavía no hay ninguna, y por eso `be-form-base-de-casa` no dispara hasta que exista.
    """
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return
    rel = os.path.relpath(p, ctx.root).replace(os.sep, "/")
    shared = bool(SHARED_DIR_RE.search(rel))
    aliases = _import_aliases(tree)
    for cls in [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]:
        if not is_form(cls, aliases):
            continue
        bases = [aliases.get(b, b) for b in bases_of(cls)]
        ctx.form_classes[cls.name] = bases
        if shared and any(MODELFORM_RE.search(b) for b in bases):
            ctx.form_bases[cls.name] = rel
            init = next((n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == "__init__"), None)
            if init:
                pos = [a.arg for a in init.args.args][1:]  # sin self
                if pos[:1] == ["request"]:
                    ctx.form_base_request_first = True


def resolve_form_family(ctx: Ctx) -> None:
    """Cierre transitivo: qué clases descienden de una base de casa (para be-form-request-primero)."""
    family = set(ctx.form_bases)
    changed = True
    while changed:
        changed = False
        for name, bases in ctx.form_classes.items():
            if name in family:
                continue
            if any(b.split(".")[-1] in family for b in bases):
                family.add(name)
                changed = True
    ctx.form_family = family


def rule_forms(tree: ast.AST, lines: list[str], p: Path, ctx: Ctx) -> None:
    rel = os.path.relpath(p, ctx.root).replace(os.sep, "/")
    define_base_here = rel in set(ctx.form_bases.values())
    aliases = _import_aliases(tree)
    django_names = _django_modelform_names(tree)

    for cls in [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]:
        if not is_form(cls, aliases):
            continue

        # be-form-fields-enumerado
        #
        # FALSO POSITIVO CORREGIDO (2026-08-25, medido sobre el backend de referencia). Si un
        # `*Settings` declara `form = EstaClase`, su `Meta.fields` es DECORATIVO: el controlador
        # crea `class ControllerForm(self.form)` con `Meta.fields = form_fields` en runtime
        # (`controller/controllers.py:110-116`) y la lista efectiva sale de sus `fieldsets`.
        # Exigirle aquí una lista blanca es pedirle que enumere algo que va a ser sobrescrito —
        # y esta regla está en `activo`, o sea que BLOQUEA. Un gate que se equivoca sobre el
        # código de casa es como se aprende a saltarse los gates (`verdict-contract.md` §Intent:
        # el código raro suele ser deliberado; búscale el porqué antes de condenarlo).
        # La regla sigue viva para el form instanciado a mano, que es donde sí protege.
        if cls.name in ctx.forms_de_controller:
            continue
        meta = next((n for n in cls.body if isinstance(n, ast.ClassDef) and n.name == "Meta"), None)
        if meta is not None:
            fields_node = _class_attr(meta, "fields")
            exclude_node = _class_attr(meta, "exclude")
            if fields_node is not None and str_const(fields_node) == "__all__":
                if not exempt(lines, fields_node.lineno, "be-form-fields-enumerado"):
                    ctx.add("be-form-fields-enumerado", p, fields_node.lineno,
                            f"{cls.name}.Meta.fields = '__all__' — el campo que alguien añada al "
                            "modelo mañana se vuelve editable en este formulario sin que nadie lo decida",
                            "enumera los campos: fields = [\"...\"]")
            if exclude_node is not None:
                if not exempt(lines, exclude_node.lineno, "be-form-fields-enumerado"):
                    ctx.add("be-form-fields-enumerado", p, exclude_node.lineno,
                            f"{cls.name}.Meta usa `exclude` — es una lista negra: protege lo que hoy "
                            "conoces y deja entrar lo que se añada después",
                            "cámbialo por fields = [...] (lista blanca)")

        # be-form-base-de-casa — solo si el proyecto YA tiene una base compartida
        if ctx.form_bases and not define_base_here:
            # A propósito con el nombre CRUDO, sin resolver el alias: si el fichero importó la
            # base de casa con otro nombre, ese nombre NO es el ModelForm de Django aunque al
            # normalizarlo coincida (en muchos proyectos la base de casa se llama igual).
            for b in bases_of(cls):
                if b not in django_names:
                    continue
                if exempt(lines, cls.lineno, "be-form-base-de-casa"):
                    continue
                donde = ", ".join(f"{n} ({f})" for n, f in sorted(ctx.form_bases.items()))
                ctx.add("be-form-base-de-casa", p, cls.lineno,
                        f"{cls.name} hereda de `{b}` (el de Django) y no de la base del proyecto "
                        f"[{donde}] — se salta lo que esa base hace por TODOS los formularios: "
                        "saneado del HTML, asignación del dueño y campos de solo lectura por perfil",
                        f"class {cls.name}({sorted(ctx.form_bases)[0]}): …")
                break


def rule_form_calls(tree: ast.AST, lines: list[str], p: Path, ctx: Ctx) -> None:
    """be-form-request-primero: la base de casa recibe `request` primero; los datos, después."""
    if not ctx.form_base_request_first:
        return
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not node.args:
            continue
        name = call_name(node).split(".")[-1]
        if name not in ctx.form_family:
            continue
        if not DATA_FIRST_RE.match(call_name(node.args[0])):
            continue
        if exempt(lines, node.lineno, "be-form-request-primero"):
            continue
        ctx.add("be-form-request-primero", p, node.lineno,
                f"{name}(request.POST…) — la firma de la base pone `request` PRIMERO, así que esto "
                "no bindea los datos: el formulario queda unbound, is_valid() devuelve False "
                "siempre y no se lanza ningún error que lo delate",
                f"{name}(request, request.POST, request.FILES)")


def rule_form_class_placement(tree: ast.AST, lines: list[str], p: Path, ctx: Ctx) -> None:
    """be-form-clase-fuera-de-forms: una clase *Form fuera de forms.py."""
    aliases = _import_aliases(tree)
    for cls in [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]:
        if not cls.name.endswith("Form") or not is_form(cls, aliases):
            continue
        if exempt(lines, cls.lineno, "be-form-clase-fuera-de-forms"):
            continue
        ctx.add("be-form-clase-fuera-de-forms", p, cls.lineno,
                f"{cls.name} se define en `{p.name}` — quien busque los formularios de la app mirará "
                "en forms.py, no la encontrará y escribirá otra igual al lado",
                "muévela a forms.py de su app")


# ─────────────────────────────────────────────────────────────────────────────
# Descubrimiento cross-file — bases de casa, apps, plantillas y capas
#
# Todo lo de aquí se DESCUBRE leyendo el repo; no hay ningún fichero de configuración que declare
# "esta es la base de casa". Es la misma decisión que ya tomaba `_collect_form_bases`: en un
# proyecto nuevo todavía no existe ninguna base, y por eso las reglas que dependen de ella no
# disparan hasta que exista. Un YAML de declaración habría hecho que el checker acusara a un
# proyecto de no seguir un patrón que aún no tiene.
# ─────────────────────────────────────────────────────────────────────────────

OWNER_FIELDS = {"owner", "propietario", "dueno", "created_by", "creado_por"}
EXPIRY_RE = re.compile(r"^(expiration_date|expires_at|expires_on|expiry_date|valid_until|"
                       r"fecha_caducidad|caduca_en|valido_hasta)$")
DRF_VIEW_BASE_RE = re.compile(r"(ViewSet|APIView|GenericAPIView|ListAPIView|RetrieveAPIView|"
                              r"CreateAPIView|UpdateAPIView|DestroyAPIView)$")
# Roles conocidos de un fichero en un proyecto Django. Lo que NO está aquí y toca el ORM es un
# script suelto (be-script-sin-runner). La lista es deliberadamente generosa: el falso positivo de
# esta regla es acusar de "script" a un módulo normal, y eso quema la regla en dos días.
ROLES_CONOCIDOS = {
    "models", "views", "viewsets", "serializers", "services", "service", "use_cases", "selectors",
    "forms", "tasks", "signals", "admin", "apps", "urls", "filters", "managers", "querysets",
    "middleware", "security", "permissions", "validators", "widgets", "mixins", "utils", "helpers",
    "constants", "enums", "choices", "controllers", "controller_settings", "inlines", "resources",
    "reports", "report", "api", "exceptions", "routers", "factories", "schema", "conftest",
    "settings", "base", "dev", "local", "prod", "production", "manage", "wsgi", "asgi", "celery",
    "__init__", "context_processors", "templatetags", "storages", "backends", "migrations",
}


def _app_dir_of(rel: str, app_dirs: set[str]) -> str | None:
    """La app a la que pertenece un fichero: el app_dir más largo que es prefijo de su ruta."""
    mejor = None
    for d in app_dirs:
        if rel == d or rel.startswith(d + "/"):
            if mejor is None or len(d) > len(mejor):
                mejor = d
    return mejor


def _template_owner(rel: str) -> tuple[str, str] | None:
    """`risks_management/templates/widgets/x.html` → ("risks_management", "widgets/x.html")."""
    parts = rel.split("/")
    if "templates" not in parts:
        return None
    i = parts.index("templates")
    if i == 0 or i == len(parts) - 1:
        return None
    return "/".join(parts[:i]), "/".join(parts[i + 1:])


def _es_abstracto(cls: ast.ClassDef) -> bool:
    meta = _meta_of(cls)
    if meta is None:
        return False
    return any(isinstance(n, ast.Assign) and is_true(n.value)
               and any(isinstance(t, ast.Name) and t.id == "abstract" for t in n.targets)
               for n in meta.body)


def _campos_de(cls: ast.ClassDef) -> list[tuple[str, int]]:
    out = []
    for n in cls.body:
        if isinstance(n, ast.Assign) and isinstance(n.value, ast.Call):
            for t in n.targets:
                if isinstance(t, ast.Name):
                    out.append((t.id, n.lineno))
    return out


def _save_calcula_invariante(cls: ast.ClassDef) -> bool:
    """¿El `save()` de este modelo escribe algo en la propia instancia?

    Es la firma del caso que duele: `int_code`, un número de serie, un slug… se calculan en
    `save()`, y `bulk_create()` no llama a `save()`. Las filas quedan con ese campo a nulo y sin
    fila de historial, sin que nada falle. Un `save()` que solo delega en `super()` no cuenta.
    """
    save = next((n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == "save"), None)
    if save is None:
        return False
    for n in ast.walk(save):
        if isinstance(n, ast.Assign):
            for t in n.targets:
                if isinstance(t, ast.Attribute) and isinstance(t.value, ast.Name) and t.value.id == "self":
                    return True
    return False


def _collect_estructura(p: Path, src: str, ctx: Ctx) -> None:
    """Índice de apps, plantillas y capa declarada. No parsea Python: solo mira rutas."""
    rel = os.path.relpath(p, ctx.root).replace(os.sep, "/")
    if p.name in ("apps.py", "models.py"):
        ctx.app_dirs.add(os.path.dirname(rel))
    if p.suffix == ".html":
        dueno = _template_owner(rel)
        if dueno:
            ctx.templates.setdefault(dueno[1], []).append((dueno[0], rel))
    if p.suffix == ".py" and "shared" in declared_layers(src):
        ctx.shared_apps.add(os.path.dirname(rel))
    if p.name == "urls.py":
        ctx.urls_files.append((rel, src))


def _collect_modelos(p: Path, src: str, ctx: Ctx) -> None:
    """Bases de modelo y de `Meta`, invariantes en `save()` y campos de caducidad."""
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return
    rel = os.path.relpath(p, ctx.root).replace(os.sep, "/")
    shared = bool(SHARED_DIR_RE.search(rel))

    for cls in [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]:
        bases = [b.split(".")[-1] for b in bases_of(cls)]
        if shared:
            ctx.shared_classes[cls.name] = rel
        meta = _meta_of(cls)
        if meta is not None:
            ctx.meta_base_uses |= {b.split(".")[-1] for b in bases_of(meta)}
        if not is_model(cls):
            continue
        ctx.model_files[cls.name] = rel
        ctx.model_parents[cls.name] = bases
        if _save_calcula_invariante(cls):
            ctx.models_save_invariante[cls.name] = rel
        campos = _campos_de(cls)
        if shared and _es_abstracto(cls):
            ctx.model_bases[cls.name] = rel
            for campo, _ in campos:
                if campo in OWNER_FIELDS and not ctx.owner_field:
                    ctx.owner_field = campo
        for campo, ln in campos:
            if EXPIRY_RE.match(campo):
                ctx.expiry_fields.setdefault(campo, (cls.name, rel, ln))


def _collect_vistas(p: Path, src: str, ctx: Ctx) -> None:
    """Vista base compartida: la que resuelve el filtrado por dueño en UN punto (REF-2)."""
    rel = os.path.relpath(p, ctx.root).replace(os.sep, "/")
    if not SHARED_DIR_RE.search(rel):
        return
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return
    for cls in [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]:
        if not any(DRF_VIEW_BASE_RE.search(b) for b in bases_of(cls)):
            continue
        if any(isinstance(n, ast.FunctionDef) and n.name == "get_queryset" for n in cls.body):
            ctx.view_bases[cls.name] = rel


def resolve_descubrimiento(ctx: Ctx) -> None:
    """Cierres transitivos. Se corre una vez, al final de `gather_context`."""
    # (a) qué modelos descienden de una base de casa
    family = set(ctx.model_bases)
    # (b) qué modelos heredan un save() con invariante
    conserva = set(ctx.models_save_invariante)
    cambio = True
    while cambio:
        cambio = False
        for name, bases in ctx.model_parents.items():
            if name not in family and any(b in family for b in bases):
                family.add(name)
                cambio = True
            if name not in conserva and any(b in conserva for b in bases):
                conserva.add(name)
                ctx.models_save_invariante[name] = ctx.model_files.get(name, "")
                cambio = True
    ctx.model_family = family
    # (c) las bases de `Meta` de casa: definidas en un módulo compartido y usadas como tal
    for nombre, fichero in ctx.shared_classes.items():
        if nombre in ctx.meta_base_uses:
            ctx.meta_bases[nombre] = fichero


# ─────────────────────────────────────────────────────────────────────────────
# Reglas — estructura del proyecto (capa 0)
# ─────────────────────────────────────────────────────────────────────────────

def rule_templates(ctx: Ctx) -> None:
    """be-tpl-ruta-duplicada — el bug que no falla: tu fichero simplemente no se renderiza.

    Django resuelve las plantillas de app por orden de `INSTALLED_APPS`: si dos apps sirven la
    misma ruta relativa, gana la primera y la otra queda muerta. No hay error, no hay warning; el
    fichero está ahí, lo editas, guardas y no pasa nada.
    """
    for ruta, dueños in sorted(ctx.templates.items()):
        apps = sorted({a for a, _ in dueños if a in ctx.app_dirs})
        if len(apps) < 2:
            continue
        ficheros = [f for a, f in dueños if a in ctx.app_dirs]
        exento = False
        for f in ficheros:
            try:
                cabecera = (ctx.root / f).read_text(encoding="utf-8", errors="replace").splitlines()
            except Exception:
                continue
            if exempt(cabecera, 1, "be-tpl-ruta-duplicada"):
                exento = True
        if exento:
            continue
        for f in sorted(ficheros)[1:]:
            ctx.findings.append(Finding(
                "be-tpl-ruta-duplicada", f, 1,
                f"`{ruta}` la sirven {len(apps)} apps ({', '.join(apps)}) — gana la primera de "
                "INSTALLED_APPS y las demás no se renderizan JAMÁS: editar este fichero no produce "
                "ningún cambio y no salta ningún error",
                "borra la copia muerta, o si el override es deliberado hazlo explícito con "
                "<!-- pattern-exempt: be-tpl-ruta-duplicada — override de <app>, razón -->"))


DOMINIO_IMPORT_RE = re.compile(r"^[a-z_][a-z0-9_]*")


def rule_capas(tree: ast.AST, lines: list[str], p: Path, ctx: Ctx) -> None:
    """be-capa-compartida-importa-dominio (sombra) — el contador del enredo entre apps.

    En SOMBRA a propósito: mide, no bloquea. Promoverla a bloqueante exige antes una lista de
    excepciones del tamaño del repo, y ese coste hay que decidirlo con el número delante.
    """
    if not ctx.shared_apps:
        return
    rel = os.path.relpath(p, ctx.root).replace(os.sep, "/")
    mia = _app_dir_of(rel, ctx.app_dirs)
    if mia is None or mia not in ctx.shared_apps:
        return
    dominio = {d for d in ctx.app_dirs if d not in ctx.shared_apps}
    nombres = {}
    for d in dominio:
        nombres[d.replace("/", ".")] = d
        nombres[d.split("/")[-1]] = d
    # Solo imports a NIVEL DE MÓDULO. El import diferido dentro de una función es el parche
    # clásico para romper un ciclo: es una señal, pero marcarlo aquí convertiría la regla en un
    # castigo por haber apagado el fuego. Se mide el acoplamiento real, no el parche.
    for node in getattr(tree, "body", []):
        if not isinstance(node, ast.ImportFrom) or node.level or not node.module:
            continue
        raiz = node.module.split(".")[0]
        objetivo = nombres.get(node.module) or nombres.get(raiz)
        if objetivo is None or objetivo == mia:
            continue
        if exempt(lines, node.lineno, "be-capa-compartida-importa-dominio"):
            continue
        ctx.add("be-capa-compartida-importa-dominio", p, node.lineno,
                f"`{mia}` es capa compartida y importa la app de dominio `{objetivo}` — la "
                "dependencia va en el sentido contrario y crea el ciclo que después se parchea "
                "metiendo imports dentro de las funciones",
                "invierte la dependencia (que el dominio importe lo compartido) o mueve lo que "
                "comparten a la capa compartida")


ORM_RE = re.compile(r"\.objects\.|from django\.db import|django\.setup\(")
RUNNER_RE = re.compile(r"#\s*runner:|django\.setup\(")


def rule_script_suelto(src: str, lines: list[str], p: Path, ctx: Ctx) -> None:
    """be-script-sin-runner — lo que SÍ sobrevivió de la regla «todo a management commands».

    La regla original ("un .py fuera de una app que importe modelos es un hallazgo") se cayó al
    verificarla: su premisa —que sin `django.setup()` un script no puede tocar el ORM— es falsa,
    `manage.py shell < script.py` funciona. Lo que sí aguanta es mucho más modesto: que el fichero
    diga cómo se ejecuta, para que el siguiente no tenga que adivinarlo.
    """
    rel = os.path.relpath(p, ctx.root).replace(os.sep, "/")
    if p.stem in ROLES_CONOCIDOS or "management/commands/" in rel or "migrations/" in rel:
        return
    if p.stem.startswith("test") or p.stem.endswith("_test") or "tests/" in rel:
        return
    if not ORM_RE.search(src):
        return
    if RUNNER_RE.search("\n".join(lines[:15])) or "django.setup(" in src:
        return
    if exempt(lines, 1, "be-script-sin-runner"):
        return
    ctx.add("be-script-sin-runner", p, 1,
            f"`{rel}` toca el ORM y no dice cómo se ejecuta — dentro de seis meses nadie sabrá si "
            "lo lanza un cron, el CI, alguien a mano, o si ya no lo lanza nadie",
            "`# runner: cron diario 03:00 en el servidor de producción` en la cabecera · o "
            "`django.setup()` explícito · o muévelo a management/commands/")


def rule_monkeypatch(tree: ast.AST, lines: list[str], p: Path, ctx: Ctx) -> None:
    """be-py-monkeypatch-django — parchear una clase de Django a nivel de módulo."""
    django_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and (node.module or "").startswith("django"):
            django_names |= {a.asname or a.name for a in node.names}
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.name.startswith("django"):
                    django_names.add(a.asname or a.name.split(".")[0])
    if not django_names:
        return
    cuerpo = getattr(tree, "body", [])
    for node in cuerpo:
        if not isinstance(node, ast.Assign):
            continue
        for t in node.targets:
            if not isinstance(t, ast.Attribute):
                continue
            raiz = call_name(t).split(".")[0]
            if raiz not in django_names:
                continue
            if exempt(lines, node.lineno, "be-py-monkeypatch-django"):
                continue
            ctx.add("be-py-monkeypatch-django", p, node.lineno,
                    f"`{call_name(t)} = …` parchea una clase de Django para TODO el proceso — "
                    "incluidos contrib.auth, el admin y cualquier librería de terceros. Desde el "
                    "sitio de uso no hay forma de llegar a la definición, y si es seguridad "
                    "(validadores de fichero) depende del orden de importación",
                    "una clase base explícita de la que hereden los modelos/formularios de casa")


MONGO_RE = re.compile(r"^\s*(?:from|import)\s+(pymongo|bson|djongo)\b|['\"]djongo['\"]")


def rule_mongo(lines: list[str], p: Path, ctx: Ctx) -> None:
    for i, line in enumerate(lines, 1):
        if not MONGO_RE.search(line):
            continue
        if exempt(lines, i, "be-no-mongo"):
            continue
        ctx.add("be-no-mongo", p, i,
                "MongoDB (pymongo/bson/djongo) — el stack canónico es PostgreSQL puro: el `JSONField` "
                "cubre el documento, un índice GIN cubre el catálogo grande y `simple_history` "
                "cubre la auditoría sin una segunda base",
                "JSONField + índice GIN · si este proyecto usa Mongo de verdad: "
                "`# pattern-exempt: be-no-mongo — <razón>`")
        return


# ─────────────────────────────────────────────────────────────────────────────
# Reglas — señales
# ─────────────────────────────────────────────────────────────────────────────

EFECTO_FUERA_RE = re.compile(
    r"\.(delay|apply_async)$|send_mail$|send_messages$|"
    r"(^|\.)(requests|httpx)\.(get|post|put|patch|delete|head|request)$|"
    r"(^|\.)(MongoClient|publish)$")


def _es_receiver(fn: ast.FunctionDef) -> bool:
    return any("receiver" in call_name(d) for d in fn.decorator_list)


def _ids_bajo_on_commit(node: ast.AST) -> set[int]:
    protegidos: set[int] = set()
    for n in ast.walk(node):
        if isinstance(n, ast.Call) and "on_commit" in call_name(n):
            for sub in ast.walk(n):
                protegidos.add(id(sub))
    return protegidos


def rule_signals(tree: ast.AST, lines: list[str], p: Path, ctx: Ctx) -> None:
    funciones = {n.name: n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
    # helpers del propio módulo que ya llevan un efecto sin proteger: el receiver que los llama
    # hereda el problema. Sin este nivel de indirección el gate da verde con el bug vivo.
    helpers_sucios = {
        name: fn for name, fn in funciones.items()
        if not _es_receiver(fn) and any(
            isinstance(n, ast.Call) and EFECTO_FUERA_RE.search(call_name(n))
            and id(n) not in _ids_bajo_on_commit(fn) for n in ast.walk(fn))
    }

    for fn in funciones.values():
        if _es_receiver(fn):
            protegidos = _ids_bajo_on_commit(fn)
            for n in ast.walk(fn):
                if not isinstance(n, ast.Call) or id(n) in protegidos:
                    continue
                nombre = call_name(n)
                directo = bool(EFECTO_FUERA_RE.search(nombre))
                via_helper = nombre.split(".")[-1] in helpers_sucios
                if not directo and not via_helper:
                    continue
                if exempt(lines, n.lineno, "be-sig-efecto-sin-on-commit"):
                    continue
                detalle = (f"`{nombre}`" if directo
                           else f"`{nombre}()`, que por dentro lanza el efecto")
                ctx.add("be-sig-efecto-sin-on-commit", p, n.lineno,
                        f"{fn.name} es un receiver y dispara {detalle} sin esperar al COMMIT — un "
                        "receiver corre DENTRO de la transacción de quien guardó, así que el "
                        "worker puede leer una fila que aún no existe, o el aviso puede salir de "
                        "una operación que termina en rollback",
                        "transaction.on_commit(partial(tarea.delay, instance.pk)) — con "
                        "functools.partial, no lambda, si estás dentro de un bucle")
            continue

        # be-sig-logica-de-negocio — una función de negocio escondida en signals.py
        if not any(isinstance(n, ast.Call) and call_name(n).split(".")[-1] in WRITE_METHODS
                   for n in ast.walk(fn)):
            continue
        if exempt(lines, fn.lineno, "be-sig-logica-de-negocio"):
            continue
        ctx.add("be-sig-logica-de-negocio", p, fn.lineno,
                f"`{fn.name}()` no es un receiver, escribe en la BD y vive en signals.py — solo se "
                "la puede llamar desde el ciclo post_save: ni una task, ni un comando, ni un test "
                "la alcanzan, así que el día que haga falta en batch se reescribe al lado",
                "muévela a la capa de servicio y que el receiver la llame")


# ─────────────────────────────────────────────────────────────────────────────
# Reglas — validación fuera del formulario, y dueño de la fila
# ─────────────────────────────────────────────────────────────────────────────

ESCRITURA_RE = re.compile(r"\.(save|create|bulk_create|update_or_create|get_or_create)$")


def rule_command_full_clean(tree: ast.AST, lines: list[str], p: Path, ctx: Ctx) -> None:
    """be-val-escritura-sin-full-clean — el comando de gestión es la otra puerta, y no valida."""
    src_dump = ast.dump(tree)
    if "full_clean" in src_dump:
        return
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not ESCRITURA_RE.search(call_name(node)):
            continue
        if exempt(lines, node.lineno, "be-val-escritura-sin-full-clean"):
            return
        ctx.add("be-val-escritura-sin-full-clean", p, node.lineno,
                f"este comando escribe en la BD (`{call_name(node)}`) y no llama a `full_clean()` "
                "en ningún sitio — el formulario es la única puerta con validación del proyecto, y "
                "esta no es esa puerta: aquí entra cualquier valor",
                "obj.full_clean() antes de guardar · y la invariante que NUNCA debe romperse, "
                "además, como CheckConstraint en el modelo")
        return


NO_BULK_RE = re.compile(r"#\s*no-bulk:")


def rule_bulk_create(tree: ast.AST, lines: list[str], p: Path, ctx: Ctx) -> None:
    """be-model-bulk-create-invariante — el daño ya materializado, no una hipótesis.

    Alcance calibrado con la medida del backend de referencia: **solo `bulk_create`**, y **fuera de
    `scripts/` y `management/`**. Incluir `.update()` subía de 7 a 43 hallazgos y el 84% eran
    mantenimiento legítimo — que es exactamente cuando la regla de inversión dice que la mala es
    la regla.
    """
    if not ctx.models_save_invariante:
        return
    rel = os.path.relpath(p, ctx.root).replace(os.sep, "/")
    if "/scripts/" in f"/{rel}" or "management/" in rel:
        return
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not call_name(node).endswith("objects.bulk_create"):
            continue
        modelo = call_name(node).split(".")[0]
        if modelo not in ctx.models_save_invariante:
            continue
        if exempt(lines, node.lineno, "be-model-bulk-create-invariante"):
            continue
        if any(NO_BULK_RE.search(lines[i]) for i in (node.lineno - 1, node.lineno - 2)
               if 0 <= i < len(lines)):
            continue
        ctx.add("be-model-bulk-create-invariante", p, node.lineno,
                f"`{modelo}.objects.bulk_create(...)` — el `save()` de este modelo "
                f"({ctx.models_save_invariante[modelo]}) calcula algo sobre la propia instancia, y "
                "`bulk_create` NO llama a `save()` ni emite `post_save`. Las filas entran a medio "
                "construir y sin fila de historial; nada falla, y el fallo aparece meses después",
                "rellena el campo tras la inserción, o declara por qué aquí da igual: "
                "`# no-bulk: el código lo asigna el proveedor externo`")


def rule_owner(tree: ast.AST, lines: list[str], p: Path, ctx: Ctx) -> None:
    """be-owner-create-sin-dueno — una fila sin dueño existe y es invisible."""
    if not ctx.owner_field or not ctx.model_family:
        return
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not call_name(node).endswith("objects.create"):
            continue
        modelo = call_name(node).split(".")[0]
        if modelo not in ctx.model_family:
            continue
        if kw(node, ctx.owner_field) is not None:
            continue
        if exempt(lines, node.lineno, "be-owner-create-sin-dueno"):
            continue
        ctx.add("be-owner-create-sin-dueno", p, node.lineno,
                f"`{modelo}.objects.create(...)` sin `{ctx.owner_field}=` — el filtrado por usuario "
                f"filtra justo por ese campo, así que la fila se crea, existe en la base de datos y "
                "NO aparece en la pantalla de nadie sin permiso de organización",
                f"{modelo}.objects.create(..., {ctx.owner_field}=usuario)")


def rule_caducidad(ctx: Ctx) -> None:
    """be-model-caducidad-no-comprobada — el campo de caducidad que no lee nadie."""
    for campo, (modelo, fichero, ln) in sorted(ctx.expiry_fields.items()):
        if re.search(rf"\b{re.escape(campo)}\b", ctx.consumer_src):
            continue
        ctx.findings.append(Finding(
            "be-model-caducidad-no-comprobada", fichero, ln,
            f"`{modelo}.{campo}` se declara, se puede editar… y no lo lee ninguna vista, servicio, "
            "task ni middleware. Una caducidad que se ve en pantalla y no se aplica es peor que no "
            "tenerla: quien la configura se queda tranquilo",
            f"comprueba la fecha donde se decide el acceso, en UN sitio "
            f"(un decorador o un mixin), no copiada por vista"))


# ─────────────────────────────────────────────────────────────────────────────
# Reglas — tests
# ─────────────────────────────────────────────────────────────────────────────

DESCUBRIBLE_RE = re.compile(r"^(test.*|.*_test)$")


def rule_tests(tree: ast.AST, lines: list[str], p: Path, ctx: Ctx) -> None:
    tiene_tests = any(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                      and n.name.startswith("test") for n in ast.walk(tree))

    # be-test-stub-vacio — el andamio de `startapp` que cuenta como cobertura y no cubre nada
    if p.name == "tests.py" and not tiene_tests:
        if not any(isinstance(n, ast.ClassDef) for n in ast.walk(tree)):
            if not exempt(lines, 1, "be-test-stub-vacio"):
                ctx.add("be-test-stub-vacio", p, 1,
                        "`tests.py` vacío: es el andamio que genera `startapp`. Cualquier informe "
                        "automático cuenta esta app como testeada — el fichero existe, y esa cifra "
                        "es la que se mira para decidir dónde hace falta trabajo",
                        "bórralo (`git rm`). Cuando haya tests de verdad, `tests/` como paquete")
                return

    # be-test-descubrible — el test que el descubridor no encuentra no se ejecuta nunca
    if tiene_tests and not DESCUBRIBLE_RE.match(p.stem) and p.name != "conftest.py":
        if not exempt(lines, 1, "be-test-descubrible"):
            ctx.add("be-test-descubrible", p, 1,
                    f"`{p.name}` tiene funciones `test_…` pero su nombre no casa con el patrón de "
                    "descubrimiento (`test*.py` en Django, `test_*.py` / `*_test.py` en pytest) — "
                    "estos tests no se ejecutan NUNCA y nadie se entera, porque no fallan",
                    f"renómbralo a `test_{p.stem.replace('_tests', '').replace('tests_', '')}.py`")


def rule_databases(ctx: Ctx) -> None:
    """be-test-db-alias-sin-engine — `manage.py test` crea una BD por alias; sin ENGINE, no puede."""
    if not ctx.settings_src:
        return
    try:
        tree = ast.parse(ctx.settings_src)
    except SyntaxError:
        return
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(t, ast.Name) and t.id == "DATABASES" for t in node.targets):
            continue
        if not isinstance(node.value, ast.Dict):
            return
        for clave, valor in zip(node.value.keys, node.value.values):
            alias = str_const(clave) or "?"
            if not isinstance(valor, ast.Dict):
                continue
            claves = {str_const(k) for k in valor.keys}
            if "ENGINE" in claves:
                continue
            ctx.findings.append(Finding(
                "be-test-db-alias-sin-engine",
                os.path.relpath(ctx.settings_path, ctx.root), getattr(valor, "lineno", 1),
                f"el alias `{alias}` de DATABASES no declara ENGINE — `manage.py test` crea una "
                "base de datos de test POR ALIAS, así que con este ahí la suite entera no arranca "
                "y el fallo no dice que la causa sea la configuración",
                f'declara el ENGINE de `{alias}`, o sácalo de DATABASES si en realidad es un '
                "diccionario de conexión que lee otra librería"))


# ─────────────────────────────────────────────────────────────────────────────
# Reglas — observabilidad
# ─────────────────────────────────────────────────────────────────────────────

SALUD_RE = re.compile(r"health|healthz|readyz|livez|/status", re.I)


def _rutas_declaradas(src: str) -> list[str]:
    """Las rutas de verdad: el primer argumento de `path()`/`re_path()`/`url()`.

    A propósito NO se busca la palabra en el texto del fichero: un comentario que hable de la ruta
    de salud haría creer al checker que existe, y esta regla sirve justo para el proyecto donde se
    habló de ella y no se puso.
    """
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return []
    rutas = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and call_name(n).split(".")[-1] in ("path", "re_path", "url"):
            if n.args and (valor := str_const(n.args[0])) is not None:
                rutas.append(valor)
    return rutas


def rule_healthcheck(ctx: Ctx) -> None:
    if not ctx.urls_files:
        return
    if any(SALUD_RE.search(r) for _, src in ctx.urls_files for r in _rutas_declaradas(src)):
        return
    rel, _ = sorted(ctx.urls_files, key=lambda x: len(x[0]))[0]
    ctx.findings.append(Finding(
        "be-obs-healthcheck", rel, 1,
        "ninguna ruta de salud en todo el proyecto — sin un `/healthz` que responda 200, saber si "
        "el proceso está vivo exige que una persona lo mire; ni el balanceador, ni el "
        "`depends_on: service_healthy` del compose, ni una alerta pueden hacerlo solos",
        'path("healthz/", lambda r: JsonResponse({"ok": True})) — sin auth, sin tocar la BD'))


# ─────────────────────────────────────────────────────────────────────────────
# Reglas — celery
# ─────────────────────────────────────────────────────────────────────────────

ENQUEUE_RE = re.compile(r"\.(delay|apply_async)$")
NET_IO_RE = re.compile(r"(^|\.)(requests|httpx|urllib|boto3|stripe|openai)\.")
# Solo llamadas con el módulo delante (`requests.post`, `httpx.get`). Un `session.get(...)` sobre
# una Session con timeout por defecto NO se marca —sería un falso positivo— y, en el otro sentido,
# tampoco se caza. Es el precio de tener 0 falsos positivos aquí, y se dice en el documento.
HTTP_CALL_RE = re.compile(r"^(requests|httpx)\.(get|post|put|patch|delete|head|options|request)$")


def rule_http_timeout(tree: ast.AST, lines: list[str], p: Path, ctx: Ctx) -> None:
    """be-http-timeout — la comprobación de mayor valor para el trabajo nocturno.

    Sin `timeout=`, `requests` espera indefinidamente: la conexión colgada aparca el worker y, si
    hay un beat encolando cada pocos segundos, por la mañana hay miles de tareas apiladas y nadie
    enterado. En el backend de referencia: 37 de 39 llamadas sin timeout, y un script escrito a
    mano para purgar la cola que eso produjo.
    """
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not HTTP_CALL_RE.match(call_name(node)):
            continue
        if kw(node, "timeout") is not None:
            continue
        if exempt(lines, node.lineno, "be-http-timeout"):
            continue
        ctx.add("be-http-timeout", p, node.lineno,
                f"`{call_name(node)}(...)` sin `timeout=` — el default de requests es esperar para "
                "siempre. Un servicio que se degrada (no que caiga: que tarde) retiene este worker "
                "indefinidamente, y el síntoma que se ve fuera no es un error, es que 'la cola va lenta'",
                "requests.post(..., timeout=10) — un número, siempre, aunque sea generoso")


def rule_celery_calls(tree: ast.AST, lines: list[str], p: Path, ctx: Ctx) -> None:
    """be-celery-delay-en-transaccion: encolar dentro de atomic() sin on_commit."""
    atomic_bodies: list[ast.AST] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.With) or isinstance(node, ast.AsyncWith):
            for item in node.items:
                if "atomic" in call_name(item.context_expr):
                    atomic_bodies.append(node)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if any("atomic" in call_name(d) for d in node.decorator_list):
                atomic_bodies.append(node)

    protected: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and "on_commit" in call_name(node):
            for sub in ast.walk(node):
                protected.add(id(sub))

    seen: set[int] = set()
    for body in atomic_bodies:
        for node in ast.walk(body):
            if isinstance(node, ast.Call) and ENQUEUE_RE.search(call_name(node)):
                if id(node) in protected or id(node) in seen:
                    continue
                seen.add(id(node))
                if exempt(lines, node.lineno, "be-celery-delay-en-transaccion"):
                    continue
                ctx.add("be-celery-delay-en-transaccion", p, node.lineno,
                        f"`{call_name(node)}` se encola dentro de una transacción — el worker puede "
                        "coger la tarea antes del COMMIT y no encontrar la fila (o correrla aunque "
                        "la transacción acabe en rollback)",
                        "transaction.on_commit(lambda: tarea.delay(obj.pk))")


def rule_celery_tasks(tree: ast.AST, lines: list[str], p: Path, ctx: Ctx) -> None:
    for fn in [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]:
        decs = task_decorators(fn)
        if not decs:
            continue
        opts: dict[str, ast.AST] = {}
        for d in decs:
            if isinstance(d, ast.Call):
                for k in d.keywords:
                    if k.arg:
                        opts[k.arg] = k.value

        does_net_io = any(isinstance(n, ast.Call) and NET_IO_RE.search(call_name(n)) for n in ast.walk(fn))
        if does_net_io and "autoretry_for" not in opts:
            if not exempt(lines, fn.lineno, "be-celery-retry-io"):
                ctx.add("be-celery-retry-io", p, fn.lineno,
                        f"`{fn.name}` llama a un servicio de red y no declara autoretry_for — un "
                        "timeout puntual la pierde para siempre, sin rastro",
                        "@shared_task(autoretry_for=(RequestException,), retry_backoff=True, max_retries=5)")

        if is_true(opts.get("acks_late")):
            needle = fn.name
            if needle not in ctx.tests_src and not exempt(lines, fn.lineno, "be-celery-ackslate-idempotente"):
                ctx.add("be-celery-ackslate-idempotente", p, fn.lineno,
                        f"`{fn.name}` usa acks_late=True (se re-entrega si el worker muere) y no "
                        "aparece en ningún test — nadie ha demostrado que ejecutarla dos veces sea inocuo",
                        f"escribe test_{fn.name}_es_idempotente(): ejecútala dos veces y comprueba el mismo estado final")


# ─────────────────────────────────────────────────────────────────────────────
# Reglas — cache
# ─────────────────────────────────────────────────────────────────────────────

def rule_cache(tree: ast.AST, lines: list[str], p: Path, ctx: Ctx) -> None:
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        dotted = call_name(node)
        meth = dotted.split(".")[-1]
        if not dotted.startswith("cache.") and ".cache." not in f".{dotted}.":
            continue

        if meth in ("set", "get_or_set", "aset") and is_none(kw(node, "timeout")):
            if not exempt(lines, node.lineno, "be-cache-ttl-infinito"):
                ctx.add("be-cache-ttl-infinito", p, node.lineno,
                        "cache.set(..., timeout=None) — la clave no caduca nunca; si la invalidación "
                        "falla una vez, el dato viejo se queda hasta que alguien vacíe Redis a mano",
                        "pon un TTL explícito (timeout=300) aunque además invalides")

        if meth in ("set", "get", "get_or_set", "delete", "add"):
            key = node.args[0] if node.args else None
            if key is None:
                continue
            if isinstance(key, ast.JoinedStr):  # f-string suelta
                if not exempt(lines, node.lineno, "be-cache-key-helper"):
                    ctx.add("be-cache-key-helper", p, node.lineno,
                            f"clave de caché construida con una f-string en el punto de uso "
                            f"(`cache.{meth}`) — quien invalide desde otro módulo tiene que "
                            "reproducir el formato de memoria",
                            "def clave_x(pk): return f\"...\" — y úsala en set y en delete")
            if isinstance(key, ast.Call):
                helper = call_name(key)
                if meth in ("set", "get_or_set"):
                    ctx.cache_set_helpers.setdefault(helper, (os.path.relpath(p, ctx.root), node.lineno))
                if meth == "delete":
                    ctx.cache_del_helpers.add(helper)


# ─────────────────────────────────────────────────────────────────────────────
# Reglas — rabbitmq
# ─────────────────────────────────────────────────────────────────────────────

def rule_rabbitmq(tree: ast.AST, lines: list[str], p: Path, ctx: Ctx) -> None:
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and call_name(node).split(".")[-1] == "Queue":
            qargs = kw(node, "queue_arguments")
            dump = ast.dump(qargs) if qargs is not None else ""
            faltan = [k for k in ("x-dead-letter-exchange", "x-delivery-limit") if k not in dump]
            if faltan:
                if not exempt(lines, node.lineno, "be-mq-dlx"):
                    ctx.add("be-mq-dlx", p, node.lineno,
                            f"Queue sin {' ni '.join(faltan)} — los dos van juntos: sin límite de "
                            "entregas un mensaje que siempre falla gira para siempre y tapa el "
                            "resto del trabajo; con límite pero sin DLX, al superarlo se BORRA, "
                            "que es cambiar un bucle infinito por una pérdida silenciosa",
                            'queue_arguments={"x-dead-letter-exchange": "dlx", "x-delivery-limit": 5}')


# ─────────────────────────────────────────────────────────────────────────────
# Reglas — settings (cross-file, se evalúan una vez)
# ─────────────────────────────────────────────────────────────────────────────

SECRET_LITERAL_RE = re.compile(
    r"""^\s*(?:-\s*)?(?:['"]?)([A-Z0-9_]*(?:PASSWORD|SECRET|TOKEN|API_KEY|APIKEY|PRIVATE_KEY|"""
    r"""ACCESS_KEY|DSN)[A-Z0-9_]*)(?:['"]?)\s*[:=]\s*(.+?)\s*$""")
# Un valor que "parece plantilla" no es un secreto: interpolación, lectura de entorno o relleno
# evidente. Ojo: aquí NO puede ir la palabra "secret" a secas — casa dentro de contraseñas reales
# ("supersecreto123") y el checker se callaría justo en el caso que existe para cazar.
PLACEHOLDER_RE = re.compile(
    r"\$\{|\$[A-Z_]|env\(|environ|getenv|config\(|<[^>]*>|CHANGE|CHANGEME|REPLACE|"
    r"your[-_]|example|placeholder|xxx+|\.\.\.", re.I)
# `env(...)` pero también `env.bool(...)`, `env.list(...)`, `env.int(...)` — django-environ se usa
# casi siempre con el tipo, y sin esto las variables tipadas escapaban al check de documentación.
# ¿este proyecto usa DRF? Un import real o la app declarada en INSTALLED_APPS — NO la palabra
# suelta en un comentario, que armaría las reglas de DRF en un proyecto que solo las menciona.
DRF_PRESENT_RE = re.compile(r"""^\s*(?:from|import)\s+rest_framework|['"]rest_framework["'.]""",
                            re.M)
ENV_READ_RE = re.compile(
    r"""(?:env(?:\.\w+)?|os\.environ\.get|os\.getenv|config)\(\s*['"]([A-Z][A-Z0-9_]*)['"]"""
    r"""|os\.environ\[\s*['"]([A-Z][A-Z0-9_]*)['"]\s*\]""")


def rule_secret_literals(lines: list[str], p: Path, ctx: Ctx) -> None:
    for i, line in enumerate(lines, 1):
        if line.lstrip().startswith("#"):
            continue
        m = SECRET_LITERAL_RE.match(line)
        if not m:
            continue
        key, val = m.group(1), m.group(2).split("#")[0].strip()
        if not val or PLACEHOLDER_RE.search(val):
            continue
        if val.strip("'\"") in ("", "None", "null", "true", "false", "True", "False"):
            continue
        if not re.match(r"""^['"]?[\w\-./:@+=]{6,}['"]?$""", val):
            continue
        if exempt(lines, i, "be-env-secreto-literal"):
            continue
        ctx.add("be-env-secreto-literal", p, i,
                f"`{key}` tiene un valor literal en un fichero versionado — queda en el historial "
                "de git para siempre, aunque lo borres en el commit siguiente",
                f"{key}=${{{key}}} en compose · env(\"{key}\") en settings · el valor, en .env (gitignored)")


def rule_settings_globals(ctx: Ctx) -> None:
    """Reglas que se comprueban una sola vez sobre el settings del proyecto."""
    if not ctx.settings_src:
        return
    src, sp = ctx.settings_src, ctx.settings_path
    lines = src.splitlines()

    def missing(rule: str, needles: tuple[str, ...], msg: str, fix: str) -> None:
        if any(n in src for n in needles):
            return
        if any(EXEMPT_RE.search(l) and rule in l for l in lines):
            return
        ctx.add(rule, Path(sp), 1, msg, fix)

    # Las tres de abajo configuran DRF. En un backend que NO es DRF —Django server-rendered, que
    # es el otro arquetipo del patrón (`backend-formularios-django.md`)— no hay nada que
    # configurar: exigirlas ahí eran 3 hallazgos ACTIVOS pidiendo instalar un framework que el
    # proyecto no usa. Mismo gate que ya llevaban Celery y CACHES: se comprueba lo que existe.
    if ctx.uses_drf:
        missing("be-view-permisos-por-defecto", ("DEFAULT_PERMISSION_CLASSES",),
                "settings no define DEFAULT_PERMISSION_CLASSES — el default de DRF es AllowAny: "
                "cualquier ViewSet que olvide permission_classes queda abierto a internet",
                'REST_FRAMEWORK = {"DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"]}')
        missing("be-api-exception-handler", ("EXCEPTION_HANDLER",),
                "settings no define EXCEPTION_HANDLER — DRF devuelve DOS formas de error distintas "
                "({\"campo\": [...]} en validación, {\"detail\": ...} en auth/404/throttling) y el "
                "cliente que lea solo una se come la otra en silencio",
                'REST_FRAMEWORK["EXCEPTION_HANDLER"] = "config.exceptions.api_exception_handler" '
                '— contrato: 400 {"errors": {campo: [msg]}}')
        missing("be-view-paginacion", ("DEFAULT_PAGINATION_CLASS",),
                "settings no define DEFAULT_PAGINATION_CLASS — el primer list de una tabla grande "
                "serializa la tabla entera en memoria",
                'REST_FRAMEWORK = {"DEFAULT_PAGINATION_CLASS": "...PageNumberPagination", "PAGE_SIZE": 50}')
    if "CELERY" in src or "celery" in src:
        missing("be-celery-serializer-json", ("TASK_SERIALIZER", "task_serializer"),
                "Celery sin task_serializer='json' — con pickle un mensaje de la cola ejecuta "
                "código arbitrario, y además deja pasar objetos del ORM como argumento",
                'CELERY_TASK_SERIALIZER = "json"; CELERY_ACCEPT_CONTENT = ["json"]')
        missing("be-celery-timeouts", ("TIME_LIMIT", "time_limit"),
                "Celery sin task_time_limit/task_soft_time_limit — una task colgada retiene su "
                "worker indefinidamente y la cola deja de avanzar sin ningún error",
                "CELERY_TASK_SOFT_TIME_LIMIT = 300; CELERY_TASK_TIME_LIMIT = 360")
    missing("be-obs-logging", ("LOGGING",),
            "settings no define LOGGING — Django manda a consola y ahí muere: el error de las 4 de "
            "la mañana no queda en ningún fichero, no llega a ninguna alerta y por la mañana solo "
            "hay 'faltan datos' sin causa. No hay autonomía sin señal de vuelta",
            'LOGGING = {"version": 1, "handlers": {...fichero...}, "root": {"level": "INFO"}} '
            "— y un Sentry (o equivalente) para que el fallo te busque a ti")
    if "CACHES" in src:
        missing("be-cache-key-prefix", ("KEY_PREFIX",),
                "CACHES sin KEY_PREFIX — dos proyectos que compartan el Redis se pisan las claves "
                "y el bug aparece en el otro proyecto",
                'CACHES["default"]["KEY_PREFIX"] = "<slug-del-proyecto>"')


def rule_env_documented(ctx: Ctx) -> None:
    if not ctx.settings_src or not ctx.env_example_found:
        return
    read: set[str] = set()
    for m in ENV_READ_RE.finditer(ctx.settings_src):
        read.add(m.group(1) or m.group(2))
    missing = sorted(read - ctx.env_example_keys - {"DJANGO_SETTINGS_MODULE", "PATH", "PYTHONPATH"})
    for name in missing:
        ctx.add("be-env-documentado", Path(ctx.settings_path), 1,
                f"settings lee `{name}` y .env.example no lo documenta — quien clone el repo "
                "descubre que falta cuando el proceso ya ha arrancado a medias",
                f"añade `{name}=` (con un valor de ejemplo) a .env.example")


# ─────────────────────────────────────────────────────────────────────────────
# Reglas — docker-compose (line-based, sin dependencia de PyYAML)
# ─────────────────────────────────────────────────────────────────────────────

def rule_compose(lines: list[str], p: Path, ctx: Ctx) -> None:
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("#"):
            continue

        m = re.match(r"^-?\s*image:\s*['\"]?([^\s'\"]+)", stripped)
        if m:
            image = m.group(1)
            tag = image.rsplit(":", 1)[-1] if ":" in image.rsplit("/", 1)[-1] else ""
            if (not tag or tag == "latest") and not exempt(lines, i, "be-compose-tag-latest"):
                ctx.add("be-compose-tag-latest", p, i,
                        f"`{image}` sin versión fija — el mismo compose levanta una imagen distinta "
                        "cada semana y el 'a mí me funciona' deja de ser comprobable",
                        f"image: {image.split(':')[0]}:<version-exacta>")

        if re.match(r"^depends_on:\s*$", stripped) or re.match(r"^depends_on:\s*\[", stripped):
            block = "\n".join(lines[i:i + 12])
            short_form = bool(re.match(r"^depends_on:\s*\[", stripped)) or \
                re.match(r"^\s*-\s", lines[i] if i < len(lines) else "")
            if short_form and "service_healthy" not in block:
                if not exempt(lines, i, "be-compose-healthcheck"):
                    ctx.add("be-compose-healthcheck", p, i,
                            "depends_on en forma corta — solo espera a que el contenedor arranque, "
                            "no a que Postgres acepte conexiones: el backend muere en el primer boot",
                            "depends_on:\\n  db:\\n    condition: service_healthy  (+ healthcheck en db)")


# ─────────────────────────────────────────────────────────────────────────────
# Motor
# ─────────────────────────────────────────────────────────────────────────────

# `_fixtures/` contiene infracciones A PROPÓSITO (son el banco de pruebas del propio checker):
# si no se excluye del barrido normal, cada run del repo reporta 27 violaciones inventadas.
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", ".mypy_cache",
             ".pytest_cache", "site-packages", ".tox", "dist", "build", "_fixtures",
  # `resources` cubre `.docs/resources/` y `resources/`: ahi viven los CUERPOS DE
  # REFERENCIA vendorizados (codigo de terceros). Auditarlos produce cientos de
  # hallazgos sobre codigo que no es nuestro — y ensena a ignorar el comprobador.
             "resources"}


def repo_root() -> Path:
    try:
        out = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True,
                             text=True, check=True).stdout.strip()
        return Path(out)
    except Exception:
        return Path.cwd()


def changed_files(root: Path) -> list[Path]:
    cmds = [["git", "diff", "--name-only", "HEAD"],
            ["git", "diff", "--cached", "--name-only"],
            ["git", "ls-files", "--others", "--exclude-standard"]]
    names: set[str] = set()
    for c in cmds:
        try:
            r = subprocess.run(c, capture_output=True, text=True, cwd=root)
            names.update(x for x in r.stdout.splitlines() if x.strip())
        except Exception:
            pass
    return [root / n for n in sorted(names) if (root / n).is_file()]


def walk_repo(root: Path, skip: set[str] | None = None) -> list[Path]:
    skip = SKIP_DIRS if skip is None else skip
    out: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in skip]
        for fn in filenames:
            # `.html` entra solo para INDEXAR plantillas (be-tpl-ruta-duplicada): `check_file` las
            # descarta al primer if. Sin ellas en el universo no hay forma de ver la colisión.
            if fn.endswith((".py", ".yml", ".yaml", ".html")) or fn.startswith(".env"):
                out.append(Path(dirpath) / fn)
    return out


def gather_context(root: Path, ctx: Ctx, universe: list[Path]) -> None:
    """settings / .env.example / tests son cross-file: se leen del repo, no del diff."""
    for p in universe:
        kinds = classify(p)
        try:
            src = p.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        if "settings" in kinds and len(src) > len(ctx.settings_src):
            ctx.settings_src, ctx.settings_path = src, str(p)
        if DRF_PRESENT_RE.search(src):
            ctx.uses_drf = True
        if "forms" in kinds or "forms" in declared_layers(src):
            _collect_form_bases(p, src, ctx)
        # En TODOS los ficheros, no solo en los de formularios: los `form = <Clase>` viven en
        # `controller_settings.py`, que es otra capa. Acotarlo a `forms.py` no encontraría ninguno.
        _collect_forms_de_controller(src, ctx)
        if "env-example" in kinds:
            ctx.env_example_found = True
            for line in src.splitlines():
                m = re.match(r"^\s*#?\s*([A-Z][A-Z0-9_]*)\s*=", line)
                if m:
                    ctx.env_example_keys.add(m.group(1))
        if "tests" in kinds:
            ctx.tests_src += src
        _collect_estructura(p, src, ctx)
        if "models" in kinds:
            _collect_modelos(p, src, ctx)
        if p.suffix == ".py":
            # la vista base de casa puede vivir en `core/views.py`, en `core/api.py` o en
            # `common/mixins.py`: la busca por CONTENIDO en cualquier módulo compartido
            _collect_vistas(p, src, ctx)
        # Las capas que CONSUMEN el modelo. Se acumulan aparte para poder preguntar "¿alguien lee
        # este campo?" — la declaración en models.py y su eco en el formulario no cuentan como
        # lectura: la pregunta es si alguien DECIDE algo con él.
        if p.suffix == ".py" and not (kinds & {"models", "forms", "serializers", "migration"}):
            ctx.consumer_src += src
    resolve_form_family(ctx)
    resolve_descubrimiento(ctx)


TECHO_LINEAS = 600
# 600 no es un número redondo elegido a ojo: se midió la distribución del repo de referencia
# (275 módulos, mediana 134 líneas) y 600 es el punto donde la regla marca ~20 ficheros — por
# debajo del umbral de inversión de patterns/README.md §2, o sea congelable. Con 400 marcaría 47
# y la regla se caería sola por ruido; con 1000 dejaría fuera media docena de módulos que sí
# duelen. Ajústalo por proyecto midiendo, no copiando.
# Exentos: lo que no es código de dominio. `.claude/` es herramienta del harness —los propios
# comprobadores pasan de 1.500 líneas— y marcarla convierte la regla en ruido sobre sí misma.
_EXENTOS_TECHO = ("migrations/", "/tests/", "test_", "conftest", ".claude/", "node_modules/")


def rule_techo_lineas(lines, p: Path, ctx: Ctx) -> None:
    """be-techo-lineas — la regla que al backend le faltaba y al frontend no.

    El comprobador de frontend tiene `fe-techo-200-lineas` desde el principio; el de backend tenía
    54 reglas y NINGUNA de tamaño. Esa asimetría dejaba fuera del radar los módulos más peligrosos
    de un proyecto real: tres ficheros de 3.600-4.600 líneas donde vivía un bucle infinito que
    costaba del orden de 100-250 USD/día y que nadie vio porque nadie tiene 4.000 líneas en la
    cabeza.

    Nace en SOMBRA a propósito: mide y no bloquea. Activarla de golpe en un repo existente produce
    el rechazo que `rules/refactor-progresivo.md` §0 describe.

    Y el matiz que evita el falso positivo caro: **el tamaño es un síntoma, no el defecto**. Un
    fichero grande con fan-in bajo (nadie lo importa) es barato de partir; uno pequeño con fan-in
    alto es el que hay que tocar con cuidado. Por eso el mensaje manda a mirar el grafo antes de
    tocar nada, en vez de decir "pártelo".
    """
    n = len(lines)
    if n <= TECHO_LINEAS:
        return
    rel = os.path.relpath(p, ctx.root).replace(os.sep, "/")
    if any(x in rel for x in _EXENTOS_TECHO) or p.stem.startswith("test"):
        return
    if exempt(lines, 1, "be-techo-lineas"):
        return
    ctx.add("be-techo-lineas", p, 1,
            f"`{rel}` tiene {n} líneas (techo {TECHO_LINEAS}): nadie lo tiene entero en la cabeza, "
            "y ahí es donde se esconden los bugs que ninguna review ve",
            "Mira primero su fan-in en el grafo (`/code-graph`): si casi nadie lo importa, partirlo "
            "por responsabilidad es de bajo riesgo. Si tiene fan-in alto, escribe la red antes "
            "(rules/refactor-progresivo.md fase 1) · o `# pattern-exempt: be-techo-lineas — razón`")


def check_file(p: Path, ctx: Ctx) -> None:
    kinds = classify(p)
    try:
        src = p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return
    lines = src.splitlines()
    # El nombre del fichero es el default; `# pattern-layer: <capa>` es la declaración explícita
    # para el proyecto que llamó a su capa de otra manera (EVO-4).
    kinds |= declared_layers(src)

    if "compose" in kinds:
        rule_compose(lines, p, ctx)
        rule_secret_literals(lines, p, ctx)
        return
    if p.suffix not in (".py",):
        return
    if "settings" in kinds:
        rule_secret_literals(lines, p, ctx)
    try:
        with warnings.catch_warnings():
            # parsear código ajeno no debe ensuciar la salida con sus SyntaxWarning
            warnings.simplefilter("ignore")
            tree = ast.parse(src, filename=str(p))
    except SyntaxError:
        return

    rule_mongo(lines, p, ctx)
    rule_techo_lineas(lines, p, ctx)
    if "migration" in kinds:
        rule_migration(tree, lines, p, ctx)
        return
    if "models" in kinds:
        rule_models(tree, lines, p, ctx)
    if "serializers" in kinds:
        rule_serializers(tree, lines, p, ctx)
    if "views" in kinds:
        rule_views(tree, lines, p, ctx)
    rule_http_contract(tree, lines, p, ctx)
    if "services" in kinds:
        rule_services(tree, lines, p, ctx)
    if "forms" in kinds:
        rule_forms(tree, lines, p, ctx)
    elif "tests" not in kinds and "migration" not in kinds:
        rule_form_class_placement(tree, lines, p, ctx)
    if "tasks" in kinds:
        rule_celery_tasks(tree, lines, p, ctx)
    if "signals" in kinds:
        rule_signals(tree, lines, p, ctx)
    rule_tests(tree, lines, p, ctx)
    if "command" in kinds:
        rule_command_full_clean(tree, lines, p, ctx)
    if "tests" not in kinds:
        rule_celery_calls(tree, lines, p, ctx)
        rule_cache(tree, lines, p, ctx)
        rule_form_calls(tree, lines, p, ctx)
        rule_http_timeout(tree, lines, p, ctx)
        rule_capas(tree, lines, p, ctx)
        rule_monkeypatch(tree, lines, p, ctx)
        rule_script_suelto(src, lines, p, ctx)
        if not (kinds & {"forms", "serializers", "migration"}):
            rule_owner(tree, lines, p, ctx)
            rule_bulk_create(tree, lines, p, ctx)
    if "settings" in kinds or "tasks" in kinds:
        rule_rabbitmq(tree, lines, p, ctx)


def finalize(ctx: Ctx) -> None:
    rule_settings_globals(ctx)
    rule_env_documented(ctx)
    # Reglas de PROYECTO: no juzgan un fichero, juzgan el conjunto. Se calculan sobre el universo
    # (no sobre el diff), porque desde dos ficheros cambiados no se puede afirmar que dos apps
    # sirven la misma plantilla ni que nadie lee un campo.
    rule_templates(ctx)
    rule_caducidad(ctx)
    rule_databases(ctx)
    rule_healthcheck(ctx)
    for helper, (path, line) in ctx.cache_set_helpers.items():
        if helper not in ctx.cache_del_helpers:
            ctx.findings.append(Finding(
                "be-cache-sin-invalidacion", path, line,
                f"`{helper}()` se usa para escribir en caché y nunca para borrar — el dato solo "
                "se corrige cuando expira el TTL",
                f"añade la invalidación: cache.delete({helper}(...)) donde cambie el dato"))


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="*", help="ficheros o directorios (default: cambiados vs git)")
    ap.add_argument("--all", action="store_true", help="escanear el repo entero")
    ap.add_argument("--json", action="store_true", help="salida JSON")
    ap.add_argument("--list", action="store_true", help="listar las reglas y su estado")
    ap.add_argument("--rules", default="", help="subconjunto de reglas, separadas por coma")
    ap.add_argument("--self-test", action="store_true", help="verificar el checker contra _fixtures/")
    args = ap.parse_args(argv)

    if args.list:
        width = max(len(k) for k in RULES)
        print(f"{'id'.ljust(width)}  {'estado'.ljust(7)} {'capa'.ljust(11)} enunciado")
        for rid, meta in RULES.items():
            print(f"{rid.ljust(width)}  {meta['estado'].ljust(7)} {meta['capa'].ljust(11)} {meta['enunciado']}")
        return 0

    root = repo_root()
    if args.self_test:
        return self_test(root)

    universe = walk_repo(root)
    if args.all:
        targets = universe
    elif args.paths:
        targets = []
        for raw in args.paths:
            p = Path(raw)
            if not p.is_absolute():
                p = (Path.cwd() / p).resolve()
            targets.extend([q for q in walk_repo(p)] if p.is_dir() else ([p] if p.is_file() else []))
    else:
        targets = changed_files(root)

    ctx = Ctx(root=root)
    gather_context(root, ctx, universe)
    for p in targets:
        check_file(p, ctx)
    finalize(ctx)

    only = {r.strip() for r in args.rules.split(",") if r.strip()}
    findings = [f for f in ctx.findings if not only or f.rule in only]
    findings.sort(key=lambda f: (f.path, f.line))

    if args.json:
        print(json.dumps([dict(rule=f.rule, estado=f.estado, path=f.path, line=f.line,
                               msg=f.msg, fix=f.fix, doc=RULES[f.rule]["doc"],
                               capa=RULES[f.rule]["capa"]) for f in findings],
                         indent=2, ensure_ascii=False))
        return 1 if any(f.estado in BLOCKING for f in findings) else 0

    visible = [f for f in findings if f.estado not in QUIET or args.all]
    if not targets:
        # `--json` tiene que emitir JSON SIEMPRE, tambien cuando no hay nada que mirar:
        # una linea de texto plano aqui rompe la tuberia
        #   comprobador --json | pattern_baseline.py check --from -
        # y el que la monta lo descubre en produccion, no aqui.
        if getattr(args, "json", False):
            print("[]")
        else:
            print("pattern-check-backend: sin ficheros que comprobar")
        return 0
    for f in visible:
        print(f.render())

    blocking = [f for f in findings if f.estado in BLOCKING]
    warns = [f for f in findings if f.estado == "debil"]
    print()
    if blocking:
        print(f"pattern-check-backend: {len(blocking)} violación(es) de patrones ACTIVOS "
              f"— el porqué de cada una, en .claude/patterns/stack/<doc>.md")
        return 1
    if warns:
        print(f"pattern-check-backend: {len(warns)} aviso(s) de patrones débiles (no bloquean)")
    print("pattern-check-backend: OK")
    return 0


# ─────────────────────────────────────────────────────────────────────────────
# Self-test — la regla 3 del README: FPR sobre ficheros conformes antes de activar
# ─────────────────────────────────────────────────────────────────────────────

def _run_fixture(root: Path) -> tuple[list[Finding], list[Path]]:
    ctx = Ctx(root=root)
    universe = walk_repo(root, skip=SKIP_DIRS - {"_fixtures"})
    gather_context(root, ctx, universe)
    for p in universe:
        check_file(p, ctx)
    finalize(ctx)
    ctx.findings.sort(key=lambda f: (f.path, f.line))
    return ctx.findings, universe


# Reglas de UMBRAL: no se verifican con un fixture, y no por descuido.
#
# `be-techo-lineas` marca ficheros de más de 600 líneas. El fixture infractor más grande tiene 47,
# así que la regla NO PUEDE disparar ahí por construcción — y el self-test la contaba como "no
# dispara" y salía FALLA. Meter un fichero de 601 líneas en el repo para contentar al test sería
# engordar el repo para siempre a cambio de nada.
#
# Se verifican SINTÉTICAMENTE, y sale mejor que con fixture: se comprueba que dispara justo por
# encima del umbral y que **NO** dispara justo por debajo. Eso segundo es el control negativo
# (`skills/code-review-gate` §7): un test que solo puede pasar no demuestra nada, y sin él una
# regla rota "hacia arriba" —que marcara siempre— pasaría igual.
UMBRAL_SINTETICO = {
    "be-techo-lineas": (TECHO_LINEAS + 1, TECHO_LINEAS - 1),
}


def _self_test_umbral(rid: str, dispara: int, no_dispara: int) -> bool:
    """Comprueba una regla de umbral por encima y por debajo. Devuelve True si se comporta."""
    import shutil
    import tempfile
    ok = True
    tmp = Path(tempfile.mkdtemp(prefix="pcb-umbral-"))
    try:
        for n, debe_disparar in ((dispara, True), (no_dispara, False)):
            caso = tmp / f"n{n}"
            (caso / "expedientes").mkdir(parents=True)
            (caso / "expedientes" / "models.py").write_text(
                "\n".join(f"# linea {i}" for i in range(n)) + "\n", encoding="utf-8")
            hallazgos, _ = _run_fixture(caso)
            disparo = any(f.rule == rid for f in hallazgos)
            if disparo is not debe_disparar:
                verbo = "NO dispara y debería" if debe_disparar else "dispara y NO debería"
                print(f"   UMBRAL → {rid} con {n} líneas: {verbo}")
                ok = False
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return ok


def self_test(root: Path) -> int:
    """Cada VARIANTE de layout es un fixture aparte, con su propio contexto.

    `conforme/` es el layout del template (apps/, settings partido, DRF); `conforme-plano/` es el
    otro layout válido (apps hermanas planas, settings.py único, Django server-rendered). Los dos
    deben puntuar 0: ese par ES la comprobación de que ninguno de los dos es obligatorio (EVO-4/A6).
    """
    fx = Path(__file__).parent / "_fixtures"
    if not fx.is_dir():
        print(f"self-test: falta {fx}")
        return 1
    ok = True

    conformes = sorted(d for d in fx.iterdir() if d.is_dir() and d.name.startswith("conforme"))
    infractores = sorted(d for d in fx.iterdir() if d.is_dir() and d.name.startswith("infractor"))
    if not conformes or not infractores:
        print("self-test: faltan fixtures conforme/ o infractor/")
        return 1

    for d in conformes:
        findings, universe = _run_fixture(d)
        print(f"── FPR [{d.name}]: {len(findings)} hallazgo(s) sobre {len(universe)} ficheros "
              f"CONFORMES (objetivo: 0 — README regla 3)")
        for f in findings:
            print("   FALSO POSITIVO →", f.render())
            ok = False

    fired: set[str] = set()
    for d in infractores:
        findings, _ = _run_fixture(d)
        propias = {f.rule for f in findings}
        fired |= propias
        print(f"── Sensibilidad [{d.name}]: {len(propias)} regla(s) disparan")

    # Las de umbral se sacan del recuento por fixture: allí no pueden disparar (ver
    # UMBRAL_SINTETICO). No quedan sin verificar — se verifican justo debajo, y más fuerte.
    expected = set(RULES) - set(UMBRAL_SINTETICO)
    missing = sorted(expected - fired)
    print(f"── Sensibilidad TOTAL: {len(fired & expected)}/{len(expected)} reglas disparan sobre "
          f"los fixtures INFRACTORES")
    for rid in missing:
        print(f"   NO DISPARA → {rid} ({RULES[rid]['enunciado']})")
        ok = False

    print(f"── Umbral (sintético, con control negativo): {len(UMBRAL_SINTETICO)} regla(s)")
    for rid, (dispara, no_dispara) in UMBRAL_SINTETICO.items():
        if _self_test_umbral(rid, dispara, no_dispara):
            print(f"   OK → {rid}: dispara con {dispara} líneas y NO con {no_dispara}")
        else:
            ok = False

    print()
    print("self-test:", "OK" if ok else "FALLA")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
