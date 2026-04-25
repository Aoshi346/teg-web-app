# Customer Journeys — TesisFar

Mapa completo de interacciones de cada rol con el sistema, desde el **descubrimiento** hasta la **fidelización / advocacy**.

> **Nota de formato:** el diagrama `journey` de Mermaid se dibuja **horizontalmente**, así que cuando hay muchas etapas se vuelve ilegible al exportar. Por eso cada rol se divide en **dos diagramas** (Fase 1: llegada al sistema · Fase 2: uso y cierre) y se incluye además una vista vertical con `flowchart TB` para exportación cómoda.

Etapas del customer journey clásico adaptadas al contexto académico de TesisFar:

| Etapa            | Qué significa aquí                                                      |
|------------------|-------------------------------------------------------------------------|
| **Descubrimiento** | El rol se entera de que TesisFar existe y para qué sirve.              |
| **Consideración**  | Entiende cómo le afecta y decide (o le toca) usarlo.                   |
| **Adquisición**    | Se registra, obtiene credenciales, entra por primera vez.             |
| **Onboarding**     | Primer contacto real con el dashboard y su rol.                       |
| **Uso**            | Flujo diario: crear, subir, comentar, evaluar, planificar.            |
| **Cierre**         | Momento de verdad — defensa, resultado, cierre de semestre.           |
| **Fidelización**   | Qué hace que vuelva o lo recomiende el próximo semestre.              |

Puntajes 1–5 = satisfacción emocional (1 = muy frustrante, 5 = excelente).

---

## Estudiante

### Fase 1 — Llegada al sistema

```mermaid
journey
    title Estudiante · Fase 1 — Descubrir y entrar
    section Descubrimiento
      Escucha en clase sobre TesisFar: 3: Estudiante
      Ve la URL en correo de coordinación: 3: Estudiante
    section Consideración
      Entiende que es obligatorio: 2: Estudiante
      Revisa requisitos del TEG: 3: Estudiante
    section Adquisición
      Se registra con email y cédula: 3: Estudiante
      Espera activación (pending): 1: Estudiante
      Recibe cuenta activa: 4: Estudiante
    section Onboarding
      Primer login al dashboard: 4: Estudiante
      Explora su rol y secciones: 4: Estudiante
```

### Fase 2 — Uso, cierre y fidelización

```mermaid
journey
    title Estudiante · Fase 2 — Operar y graduarse
    section Uso
      Crea proyecto y asigna partner: 4: Estudiante
      Sube archivos pdf / word: 3: Estudiante
      Lee comentarios y corrige: 2: Estudiante
      Consulta fecha de presentación: 4: Estudiante
    section Cierre
      Defiende ante el jurado: 3: Estudiante
      Observa avance por estados (pending_review_1 → pending_defense → approved): 3: Estudiante
      Espera el resultado: 1: Estudiante
      Lee comments.general: 3: Estudiante
      Ve pass_status = Pass: 5: Estudiante
    section Fidelización
      Recomienda a compañeros menores: 5: Estudiante
      Vuelve como egresado por constancia: 4: Estudiante
```

---

## Tutor

### Fase 1 — Llegada al sistema

```mermaid
journey
    title Tutor · Fase 1 — Aceptar y entrar
    section Descubrimiento
      Coordinación le informa del rol: 3: Tutor
      Ve documentación del dashboard: 3: Tutor
    section Consideración
      Evalúa carga de asesorados: 2: Tutor
      Decide aceptar el rol: 4: Tutor
    section Adquisición
      Admin crea su cuenta Tutor: 4: Tutor
      Primer login: 3: Tutor
    section Onboarding
      Descubre vista filtrada a asesorados: 4: Tutor
      Explora agenda de presentaciones: 3: Tutor
```

### Fase 2 — Uso, cierre y fidelización

```mermaid
journey
    title Tutor · Fase 2 — Acompañar y cerrar
    section Uso
      Lee proyectos y archivos: 3: Tutor
      Comenta iteraciones: 4: Tutor
      Solicita correcciones: 3: Tutor
      Revisa versión final: 4: Tutor
    section Cierre
      Acompaña la defensa: 4: Tutor
      Observa evaluación del jurado: 3: Tutor
      Ve asesorados aprobados: 5: Tutor
    section Fidelización
      Acepta tutorar otro semestre: 4: Tutor
      Recomienda TesisFar a docentes: 4: Tutor
```

