# Tesisfar - Sistema de Gestión del Trabajo Especial de Grado

![Tesisfar Logo](frontend/public/usmlogo.png)

## 📋 Descripción

Tesisfar es una plataforma web moderna y completa para la gestión, entrega y evaluación del Trabajo Especial de Grado (TEG). Diseñada específicamente para la Universidad Santa María, facilita la colaboración entre estudiantes, tutores y jurados, centralizando todo el proceso de evaluación en una interfaz intuitiva y eficiente.

## ✨ Características Principales

### Para Estudiantes
- 📝 **Gestión de Entregas**: Registro y seguimiento de entregas con fechas límite
- 🤝 **Colaboración**: Comunicación directa con tutores y compañeros
- 📚 **Recursos Centralizados**: Acceso a guías, plantillas y material de apoyo
- 📊 **Seguimiento de Progreso**: Visualización del estado del proyecto

### Para Docentes
- 👥 **Gestión de Jurados**: Organización y asignación de evaluadores
- 📋 **Evaluación con Rúbricas**: Sistema de calificación estructurado
- 📅 **Calendario de Defensas**: Programación y gestión de fechas
- 💬 **Retroalimentación**: Comentarios y sugerencias detalladas

## 🚀 Tecnologías

### Frontend
- **Next.js 15** - Framework React con App Router
- **TypeScript** - Tipado estático para mayor robustez
- **Tailwind CSS** - Framework de estilos utilitarios
- **shadcn/ui** - Componentes de interfaz modernos
- **GSAP** - Animaciones fluidas y atractivas
- **Framer Motion** - Animaciones adicionales
- **Supabase** - Autenticación y base de datos

### Backend (Próximamente)
- **Node.js** - Runtime de JavaScript
- **Express.js** - Framework web
- **PostgreSQL** - Base de datos relacional
- **Prisma** - ORM para TypeScript
- **JWT** - Autenticación basada en tokens

## 📁 Estructura del Proyecto

```
TEG project/
├── frontend/                 # Aplicación Next.js
│   ├── src/
│   │   ├── app/             # Páginas y layouts
│   │   ├── components/      # Componentes reutilizables
│   │   ├── lib/            # Utilidades y configuraciones
│   │   └── types/          # Definiciones de TypeScript
│   ├── public/             # Archivos estáticos
│   └── package.json        # Dependencias del frontend
├── backend/                # API y lógica del servidor
│   ├── src/
│   │   ├── controllers/    # Controladores de rutas
│   │   ├── models/         # Modelos de datos
│   │   ├── routes/         # Definición de rutas
│   │   ├── middleware/     # Middleware personalizado
│   │   └── utils/          # Utilidades del servidor
│   └── package.json        # Dependencias del backend
└── README.md              # Este archivo
```

## 🛠️ Instalación y Configuración

### Prerrequisitos
- Node.js 18+ 
- npm o yarn
- Git

### Instalación del Frontend

1. **Clonar el repositorio**
   ```bash
   git clone <repository-url>
   cd TEG project
   ```

2. **Instalar dependencias**
   ```bash
   cd frontend
   npm install
   ```

3. **Configurar variables de entorno**
   ```bash
   cp .env.example .env.local
   ```
   Editar `.env.local` con tus configuraciones:
   ```env
   NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
   NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
   ```

4. **Ejecutar en desarrollo**
   ```bash
   npm run dev
   ```

5. **Abrir en el navegador**
   ```
   http://localhost:3000
   ```

### Instalación del Backend (Próximamente)

```bash
cd backend
npm install
npm run dev
```

## 🎯 Roadmap

### Fase 1 - MVP (Actual)
- [x] Landing page con animaciones
- [x] Sistema de autenticación básico
- [x] Diseño responsive
- [x] Componentes UI base

### Fase 2 - Funcionalidades Core
- [ ] Dashboard de estudiantes
- [ ] Sistema de entregas
- [ ] Gestión de tutores
- [ ] Notificaciones básicas

### Fase 3 - Evaluación
- [ ] Sistema de rúbricas
- [ ] Calendario de defensas
- [ ] Gestión de jurados
- [ ] Reportes y estadísticas

### Fase 4 - Avanzado
- [ ] Integración con sistemas universitarios
- [ ] App móvil
- [ ] Analytics avanzados
- [ ] Automatización de procesos

## 🤝 Contribución

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📝 Scripts Disponibles

### Frontend
```bash
npm run dev          # Ejecutar en desarrollo
npm run build        # Construir para producción
npm run start        # Ejecutar en producción
npm run lint         # Ejecutar linter
npm run type-check   # Verificar tipos TypeScript
```

## 🐛 Reportar Issues

Si encuentras algún bug o tienes una sugerencia, por favor:

1. Verifica que no haya un issue similar ya reportado
2. Crea un nuevo issue con:
   - Descripción detallada del problema
   - Pasos para reproducir
   - Capturas de pantalla (si aplica)
   - Información del entorno

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 👥 Equipo

- **Aoshi Blanco** - Desarrollador Principal
- **Universidad Santa María** - Institución

## 📞 Contacto

- **Email**: decanato.farmacia@usm.edu.ve
- **Universidad**: Universidad Santa María
- **Dirección**: La Florencia - Caracas. Km. 3 de la carretera Petare-Santa Lucía, Estado Miranda

## 🙏 Agradecimientos

- Universidad Santa María por el apoyo y recursos
- Comunidad de Next.js por la excelente documentación
- Contribuidores de las librerías utilizadas

---

**Tesisfar** - Simplificando la gestión del Trabajo Especial de Grado 🎓
