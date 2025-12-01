# 🛠️ Guía de Troubleshooting - DOLMEN RAG MVP

## 📋 Índice Rápido

1. **Problemas de Conexión**
2. **Errores de Autenticación**
3. **Problemas de RAG/Embeddings**
4. **Errores de Deployment**
5. **Performance y Timeouts**
6. **Problemas de Tokens**

---

## 1. Problemas de Conexión 🔌

### Error: "Could not connect to Supabase"

**Síntomas:**
```
Error: Failed to connect to supabase
timeout: the server did not respond in time
```

**Causas Posibles:**
- SUPABASE_URL incorrea
- SUPABASE_KEY expirada o inválida
- Firewall bloquea conexión a Supabase
- Red sin conexión a Internet

**Soluciones:**
1. Verifica credenciales en `.env`:
   ```bash
   echo $SUPABASE_URL
   echo $SUPABASE_KEY
   ```

2. Prueba conexión directa con psycopg2:
   ```bash
   python -c "
   import psycopg2
   conn = psycopg2.connect(
       host='xxxxx.supabase.co',
       port=5432,
       database='postgres',
       user='postgres',
       password='your-key',
       sslmode='require'
   )
   print('✅ Conexión exitosa')
   conn.close()
   "
   ```

3. Verifica que la extensión vector esté habilitada:
   ```sql
   SELECT * FROM pg_extension WHERE extname = 'vector';
   ```

---

### Error: "Table 'products' does not exist"

**Soluciones:**
1. Ejecuta el script setup:
   ```bash
   python scripts/setup_supabase.py
   ```

2. Verifica tablas creadas:
   ```bash
   python -c "
   from supabase import create_client
   supabase = create_client('https://xxxxx.supabase.co', 'key')
   response = supabase.table('products').select('COUNT(*)').execute()
   print(response)
   "
   ```

3. Si aún no existen, crea manualmente en Supabase SQL Editor:
   ```sql
   -- Ver plan_proyecto sección "Supabase Setup"
   CREATE TABLE products (
       id SERIAL PRIMARY KEY,
       product_id VARCHAR(50),
       local_id VARCHAR(50),
       nombre VARCHAR(255),
       -- ... más campos en README.md
   );
   ```

---

## 2. Errores de Autenticación 🔐

### Error: "Invalid credentials" en login

**Síntomas:**
```
POST /auth/login → 401 Unauthorized
Invalid credentials
```

**Causas Posibles:**
- Usuario no existe en tabla `users`
- Contraseña incorrecta
- Email incorrecto
- Usuario está inactivo

**Soluciones:**
1. Verifica usuario demo existe:
   ```bash
   python scripts/setup_supabase.py
   ```

2. Verifica usuario en Supabase:
   ```sql
   SELECT email, role FROM users WHERE email = 'demo@dolmen.com';
   ```

3. Resetea contraseña si es necesario:
   ```bash
   python -c "
   from passlib.context import CryptContext
   pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
   print(pwd_context.hash('demo123'))
   "
   # Copia el hash y actualiza en Supabase
   ```

---

### Error: "Invalid token" en query

**Síntomas:**
```
POST /query → 401 Unauthorized
Invalid token
```

**Causas Posibles:**
- Token expirado (15 minutos)
- Token malformado
- JWT_SECRET_KEY diferente entre instancias
- Header Authorization incorrecto

**Soluciones:**
1. Verifica header en Streamlit (frontend/app.py):
   ```python
   headers = {"Authorization": f"Bearer {access_token}"}
   # Debe ser: "Bearer <token>" exactamente
   ```

2. Verifica JWT_SECRET_KEY es el mismo en todas partes:
   ```bash
   # En backend
   echo $JWT_SECRET_KEY
   # Debe ser único pero consistente
   ```

3. Obtén nuevo token con refresh:
   ```bash
   curl -X POST http://localhost:8000/auth/refresh \
     -H "Authorization: Bearer <refresh_token>"
   ```

---

## 3. Problemas de RAG/Embeddings 🤖

### Error: "Embedding generation failed"

**Síntomas:**
```
Error: Failed to generate embedding
OpenAI API error: 401 Unauthorized
```

**Causas Posibles:**
- OPENAI_API_KEY inválida
- API key sin créditos
- OpenAI API down

**Soluciones:**
1. Verifica API key:
   ```bash
   python -c "
   from openai import OpenAI
   client = OpenAI(api_key='sk-your-key')
   response = client.embeddings.create(
       model='text-embedding-3-small',
       input='test'
   )
   print('✅ API OK')
   "
   ```

2. Verifica créditos en platform.openai.com/account/usage