---

## Jurado

### Fase 1 — Llegada al sistema

```mermaid
journey
    title Jurado · Fase 1 — Nombramiento y entrada
    section Descubrimiento
      Admin le comunica el nombramiento: 3: Jurado
      Admin lo asigna como reviewer de un proyecto: 3: Jurado
      Ve el nombre TesisFar: 3: Jurado
    section Consideración
      Pregunta cuántas defensas evaluará: 2: Jurado
      Decide aceptar el panel: 4: Jurado
    section Adquisición
      Cuenta creada con rol Jurado: 4: Jurado
      Primer login: 3: Jurado
    section Onboarding
      Descubre vista de todos los proyectos: 4: Jurado
      Revisa la rúbrica: 3: Jurado
```

### Fase 2 — Uso, cierre y fidelización

```mermaid
journey
    title Jurado · Fase 2 — Evaluar y cerrar
    section Uso
      Recibe agenda del día: 4: Jurado
      Revisa proyectos y archivos: 3: Jurado
      Escucha defensa del estudiante: 4: Jurado
      Llena ratings y section_scores: 2: Jurado
      Escribe comments.general: 4: Jurado
      Guarda Evaluation: 4: Jurado
    section Cierre
      Cierra el día de presentaciones: 4: Jurado
      Confirma evaluaciones registradas: 4: Jurado
    section Fidelización
      Vuelve como jurado otro semestre: 4: Jurado
      Sugiere mejoras a la rúbrica: 3: Jurado
```

---

## Administrador

### Fase 1 — Adopción y configuración

```mermaid
journey
    title Administrador · Fase 1 — Adoptar y configurar
    section Descubrimiento
      Conoce TesisFar como solución al TEG: 4: Admin
      Evalúa alternativas (hojas, correos): 2: Admin
    section Consideración
      Verifica cobertura de roles: 4: Admin
      Decide adoptarla: 5: Admin
    section Adquisición
      Despliega backend y frontend: 3: Admin
      Crea superuser y primer semestre: 4: Admin
    section Onboarding
      Configura start_month / end_month: 4: Admin
      Activa el Semester: 5: Admin
      Valida flujo con usuarios prueba: 3: Admin
```

### Fase 2 — Operación del semestre

```mermaid
journey
    title Administrador · Fase 2 — Operar el semestre
    section Uso
      Aprueba usuarios pending: 3: Admin
      Asigna roles Tutor / Jurado: 4: Admin
      Reasigna estudiantes: 2: Admin
      Crea PresentationDay y slots: 4: Admin
      Asigna tutor + jurados: 3: Admin
      Monitorea SessionLog: 3: Admin
      Responde reclamos: 2: Admin
      Fuerza estado de PTEG (con razón + auditoría): 4: Admin
      Revisa dashboard por estado (chips): 5: Admin
    section Cierre
      Verifica evaluaciones completas: 4: Admin
      Cierra y archiva el semestre: 5: Admin
    section Fidelización
      Activa el siguiente semestre: 5: Admin
      Propone TesisFar a otras carreras: 5: Admin
      Solicita mejoras al equipo: 4: Admin
```

---

## Vista vertical unificada (para exportar cómodamente)

Si necesitas una sola imagen por rol que quepa en PDF/slide, usa este formato `flowchart TB` (top-bottom) que crece hacia abajo en vez de a lo ancho. Los iconos al inicio de cada nodo indican el score emocional:

- 😟 score 1 · 😕 score 2 · 😐 score 3 · 🙂 score 4 · 😄 score 5

### Estudiante — vista vertical

