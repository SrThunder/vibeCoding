# 📋 Checklist de Deployment - DOLMEN RAG MVP

## ✅ PRE-DEPLOYMENT (Día 0)

### Cuentas & Accesos
- [ ] GitHub account creada
- [ ] Supabase account creada
- [ ] OpenAI account con API key
- [ ] Render account creada
- [ ] Streamlit Cloud account creada
- [ ] Repositorio Git inicializado

### Configuración Local
- [ ] Python 3.11+ instalado
- [ ] Entorno virtual creado
- [ ] Dependencias instaladas
- [ ] `.env` configurado con credenciales reales

---

## ✅ SUPABASE SETUP (Día 1)

### Base de Datos
- [ ] Proyecto Supabase creado
- [ ] Extensión `vector` habilitada
- [ ] Tablas creadas (users, refresh_tokens, products, faqs, logs)
- [ ] Índices vectoriales creados
- [ ] Funciones SQL creadas (search_faqs, search_products)

### Variables & Keys
- [ ] `SUPABASE_URL` obtenida (Settings > API)
- [ ] `SUPABASE_KEY` (service_role) obtenida
- [ ] Permisos RLS configurados si es necesario

### Datos Iniciales
- [ ] Usuario demo creado en tabla `users`
- [ ] Datos de prueba en `products` y `faqs`

---

## ✅ INGESTA DE DATOS (Día 2-3)

### Embeddings & Indexación
- [ ] Script `ingest_catalog.py` ejecutado
- [ ] Todos los productos ingresados
- [ ] Todos los FAQs ingresados
- [ ] Vectores generados correctamente
- [ ] Búsqueda vectorial testeada

### Verificación en Supabase
```sql
-- Verificar que existan registros
SELECT COUNT(*) FROM products;
SELECT COUNT(*) FROM faqs;
SELECT COUNT(*) FROM users;

-- Verificar vectores
SELECT id, nombre, vector FROM products LIMIT 1;
```

---

## ✅ TESTING LOCAL (Día 3-4)

### Backend
- [ ] `uvicorn main:app --reload` inicia sin errores
- [ ] `GET /health` retorna 200
- [ ] `POST /auth/login` funciona con credenciales demo
- [ ] `POST /query` retorna respuestas RAG
- [ ] `GET /me` retorna info del usuario
- [ ] `POST /auth/logout` revoca tokens

### Frontend
- [ ] `streamlit run app.py` inicia sin errores
- [ ] Login page carga correctamente
- [ ] Login con demo@dolmen.com/demo123 funciona
- [ ] Chat interface carga
- [ ] Prueba query: "¿Qué pintura para exterior?"
- [ ] Respuesta incluye pdf_link
- [ ] Logout funciona

### Integration Test
- [ ] Correr `python scripts/test_backend.py`
- [ ] Todos los tests pasan
- [ ] Logs de query guardados en Supabase

---

## ✅ GITHUB SETUP (Día 4)

### Repositorio
- [ ] Repositorio creado en GitHub
- [ ] `.gitignore` aplicado
- [ ] `README.md` completado
- [ ] Primer commit: "Initial commit: MVP ready"
- [ ] Branch `main` protegida

### Estructura en GitHub
```
Archivos necesarios para Render/Streamlit:
- backend/main.py ✅
- backend/rag_pipeline.py ✅
- backend/requirements.txt ✅
- frontend/app.py ✅
- README.md ✅
```

---

## ✅ RENDER DEPLOYMENT - Backend (Día 5)

### Crear Web Service
- [ ] Loguearse en Render.com
- [ ] "New +" → "Web Service"
- [ ] Conectar GitHub account
- [ ] Seleccionar repositorio `vibeCoding`

### Configurar Servicio
- [ ] **Name:** `dolmen-rag-backend`
- [ ] **Runtime:** Python 3
- [ ] **Build Command:** `pip install -r backend/requirements.txt`
- [ ] **Start Command:** `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`
- [ ] **Plan:** Starter ($7/mes) o Standard
- [ ] **Region:** Elegir más cercano

### Environment Variables (Render)
```
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=your-service-role-key
OPENAI_API_KEY=sk-your-key
JWT_SECRET_KEY=generate-with-openssl-rand-hex-32
JWT_ALGORITHM=HS256
JWT_EXPIRES_MINUTES=15
JWT_REFRESH_EXPIRES_DAYS=7
CATALOG_PDF_URL=https://dolmen.com/catalogo.pdf
```