3. Si falla, usa modo offline (sin RAG):
   ```python
   # backend/main.py
   @app.post("/query")
   async def query(request: QueryRequest):
       # Devolver respuesta básica sin RAG
       return QueryResponse(
           respuesta="Sistema en mantenimiento",
           fuente="offline"
       )
   ```

---

### Error: "No relevant products found"

**Síntomas:**
```
Query: "¿Qué pintura para exterior?"
Response: "No encontré información relevante"
```

**Causas Posibles:**
- Productos no ingresados (tabla vacía)
- Embeddings no generados
- Similitud threshold muy alto (0.75)
- Pregunta en idioma diferente o sin palabras clave

**Soluciones:**
1. Verifica productos ingresados:
   ```sql
   SELECT COUNT(*) FROM products WHERE local_id = 'LOCAL_001';
   SELECT COUNT(*) FROM faqs WHERE local_id = 'LOCAL_001';
   ```

2. Verifica embeddings generados:
   ```sql
   SELECT COUNT(*) FROM products 
   WHERE local_id = 'LOCAL_001' 
   AND embedding IS NOT NULL;
   ```

3. Si vacío, ejecuta ingesta:
   ```bash
   python scripts/ingest_catalog.py
   ```

4. Baja threshold de similitud (en rag_pipeline.py):
   ```python
   # De 0.75 a 0.5
   if (1 - (similarity)) > 0.5:  # Antes era 0.75
       return producto
   ```

5. Prueba búsqueda directa:
   ```bash
   curl -X POST http://localhost:8000/query \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"pregunta": "acero varilla refuerzo"}'
   ```

---

### Error: "Token limit exceeded for embedding"

**Síntomas:**
```
Error: This model's maximum context length is 2048 tokens
Text exceeds limit for embedding
```

**Causas Posibles:**
- Descripción de producto muy larga
- Chunk_size demasiado grande (debe ser 500)
- Concatenación incorrecta de campos

**Soluciones:**
1. Verifica chunk_size en ingest_catalog.py:
   ```python
   chunks = chunk_text(product_text, chunk_size=500, overlap=100)
   # Mínimo 100, máximo 500 recomendado
   ```

2. Recorta descripciones en catalogo_jerarquia.json:
   ```json
   "descripcion": "Máximo 200 caracteres por descripción"
   ```

3. Reingesta:
   ```bash
   python scripts/ingest_catalog.py
   ```

---

## 4. Errores de Deployment 🚀

### Error: "Build failed" en Render

**Síntomas:**
```
Render Dashboard: Build Failed
Error during build: No such file or directory
```

**Causas Posibles:**
- requirements.txt incompleto
- Path a archivo incorrecto
- Python version incompatible

**Soluciones:**
1. Verifica requirements.txt tiene todas las dependencias:
   ```bash
   pip freeze > /tmp/deps.txt
   # Compara con backend/requirements.txt
   ```

2. Reconstruye Build en Render:
   - Dashboard > dolmen-rag-backend
   - "Manual Deploy" > Redeploy latest commit

3. Ver logs detallados:
   ```bash
   curl -H "Authorization: Bearer $RENDER_API_KEY" \
     https://api.render.com/v1/services/srv-xxx/deploys | jq '.[]|.buildLogs'
   ```

---

### Error: "Frontend not connecting to backend"

**Síntomas:**
```
Streamlit: "ConnectionError: Failed to connect to backend"
Network tab: CORS error or 404
```

**Causas Posibles:**
- BACKEND_URL incorrecto en Streamlit Secrets
- Backend offline/down
- CORS no habilitado

**Soluciones:**
1. Verifica BACKEND_URL en Streamlit Secrets:
   ```
   https://share.streamlit.io/xxx
   Settings > Secrets > BACKEND_URL = https://dolmen-rag-backend.onrender.com
   ```

2. Prueba conexión:
   ```bash
   curl https://dolmen-rag-backend.onrender.com/health
   # Debe retornar: {"status": "healthy"}
   ```

3. Si Render está en sleep (cold start):
   ```bash
   # Esperar 30 segundos, reintentar
   # O cambiar a plan Standard ($12/mes) para evitar
   ```

4. Verifica CORS en backend/main.py:
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["*"],  # En prod: ["https://share.streamlit.io"]
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

---

## 5. Performance y Timeouts ⏱️

### Error: "Query timeout - took longer than 30s"

**Síntomas:**
```
Streamlit spinning wheel > 30 segundos
Render logs: timeout
```

**Causas Posibles:**
- Supabase query lenta
- Vector search sin índices
- OpenAI API lenta
- Red lenta

**Soluciones:**
1. Verifica índices vectoriales existen:
   ```sql
   SELECT * FROM pg_indexes 
   WHERE tablename IN ('products', 'faqs');
   ```

