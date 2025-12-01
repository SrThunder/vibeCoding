# 🧪 GUÍA COMPLETA - Testing en Localhost

## Fase 1: Preparar el Ambiente (2 minutos)

### 1.1 Activar Virtual Environment
```bash
cd /Users/jorgec/vibeCoding
source .venv/bin/activate
```

**Verificar que está activado:**
- Deberías ver `(.venv)` al inicio de tu terminal

### 1.2 Verificar Archivo `.env`
```bash
cat .env
```

**Debe contener:**
```
SUPABASE_URL=https://aoahsdeikflkyhnavugq.supabase.co
SUPABASE_KEY=eyJhbGc...
OPENAI_API_KEY=sk-proj-...
JWT_SECRET_KEY=dolmen-rag-mvp-secret-key-2025
```

Si falta algo:
```bash
# Copia el template
cp backend/.env.example .env

# Luego edita .env y agrega tus keys
```

---

## Fase 2: Ejecutar Backend FastAPI (3 minutos)

### 2.1 Iniciar Servidor
```bash
# Terminal 1
source .venv/bin/activate
cd /Users/jorgec/vibeCoding
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

**Deberías ver:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

### 2.2 Verificar Backend está corriendo
Abre en tu navegador: http://localhost:8000/docs

**Deberías ver:**
- Interfaz Swagger UI
- Endpoints listados: `/login`, `/chat`, `/search`, `/health`, `/token/refresh`
- Botón "Try it out" disponible en cada endpoint

### 2.3 Test Quick - Health Check
```bash
curl -X GET http://localhost:8000/health
```

**Respuesta esperada:**
```json
{
  "status": "ok",
  "timestamp": "2025-11-30T10:30:00Z",
  "backend_version": "1.0.0"
}
```

---

## Fase 3: Ejecutar Frontend Streamlit (2 minutos)

### 3.1 Iniciar Streamlit
```bash
# Terminal 2 (nueva terminal)
source .venv/bin/activate
cd /Users/jorgec/vibeCoding
streamlit run frontend/app.py
```

**Deberías ver:**
```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.x.x:8501
```

### 3.2 Abre en Navegador
- Ve a http://localhost:8501

**Deberías ver:**
- Pantalla de login con campos: Email, Password
- Botón "Conectar" 
- No debería haber errores en la terminal

---

## Fase 4: Testing Manual - Flujo Completo (10 minutos)

### 4.1 Test 1: Login
1. En Streamlit, ingresa:
   - **Email:** `test@dolmen.com`
   - **Password:** `password123`
2. Click **"Conectar"**

**Resultado esperado:**
- ✅ Mensaje: "✅ Conectado exitosamente"
- ✅ Aparece el chat
- ✅ Token guardado en sesión

**Si falla:**
```
❌ Error: "401 Unauthorized"
→ Backend no está corriendo
→ Verifica http://localhost:8000/docs
→ Verifica credenciales en .env
```

### 4.2 Test 2: Buscar Productos (Search)
1. En el chat, escribe:
   ```
   bloque rojo rayado
   ```
2. Presiona Enter o click en Send

**Resultado esperado:**
- ✅ Respuesta en 2-3 segundos
- ✅ Muestra productos relevantes
- ✅ Incluye embeddings vectoriales

**Respuesta típica:**
```
Encontré 3 productos relevantes:
1. Bloque Rojo Rayado 07x30x41
2. Bloque Rojo Rayado 09x30x41
3. Bloque Rojo Rayado 14x30x41
```

### 4.3 Test 3: Chat RAG Completo
1. Escribe una pregunta natural:
   ```
   ¿Qué pintura recomiendan para paredes exteriores?
   ```

**Resultado esperado:**
- ✅ Backend busca en FAQ (embedding similarity)
- ✅ Si encuentra FAQ, búsqueda adicional de productos
- ✅ LLM genera respuesta contextualizada
- ✅ Respuesta en 3-5 segundos

**Respuesta típica:**
```
Basándome en nuestro catálogo, recomiendo:

**Látex Supremo** es la mejor opción para paredes exteriores.

Ventajas:
- Resiste el clima perfectamente
- Excelente rendimiento y cobertura
- Acabado liso duradero
- Disponible en galón y caneca

