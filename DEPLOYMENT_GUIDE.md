# Guía de Despliegue - DOLMEN RAG MVP

## 🚀 Despliegue Rápido

### 1. Backend en Render.com ($7/mes)

1. Crea cuenta en https://render.com
2. Conecta GitHub (Settings → GitHub)
3. Crea Web Service:
   - Repository: `SrThunder/vibeCoding`
   - Build Command: `pip install -r backend/requirements.txt`
   - Start Command: `uvicorn backend.main:app --host 0.0.0.0 --port 8000`

4. Variables de entorno:
```
SUPABASE_URL=https://aoahsdeikflkyhnavugq.supabase.co
SUPABASE_KEY=[tu-service-role-key]
OPENAI_API_KEY=[tu-openai-api-key]
JWT_SECRET_KEY=dolmen-rag-mvp-secret-key-2025
```

URL Backend: `https://[nombre].onrender.com`

---

### 2. Frontend en Streamlit Cloud (Gratis)

1. Crea cuenta en https://streamlit.io/cloud
2. Conecta GitHub
3. Crea app:
   - Repository: `SrThunder/vibeCoding`
   - Main file: `frontend/app.py`

4. Secrets (Settings → Secrets):
```
BACKEND_URL=https://[nombre].onrender.com
OPENAI_API_KEY=[tu-key]
```

URL Frontend: `https://[nombre]-[random].streamlit.app`

---

### 3. Desarrollo Local

**Terminal 1 - Backend:**
```bash
cd /Users/jorgec/vibeCoding
source .venv/bin/activate
uvicorn backend.main:app --reload --port 8001
```

**Terminal 2 - Frontend:**
```bash
cd /Users/jorgec/vibeCoding
source .venv/bin/activate
streamlit run frontend/app.py
```

Accede a: http://localhost:8501

---

## ✅ Checklist Final

- [ ] Backend corriendo en Render
- [ ] Frontend corriendo en Streamlit Cloud
- [ ] Todas las variables de entorno configuradas
- [ ] Base de datos con 31 registros ingestados
- [ ] API Docs accesibles: `/docs`
- [ ] Chat RAG funcionando
- [ ] Login funcionando

---

## 🔗 URLs Finales

- **API**: `https://[backend-url]`
- **Docs**: `https://[backend-url]/docs`
- **Chat**: `https://[frontend-url]`
- **GitHub**: `https://github.com/SrThunder/vibeCoding`

---

## 📞 Soporte

- Logs de Render: Dashboard → Logs
- Logs de Streamlit: Logs de Streamlit Cloud
- Error Handler: Ver `TROUBLESHOOTING.md`
