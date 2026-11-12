# Prueba con personas — 5 tareas, 5 participantes

> Plantilla (UX-15, sub-ola 3.64). Se copia a `.docs/feedback/personas/<fecha>/PROTOCOLO.md` cuando
> un proyecto tiene cliente con usuarios de verdad. Es la alternativa a Lidia (y su modo primer uso), que son
> **usuarios sintéticos**: sirven para preparar el estudio y sacar hipótesis, no para validar
> (NN/g, «Synthetic Users», 21-06-2024: tienden a ser complacientes y no sustituyen a la investigación
> con personas). Cinco participantes bastan para encontrar la mayoría de los problemas gordos de un
> flujo; no bastan para dar porcentajes: con N=5 se cuentan casos, no se publica «el 80 %».

## 1. Antes

- **Qué se decide con esto** (una frase). Si no cambia ninguna decisión, no se hace la prueba.
- **Las 5 tareas**, escritas como objetivos del usuario, sin el nombre del botón:
  «Has recibido la factura de marzo y quieres saber si ya está pagada», no «pulsa Facturas».
  Cada una con su **criterio de éxito** observable y un **tope de tiempo**.
- **Los 5 participantes**: del perfil real del producto (no del equipo, no familiares del equipo).
  Anota por cada uno solo lo que haga falta para leer el resultado (rol, cuánto usa el ordenador).
- **Consentimiento por escrito** antes de grabar: qué se graba, para qué, quién lo ve, cuándo se
  borra. Sin consentimiento, se toman notas y no se graba. Datos de prueba, nunca los suyos reales.
- **Grabación**: pantalla y voz, con consentimiento. En un Django, el grabador de sesión de fitapp
  (`django-traza`) cuando esté en el template; mientras, la grabación de pantalla del sistema.
- **La misma ronda a Lidia** (modo primer uso si es onboarding), con las mismas 5 tareas y **antes** de ver a las personas: es la
  única forma de medir su validez (`agents/lidia-naive-tester.md` §Lo que NO puedo demostrar).

## 2. Durante (por participante, ~30 min)

1. «Probamos la aplicación, no a ti. No hay respuestas malas.» Piensa en voz alta.
2. Una tarea cada vez, leída tal cual. **No se ayuda**; si pregunta, «¿qué harías tú?».
3. Por tarea se anota: éxito (sí · con ayuda · no), tiempo, errores y la cita literal donde se atasca.
4. Tras cada tarea: «Del 1 al 7, ¿cuánto te ha costado?» (SEQ).

## 3. Después

| Tarea | Éxito (5) | Tiempo mediano | Atasco más repetido (cita) | Lidia lo vio |
|---|---|---|---|---|
| 1 | n/5 | | | sí / no / al revés |

- Un problema cuenta cuando lo sufren **≥2 de 5**; uno solo va como observación.
- El cruce con la ronda sintética va en la última columna y se anota en la `memory.md` del agente:
  qué vio que las personas no sufrieron (falso positivo) y qué sufrieron que no vio (falso negativo).
- Las grabaciones se borran en la fecha que dice el consentimiento.