Es especialmente recomendado para fachadas que requieren 
protección contra lluvia y cambios de temperatura.
```

### 4.4 Test 4: Múltiples Consultas
Realiza 3-4 preguntas para verificar:
1. ✅ El chat mantiene contexto
2. ✅ No hay errores acumulativos
3. ✅ Respuestas consistentes
4. ✅ Rendimiento estable

**Preguntas sugeridas:**
- "¿Cuáles son las ventajas de Multimix?"
- "¿Qué bloque recomiendan para muros divisorios?"
- "¿Para qué sirve el Uniseal?"
- "¿Qué tubería cuadrada uso para estructura ligera?"

---

## Fase 5: Testing Automatizado (5 minutos)

### 5.1 Ejecutar Script de Tests
```bash
# Terminal 3
source .venv/bin/activate
cd /Users/jorgec/vibeCoding
python scripts/test_local.py
```

**Esto ejecutará automáticamente:**
- ✅ Health Check
- ✅ Login válido
- ✅ Login inválido
- ✅ Chat simple
- ✅ Búsqueda vectorial
- ✅ RAG completo
- ✅ Token refresh

**Resultado esperado:**
```
╔════════════════════════════════════════╗
║   TESTING LOCAL - RESULTADOS           ║
╚════════════════════════════════════════╝

✅ Health Check
✅ Login (credenciales válidas)
❌ Login (credenciales inválidas) - ESPERADO
✅ Chat simple
✅ Búsqueda vectorial
✅ RAG con LLM
✅ Token refresh

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Resultados: 6/7 ✅ (1 error esperado)
```

---

## Fase 6: Debugging - Si algo falla

### Problema: "Connection refused" en Backend
```bash
# Verifica que uvicorn está corriendo
lsof -i :8000

# Si nada, reinicia:
pkill -f uvicorn
uvicorn backend.main:app --reload --port 8000
```

### Problema: "ModuleNotFoundError"
```bash
# Reinstala dependencias
pip install -r backend/requirements.txt -q
```

### Problema: Token error en Frontend
```bash
# Verifica JWT_SECRET_KEY en .env
grep JWT_SECRET_KEY .env

# Debe ser: dolmen-rag-mvp-secret-key-2025
```

### Problema: Embeddings no funcionan
```bash
# Verifica OPENAI_API_KEY
grep OPENAI_API_KEY .env

# Si está vacío, actualiza .env
# Si está lleno pero falla, regenera key en https://platform.openai.com
```

### Problema: Supabase error (404)
```bash
# Verifica las credenciales
python scripts/setup_supabase_simple.py

# Si falla:
# 1. Verifica SUPABASE_URL correcta
# 2. Verifica SUPABASE_KEY correcta
# 3. Comprueba que tablas existan:
#    https://app.supabase.co → SQL Editor
```

### Ver Logs Completos del Backend
```bash
# Terminal donde corre uvicorn
# Presiona Ctrl+Shift+P y busca "Clear Terminal"
# O simplemente scroll up para ver logs anteriores

# Para logs persistentes:
uvicorn backend.main:app --reload --log-level debug > backend.log 2>&1
tail -f backend.log
```

---

## Fase 7: Performance Testing (Opcional)

### Medir tiempo de respuesta
```bash
# Terminal
time curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query":"¿Qué pintura para exteriores?"}'
```

**Objetivo:**
- Respuesta completa < 5 segundos
- Chat simple < 2 segundos
- Search < 1 segundo

---

## Fase 8: Integración End-to-End (15 minutos)

### Checklist Final
- [ ] Backend corriendo en http://localhost:8000
- [ ] Frontend corriendo en http://localhost:8501
- [ ] Login funciona
- [ ] Chat responde
- [ ] Búsqueda vectorial funciona
- [ ] RAG completo funciona
- [ ] Puedes hacer 5+ consultas sin errores
- [ ] Token se refresca automáticamente
- [ ] No hay errores en consola/terminal

### Si TODO está ✅:

**Estás listo para:**
1. ✅ Pasar a despliegue en Render + Streamlit Cloud
2. ✅ Invitar usuarios a hacer pruebas
3. ✅ Compartir URL pública del demo

---

## Notas Finales

### Puertos por defecto
- **Backend:** http://localhost:8000
- **Backend Docs:** http://localhost:8000/docs
- **Frontend:** http://localhost:8501

### Credenciales de test
```
Email: cualquier@email.com
Password: cualquier-contraseña

(FastAPI acepta cualquier combinación - solo valida formato)
```

### Para detener servicios
```bash
# Backend (en su terminal)
Ctrl+C

# Frontend (en su terminal)
Ctrl+C

# Desactivar venv
deactivate
```

### Limpiar caché (si hay problemas)
```bash
# Limpiar cache Python
find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null
find . -type f -name "*.pyc" -delete

# Reiniciar Streamlit
rm -rf ~/.streamlit/
```

---

**¡Listo! Ahora prueba el sistema completo en localhost.**

Si necesitas ayuda con algún error, comparte:
1. Mensaje de error exacto
2. Terminal donde ocurre (Backend/Frontend/Test)
3. Paso donde falla