2. Si faltan, crea:
   ```sql
   CREATE INDEX idx_products_embedding ON products 
   USING ivfflat (embedding vector_cosine_ops);
   ```

3. Reduce límite de búsqueda (en rag_pipeline.py):
   ```python
   def _search_faqs(self, pregunta: str, local_id: str):
       # De limit=10 a limit=3
       results = supabase.rpc('search_faqs', {
           'query_embedding': embedding,
           'local_id_param': local_id,
           'limit_results': 3  # Antes era 10
       }).execute()
   ```

4. Aumenta timeout en frontend/app.py:
   ```python
   response = requests.post(
       f"{BACKEND_URL}/query",
       headers={"Authorization": f"Bearer {access_token}"},
       json={"pregunta": pregunta},
       timeout=60  # Antes era 30
   )
   ```

---

### Error: "Cold start delay" en Render

**Síntomas:**
```
Primera query: 10+ segundos
Siguientes: < 1 segundo
```

**Causas:**
- Plan Starter tiene cold starts cuando inactivo 15 min

**Soluciones:**
1. Usar Plan Standard ($12/mes) - sin cold starts
2. O keep-alive script:
   ```bash
   # Ejecutar cada 10 minutos
   curl -s https://dolmen-rag-backend.onrender.com/health >/dev/null
   ```

---

## 6. Problemas de Tokens 🎫

### Error: "Refresh token expired"

**Síntomas:**
```
POST /auth/refresh → 401 Unauthorized
Refresh token expired or invalid
```

**Causas:**
- Refresh token viejo (> 7 días)
- Token revocado en logout

**Soluciones:**
1. Usuario debe hacer login de nuevo:
   ```python
   # En frontend/app.py
   if "access_token" not in st.session_state:
       show_login()
   ```

2. Opcional: Extender duración (en backend/main.py):
   ```python
   JWT_REFRESH_EXPIRES_DAYS = 30  # Antes era 7
   ```

---

### Error: "Access token already revoked"

**Síntomas:**
```
POST /query → 401 Unauthorized
Token has been revoked
```

**Causas:**
- Usuario hizo logout
- Refresh token fue eliminado
- Token válido pero user fue borrado

**Soluciones:**
1. Login nuevamente - automático en Streamlit
2. Verificar usuario existe en BD:
   ```sql
   SELECT * FROM users WHERE email = 'xxx@dolmen.com';
   ```

---

## 📞 Escalation Paths

| Problema | Responsable | Acción |
|----------|-------------|--------|
| OpenAI API Issues | OpenAI Support | support.openai.com |
| Supabase DB Issues | Supabase Support | Soporte integrado en Supabase Dashboard |
| Render Deployment Issues | Render Support | Dashboard > Support ticket |
| Streamlit Issues | Streamlit Community | streamlit.io/cloud/support |
| Código / Lógica RAG | Equipo Dev Local | Debugging en main.py + rag_pipeline.py |

---

## 🔧 Herramientas de Debug

### 1. Test Backend Local
```bash
cd backend
uvicorn main:app --reload --log-level debug

# En otra terminal:
python scripts/test_backend.py
```

### 2. Check Supabase
```bash
# Ver logs de queries
SELECT * FROM logs ORDER BY created_at DESC LIMIT 10;

# Ver productos ingresados
SELECT id, nombre, categoria FROM products LIMIT 5;

# Buscar FAQs específico
SELECT * FROM faqs WHERE pregunta LIKE '%pintura%';
```

### 3. Monitor Render Logs
```bash
# Dashboard Render > Logs
# O vía API:
curl https://api.render.com/v1/services/srv-xxx/logs \
  -H "Authorization: Bearer $RENDER_API_KEY"
```

### 4. Test RAG Pipeline Local
```bash
python -c "
from rag_pipeline import HybridRAGPipeline
rag = HybridRAGPipeline()
response = rag.query('¿Qué pintura para exterior?', 'LOCAL_001')
print(response)
"
```

---

## ✅ Health Check Rápido

Ejecutar diariamente:
```bash
#!/bin/bash

echo "🔍 Backend Health:"
curl -s https://dolmen-rag-backend.onrender.com/health | jq '.'

echo -e "\n🔍 Supabase Tables:"
python -c "
from supabase import create_client
import os
from dotenv import load_dotenv
load_dotenv()

supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
for table in ['users', 'products', 'faqs', 'logs']:
    response = supabase.table(table).select('COUNT(*)').execute()
    print(f'{table}: {len(response.data)} registros')
"

echo -e "\n🔍 Frontend Status:"
curl -s https://share.streamlit.io/user/vibeCoding/main/ -I | head -1
```

---

**Última actualización:** $(date)  
**Versión:** 1.0  
**Autor:** Equipo de Desarrollo
