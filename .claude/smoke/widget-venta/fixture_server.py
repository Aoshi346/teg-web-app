#!/usr/bin/env python3
"""Servidor de pruebas de `probar-widget` (sub-ola 3.68): dos anfitriones y un bot de mentira.

    python3 .claude/smoke/widget-venta/fixture_server.py [--port 8768]

Escucha SOLO en 127.0.0.1 (rules/security.md). Sirve:
  /estatico/            una página HTML sin tema (anfitrión 1)
  /tienda/              una «tienda» con tema hostil: `* {}`, `button {… !important}` y un `$` global
                        como el jQuery de un WordPress (anfitrión 2)
  /tienda/checkout/     el checkout nativo de la tienda: aquí se paga, nunca en el chat
  /widget.js            el widget de referencia (`widget.js` de esta carpeta)
  /api/widget/chat/     POST {message} → el JSON propio del patrón (§6): text · suggestions · products · cart
`?sabotage=<nombre>` en la URL del anfitrión llega al widget como `data-sabotage` (control negativo).
No llama a ningún modelo: las respuestas están escritas aquí, para que la prueba cueste 0 € y sea
reproducible.
"""
from __future__ import annotations

import argparse
import json
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

HERE = Path(__file__).resolve().parent
PUBLIC_TOKEN = "pk_test_fixture"
SABOTAGES = {"carrusel-9", "carrusel-sin-foco", "tres-acciones", "sin-live", "autoscroll", "pago-externo",
             "sin-humano", "fuga-css", "error-consola", "sin-chips", "objetivo-pequeno"}

IMG = ("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='160' height='90'>"
       "<rect width='160' height='90' fill='%23d1fae5'/></svg>")
PRODUCTS = [
    {"id": "c1", "name": "Crema hidratante 50 ml", "price": 24.9, "stock": 12, "image_url": IMG},
    {"id": "c2", "name": "Crema de noche 50 ml", "price": 29.5, "stock": 4, "image_url": IMG},
    {"id": "c3", "name": "Sérum calmante 30 ml", "price": None, "stock": 3, "image_url": IMG},
    {"id": "c4", "name": "Crema SPF 50", "price": 19.0, "stock": 0, "image_url": IMG},
]
ACCESSORY = {"id": "a1", "name": "Espátula de aplicación", "price": 3.5, "stock": 30, "image_url": IMG,
             "label": "Va con tu crema: para no meter los dedos en el tarro"}

HOSTS = {
    "estatico": ("Página de pruebas", "", "<h1>Página sin tema</h1><p>Anfitrión mínimo.</p>"),
    "tienda": (
        "Tienda de pruebas",
        "<style>*{box-sizing:content-box;font-family:Georgia,serif}h1{color:#1e3a8a}"
        "button{background:#dc2626 !important;color:#fff !important;padding:20px !important}"
        "body{font-size:19px;line-height:2}</style>"
        "<script>window.$=window.jQuery=function(){return {on:function(){}}};</script>",
        "<header><h1>Tienda de cosmética</h1></header><main><p>Crema hidratante 50 ml — 24,90 €</p>"
        "<button type='button'>Añadir al carrito de la tienda</button></main>",
    ),
}

CARTS: dict[str, list[str]] = {}


