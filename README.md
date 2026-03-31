# Tesisfar Frontend

Aplicación frontend para el sistema de gestión del Trabajo Especial de Grado (TEG), construida con Next.js 15, TypeScript y Tailwind CSS.

## 🚀 Características

- **Framework**: Next.js 15 con App Router
### Tesisfar Frontend

Aplicación frontend para el sistema de gestión del Trabajo Especial de Grado (TEG), construida con Next.js 15, TypeScript y Tailwind CSS.

## 🚀 Características

- **Framework**: Next.js 15 con App Router
- **Lenguaje**: TypeScript para tipado estático
- **Estilos**: Tailwind CSS con diseño responsive
- **Componentes**: shadcn/ui para componentes modernos
- **Animaciones**: GSAP y Framer Motion
- **Autenticación**: Integración con Supabase
- **Performance**: Optimizado para velocidad y SEO

## 📦 Dependencias Principales

```json
{
  "next": "15.5.0",
  "react": "19.1.0",
  "typescript": "^5",
  "tailwindcss": "^4",
  "@radix-ui/react-slot": "^1.2.3",
  "gsap": "^3.13.0",
  "framer-motion": "^12.23.12",
  "@supabase/supabase-js": "^2.56.1"
}
```

## 🛠️ Instalación

1. **Instalar dependencias**
   ```bash
   npm install
   ```

2. **Configurar variables de entorno**
   ```bash
   cp .env.example .env.local
   ```
   
   Configurar en `.env.local`:
   ```env
   NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
   NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
   ```

3. **Ejecutar en desarrollo**
   ```bash
   npm run dev
   ```

4. **Abrir en navegador**
   ```
   http://localhost:3000
   ```

## 📁 Estructura de Carpetas

```
src/
├── app/                    # App Router de Next.js
│   ├── globals.css        # Estilos globales
│   ├── layout.tsx         # Layout principal
│   └── page.tsx           # Página de inicio
├── components/            # Componentes reutilizables
│   ├── ui/               # Componentes base (shadcn/ui)
│   │   ├── button.tsx    # Botón personalizado
│   │   ├── card.tsx      # Tarjeta personalizada
│   │   └── input.tsx     # Input personalizado
│   ├── Header.tsx        # Header de navegación
│   ├── Hero.tsx          # Sección hero con animaciones
│   ├── FeaturesSection.tsx # Sección de características
│   ├── Footer.tsx        # Footer de la página
│   ├── LoginModal.tsx    # Modal de autenticación
│   └── FeatureCard.tsx   # Tarjeta de característica
└── lib/                  # Utilidades y configuraciones
    └── utils.ts          # Funciones utilitarias
```

## 🎨 Componentes

### Header
- Navegación responsive
- Logo de la universidad
- Botón de autenticación
- Animaciones con GSAP

### Hero
- Imagen de fondo con efecto Ken Burns
- Texto animado con gradientes
- Indicador de scroll animado
- Diseño responsive

### FeaturesSection
- Secciones para estudiantes y docentes
- Animaciones de scroll trigger
- Tarjetas de características
- Diseño en grid responsive

### LoginModal
- Modal de autenticación
- Formularios de login y registro
- Validación de campos
- Animaciones de transición

## 🎭 Animaciones

### GSAP
- Animaciones de entrada
- Efectos de hover
- Transiciones suaves
- Scroll triggers

### Framer Motion
- Animaciones de componentes
- Gestos de usuario
- Transiciones de página

## 🎨 Diseño

