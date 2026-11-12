/* Widget de venta de referencia (sub-ola 3.68): la forma de patterns/stack/chat-ui-comercio.md en
 * JavaScript sin build, para probar `probar-widget` contra algo que cumple y contra sus sabotajes.
 * No es código de producto: un proyecto real lo escribe en React (frontend-embeddable-widget.md).
 * Contrato con el servidor: el JSON propio de §6 del patrón (text, suggestions, products, cart).
 * `data-sabotage` rompe UNA regla a propósito, para ver fallar su check (control negativo). */
(function () {
  "use strict";
  var cs = document.currentScript;
  var token = cs.dataset.publicToken;
  var api = cs.dataset.apiUrl || "/api/widget/chat/";
  var sab = cs.dataset.sabotage || "";

  var css = [
    ":host{all:initial;font-family:system-ui,-apple-system,'Segoe UI',sans-serif}",
    "*{box-sizing:border-box;font-family:system-ui,-apple-system,'Segoe UI',sans-serif}",
    ".launcher{position:fixed;right:16px;bottom:16px;min-width:56px;min-height:56px;border-radius:28px;",
    "border:0;background:#14532d;color:#fff;font-size:15px;font-weight:600;padding:0 20px;cursor:pointer}",
    ".panel{position:fixed;right:16px;bottom:84px;width:380px;max-width:calc(100vw - 32px);",
    "height:min(600px,calc(100vh - 100px));display:flex;flex-direction:column;background:#fff;color:#1f2937;",
    "border:1px solid #d1d5db;border-radius:12px;box-shadow:0 8px 24px rgba(0,0,0,.15);font-size:14px}",
    ".panel[hidden]{display:none}",
    "header{display:flex;align-items:center;justify-content:space-between;gap:8px;padding:10px 12px;",
    "border-bottom:1px solid #e5e7eb}",
    "h2{margin:0;font-size:15px;flex:1;min-width:0}",
    ".log{flex:1;overflow-y:auto;padding:12px;display:flex;flex-direction:column;gap:8px}",
    ".msg{max-width:85%;padding:8px 10px;border-radius:10px;line-height:1.4}",
    ".bot{background:#f3f4f6;align-self:flex-start}.user{background:#14532d;color:#fff;align-self:flex-end}",
    ".chips{display:flex;flex-wrap:wrap;gap:6px}",
    // La familia se repite aquí: `font:inherit` heredaría la del anfitrión, que gana a `:host`.
    "button{font-size:inherit;font-family:system-ui,-apple-system,'Segoe UI',sans-serif;cursor:pointer}",
    ".human{font-size:13px}",
    ".chip{min-height:32px;padding:4px 12px;border-radius:16px;border:1px solid #14532d;background:#fff;color:#14532d}",
    ".carousel{display:flex;gap:8px;overflow-x:auto;padding:2px 2px 6px;list-style:none;margin:0}",
    ".carousel:focus-visible,button:focus-visible,a:focus-visible{outline:3px solid #2563eb;outline-offset:2px}",
    ".card{flex:0 0 160px;border:1px solid #d1d5db;border-radius:10px;overflow:hidden;background:#fff}",
    ".card img{display:block;width:100%;height:90px;object-fit:cover;background:#e5e7eb}",
    ".card .b{padding:6px 8px}.card p{margin:0 0 4px}",
    ".price{font-weight:700}.out{color:#991b1b;font-weight:600}",
    ".label{font-size:12px;color:#4b5563}",
    ".acts{display:flex;gap:6px;padding:0 8px 8px}",
    ".acts button{min-height:32px;flex:1;border-radius:8px;border:1px solid #14532d;background:#fff;color:#14532d}",
    ".acts .add{background:#14532d;color:#fff}.acts .add:disabled{background:#e5e7eb;color:#4b5563;border-color:#9ca3af}",
    ".cart{display:flex;align-items:center;gap:8px;padding:8px 12px;border-top:1px solid #e5e7eb;background:#f0fdf4}",
    ".cart[hidden]{display:none}",
    ".cart span{flex:1}",
    ".checkout{min-height:32px;display:inline-flex;align-items:center;padding:0 12px;border-radius:8px;",
    "background:#14532d;color:#fff;text-decoration:none;font-weight:600}",
    "form{display:flex;gap:6px;padding:8px 12px;border-top:1px solid #e5e7eb}",
    "input{flex:1;min-width:0;min-height:36px;padding:0 8px;border:1px solid #6b7280;border-radius:8px;font:inherit}",
    ".send,.human,.close{flex:0 0 auto;padding:0 10px;min-height:36px;min-width:36px;border-radius:8px;border:1px solid #6b7280;background:#fff;color:#1f2937}",
    ".typing{font-style:italic;color:#4b5563}",
  ].join("");
  if (sab === "objetivo-pequeno")
    css +=
      ".chip,.acts button{min-height:14px;height:14px;padding:0 2px;font-size:9px}";

  var host = document.createElement("div");
  host.id = "cw-root";
  document.body.appendChild(host);
  var root = host.attachShadow({ mode: "open" });
  var st = document.createElement("style");
  st.textContent = css;
  if (sab === "fuga-css") {
    var g = document.createElement("style");
    g.textContent = "h1{color:#c026d3 !important}";
    document.head.appendChild(g);
  }
  root.appendChild(st);

  function el(tag, attrs, text) {
    var e = document.createElement(tag);
    for (var k in attrs || {}) e.setAttribute(k, attrs[k]);
    if (text != null) e.textContent = text; // nunca innerHTML: el texto del bot es dato
    return e;
  }

  var launcher = el(
    "button",
    {
      class: "launcher",
      "data-cw": "launcher",
      "aria-expanded": "false",
      "aria-controls": "cw-panel",
    },
    "Asistente de compra",
  );
  var panel = el("section", {
    id: "cw-panel",
    class: "panel",
    role: "complementary",
    "aria-label": "Asistente de compra",
    hidden: "",
  });
  var head = el("header");
  head.appendChild(el("h2", {}, "Asistente de compra"));
  var close = el(
    "button",
    { class: "close", "aria-label": "Cerrar el asistente" },
    "×",
  );
  var tools = el("div", { style: "display:flex;gap:6px" });
  head.appendChild(tools);
  var logAttrs = {
    class: "log",
    "data-cw": "log",
    "aria-label": "Conversación con el asistente",
    tabindex: "0",
  };
  if (sab !== "sin-live") {
    logAttrs.role = "log";
    logAttrs["aria-live"] = "polite";
  }
  var log = el("div", logAttrs);
  var cart = el("div", { class: "cart", "data-cw": "cart", hidden: "" });
  var form = el("form");
  var input = el("input", {
    "data-cw": "input",
    "aria-label": "Escribe tu pregunta",
    autocomplete: "off",
  });
  var send = el(
    "button",
    { class: "send", type: "submit", "data-cw": "send" },
    "Enviar",
  );
  form.appendChild(input);
  form.appendChild(send);
  if (sab !== "sin-humano") {
    var human = el(
      "button",
      { class: "human", type: "button", "data-cw": "handoff" },
      "Hablar con una persona",
    );
    tools.appendChild(human);
    human.addEventListener("click", function () {
      ask("quiero hablar con una persona");
    });
  }
  tools.appendChild(close);
  panel.appendChild(head);
  panel.appendChild(log);
  panel.appendChild(cart);
  panel.appendChild(form);
  root.appendChild(launcher);
  root.appendChild(panel);

  // Solo se baja al final si el cliente ya estaba abajo: no se le quita lo que está leyendo.
  function atBottom() {
    return log.scrollHeight - log.scrollTop - log.clientHeight < 40;
  }
  function append(node) {
    var stick = sab === "autoscroll" || atBottom();
    log.appendChild(node);
    if (stick) log.scrollTop = log.scrollHeight;
  }

  function money(v) {
    if (v === null || v === undefined || v === "" || !isFinite(Number(v)))
      return "Sin precio";
    return Number(v).toLocaleString("es-ES", {
      style: "currency",
      currency: "EUR",
    });
  }

  function card(p) {
    var li = el("li", { class: "card", "data-cw": "card" });
    li.appendChild(
      el("img", { src: p.image_url, alt: p.name, width: "160", height: "90" }),
    );
    var b = el("div", { class: "b" });
    b.appendChild(el("p", {}, p.name));
    if (p.label) b.appendChild(el("p", { class: "label" }, p.label));
    b.appendChild(el("p", { class: "price" }, money(p.price)));
    if (p.stock === 0) b.appendChild(el("p", { class: "out" }, "Sin stock"));
    li.appendChild(b);
    var acts = el("div", { class: "acts" });
    var see = el(
      "button",
      { type: "button", "aria-label": "Ver " + p.name },
      "Ver",
    );
    see.addEventListener("click", function () {
      ask("ficha:" + p.id);
    });
    var add = el(
      "button",
      {
        type: "button",
        class: "add",
        "data-cw": "add",
        "aria-label": "Añadir " + p.name + " al carrito",
      },
      "Añadir",
    );
    if (p.stock === 0) add.disabled = true;
    add.addEventListener("click", function () {
      ask("añadir:" + p.id);
    });
    acts.appendChild(see);
    acts.appendChild(add);
    if (sab === "tres-acciones")
      acts.appendChild(el("button", { type: "button" }, "Comparar"));
    li.appendChild(acts);
    return li;
  }

  function render(r) {
    var m = el("div", { class: "msg bot" });
    m.appendChild(el("p", { style: "margin:0" }, r.text));
    var items = r.products || [];
    if (sab === "carrusel-9" && items.length) {
      while (items.length < 9)
        items = items.concat(items.slice(0, 9 - items.length));
    }
    if (items.length) {
      var ul = el("ul", {
        class: "carousel",
        "data-cw": "carousel",
        "aria-label": "Productos sugeridos",
      });
      if (sab !== "carrusel-sin-foco") ul.setAttribute("tabindex", "0");
      items.forEach(function (p) {
        ul.appendChild(card(p));
      });
      m.appendChild(ul);
    }
    if (r.suggestions && r.suggestions.length && sab !== "sin-chips") {
      var c = el("div", { class: "chips" });
      r.suggestions.forEach(function (s) {
        var b = el(
          "button",
          { type: "button", class: "chip", "data-cw": "chip" },
          s,
        );
        b.addEventListener("click", function () {
          ask(s);
        });
        c.appendChild(b);
      });
      m.appendChild(c);
    }
    append(m);
    if (r.cart && r.cart.items > 0) {
      cart.hidden = false;
      cart.textContent = "";
      cart.appendChild(
        el(
          "span",
          {},
          r.cart.items +
            (r.cart.items === 1 ? " producto · " : " productos · ") +
            money(r.cart.total),
        ),
      );
      var href = r.cart.checkout_url;
      if (sab === "pago-externo") href = "https://pago-falso.example/checkout";
      cart.appendChild(
        el(
          "a",
          { class: "checkout", "data-cw": "checkout", href: href },
          "Ir a pagar en la tienda",
        ),
      );
    }
  }

  function ask(text) {
    append(
      el(
        "div",
        { class: "msg user" },
        text.indexOf("añadir:") === 0 ? "Añadir al carrito" : text,
      ),
    );
    var t = el(
      "p",
      { class: "typing", role: "status" },
      "El asistente está escribiendo…",
    );
    log.appendChild(t);
    fetch(api, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Public-Token": token },
      body: JSON.stringify({ message: text }),
    })
      .then(function (r) {
        return r.json();
      })
      .then(function (r) {
        t.remove();
        render(r);
      })
      .catch(function () {
        t.textContent =
          "No he podido contestar. Prueba otra vez o habla con una persona.";
      });
  }

  launcher.addEventListener("click", function () {
    var open = panel.hidden;
    panel.hidden = !open;
    launcher.setAttribute("aria-expanded", String(open));
    if (open && !log.childElementCount) ask("hola");
    if (open) input.focus();
  });
  close.addEventListener("click", function () {
    panel.hidden = true;
    launcher.setAttribute("aria-expanded", "false");
    launcher.focus();
  });
  form.addEventListener("submit", function (e) {
    e.preventDefault();
    if (input.value.trim()) {
      ask(input.value.trim());
      input.value = "";
    }
  });
  if (sab === "error-consola") console.error("widget: fallo plantado");
})();
