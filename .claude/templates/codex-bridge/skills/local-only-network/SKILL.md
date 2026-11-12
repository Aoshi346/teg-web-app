---
name: local-only-network
description: Usar SIEMPRE antes de levantar cualquier servidor o contenedor — runserver, npm run dev, vite, http.server, servir un HTML, docker compose up, publicar un puerto, abrir un panel, enseñar una página a alguien. Dice en qué interfaz se escucha (127.0.0.1, nunca 0.0.0.0), cómo se llega desde fuera (túnel SSH) y por qué en Docker el cortafuegos no protege.
---

# Nada escucha en `0.0.0.0`

Este servidor tiene IP pública. Lo que escucha en todas las interfaces queda publicado en internet,
sin autenticación y sin aviso. Los bots barren internet entera cada pocas horas.

## Siempre

```bash
python3 -m http.server 8899 --bind 127.0.0.1          # ✅  (sin --bind escucha en 0.0.0.0 ❌)
python manage.py runserver 127.0.0.1:8000             # ✅
npm run dev -- --host 127.0.0.1                       # ✅
```

En Docker, el puerto se publica **con la IP delante**:

```yaml
ports:
  - "127.0.0.1:5432:5432"     # ✅
  # - "5432:5432"             # ❌ Docker abre el puerto saltándose el cortafuegos del sistema
```

Y cuidado con `network_mode: host`: el contenedor escucha donde diga su programa, sin pasar por ahí.

## Para llegar desde fuera, solo hay dos caminos

| Camino | Cuándo |
|---|---|
| **Túnel SSH**: `ssh -N -L 8899:127.0.0.1:8899 <usuario>@<servidor>` | Paneles, bases de datos, informes, cualquier herramienta de trabajo |
| **URL pública con dominio y HTTPS** | Lo que tiene que ver un usuario final. Solo el proxy (nginx) escucha en 80 y 443; la aplicación sigue en `127.0.0.1` detrás |

No hay una tercera forma. «Lo abro un momento para probar» es la frase que precede al incidente.

## Al terminar

Los servidores que lanzas no mueren solos. Un puerto por cosa, y se cierra al acabar:

```bash
ss -tlnp | grep '0.0.0.0'          # lo que está EXPUESTO ahora mismo
```