```mermaid
flowchart TB
    E((Estudiante))
    E --> D1["🔍 Descubrimiento<br/>😐 Escucha sobre TesisFar en clase<br/>😐 Ve la URL en correo"]
    D1 --> C1["🤔 Consideración<br/>😕 Entiende obligatoriedad<br/>😐 Revisa requisitos del TEG"]
    C1 --> A1["📝 Adquisición<br/>😐 Registro con email y cédula<br/>😟 Espera activación (pending)<br/>🙂 Recibe cuenta activa"]
    A1 --> O1["🚀 Onboarding<br/>🙂 Primer login<br/>🙂 Explora su rol"]
    O1 --> U1["⚙️ Uso<br/>🙂 Crea proyecto + partner<br/>😐 Sube archivos<br/>😕 Corrige iterativamente<br/>🙂 Consulta fecha de defensa"]
    U1 --> Cl1["🎯 Cierre<br/>😐 Defiende ante jurado<br/>😟 Espera resultado<br/>😐 Lee comentarios<br/>😄 pass_status = Pass"]
    Cl1 --> F1["💚 Fidelización<br/>😄 Recomienda a compañeros<br/>🙂 Vuelve por constancia"]

    style E fill:#dbeafe,stroke:#1e40af,stroke-width:2px,color:#000
    style D1 fill:#fef3c7,stroke:#b45309,color:#000
    style C1 fill:#fef3c7,stroke:#b45309,color:#000
    style A1 fill:#dbeafe,stroke:#1e40af,color:#000
    style O1 fill:#dbeafe,stroke:#1e40af,color:#000
    style U1 fill:#e0f2fe,stroke:#0369a1,color:#000
    style Cl1 fill:#fce7f3,stroke:#be185d,color:#000
    style F1 fill:#dcfce7,stroke:#15803d,color:#000
```

### Tutor — vista vertical

```mermaid
flowchart TB
    T((Tutor))
    T --> D2["🔍 Descubrimiento<br/>😐 Coordinación le informa<br/>😐 Ve documentación"]
    D2 --> C2["🤔 Consideración<br/>😕 Evalúa carga<br/>🙂 Acepta el rol"]
    C2 --> A2["📝 Adquisición<br/>🙂 Cuenta creada por admin<br/>😐 Primer login"]
    A2 --> O2["🚀 Onboarding<br/>🙂 Descubre vista filtrada<br/>😐 Explora agenda"]
    O2 --> U2["⚙️ Uso<br/>😐 Lee proyectos<br/>🙂 Comenta iteraciones<br/>😐 Solicita correcciones<br/>🙂 Revisa versión final"]
    U2 --> Cl2["🎯 Cierre<br/>🙂 Acompaña defensa<br/>😐 Observa evaluación<br/>😄 Asesorados aprobados"]
    Cl2 --> F2["💚 Fidelización<br/>🙂 Acepta otro semestre<br/>🙂 Recomienda a docentes"]

    style T fill:#dbeafe,stroke:#1e40af,stroke-width:2px,color:#000
    style D2 fill:#fef3c7,stroke:#b45309,color:#000
    style C2 fill:#fef3c7,stroke:#b45309,color:#000
    style A2 fill:#dbeafe,stroke:#1e40af,color:#000
    style O2 fill:#dbeafe,stroke:#1e40af,color:#000
    style U2 fill:#e0f2fe,stroke:#0369a1,color:#000
    style Cl2 fill:#fce7f3,stroke:#be185d,color:#000
    style F2 fill:#dcfce7,stroke:#15803d,color:#000
```

### Jurado — vista vertical

```mermaid
flowchart TB
    J((Jurado))
    J --> D3["🔍 Descubrimiento<br/>😐 Admin le comunica rol<br/>😐 Ve nombre TesisFar"]
    D3 --> C3["🤔 Consideración<br/>😕 Pregunta carga<br/>🙂 Acepta el panel"]
    C3 --> A3["📝 Adquisición<br/>🙂 Cuenta creada<br/>😐 Primer login"]
    A3 --> O3["🚀 Onboarding<br/>🙂 Descubre vista global<br/>😐 Revisa rúbrica"]
    O3 --> U3["⚙️ Uso<br/>🙂 Recibe agenda del día<br/>😐 Revisa proyectos<br/>🙂 Escucha defensa<br/>😕 Llena ratings JSON<br/>🙂 Escribe comentario<br/>🙂 Guarda Evaluation"]
    U3 --> Cl3["🎯 Cierre<br/>🙂 Cierra el día<br/>🙂 Confirma registros"]
    Cl3 --> F3["💚 Fidelización<br/>🙂 Vuelve otro semestre<br/>😐 Sugiere mejoras"]

    style J fill:#dbeafe,stroke:#1e40af,stroke-width:2px,color:#000
    style D3 fill:#fef3c7,stroke:#b45309,color:#000
    style C3 fill:#fef3c7,stroke:#b45309,color:#000
    style A3 fill:#dbeafe,stroke:#1e40af,color:#000
    style O3 fill:#dbeafe,stroke:#1e40af,color:#000
    style U3 fill:#e0f2fe,stroke:#0369a1,color:#000
    style Cl3 fill:#fce7f3,stroke:#be185d,color:#000
    style F3 fill:#dcfce7,stroke:#15803d,color:#000
```

