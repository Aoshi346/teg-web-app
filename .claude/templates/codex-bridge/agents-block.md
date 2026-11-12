## Reglas críticas de la casa (las mismas que sigue Claude Code)

Codex no pasa por los hooks ni los permisos de Claude Code: aquí nada te frena, así que estas reglas
las cumples tú. Cada una tiene su skill en `.agents/skills/` con el detalle.

1. **Tests, siempre por módulo y con el gate de memoria antes.** `bash .claude/hooks/check-ram.sh`;
   si bloquea, **espera**, no lo saltes. Luego `{{pytest}} <ruta-del-modulo>/ -v --maxfail=3`. Nunca la
   suite entera, ni `-n auto`, ni `--cov`: agota la memoria del servidor compartido.
   → `ram-before-pytest`
2. **Lo que no decides tú.** `git push`, merge, cualquier despliegue, migraciones destructivas,
   configuración de producción, gasto externo, dependencias del sistema y reescribir historia: para y
   pide permiso con tu propuesta dentro. Sí puedes hacer commit en la rama de trabajo, **con rutas
   explícitas** (`git commit -m "…" -- <ruta> <ruta>`), nunca `git add -A`: puede haber otra sesión
   trabajando en el mismo repo. → `no-push-merge-deploy`
3. **Nada escucha en `0.0.0.0`.** Todo servidor de prueba en `127.0.0.1`, y se llega por túnel SSH;
   en Docker, `"127.0.0.1:PUERTO:PUERTO"`. → `local-only-network`
4. **Secretos.** No leas `.env` ni ficheros de claves, y no los metas en un commit.
5. **Nada está hecho sin verificar.** El código corre, los tests del módulo pasan, y si hay pantalla,
   captura. Si un instrumento no puede medir, dilo («sin datos»): no lo cuentes como un cero.
6. **Idioma.** Identificadores (ficheros, clases, funciones, variables, claves JSON, rutas de API) en
   inglés; comentarios, docstrings y textos que lee una persona, en castellano.
7. **`.claude/` es la configuración de Claude Code.** Sus `rules/` son la fuente de estas reglas: léelas
   si dudas, pero no las edites salvo que la tarea sea justo esa.

Si dudas del **procedimiento**, decide y sigue. Si dudas del **objetivo**, para y pregunta: qué harías,
cuál es la alternativa y qué pasa si te equivocas.