### Deploy
- [ ] "Create Web Service" clickeado
- [ ] Deploy inicia automáticamente
- [ ] Esperar a que termine (5-10 min)
- [ ] Backend URL obtenida (ej: https://dolmen-rag-backend.onrender.com)
- [ ] Testear: `curl https://dolmen-rag-backend.onrender.com/health`

---

## ✅ STREAMLIT CLOUD DEPLOYMENT - Frontend (Día 6)

### Crear App
- [ ] Loguearse en share.streamlit.io
- [ ] "New App"
- [ ] Conectar GitHub account
- [ ] Seleccionar repositorio `vibeCoding`
- [ ] **Branch:** main
- **Repo:** user/vibeCoding
- **Main file path:** frontend/app.py

### Environment Variables (Streamlit Secrets)
```
BACKEND_URL=https://dolmen-rag-backend.onrender.com
```

### Deploy
- [ ] "Deploy" clickeado
- [ ] Esperar a que termine (2-5 min)
- [ ] App URL obtenida (ej: https://share.streamlit.io/user/vibeCoding/main)
- [ ] Testear login con demo@dolmen.com/demo123
- [ ] Testear query desde Streamlit

---

## ✅ TESTING E2E (Días 7-10)

### Flujo Completo
- [ ] Abrir app Streamlit Cloud
- [ ] Login con credentials demo
- [ ] Hacer pregunta: "¿Qué bloque para muros divisorios?"
- [ ] Verificar respuesta correcta
- [ ] Verificar pdf_link en respuesta
- [ ] Verificar log en Supabase (tabla logs)
- [ ] Logout funciona
- [ ] Volver a login exitoso

### Casos de Uso
- [ ] Pregunta en FAQ → respuesta rápida
- [ ] Pregunta no en FAQ → RAG busca productos
- [ ] Comparativas entre productos
- [ ] Preguntas sobre especificaciones técnicas
- [ ] Links a secciones del PDF

### Validación con Piloto
- [ ] 5-10 vendedores testean
- [ ] Recopilar feedback
- [ ] Ajustes si es necesario
- [ ] Documentar issues

---

## 📊 MONITOREO POST-DEPLOYMENT

### Logs & Metrics
- [ ] Render: Ver logs de backend en dashboard
- [ ] Streamlit: Ver health en app settings
- [ ] Supabase: Monitorear uso de BD (queries, storage)
- [ ] OpenAI: Verificar usage en dashboard

### Alertas a Configurar
- [ ] Backend down (Render notifications)
- [ ] Queries lentas (custom logging)
- [ ] Errores de embeddings

### Mantener Actualizado
- [ ] GitHub secrets rotados anualmente
- [ ] Dependencias actualizadas (vulnerabilidades)
- [ ] Logs limpios semanalmente
- [ ] Backups de Supabase habilitados

---

## 🎯 Criterios de Éxito MVP

- [x] Sistema en producción accesible
- [x] Autenticación funcionando
- [x] RAG responde preguntas correctamente
- [x] PDFs linkeados en respuestas
- [x] Logs registrando queries
- [x] 5-10 vendedores testeando
- [x] Disponibilidad 24/7 (Render Starter)
- [x] Presupuesto ~$20/mes

---

## 📝 Notas Importantes

1. **JWT Secret:** Generar con `openssl rand -hex 32`, NUNCA reutilizar
2. **Render:** Plan Starter ($7/mes) evita cold starts críticos
3. **Supabase:** Free plan soporta ~50k vectores
4. **OpenAI:** Monitorear costos (gpt-4o-mini + embeddings)
5. **CORS:** Ya habilitado para Streamlit Cloud
6. **Escalabilidad:** local_id preparado para multi-local en futuro

---

## 🆘 Troubleshooting

| Problema | Solución |
|----------|----------|
| Backend no inicia | Ver logs Render, verificar SUPABASE_URL |
| Login falla | Verificar usuario demo en Supabase |
| Query timeout | Aumentar timeout en frontend, verificar embeddings |
| PDF links rotos | Verificar CATALOG_PDF_URL y pdf_link en BD |
| Tokens expirados | Implementar auto-refresh en frontend |

---

**Status:** 🟢 Checklist Completo  
**Responsable:** Equipo de Desarrollo  
**Fecha Estimada:** 10 días  
**Fecha Real:** [Completar después]
