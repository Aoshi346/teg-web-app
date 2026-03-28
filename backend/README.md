# Tesisfar Backend

API backend para el sistema de gestión del Trabajo Especial de Grado (TEG), construida con Node.js, Express y PostgreSQL.

## 🚀 Características

- **Runtime**: Node.js 18+
- **Framework**: Express.js
- **Base de Datos**: PostgreSQL con Prisma ORM
- **Autenticación**: JWT con refresh tokens
- **Validación**: Joi para validación de esquemas
- **Documentación**: Swagger/OpenAPI
- **Testing**: Jest y Supertest
- **Logging**: Winston
- **Seguridad**: Helmet, CORS, Rate limiting

## 📦 Dependencias Principales

```json
{
  "express": "^4.18.2",
  "prisma": "^5.0.0",
  "@prisma/client": "^5.0.0",
  "jsonwebtoken": "^9.0.0",
  "bcryptjs": "^2.4.3",
  "joi": "^17.9.0",
  "helmet": "^7.0.0",
  "cors": "^2.8.5",
  "express-rate-limit": "^6.8.0",
  "winston": "^3.10.0",
  "nodemailer": "^6.9.0"
}
```

## 🛠️ Instalación

1. **Instalar dependencias**
   ```bash
   npm install
   ```

2. **Configurar variables de entorno**
   ```bash
   cp .env.example .env
   ```
   
   Configurar en `.env`:
   ```env
   NODE_ENV=development
   PORT=5000
   DATABASE_URL="postgresql://username:password@localhost:5432/Tesisfar"
   JWT_SECRET=your_jwt_secret
   JWT_REFRESH_SECRET=your_refresh_secret
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_USER=your_email@gmail.com
   EMAIL_PASS=your_app_password
   ```

3. **Configurar base de datos**
   ```bash
   npx prisma generate
   npx prisma db push
   npx prisma db seed
   ```

4. **Ejecutar en desarrollo**
   ```bash
   npm run dev
   ```

5. **Verificar funcionamiento**
   ```
   http://localhost:5000/api/health
   ```

## 📁 Estructura de Carpetas

```
src/
├── controllers/           # Controladores de rutas
│   ├── auth.controller.js
│   ├── user.controller.js
│   ├── teg.controller.js
│   └── evaluation.controller.js
├── models/               # Modelos de datos
│   ├── User.js
│   ├── TEG.js
│   └── Evaluation.js
├── routes/               # Definición de rutas
│   ├── auth.routes.js
│   ├── user.routes.js
│   ├── teg.routes.js
│   └── evaluation.routes.js
├── middleware/           # Middleware personalizado
│   ├── auth.middleware.js
│   ├── validation.middleware.js
│   ├── error.middleware.js
│   └── upload.middleware.js
├── services/             # Lógica de negocio
│   ├── auth.service.js
│   ├── user.service.js
│   ├── teg.service.js
│   └── email.service.js
├── utils/                # Utilidades
│   ├── logger.js
│   ├── validation.js
│   └── helpers.js
├── config/               # Configuraciones
│   ├── database.js
│   ├── jwt.js
│   └── email.js
└── app.js                # Aplicación principal
```

## 🗄️ Modelo de Datos

### Usuario
```typescript
interface User {
  id: string
  email: string
  password: string
  firstName: string
  lastName: string
  role: 'student' | 'tutor' | 'admin'
  studentId?: string
  department?: string
  createdAt: Date
  updatedAt: Date
}
```

### TEG (Trabajo Especial de Grado)
```typescript
interface TEG {
  id: string
  title: string
  description: string
  studentId: string
  tutorId: string
  status: 'draft' | 'submitted' | 'under_review' | 'approved' | 'rejected'
  submissionDate?: Date
  defenseDate?: Date
  finalGrade?: number
  createdAt: Date
  updatedAt: Date
}
```

### Evaluación
```typescript
interface Evaluation {
  id: string
  tegId: string
  evaluatorId: string
  criteria: {
    content: number
    methodology: number
    presentation: number
    innovation: number
  }
  comments: string
  recommendation: 'approve' | 'reject' | 'revise'
  submittedAt: Date
}
```

## 🔐 Autenticación

### JWT Tokens
- **Access Token**: 15 minutos
- **Refresh Token**: 7 días
- **Algoritmo**: HS256

