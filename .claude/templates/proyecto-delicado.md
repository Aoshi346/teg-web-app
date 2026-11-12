<!-- Plantilla del marcador «proyecto delicado» (sub-ola 2.29, SE-40). Se copia a
     .claude/proyecto-delicado.md. La PRIMERA línea con texto que no sea un comentario ni un título
     es el motivo: el hook aviso-envio-externo.sh la enseña cada vez que pide confirmación. La
     rellena la skill `arrancar` en la fase de ética (4c); si no, la persona que lo decida. -->
# Proyecto delicado
<motivo en una línea: «la marca es de un cliente y el contrato no permite mandarla a terceros» · «datos de salud de pacientes» · «datos fiscales de clientes de un tercero»>

## Qué lo hace delicado
- [ ] La marca o el material son de un **cliente** (y no hay permiso escrito para enviarlos a terceros)
- [ ] Hay datos **de salud** o de categorías especiales (RGPD art. 9)
- [ ] Hay datos **personales de terceros** (clientes, trabajadores o pacientes del cliente)
- [ ] El contrato no cubre **subencargados** (proveedores de IA, generadores, alojamiento)

## Qué cambia en este proyecto
- `aviso-envio-externo.sh` **pregunta** antes de cada envío a un servicio externo: lo declarado en
  `.claude/envios-externos.json`, un `curl`/`wget` que sube algo fuera, publicar un Artifact y las
  tools MCP que suben, crean o mandan.
- `screenshot.py` pasa la **guarda de datos personales** antes de guardar cualquier captura
  (`scripts/guarda_pii_capturas.py`), y lo que se entrega pasa la revisión visual
  (`guarda_pii_capturas.py --comprobar <carpeta>`).

Decidido por: <persona> · fecha: <YYYY-MM-DD>
