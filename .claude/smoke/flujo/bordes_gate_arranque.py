#!/usr/bin/env python3
"""Los bordes que sacaron los auditores de la 2.17 contra `gate_arranque.py`, uno por línea.

    python3 bordes_gate_arranque.py <dir con gate_arranque.py>

Sale con 1 si alguno no da lo esperado. Cubre el stack elegido (`_extra('stack_completo')`), la
firma (`revisa_firma`) y quién es un agente (`es_agente`). Lo corre `correr.sh` (caso B-01), así
que apagar cualquiera de esos mecanismos pone el smoke en rojo.
"""
import datetime
import importlib.util
import pathlib
import sys

d = pathlib.Path(sys.argv[1]).resolve()
sys.path.insert(0, str(d))
spec = importlib.util.spec_from_file_location("ga", d / "gate_arranque.py")
ga = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ga)

STACK = [  # (texto del 05-stack, ¿cumple?)
    ("Python con Django, PostgreSQL y Docker en un VPS.", True),
    ("Python3 con Django y SQLite3, Docker en un VPS.", True),
    ("Python con Django, Postgres16 y Docker en un VPS.", True),
    ("Node20 con Vue3, MySQL y Docker en un VPS.", True),
    ("## Decisión y alternativas\nPython con Django, PostgreSQL y Docker en un VPS.", True),
    ("## Stack elegido y alternativas descartadas\nPython con Django, PostgreSQL y Docker.", True),
    ("Python con Django, una base de datos no relacional MongoDB y Docker.", True),
    ("Python con Django. En lugar de MongoDB usamos PostgreSQL. Docker en un VPS.", True),
    ("Python con Django. Base de datos: PostgreSQL (descartados MySQL y MongoDB). Docker.", True),
    ("Python. En vez de React elegimos Vue. PostgreSQL. Docker.", True),
    ("Python con Django y PostgreSQL. Desplegado sin Docker en Coolify.", True),
    ("Python con Django, sin base de datos, desplegado con Docker en un VPS.", True),
    # segunda pasada del verificador
    ("| Pieza | Decisión (vs. alternativas) |\n|---|---|\n"
     "| Todo | Python, Django, PostgreSQL, Docker |",
     True),
    ("| Pieza | Elección frente a alternativas |\n|---|---|\n| Todo | Python, Django, MySQL, VPS |",
     True),
    ("## Alternativas y decisión final\nPython con Django, PostgreSQL y Docker en un VPS.", True),
    # tercera pasada (M-1): lo descartado sale hasta el final de SU cláusula, no la línea entera
    ("Python con Django y Docker.\nEn lugar de MongoDB usamos PostgreSQL.", True),
    ("Python con Django y Docker.\nEn vez de Mongo, Postgres.", True),
    ("Python con Django y Docker.\nDescartado MongoDB; usamos PostgreSQL.", True),
    ("Python con Django y Docker.\nDescartado MongoDB, elegimos PostgreSQL.", True),
    ("Python con Django y Docker.\nRechazadas MongoDB y MySQL. Base: SQLite.", True),
    ("Python con Django y Docker.\n- Descartados: MongoDB, MySQL. Elegida: PostgreSQL 16.", True),
    ("Python con Django y Docker.\nAlternativas y decisión final: PostgreSQL.", True),
    # tercera pasada (M-2): controles que la negación nueva no puede comerse
    ("Python con Django y Docker. Usaremos Mongo, no Postgres.", True),
    ("Python con Django y Docker. No usamos Postgres, usamos Mongo.", True),
    ("Python con Django y Docker. No hay duda: PostgreSQL.", True),
    ("Python con Django y Docker. Se ha descartado usar MongoDB; usamos PostgreSQL.", True),
    ("Python con Django y Docker. PostgreSQL fuera de Docker, en el host.", True),
    ("Python con Django, PostgreSQL y Docker, descartado Kubernetes.", True),
    ("Python con Django, PostgreSQL y Redis. Docker. MongoDB descartado.", True),
    ("Python con Django y Docker. PostgreSQL. No usamos MongoDB.", True),
    ("Python con Django y Docker. Base: PostgreSQL. Descartado todo lo demás.", True),
    ("Python con Django, PostgreSQL y Docker, queda fuera Kubernetes.", True),
    ("Python con Django y Docker. PostgreSQL y SQLite, descartado por lento.", True),
    ("Python con Django, Docker y PostgreSQL, no usamos nada más.", True),
    ("Python con Django y Docker. Se descartan por coste MongoDB y MySQL; base: PostgreSQL.", True),
    # verificador de M-1/M-2 (tercera pasada): sus regresiones (R1, R2) y los huecos que señaló
    ("Python con Django y Docker.\nRechazado: Kubernetes. PostgreSQL en Docker.", True),
    ("Python con Django y Docker.\nDescartado MongoDB (no encaja con el modelo); PostgreSQL"
     " 16.2.", True),
    ("Python con Django y Docker.\nDescartadas: MongoDB; MySQL, usamos PostgreSQL.", True),
    ("Python con Django y Docker. Elegidas: PostgreSQL y Redis, MongoDB y MySQL"
     " descartadas.", True),
    ("Python con Django, PostgreSQL y Docker, MongoDB y MySQL descartadas.", True),
    ("Python con django y docker. postgres y redis, descartados mongo y mysql.", True),
    ("Python con Django, PostgreSQL y Docker, descartado kubernetes por complejo.", True),
    ("Python con Django y Docker.\nDescartado Mongo: usaremos PostgreSQL.", True),
    ("Python con Django y Docker.\nDescartado MongoDB — usamos PostgreSQL.", True),
    ("Python con Django y Docker.\nDescartado MongoDB, se usa PostgreSQL.", True),
    ("Python con Django y Docker.\nDescartados MongoDB y MySQL y nos quedamos con"
     " PostgreSQL.", True),
    ("Python con Django y Docker.\n(Descartado MongoDB) PostgreSQL 16.", True),
    ("Python con Django y Docker. Base: PostgreSQL, descartado el resto.", True),
    # segundo verificador de M-1/M-2: palabras partidas (H3), la coma tras «no» (H2), «así que»
    ("Python con Django y Docker. MongoDB descartado, PostgreSQL elegido.", True),
    ("Node, Express, PostgreSQL y Docker en un VPS.", True),
    ("Python con Django y Docker. No hay MongoDB, PostgreSQL sí.", True),
    ("Python, PostgreSQL y Docker. No usamos React, Django con plantillas.", True),
    ("Python con Django y Docker.\nDescartado MongoDB por el coste, así que usamos PostgreSQL.",
     True),
    # tercer verificador: «; usamos» cierra la lista, el participio pospuesto, la lista ya cerrada
    ("Python con Django y Docker.\nRechazadas: MongoDB y MySQL; usamos PostgreSQL.", True),
    ("Python con Django y Docker. MongoDB y MySQL descartadas: PostgreSQL.", True),
    ("Python con Django y Docker. MongoDB no se usa: PostgreSQL basta.", True),
    ("Python con Django y Docker. Sin MongoDB ni MySQL, PostgreSQL y Redis.", True),
    ("Python con Django y Docker.\nDescartado MongoDB, la base es PostgreSQL.", True),
    ("Python con Django y Docker.\n**Descartadas:**\n- MongoDB (esquema libre)\n- MySQL (licencia)"
     "\n\nBase: PostgreSQL 16.", True),
    ("Python con Django y Docker. Base de datos: PostgreSQL, pendiente de migrar a la 16.", True),
    # Y lo que tiene que seguir fallando
    ("Python con Django, desplegado en un VPS con Docker. Única, sin Mongo.", False),
    ("Python con Django y Docker. MongoDB (descartado).", False),
    ("Python con Django y Docker. MongoDB, descartado por coste.", False),
    ("Python con Django y Docker. ~~PostgreSQL~~", False),
    ("Python con Django y Docker.\n## Alternativas\nPostgreSQL o MySQL.", False),
    ("Python con Django y Docker.\n- Descartado: MongoDB", False),
    ("Python con Django y Docker.\n- Alternativas miradas: MongoDB, MySQL", False),
    ("Python con Django y Docker. No usamos MongoDB.", False),
    ("Python con Django y Docker.\n## Opciones descartadas\n- MongoDB, por el esquema.", False),
    ("Python con Django y Docker.\n## Por qué descartamos MongoDB\n"
     "MongoDB obliga a duplicar el esquema.",
     False),
    ("Python con Django y Docker. MongoDB quedó descartada por el coste.", False),
    ("Python con Django y Docker. Base de datos: por decidir (MongoDB o MySQL).", False),
    ("Python con Django y Docker. Descartamos MySQL y MongoDB.", False),
    ("Framework Django, base de datos Postgres, desplegado en un VPS con Docker.",
     False),  # sin lenguaje
    # tercera pasada (M-1): la cláusula descartada sale entera, con versiones y paréntesis dentro
    ("Python con Django y Docker.\nDescartados: MongoDB (por el esquema), MySQL.", False),
    ("Python con Django y Docker.\nAlternativas: PostgreSQL 16.2 o MySQL 8.0", False),
    # tercera pasada (M-2): la negación detrás de una lista, y las formas que no se veían
    ("Python con Django y Docker. MongoDB y MySQL descartados.", False),
    ("Python con Django y Docker. MongoDB, MySQL y SQLite: descartados.", False),
    ("Python con Django y Docker. MongoDB y MySQL quedaron descartados.", False),
    ("Python con Django y Docker. MongoDB y MySQL, descartadas.", False),
    ("Python con Django y Docker. MongoDB y MySQL se descartan.", False),
    ("Python con Django y Docker. Se ha descartado usar MongoDB.", False),
    ("Python con Django y Docker. Descartamos usar MongoDB.", False),
    ("Python con Django y Docker. No se usará MongoDB.", False),
    ("Python con Django y Docker. MongoDB no se usa.", False),
    ("Python con Django y Docker. No hay MongoDB.", False),
    ("Python con Django y Docker. No necesitamos MongoDB.", False),
    ("Python con Django y Docker. MongoDB queda fuera.", False),
    ("Python con Django y Docker. MongoDB (no)", False),
    # verificador de M-1/M-2: la lista de descartes con «;» (R1) y las formas que faltaban
    ("Python con Django y Docker.\nDescartadas: MongoDB por el esquema libre; MySQL por la"
     " licencia.", False),
    ("Python con Django y Docker.\n- Descartados: MongoDB (sin transacciones); MySQL"
     " (licencia).", False),
    ("Python con Django y Docker.\nDescartadas: MongoDB por el esquema; MySQL por la licencia;"
     " Docker elegido para desplegar.", False),
    ("Python con Django y Docker. MongoDB y MySQL, ambas descartadas.", False),
    ("Python con Django y Docker. MongoDB y MySQL se han descartado.", False),
    ("Python con Django y Docker. MongoDB y MySQL han quedado descartados.", False),
    ("Python con Django y Docker. MongoDB no lo usaremos.", False),
    ("Python con Django y Docker. MongoDB no es una opción.", False),
    # segundo verificador: la lista con «;» que se escapaba (H1) y las formas que faltaban (H4, H5)
    ("Python con Django y Docker.\nDescartadas: MongoDB por el esquema libre; también MySQL, por"
     " la licencia.", False),
    ("Python con Django y Docker.\nRechazadas: 1) MongoDB, por el esquema; 2) MySQL, por la"
     " licencia.", False),
    ("Python con Django y Docker.\nDescartado MongoDB por el esquema; también MySQL por la"
     " licencia.", False),
    ("Python con Django y Docker.\nDescartado MongoDB, tenemos malas experiencias, y MySQL por la"
     " licencia.", False),
    ("Python con Django y Docker. MongoDB y MySQL no son una opción.", False),
    ("Python con Django y Docker. MySQL y MongoDB han quedado fuera.", False),
    ("Python con Django y Docker. MongoDB no se va a usar.", False),
    ("Python con Django y Docker. Base de datos: por decidir entre PostgreSQL y MySQL.", False),
    ("Python con Django y Docker. Base de datos: aún no hemos decidido entre PostgreSQL y MySQL.",
     False),
    # tercer verificador: la lista en plural sin «:», «Descartamos…», la base sin decidir dicha de
    # otras formas, las viñetas bajo «Descartadas:»
    ("Python con Django y Docker.\nDescartados MongoDB, por el esquema; MySQL, por la licencia.",
     False),
    ("Python con Django y Docker.\nDescartamos MongoDB por el esquema libre y MySQL por la"
     " licencia.", False),
    ("Python con Django y Docker. Base de datos: por definir (PostgreSQL o MySQL).", False),
    ("Python con Django y Docker. Base de datos: PostgreSQL o MySQL, a decidir en la fase 2.",
     False),
    ("Python con Django y Docker. Base de datos: PostgreSQL o MySQL (pendiente).", False),
    ("Python con Django y Docker. Dudamos entre PostgreSQL y MySQL.", False),
    ("Python con Django y Docker. Aún no hemos elegido base de datos: PostgreSQL o MySQL.", False),
    ("Python con Django y Docker.\nBase de datos: por decidir.\nDescartadas:\n- MongoDB, por el"
     " esquema libre.\n- MySQL, por la licencia.", False),
    ("Python con Django y Docker. MongoDB y MySQL ya no son una opción.", False),
    ("Python con Django y Docker. Mongo no hace falta.", False),
    ("Python con Django y Docker. Quedan fuera MongoDB y MySQL.", False),
]
AGENTE = [  # (firma, ¿es un agente?)
    ("Ana Ruiz", False), ("A", False), ("Miller", False), ("Usuario", False),
    ("Usuario — confirmó por tandas el 29-sep", False),
    ("Usuario, sobre el borrador del agente", False),
    ("Usuario (Proxera) — entrevista con Claude del 2026-09-16", False),
    ("Miller (revisión con el agente de stack)", False),
    ("Ana Ruiz, Tech Lead de Proxera, con ayuda de Claude", False),
    ("Claude Martin", False), ("Bot García", False),
    ("Miller en la sesión del 2 de octubre", False), ("Miller tras la sesión de trabajo", False),
    ("Tech Lead (agente) · borrador para que lo confirme el Usuario", True),
    ("Tech Lead (sesión tech-lead-template)", True), ("Tech Lead", True), ("TL", True),
    ("el agente de stack", True), ("IA", True), ("Claude", True), ("Claude Opus 5.5", True),
    ("claude-opus-5-5", True), ("sofia-pentester", True), ("GPT-5", True), ("Claude Fable", True),
    ("directora `elvion-platform-consolidation` (en modo yolo)", True),
    ("la directora elvion-platform-consolidation", True), ("Revisión automática", True),
    ("Generado automáticamente", True), ("Mistral Large", True),
    # tercera pasada: un nombre de pila delante de «Claude» es una persona (m-5); el modelo a secas
    # y el «;» como corte de la cabeza tenían mutantes vivos (m-6)
    ("Jean Claude", False), ("Jean-Claude Pérez", False), ("Anne Claude, revisora", False),
    ("Revisado por Claude", True), ("Asistente Claude", True), ("Por Claude", True),
    ("Opus 4", True), ("Sonnet 4.5", True), ("Haiku", True),
    ("Ana Ruiz; borrador del agente", False),
]
FIRMA = [  # (frontmatter sin las ---, ¿firmado?)
    ("reviewed: 2026-01-01\nreviewed_by: Ana Ruiz", True),
    ("reviewed: 2026-10-01T10:00\nreviewed_by: Ana Ruiz", True),
    ("reviewed: 2026-01-01\nreviewed_by:\n  - Ana Ruiz", True),
    ("reviewed: 2026-01-01\nreviewed_by:\n  Ana Ruiz, en la entrevista", True),
    ('reviewed: 2026-01-01\nreviewed_by: "Ana #2 Ruiz"', True),
    ("reviewed: 2026-01-01\nreviewed_by: Ana Ruiz   # comentario en línea", True),
    ("autor: Ana Ruiz\nrevisado: 2026-01-01", True),
    ("reviewed: 2026-01-01\nreviewed_by:", False),
    ("reviewed: 2026-13-45\nreviewed_by: Ana Ruiz", False),
    ("reviewed: 2026-02-30\nreviewed_by: Ana Ruiz", False),
    ("reviewed: 2099-01-01\nreviewed_by: Ana Ruiz", False),
    ("reviewed: 2026-01-01\nreviewed_by: pendiente de firmar", False),
    ("reviewed: 2026-01-01\nreviewed_by: —", False),
    ("reviewed: 2026-01-01\nreviewed_by: null", False),
    ("reviewed: 2026-01-01\nreviewed_by: n/a", False),
    ("reviewed: 2026-01-01", False),                       # sin clave de firmante
    ("reviewed: mañana\nreviewed_by: Ana Ruiz", False),    # una fecha que no es fecha
    (f"reviewed: {datetime.date.today().isoformat()}\nreviewed_by: Ana Ruiz", True),  # hoy vale
    ('autor: "Tech Lead (agente)"\nrevisado: 2026-01-01', False),
]
VALOR = [  # (frontmatter, firmante que se tiene que leer)
    ('reviewed: 2026-01-01\nreviewed_by: "Ana #2 Ruiz"', "Ana #2 Ruiz"),
    ("reviewed: 2026-01-01\nreviewed_by: Ana Ruiz   # comentario en línea", "Ana Ruiz"),
    ("reviewed: 2026-01-01\nreviewed_by:\n  - Ana Ruiz", "Ana Ruiz"),
]
malos = 0
for txt, esperado in STACK:
    est, det = ga._extra("stack_completo", txt + "\n", "05-stack.md")
    ok = (est == ga.CUMPLE) == esperado
    malos += not ok
    marca = "✓" if ok else "✗"
    print(f"{marca} stack  {'cumple' if esperado else 'falla '}  {txt[:70]!r}  → {est}")
for firma, esperado in AGENTE:
    ok = ga.es_agente(firma) == esperado
    malos += not ok
    print(f"{'✓' if ok else '✗'} agente {'sí' if esperado else 'no'}      {firma!r}")
for fm, esperado in FIRMA:
    motivo, _ = ga.revisa_firma(f"---\n{fm}\n---\n# Doc\n")
    ok = (motivo is None) == esperado
    malos += not ok
    marca = "✓" if ok else "✗"
    print(f"{marca} firma  {'vale' if esperado else 'no  '}    {fm!r}  → {motivo or 'firmado'}")
for fm, esperado in VALOR:
    _, medido = ga.revisa_firma(f"---\n{fm}\n---\n# Doc\n")
    ok = medido.get("reviewed_by") == esperado
    malos += not ok
    print(f"{'✓' if ok else '✗'} valor  {esperado!r:16} {fm!r}  → {medido.get('reviewed_by')!r}")
total = len(STACK) + len(AGENTE) + len(FIRMA) + len(VALOR)
print(f"\n{total - malos}/{total} como se esperaba")
sys.exit(1 if malos else 0)