### Administrador — vista vertical

```mermaid
flowchart TB
    A((Administrador))
    A --> D4["🔍 Descubrimiento<br/>🙂 Conoce la solución<br/>😕 Evalúa alternativas"]
    D4 --> C4["🤔 Consideración<br/>🙂 Verifica cobertura<br/>😄 Decide adoptar"]
    C4 --> A4["📝 Adquisición<br/>😐 Despliega stack<br/>🙂 Crea superuser"]
    A4 --> O4["🚀 Onboarding<br/>🙂 Configura meses<br/>😄 Activa Semester<br/>😐 Valida con usuarios prueba"]
    O4 --> U4["⚙️ Uso<br/>😐 Aprueba pending<br/>🙂 Asigna roles<br/>😕 Reasigna estudiantes<br/>🙂 Crea PresentationDay<br/>😐 Asigna jurados<br/>😐 Monitorea sesiones<br/>😕 Responde reclamos<br/>🙂 Fuerza estado PTEG<br/>😄 Dashboard por estado"]
    U4 --> Cl4["🎯 Cierre<br/>🙂 Verifica evaluaciones<br/>😄 Cierra el semestre"]
    Cl4 --> F4["💚 Fidelización<br/>😄 Activa siguiente semestre<br/>😄 Propone a otras carreras<br/>🙂 Solicita mejoras"]

    style A fill:#dbeafe,stroke:#1e40af,stroke-width:2px,color:#000
    style D4 fill:#fef3c7,stroke:#b45309,color:#000
    style C4 fill:#fef3c7,stroke:#b45309,color:#000
    style A4 fill:#dbeafe,stroke:#1e40af,color:#000
    style O4 fill:#dbeafe,stroke:#1e40af,color:#000
    style U4 fill:#e0f2fe,stroke:#0369a1,color:#000
    style Cl4 fill:#fce7f3,stroke:#be185d,color:#000
    style F4 fill:#dcfce7,stroke:#15803d,color:#000
```

---

## Puntos de dolor críticos (score ≤ 2)

| Rol          | Momento                                          | Score | Oportunidad                                  |
|--------------|--------------------------------------------------|-------|----------------------------------------------|
| Estudiante   | Espera activación (`status=pending`)             | 1     | Auto-activación por dominio institucional    |
| Estudiante   | Leer comentarios y corregir                      | 2     | Ratings detallados visibles + historial      |
| Estudiante   | Esperar resultado post-defensa                   | 2     | ✅ Notificación in-app + email automática (task `20260425-003`) — campana en header, bandeja en Configuración → Notificaciones |
| Tutor        | Evaluar carga al aceptar                         | 2     | Vista previa de asesorados antes de aceptar  |
| Jurado       | Llenar ratings y section_scores                  | 2     | Plantilla por tipo de proyecto (no JSON)     |
| Admin        | Reasignar estudiantes entre tutores              | 2     | Drag-and-drop bulk en planificación          |
| Admin        | Responder reclamos de los 3 roles                | 2     | Bandeja de incidencias / tickets             |

---

## Leyenda

| Puntaje | Emoji | Significado                                  |
|---------|-------|----------------------------------------------|
| 1       | 😟    | Muy frustrante — dolor real, bloquea al rol  |
| 2       | 😕    | Incómodo — fricción o espera                 |
| 3       | 😐    | Neutro — funciona pero sin brillo            |
| 4       | 🙂    | Satisfactorio — el sistema ayuda             |
| 5       | 😄    | Excelente — momento de valor claro           |