### Endpoints de Autenticación
```bash
POST /api/auth/register    # Registro de usuario
POST /api/auth/login       # Inicio de sesión
POST /api/auth/refresh     # Renovar token
POST /api/auth/logout      # Cerrar sesión
POST /api/auth/forgot      # Recuperar contraseña
POST /api/auth/reset       # Resetear contraseña
```

## 📡 API Endpoints

### Usuarios
```bash
GET    /api/users          # Listar usuarios
GET    /api/users/:id      # Obtener usuario
PUT    /api/users/:id      # Actualizar usuario
DELETE /api/users/:id      # Eliminar usuario
```

### TEG
```bash
GET    /api/teg            # Listar TEGs
POST   /api/teg            # Crear TEG
GET    /api/teg/:id        # Obtener TEG
PUT    /api/teg/:id        # Actualizar TEG
DELETE /api/teg/:id        # Eliminar TEG
POST   /api/teg/:id/submit # Enviar TEG
```

### Evaluaciones
```bash
GET    /api/evaluations    # Listar evaluaciones
POST   /api/evaluations    # Crear evaluación
GET    /api/evaluations/:id # Obtener evaluación
PUT    /api/evaluations/:id # Actualizar evaluación
```

## 🛡️ Middleware

### Autenticación
```javascript
const authMiddleware = (req, res, next) => {
  // Verificar JWT token
  // Agregar usuario a req.user
  next()
}
```

### Validación
```javascript
const validateRequest = (schema) => {
  return (req, res, next) => {
    const { error } = schema.validate(req.body)
    if (error) {
      return res.status(400).json({ error: error.details[0].message })
    }
    next()
  }
}
```

### Manejo de Errores
```javascript
const errorHandler = (err, req, res, next) => {
  // Log del error
  // Respuesta apropiada
  res.status(err.status || 500).json({
    error: err.message || 'Error interno del servidor'
  })
}
```

## 📧 Servicios

### Email Service
- Envío de notificaciones
- Recuperación de contraseña
- Invitaciones a evaluadores
- Recordatorios de fechas límite

### File Upload
- Subida de documentos TEG
- Validación de tipos de archivo
- Compresión de imágenes
- Almacenamiento en cloud

## 🧪 Testing

### Configuración
```bash
# Instalar dependencias de testing
npm install --save-dev jest supertest

# Ejecutar tests
npm run test

# Tests con coverage
npm run test:coverage

# Tests en modo watch
npm run test:watch
```

### Estructura de Tests
```
tests/
├── unit/                 # Tests unitarios
│   ├── controllers/
│   ├── services/
│   └── utils/
├── integration/          # Tests de integración
│   ├── auth.test.js
│   ├── teg.test.js
│   └── evaluation.test.js
└── fixtures/             # Datos de prueba
    ├── users.json
    └── teg.json
```

## 📊 Logging

### Winston Configuration
```javascript
const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  transports: [
    new winston.transports.File({ filename: 'error.log', level: 'error' }),
    new winston.transports.File({ filename: 'combined.log' })
  ]
})
```

## 🔒 Seguridad

### Headers de Seguridad
- Helmet para headers HTTP
- CORS configurado
- Rate limiting
- Validación de entrada

### Validación de Datos
- Joi para esquemas
- Sanitización de entrada
- Validación de tipos
- Límites de tamaño

## 🚀 Deployment

### Docker
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
EXPOSE 5000
CMD ["npm", "start"]
```

### Variables de Entorno de Producción
```env
NODE_ENV=production
PORT=5000
DATABASE_URL=postgresql://...
JWT_SECRET=strong_secret
```

## 📈 Monitoreo

### Health Checks
```bash
GET /api/health          # Estado de la API
GET /api/health/db       # Estado de la base de datos
GET /api/health/redis    # Estado de Redis (si se usa)
```

### Métricas
- Tiempo de respuesta
- Tasa de errores
- Uso de memoria
- Conexiones de DB

## 🔧 Scripts

```bash
npm run dev              # Desarrollo con nodemon
npm run start            # Producción
npm run build            # Construir para producción
npm run test             # Ejecutar tests
npm run test:coverage    # Tests con coverage
npm run lint             # Linter ESLint
npm run db:generate      # Generar cliente Prisma
npm run db:push          # Sincronizar esquema
npm run db:seed          # Poblar base de datos
```

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
