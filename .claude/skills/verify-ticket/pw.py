"""pw.py — lo genérico de los `pwlib.py` de cada ticket: navegador, contexto por usuario, espera y captura.

Lo que se copiaba de EVO-2834 a GENCAT-49 (WA-4). La guarda de datos personales NO se reescribe aquí:
`pii_guard` y la sustitución de celdas son las de `scripts/guarda_pii_capturas.py` (2.29), y el
binario de Chromium lo busca `scripts/screenshot.py`. Lo de la UI de cada proyecto (abrir una ficha,
un nodo del árbol) se queda en el proyecto: aquí solo lo que vale para cualquier Django.
"""
from __future__ import annotations

import pathlib
import sys

SCRIPTS = pathlib.Path(__file__).resolve().parent.parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))
import guarda_pii_capturas as gp  # noqa: E402
from screenshot import find_chrome  # noqa: E402

#: Lo que suele girar mientras carga; `ticket.json → wait_loader` suma los del proyecto.
DEFAULT_LOADERS = [".loading", ".spinner", "[aria-busy='true']", ".blockUI", ".dataTables_processing"]


class PiiFound(RuntimeError):
    """La página lleva datos personales fuera de la lista blanca: no se captura."""

    def __init__(self, found: list[dict], where: str):
        super().__init__(gp.informe(found, where))
        self.found = found


def launch(playwright, headless: bool = True):
    chrome = find_chrome()
    kwargs = {"headless": headless, "args": ["--no-sandbox"]}
    if chrome:
        kwargs["executable_path"] = chrome
    return playwright.chromium.launch(**kwargs)


def user_context(browser, cookie: dict | None, viewport=(1440, 900)):
    """Un contexto aislado por actor: su cookie y nada compartido con los demás."""
    ctx = browser.new_context(viewport={"width": viewport[0], "height": viewport[1]})
    if cookie:
        ctx.add_cookies([cookie])
    return ctx


def wait_loader(page, selectors: list[str] | None = None, timeout_ms: int = 15000) -> None:
    """Espera a la red y a que desaparezca todo indicador de carga visible."""
    try:
        page.wait_for_load_state("networkidle", timeout=timeout_ms)
    except Exception:  # noqa: BLE001 — una página con long-polling no llega nunca a networkidle
        pass
    for sel in DEFAULT_LOADERS + [x for x in selectors or [] if x not in DEFAULT_LOADERS]:
        try:
            page.wait_for_selector(sel, state="hidden", timeout=timeout_ms)
        except Exception as exc:  # noqa: BLE001
            raise TimeoutError(f"el indicador de carga «{sel}» sigue visible tras {timeout_ms} ms") from exc


def pii_config(project_root: pathlib.Path, extra_mask: list[str] | None = None,
               extra_allow: list[str] | None = None) -> dict:
    """La config de la guarda del proyecto (`.claude/pii-capturas.json`), SIEMPRE activa en el kit,
    más lo que el criterio añada para su pantalla."""
    conf = gp.cargar_config(project_root) or {"_propios": []}
    conf = dict(conf)
    conf["enmascarar"] = list(conf.get("enmascarar") or []) + list(extra_mask or [])
    conf["lista_blanca"] = list(conf.get("lista_blanca") or []) + list(extra_allow or [])
    return conf


def pii_guard(page, conf: dict, where: str) -> int:
    """Enmascara las celdas declaradas y lee el DOM: lanza PiiFound si queda algo personal."""
    masked = gp.enmascarar(page, conf)
    found = gp.revisar_pagina(page, conf)
    if found:
        raise PiiFound(found, where)
    return masked


def capture(page, path: pathlib.Path, conf: dict, where: str, full_page: bool = True) -> int:
    """La única forma de capturar del kit: guarda primero, captura después."""
    masked = pii_guard(page, conf, where)
    path.parent.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(path), full_page=full_page)
    return masked