### Colores
- **Primario**: Indigo (#4F46E5)
- **Secundario**: Blue (#3B82F6)
- **Acento**: Yellow (#FBBF24)
- **Fondo**: Slate (#F8FAFC)

### Tipografía
- **Sans**: Geist Sans
- **Mono**: Geist Mono

### Breakpoints
- **Mobile**: 320px - 768px
- **Tablet**: 768px - 1024px
- **Desktop**: 1024px+

## 📱 Responsive Design

- Mobile-first approach
- Grid system flexible
- Componentes adaptativos
- Imágenes optimizadas

## 🔧 Scripts

```bash
npm run dev          # Desarrollo con hot reload
npm run build        # Construcción para producción
npm run start        # Ejecutar en producción
npm run lint         # Linter ESLint
npm run type-check   # Verificación de tipos
```

## 🚀 Deployment

### Vercel (Recomendado)
1. Conectar repositorio a Vercel
2. Configurar variables de entorno
3. Deploy automático en cada push

### Otras Plataformas
- Netlify
- AWS Amplify
- Railway

## 🐛 Debugging

### Herramientas de Desarrollo
- React Developer Tools
- Next.js DevTools
- Chrome DevTools

### Logs
```bash
# Ver logs en desarrollo
npm run dev

# Ver logs de build
npm run build
```

## 📊 Performance

### Métricas Objetivo
- **LCP**: < 2.5s
- **FID**: < 100ms
- **CLS**: < 0.1
- **FCP**: < 1.8s

### Optimizaciones
- Image optimization con Next.js
- Code splitting automático
- Lazy loading de componentes
- Bundle analysis

## 🔒 Seguridad

- Validación de entrada
- Sanitización de datos
- HTTPS obligatorio
- Headers de seguridad

## 🧪 Testing

```bash
# Ejecutar tests
npm run test

# Tests con coverage
npm run test:coverage

# Tests e2e
npm run test:e2e
```

## 📈 Analytics

- Google Analytics 4
- Vercel Analytics
- Custom events tracking

## 🌐 Internacionalización

- Soporte para múltiples idiomas
- Localización de fechas
- Formateo de números

## 📝 Contribución

1. Fork el proyecto
2. Crea una rama feature
3. Commit tus cambios
4. Push a la rama
5. Abre un Pull Request

## 📄 Licencia

MIT License - ver LICENSE para detalles.

---

**Desarrollado con ❤️ para la Universidad Santa María**

## 🎯 Objetivos y Alcance del Proyecto

### Objetivo General de la APP

La aplicación TesisFar tiene como objetivo general proporcionar una plataforma web integrada, segura y accesible para la gestión completa del Trabajo Especial de Grado (TEG). Busca centralizar y automatizar el flujo de trabajo entre estudiantes, tutores, jurados y personal administrativo, facilitando la entrega de documentos, la evaluación mediante rúbricas, la programación de defensas y la generación de reportes institucionales. La plataforma pretende mejorar la trazabilidad, reducir errores administrativos y ofrecer herramientas analíticas que apoyen la toma de decisiones académicas.

### Objetivos Específicos

- Proveer un portal de usuario con roles (estudiante, tutor/docente, jurado, administrador) y control de acceso granular.
- Permitir la subida y gestión de entregables (documentos, anexos, versiones) con control de versiones y metadatos.
- Implementar un sistema de plazos y recordatorios automáticos (notificaciones por correo y notificaciones en la interfaz) que reduzca incumplimientos de fechas.
- Facilitar la evaluación mediante rúbricas configurables, registro de calificaciones y comentarios estructurados por entregable.
- Soportar la organización y notificación de convocatorias y defensas (calendario, asignación de jurados, comunicación con participantes).
- Generar reportes exportables (CSV / PDF) para seguimiento académico y auditoría administrativa.
- Mantener trazabilidad y registro de acciones (audit logs) para cumplir requisitos institucionales de control y seguridad.
- Garantizar una experiencia accesible y responsive para dispositivos móviles y de escritorio, con buenas prácticas de usabilidad.

### Alcances Esperados (Qué incluye y qué queda fuera)

Incluido (in-scope):

- Módulo de autenticación y gestión de sesiones (registro, inicio de sesión, roles) con integración básica a proveedores (ej. Supabase como demo).
- Interfaz pública (landing page) y sección privada (dashboard) que muestra información contextualizada por rol.
- Flujo de entregas: creación de entregables, subida de archivos, control de versiones y metadatos (título, fecha, estado).
- Sistema de plazos y notificaciones: recordatorios programados, alertas en la UI y envío de correos mediante adaptadores configurables.
- Rúbricas: creación/edición de rúbricas por administradores, uso de rúbricas por jurados y tutores para evaluación.
- Gestión de jurados y programación de defensas: invitaciones, confirmaciones y vista de calendario.
- Generación de reportes: listados filtrables, exportación CSV, y plantilla básica para PDF (por ejemplo, actas de evaluación).
- Registro de auditaría (quién hizo qué y cuándo) para entregables y calificaciones.
- Calidad de experiencia: accesibilidad básica (WCAG-level considerations), responsive design, y rendimiento frontend optimizado.

Fuera de alcance (out-of-scope inicialmente):

- Integración profunda y bidireccional con sistemas externos institucionales (SIS/ERP) que requieran adaptadores específicos o SSO corporativo avanzado.
- Funcionalidades avanzadas de detección automática de plagio, análisis semántico o calificación automática por IA.
- Videoconferencias integradas o streaming en vivo de defensas (se pueden integrar mediante enlaces externos, pero no se provee infraestructura de videoconferencia).
- Soporte offline avanzado o sincronización compleja entre dispositivos sin conexión.

Restricciones y supuestos clave:

- La primera fase asume almacenamiento de archivos en el proveedor configurado (p. ej. Supabase Storage o bucket S3) y un límite razonable por archivo (ej. 50 MB por archivo), ampliable según necesidades.
- La seguridad del sistema dependerá de la correcta configuración de variables de entorno y de los controles del proveedor (TLS, políticas CORS, reglas de almacenamiento).
- La solución está pensada como MVP/POC: prioriza estabilidad, seguridad y facilidad de despliegue; funcionalidades avanzadas pueden planificarse en iteraciones posteriores.

Criterios de aceptación y métricas de éxito:

- Usuarios (estudiantes/tutores) pueden completar el flujo de entrega y confirmación de recepción en menos de 5 pasos.
- Jurados pueden evaluar un entregable usando una rúbrica y dejar retroalimentación en menos de 10 minutos por evaluación promedio.
- El sistema envía notificaciones de recordatorio con al menos 95% de entrega en entorno de pruebas (dependiente del proveedor de correo configurado).
- Métricas de rendimiento objetivo: LCP < 2.5s, CLS < 0.1 en escenarios típicos de laboratorio.
- Trazabilidad mínima: todas las acciones críticas (subida, evaluación, cambios de estado) registradas con user-id y timestamp.

Entregables esperados al finalizar la primera versión (MVP):

- Código fuente frontend con documentación de despliegue y configuración (.env.example). 
- Componentes clave: autenticación, panel de usuario, módulos de entrega, rúbricas, calendario de defensas y generación básica de reportes.
- Documentación de uso y guía rápida para administradores y docentes.
- Tests básicos (unitarios/integ.) para los flujos críticos y verificación de tipado mediante TypeScript.

Roadmap sugerido (alto nivel):

1. MVP: autenticación, entrega de documentos, evaluación con rúbricas, notificaciones básicas y reportes exportables.
2. Integraciones: almacenamiento escalable, correo institucional, SSO (opcional) y sincronización con calendarios institucionales.
3. Mejora UX/Accesibilidad y optimizaciones de rendimiento.
4. Funcionalidades avanzadas (plagio, analítica avanzada, automatizaciones) y soporte a gran escala.

---
