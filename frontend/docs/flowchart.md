# Flujogramas del Proyecto (Mermaid)

> Referencia rápida en español, centrada en el rol **Docente/Evaluador** (otros roles se integrarán más adelante).

## Navegación principal (rol Docente/Evaluador)
```mermaid
flowchart TD
  subgraph Rol
    U[Docente / Evaluador]
  end

  L[Login] --> D[Dashboard]
  D --> PFiltros[Buscar / Filtrar / Ordenar]
  D --> P[Proyectos]
  D --> T[Tesis]

  P --> PList[Listado de Proyectos]
  T --> TList[Listado de Tesis]

  PList --> PDet[Detalle de Proyecto]
  TList --> TDet[Detalle de Tesis]

  %% Proyectos
  PDet --> PEval["Evaluar Proyecto"]
  PEval --> PScore["Calcular puntaje 0-20"]
  PScore --> PEstado["Asignar estado: Aprobado/Pendiente/Rechazado"]
  PEstado --> PRes["Resultado mostrado"]

  %% Tesis con dos fases
  TDet --> F1["Fase 1 Evaluacion"]
  F1 --> TScore1["Puntaje F1 0-20"]
  TScore1 -->|">= 15"| SaveSession["Guardar pass en sessionStorage (demo)"]
  SaveSession --> GatePass["Habilitar Fase 2"]
  TScore1 -->|"< 15"| GateBlock["Bloqueo: sin acceso a F2"]
  GatePass --> F2["Fase 2 Evaluacion"]
  F2 --> TScore2["Puntaje F2 0-20"]
  TScore2 --> TRes["Resultado final mostrado"]
```

## Flujo detallado: Proyectos (Docente)
```mermaid
flowchart TD
  U[Docente] --> Login[Login]
  Login --> Dash[Dashboard]
  Dash --> ProyList[Listado de Proyectos]
  ProyList --> Card[Card ProjectCard]
  Card --> Det[Detalle de Proyecto]
  Det --> Eval[Formulario de Evaluación]
  Eval --> Puntaje["Calcular puntaje 0-20"]
  Puntaje --> Estado[Asignar estado]
  Estado --> Resultado[Mostrar resultado]
```

## Flujo detallado: Tesis (Docente, con Fase 1 / Fase 2)
```mermaid
flowchart TD
  U[Docente] --> Login[Login]
  Login --> Dash[Dashboard]
  Dash --> TesisList[Listado de Tesis]
  TesisList --> Card[Card ProjectCard]
  Card --> Det[Tesis Detalle]
  Det --> F1["Fase 1"]
  F1 --> Resp1["Responder preguntas F1"]
  Resp1 --> Score1["Calcular puntaje F1 0-20"]
  Score1 -->|">= 15"| SaveSession["Guardar pass en sessionStorage (demo)"]
  SaveSession --> FlagPass["Marcar F1 aprobada"]
  Score1 -->|"< 15"| FlagFail["Mostrar bloqueo de F2"]
  FlagPass --> F2["Fase 2"]
  F2 --> Resp2["Responder preguntas F2"]
  Resp2 --> Score2["Calcular puntaje F2 0-20"]
  Score2 --> Res[Resultado final]
```

### Notas
- Puntaje: escala 0–20; umbral de aprobación ≥ 15.
- Datos mock: `src/lib/data/mockData.ts`.
- Lógica de puntaje: `src/lib/questions/scoring.ts`.
- Gateo de Fase 2 (tesis): depende de aprobar Fase 1 (demo actual: `sessionStorage`).
- Rutas de detalle: `/dashboard/proyectos/[id]`, `/dashboard/tesis/[id]`.
- El foco actual es el rol Docente/Evaluador; otros roles (admin, estudiante) se añadirán más adelante.
