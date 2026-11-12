# Widget embebible — un fichero, su propio Shadow DOM y ni un secreto dentro

> **Cuándo aplicar:** al construir algo que el cliente pega en **su** web con una línea `<script>`: el
> chat de un bot, un buscador de citas, un formulario de reserva. Convive con el CSS y el JS de otro
> (un WordPress con su tema y su jQuery) y lo descarga cualquiera.
>
> **NO aplicar:** a nuestra propia SPA (`frontend-stack.md`) · a comprobar un widget ya hecho: skill
> `widget-embed-test` · a qué puede pintar de lo que escribe el modelo: `saneado.md` §Salida del LLM ·
> al endpoint y su auth: `backend-vistas.md`, skill `code-review-gate` (§Seguridad Django/DRF).
>
> **Relacionado:** `skills/widget-embed-test/widget_check.py` (W1-W5, el comprobador) ·
> `frontend-stack.md` (la fila «Widget embebido en una web ajena») · `backend-channel-adapter.md` (el
> canal web del lado del servidor) · `templates/canal-bot/` (topes de coste y enlaces permitidos).
>
> El saber vivía en el agente `especialista-widget-embebido` (cosechado de `proxera_musa`,
> `frontend/widget/`, en la 3.41). Desde AN-18 vive aquí, con su comprobador; el agente lo aplica.

## La regla (una frase)

**Un único fichero IIFE con el CSS dentro, montado en un Shadow DOM propio, que lee su configuración
pública de los `data-*` del script, sanea todo HTML del bot y no lleva más credencial que el
`public_token`.**

## 1. La forma

```
frontend/widget/
├── vite.config.widget.ts   # formats: ['iife'], cssCodeSplit: false, inlineDynamicImports: true
├── src/main.tsx            # lee data-* de document.currentScript y monta en Shadow DOM
├── src/Widget.tsx          # lanzador + panel
├── src/api/client.ts       # POST al endpoint del widget con X-Public-Token
├── src/lib/sanitize.ts     # DOMPurify sobre todo HTML que venga del servidor
└── dist/widget.js          # un fichero, < 250 KB gzip
```

```tsx
// src/main.tsx
const cs = document.currentScript as HTMLScriptElement;     // leerlo YA: luego es null
const host = document.createElement('div');
document.body.appendChild(host);
const shadow = host.attachShadow({ mode: 'open' });
const style = document.createElement('style');
style.textContent = widgetCSS;                              // import widgetCSS from './styles.css?inline'
shadow.appendChild(style);
const mount = document.createElement('div');
shadow.appendChild(mount);
createRoot(mount).render(<Widget publicToken={cs?.dataset.publicToken} apiUrl={cs?.dataset.apiUrl} />);
```

Lo que pega el cliente, y nada más:

```html
<script src="https://<nuestro-dominio>/widget.js" data-public-token="pk_…" data-api-url="https://…"></script>
```

## 2. Las cinco reglas — cada una con su check

| # | Regla | Por qué | Check |
|---|---|---|---|
| 1 | **Tope de tamaño escrito** (250 KB gzip por defecto) | Se descarga en la web de otro, en móvil | W1 |
| 2 | **Solo el `public_token`**: ni claves de API, ni el consumer secret de la tienda, ni `import.meta.env.VITE_*` con algo sensible. El token se limita en el servidor (origen, tenant, topes) | El bundle es público: un secreto dentro es un incidente aunque nadie lo haya visto aún | W2 |
| 3 | **IIFE autocontenido**: sin `import`/`export` de módulo, sin `<script src>` a un CDN, sin `import()` de otro dominio | Deja de depender de un tercero y de la página que lo aloja | W3 |
| 4 | **Shadow DOM y nada en el `<head>` del host** | El tema del cliente deforma el widget, o el widget rompe el tema | W4 |
| 5 | **DOMPurify sobre todo HTML** del bot, y los enlaces por lista blanca | Lo que escribe el modelo es dato no confiable | W5 |

```bash
npm --prefix frontend/widget run build
python3 .claude/skills/widget-embed-test/widget_check.py frontend/widget/dist/widget.js --max-kb 250
python3 .claude/skills/widget-embed-test/widget_check.py --autoprueba   # cada check visto fallar
```

W1-W5 en verde no bastan para entregar: falta montarlo en un host real en `127.0.0.1` y mirar la
consola (skill `widget-embed-test`, paso 4). Y W2 busca patrones conocidos: si el widget llama a un
tercero, se mira de dónde sale la credencial.

## Anti-patterns

- ❌ Leer `document.currentScript` dentro de un efecto o un callback: para entonces es `null`.
- ❌ Montarlo en el DOM normal «porque el CSS es poco»: el primer tema con `* { … }` lo rompe.
- ❌ Trocear el bundle (`cssCodeSplit`, chunks dinámicos): la segunda petición falla en la web ajena.
- ❌ Un React compartido con el host: dos versiones en la misma página.
- ❌ Una clave «solo para el widget»: el widget es público, la clave también.
