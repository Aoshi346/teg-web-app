---
name: no-push-merge-deploy
description: Usar antes de cualquier operación que salga de esta máquina o toque producción — push, subir, publicar, merge, fusionar, desplegar, deploy, migración destructiva, borrar datos, borrar columna, tocar producción, instalar dependencias del sistema, gastar en una API de pago, reescribir historia. Dice qué puede decidir el agente solo, qué necesita permiso y cómo se hace un commit cuando hay otras sesiones en el repo.
---

# Lo que no decides tú

Cada línea de la lista de abajo es algo que no se deshace con un `git revert`. Por eso se pregunta.

## Autónomo — hazlo sin preguntar

Leer y editar código · crear ficheros · refactorizar · escribir y correr tests (por módulo) ·
**`git commit` en la rama de trabajo** · instalar dependencias del proyecto (`pip`, `npm`, `poetry`) ·
crear migraciones y aplicarlas en desarrollo.

## Para y pide permiso

`git push` · merge a `main` o a una rama protegida · **cualquier despliegue** · migraciones
destructivas (`DROP`, borrar columna, borrado masivo) · configuración de producción (`settings` de
producción, nginx, secretos, CORS, autenticación) · gasto externo (APIs de pago, nube) · dependencias
del sistema (`apt`, `brew`) · borrar ficheros o carpetas importantes · `push --force`,
`reset --hard` sobre commits compartidos o reescribir historia.

Y, aunque sea técnicamente fácil, también se pregunta: cambiar el **alcance** del producto, los
**precios** o la lógica de cobro, un **flujo principal** de la interfaz, o borrar datos de personas reales.

Si el proyecto declara otra cosa (por ejemplo, que los commits los hace una persona), manda el
proyecto: deja el cambio listo y avisa.

## El commit, con otras sesiones vivas

Un `git commit` sin rutas se lleva dentro el trabajo de otra sesión que esté en el mismo repo, bajo
tu mensaje. Ha pasado.

```bash
git add <ruta> <ruta>
git commit -m "tipo(ámbito): qué cambia" -- <ruta> <ruta>     # SIEMPRE con rutas; nunca `git add -A`
```

## Cómo se pide

Con tu propuesta dentro. **Nunca en blanco**: qué harías, cuál es la alternativa y qué pasa si te
equivocas. Un agente que pregunta sin traer respuesta es un formulario.
