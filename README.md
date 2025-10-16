# Tesisfar Frontend

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