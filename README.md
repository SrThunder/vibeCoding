# 🏗️ DOLMEN - Sistema de Recomendación de Materiales (RAG)

Sistema RAG híbrido para asistencia a vendedores en mostrador. Pregunta-Respuesta inteligente sobre productos de construcción.

## 📋 Requisitos

- Python 3.11+
- Pip
- Cuentas en: Supabase, OpenAI, Render, Streamlit Cloud

## 🚀 Instalación Local (Desarrollo)

### 1. Clonar el repositorio
```bash
git clone <repo-url>
cd vibeCoding
```

### 2. Crear entorno virtual
```bash
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# o
venv\Scripts\activate     # Windows
```

### 3. Instalar dependencias
```bash
pip install -r backend/requirements.txt
```

### 4. Configurar variables de entorno
```bash
# Copiar archivo de ejemplo
cp backend/.env.example backend/.env

# Editar .env con tus credenciales
nano backend/.env
```

**Variables requeridas:**
```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key
OPENAI_API_KEY=sk-your-key
JWT_SECRET_KEY=your-super-secret-key
CATALOG_PDF_URL=https://dolmen.com/catalogo.pdf
```

### 5. Ejecutar backend
```bash
cd backend
uvicorn main:app --reload
# Backend corriendo en http://localhost:8000
```

### 6. Ejecutar frontend (en otra terminal)
```bash
cd frontend
streamlit run app.py
# Frontend en http://localhost:8501
```

## 🛠️ Configuración en Supabase

### 1. Crear extensión vector
En SQL Editor:
```sql
CREATE EXTENSION vector;
```

### 2. Crear tablas
```sql
-- Tabla de usuarios
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  local_id TEXT NOT NULL,
  role TEXT DEFAULT 'vendedor',
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Tabla de refresh tokens
CREATE TABLE refresh_tokens (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  token_hash TEXT NOT NULL,
  expires_at TIMESTAMP NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Tabla de productos
CREATE TABLE products (
  id TEXT PRIMARY KEY,
  product_id TEXT NOT NULL,
  nombre TEXT NOT NULL,
  categoria TEXT NOT NULL,
  subcategoria TEXT,
  descripcion TEXT,
  contenido TEXT,
  variantes TEXT[],
  usos TEXT[],
  beneficios TEXT[],
  pdf_link TEXT,
  stock BOOLEAN DEFAULT TRUE,
  local_id TEXT NOT NULL,
  vector vector(1536),
  created_at TIMESTAMP DEFAULT NOW()
);

-- Tabla de FAQs
CREATE TABLE faqs (
  id TEXT PRIMARY KEY,
  question TEXT NOT NULL,
  answer TEXT NOT NULL,
  category TEXT,
  pdf_link TEXT,
  local_id TEXT NOT NULL,
  vector vector(1536),
  created_at TIMESTAMP DEFAULT NOW()
);

-- Tabla de logs
CREATE TABLE logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  local_id TEXT NOT NULL,
  query TEXT NOT NULL,
  response TEXT NOT NULL,
  product_recommended TEXT,
  pdf_link_sent TEXT,
  confidence FLOAT,
  source TEXT,
  timestamp TIMESTAMP DEFAULT NOW()
);
```

### 3. Crear índices vectoriales
```sql
CREATE INDEX ON products USING ivfflat (vector vector_cosine_ops) WITH (lists = 100);
CREATE INDEX ON faqs USING ivfflat (vector vector_cosine_ops) WITH (lists = 100);
```

### 4. Crear funciones de búsqueda
Ver `rag_pipeline.py` - copiar las funciones SQL `search_faqs()` y `search_products()`

## 📊 Ingesta de Datos

### 1. Ejecutar script de ingesta
```bash
python scripts/ingest_catalog.py
```

Esto:
- Carga productos desde `catalogo_jerarquia.json`
- Carga FAQs desde `faq_poc.json`
- Genera embeddings con OpenAI
- Popula las tablas en Supabase

### 2. Crear usuarios de prueba
```python
from backend.main import hash_password
import requests

# Registrar usuario demo
response = requests.post(
    "http://localhost:8000/auth/register",  # endpoint por implementar si es necesario
    json={
        "email": "demo@dolmen.com",
        "password": "demo123",
        "local_id": "LOCAL_001"
    }
)
```

O insertar directamente en Supabase:
```sql
INSERT INTO users (email, password_hash, local_id)
VALUES ('demo@dolmen.com', 'hashed_password', 'LOCAL_001');
```

## 📝 Estructura del Proyecto

```
vibeCoding/
├── backend/
│   ├── main.py              # FastAPI principal
│   ├── rag_pipeline.py      # Pipeline RAG
│   ├── requirements.txt
│   ├── .env.example
│   └── .gitignore
├── frontend/
│   └── app.py               # Streamlit frontend
├── scripts/
│   └── ingest_catalog.py    # Script de ingesta
├── catalogo_jerarquia.json  # Catálogo normalizado
├── faq_poc.json             # FAQs POC
├── plan_proyecto            # Documentación del plan
└── README.md
```

## 🔐 Seguridad

- **Autenticación:** JWT con access + refresh tokens
- **Contraseñas:** Hasheadas con bcrypt
- **Tokens:** Refresh tokens hasheados en BD
- **CORS:** Habilitado para Streamlit Cloud
- **Secretos:** Usar variables de entorno, nunca hardcodear

## 🚢 Despliegue a Producción

### Backend en Render
```bash
# 1. Conectar repo GitHub
# 2. Crear Web Service
# 3. Configurar variables de entorno
# 4. Deploy automático
```

**Comando de inicio:**
```
uvicorn main:app --host 0.0.0.0 --port $PORT
```

### Frontend en Streamlit Cloud
```bash
# 1. Conectar repo GitHub
# 2. Seleccionar rama y archivo app.py
# 3. Configurar BACKEND_URL en secrets
# 4. Deploy automático
```

## 📊 API Endpoints

### Autenticación
- `POST /auth/login` - Login (email + password)
- `POST /auth/refresh` - Renovar access token
- `POST /auth/logout` - Logout y revocar tokens

### RAG
- `POST /query` - Procesar pregunta sobre productos
- `GET /me` - Info del usuario actual
- `GET /catalog/pdf` - URL del catálogo PDF

### Utilidad
- `GET /health` - Health check

## 🧪 Testing

```bash
# Testear login
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@dolmen.com","password":"demo123"}'

# Testear query (usar token del login)
curl -X POST "http://localhost:8000/query" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"pregunta":"¿Qué pintura recomiendan para exterior?"}'
```

## 📞 Soporte

Para preguntas o issues, contactar al equipo de desarrollo.

## 📄 Licencia

Propietario de DOLMEN
