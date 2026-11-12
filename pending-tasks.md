# Peticiones pendientes — lo que se ha pedido en este plan

> Lo escribe el hook `capture-task.sh` en cada petición del Usuario, y lo marca el TL al terminar.
> **No se edita a mano para "limpiar"**: una tarea que desaparece sin marcarse es una tarea perdida,
> que es justo lo que este fichero existe para impedir.
>
> `[ ]` pendiente · `[>]` en curso · `[~]` en background · `[x]` hecha · `[!]` bloqueada o descartada

## Pendientes

## En background

## Hechas
- [x] `T-007` (09-28 17:41) Ok, listo. Una cosa, es posible tener una base de datos en un servidor de una pc con un dominio de vercel o gratis?  — Pregunta respondida en chat (opciones de BD/hosting gratis)
- [x] `T-006` (09-28 16:42) quiero que cambies el archivo informe avance que es un pdf en la raiz, ese archivo lo debemos cambiar para indicar el 100% de la app con los nuevos cambios siguiendo el mismo formato del pdf, solo sustituyendo con lo nuevo. No subas a cloud ni nada, hazlo e…  — informeavance2.pdf regenerado al 100% (6 pags); original en informeavance2-original.pdf
- [x] `T-005` (09-28 16:39) ok, entonces no hubo absolutamente nada en contra de esos servicio? No se rompieron, siguen como si nada?  — Verificado en logs: 502 de chatbot-crm y 500 de proxera-agent son previos al cambio (desde 27-sep y 13-sep); confs ajenas intactas
- [x] `T-004` (09-28 16:38) no toues nada que no sea tesisfar, nada de proxera, etc  — Confirmado: no se modificó nada ajeno a tesisfar; regla guardada en memoria
- [x] `T-003` (09-28 16:36) quita el nginx, quita todo lo de prod  — Repo: deploy/, README prod y gunicorn fuera. Servidor: vhost tesisfar, cert y enlace teg-ctl borrados (backup en /root/backups/retirada-tesisfar-2026-09-13/). nginx sigue activo.
- [x] `T-002` (09-28 16:34) Sabes que hace este proyecto? Audita revisa, progreso, que hace, modulos, UI, secciones y dime que hay hecho  — Auditoría de estado entregada en chat (solo lectura)
- [x] `T-001` (09-21 21:13) prueba del registro de peticiones  — prueba de instalacion del registro