def reply(message: str, session: str) -> dict:
    m = message.lower()
    cart = CARTS.setdefault(session, [])
    if m == "hola":  # cada recorrido empieza con el carrito vacío: la prueba es repetible
        cart.clear()
    if m.startswith("añadir:"):
        pid = m.split(":", 1)[1]
        cart.append(pid)
        return {"text": "Añadido. ¿Quieres algo más o pasas a pagar en la tienda?",
                "suggestions": ["Pasar a pagar", "Seguir mirando"],
                # Un complemento, una vez, etiquetado y con su porqué (agente-catalogo-y-venta.md §5).
                "products": [ACCESSORY] if len(cart) == 1 else [],
                "cart": cart_state(cart)}
    if m.startswith("ficha:"):
        p = next((x for x in PRODUCTS if x["id"] == m.split(":", 1)[1]), None)
        return {"text": f"{p['name']}: textura ligera, para piel normal." if p else "No lo encuentro.",
                "suggestions": ["Ver cremas"], "cart": cart_state(cart)}
    if "crema" in m or "ver" in m:
        return {"text": "Estas son las que tenemos para piel normal:", "products": PRODUCTS,
                "suggestions": ["¿Cuál es para piel seca?"], "cart": cart_state(cart)}
    if "persona" in m:
        return {"text": "Te paso con el equipo de la tienda; te contestan en horario de 9 a 18.",
                "handoff": True, "cart": cart_state(cart)}
    return {"text": "Hola, soy el asistente de compra. ¿Qué buscas?",
            "suggestions": ["Ver cremas", "Envíos y devoluciones"], "cart": cart_state(cart)}


def cart_state(cart: list[str]) -> dict:
    items = [p for pid in cart for p in PRODUCTS + [ACCESSORY] if p["id"] == pid]
    total = sum(p["price"] or 0 for p in items) if all(p["price"] is not None for p in items) else None
    return {"items": len(items), "total": total, "checkout_url": "/tienda/checkout/?c=" + ",".join(cart)}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):  # silencio: la prueba lee la consola del navegador, no esta
        pass

    def send(self, code: int, body: bytes, ctype: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        u = urlparse(self.path)
        if u.path == "/widget.js":
            return self.send(200, (HERE / "widget.js").read_bytes(), "application/javascript; charset=utf-8")
        if u.path == "/favicon.ico":
            return self.send(204, b"", "image/x-icon")
        if u.path == "/tienda/checkout/":
            body = ("<!doctype html><html lang='es'><head><meta charset='utf-8'><title>Checkout</title></head>"
                    "<body><main><h1>Checkout de la tienda</h1><p>Productos: "
                    f"{parse_qs(u.query).get('c', [''])[0] or 'ninguno'}</p></main></body></html>")
            return self.send(200, body.encode(), "text/html; charset=utf-8")
        name = u.path.strip("/")
        if name in HOSTS:
            sab = parse_qs(u.query).get("sabotage", [""])[0]
            if sab and sab not in SABOTAGES:
                return self.send(400, f"sabotaje desconocido: {sab}".encode(), "text/plain; charset=utf-8")
            title, head, body = HOSTS[name]
            attr = f' data-sabotage="{sab}"' if sab else ""
            html = (f"<!doctype html><html lang='es'><head><meta charset='utf-8'>"
                    f"<meta name='viewport' content='width=device-width,initial-scale=1'><title>{title}</title>"
                    f"{head}</head><body>{body}<script src='/widget.js' data-public-token='{PUBLIC_TOKEN}'"
                    f" data-api-url='/api/widget/chat/'{attr}></script></body></html>")
            return self.send(200, html.encode(), "text/html; charset=utf-8")
        return self.send(404, b"no existe", "text/plain; charset=utf-8")

    def do_POST(self):
        if urlparse(self.path).path != "/api/widget/chat/":
            return self.send(404, b"no existe", "text/plain; charset=utf-8")
        if self.headers.get("X-Public-Token") != PUBLIC_TOKEN:
            return self.send(401, b'{"error":"token"}', "application/json")
        n = int(self.headers.get("Content-Length") or 0)
        try:
            msg = str(json.loads(self.rfile.read(n) or b"{}").get("message", ""))
        except json.JSONDecodeError:
            return self.send(400, b'{"error":"json"}', "application/json")
        session = re.sub(r"\W", "", self.headers.get("Referer", "x"))[-40:]
        return self.send(200, json.dumps(reply(msg, session), ensure_ascii=False).encode(), "application/json")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--port", type=int, default=8768)
    a = ap.parse_args()
    srv = ThreadingHTTPServer(("127.0.0.1", a.port), Handler)
    print(f"http://127.0.0.1:{a.port}/estatico/ · /tienda/", flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
