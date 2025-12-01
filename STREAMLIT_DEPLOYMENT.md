# Despliegue Streamlit Cloud - Paso a Paso

## Requisitos

✅ Código en GitHub (ya está en: https://github.com/SrThunder/vibeCoding)
✅ Cuenta de Streamlit (gratis en streamlit.io)
✅ Cuenta de GitHub conectada

---

## Paso 1: Preparar Backend (Render.com) - IMPORTANTE PRIMERO

Antes de desplegar el frontend, necesitas el backend corriendo:

1. Ve a https://render.com
2. Crea Web Service:
   - Repo: `SrThunder/vibeCoding`
   - Build: `pip install -r backend/requirements.txt`
   - Start: `uvicorn backend.main:app --host 0.0.0.0 --port 8000`
   - Variables de entorno:
     - `SUPABASE_URL=https://aoahsdeikflkyhnavugq.supabase.co`
     - `SUPABASE_KEY=[tu-service-role-key]`
     - `OPENAI_API_KEY=[tu-openai-key]`
     - `JWT_SECRET_KEY=dolmen-rag-mvp-secret-key-2025`

3. **Espera a que esté listo** (verás: "Your service is live")
4. **Copia la URL**: `https://[nombre-backend].onrender.com`

---

## Paso 2: Desplegar Frontend (Streamlit Cloud)

### 2.1 - Abre Streamlit Cloud

Ve a: https://share.streamlit.io/

### 2.2 - Crea Nueva App

Click "New app" → Selecciona:
- **Repository:** `SrThunder/vibeCoding`
- **Branch:** `main`
- **Main file path:** `frontend/app.py`

### 2.3 - Configurar Secrets

Después de crear, ve a:
1. Click ⚙️ Settings (arriba a la derecha)
2. Click "Secrets"
3. **Pega esto** (y reemplaza valores):

```toml
BACKEND_URL = "https://[nombre-backend].onrender.com"
OPENAI_API_KEY = "sk-proj-[tu-openai-key]"
```

**Donde:**
- `[nombre-backend]` = Tu URL de Render (ej: my-app-5k2l.onrender.com)
- `[tu-openai-key]` = Tu OpenAI API Key

### 2.4 - Guarda y Espera

Click "Save" y espera 2-3 minutos a que Streamlit haga deploy.

---

## ✅ Tu App Estará Lista En:

```
https://[nombre-random]-[random].streamlit.app
```

Ejemplo: `https://vibeoding-74hg2k.streamlit.app`

---

## 🧪 Prueba tu App

1. Abre la URL en el navegador
2. Prueba el login con cualquier email/contraseña
3. Haz una pregunta en el chat (ej: "¿Qué pintura recomiendan para exteriores?")
4. Deberías ver respuesta del RAG

---

## ❌ Si Hay Errores

### Error: "Connection refused"
→ Backend no está listo en Render
→ Espera a que esté "live" en Render dashboard

### Error: "Invalid token"
→ JWT_SECRET_KEY no coincide entre Backend y Frontend
→ Verifica que sean iguales en Render

### Error: "API key not found"
→ Las Secrets no se guardaron bien
→ Ve a Settings → Secrets y verifica

---

## 📊 URLs Finales

- **Frontend (Chat):** `https://[tu-app].streamlit.app`
- **Backend (API):** `https://[tu-backend].onrender.com`
- **API Docs:** `https://[tu-backend].onrender.com/docs`
- **GitHub:** `https://github.com/SrThunder/vibeCoding`

---

## 🚀 Para Compartir la Demo

Comparte esta URL: `https://[tu-app].streamlit.app`

¡Ya está listo para demostración!
