"""
Frontend Streamlit - Sistema de Recomendación de Materiales DOLMEN
Chat interactivo con autenticación JWT y manejo de tokens
"""

import os
import requests
import streamlit as st
from datetime import datetime
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# ===================== CONFIGURACIÓN PÁGINA =====================
st.set_page_config(
    page_title="DOLMEN - Asistente RAG",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    .main {
        max-width: 1000px;
    }
    .stChatMessage {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 12px;
        margin: 8px 0;
    }
    .pdf-link {
        background-color: #e8f4f8;
        padding: 10px;
        border-left: 4px solid #0066cc;
        margin: 10px 0;
        border-radius: 4px;
    }
    .product-card {
        background-color: #fff3e0;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
        border-left: 4px solid #ff9800;
    }
</style>
""", unsafe_allow_html=True)

# ===================== GESTIÓN DE ESTADO =====================
if "access_token" not in st.session_state:
    st.session_state.access_token = None
    st.session_state.user_email = None
    st.session_state.authenticated = False
    st.session_state.chat_history = []


def login_user(email: str, password: str) -> bool:
    """Autentica al usuario y almacena tokens."""
    try:
        response = requests.post(
            f"{BACKEND_URL}/auth/login",
            json={"email": email, "password": password},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            st.session_state.access_token = data["access_token"]
            st.session_state.refresh_token = data["refresh_token"]
            st.session_state.user_email = email
            st.session_state.authenticated = True
            return True
        else:
            st.error(f"Login fallido: {response.json().get('detail', 'Error desconocido')}")
            return False
    except Exception as e:
        st.error(f"Error de conexión: {str(e)}")
        return False


def logout_user():
    """Cierra la sesión del usuario."""
    try:
        if st.session_state.access_token:
            requests.post(
                f"{BACKEND_URL}/auth/logout",
                headers={"Authorization": f"Bearer {st.session_state.access_token}"},
                timeout=10
            )
    except:
        pass
    
    st.session_state.access_token = None
    st.session_state.refresh_token = None
    st.session_state.user_email = None
    st.session_state.authenticated = False
    st.session_state.chat_history = []


def query_backend(pregunta: str) -> dict:
    """Envía una pregunta al backend RAG."""
    try:
        response = requests.post(
            f"{BACKEND_URL}/query",
            json={"pregunta": pregunta},
            headers={"Authorization": f"Bearer {st.session_state.access_token}"},
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "error": response.json().get("detail", "Error en servidor"),
                "status_code": response.status_code
            }
    except requests.exceptions.Timeout:
        return {"error": "Timeout: El servidor tardó demasiado en responder"}
    except Exception as e:
        return {"error": f"Error de conexión: {str(e)}"}


# ===================== PÁGINA DE LOGIN =====================
def show_login():
    """Muestra la página de login."""
    st.markdown("# 🏗️ DOLMEN - Asistente de Vendedores")
    st.markdown("### Sistema de Recomendación de Materiales (RAG)")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("---")
        st.markdown("### 🔐 Ingresa a tu cuenta")
        
        email = st.text_input("📧 Email", placeholder="vendedor@dolmen.com")
        password = st.text_input("🔑 Contraseña", type="password", placeholder="Tu contraseña")
        
        if st.button("✅ Ingresar", use_container_width=True, type="primary"):
            if email and password:
                with st.spinner("Verificando credenciales..."):
                    if login_user(email, password):
                        st.success("¡Login exitoso! Recargando...")
                        st.rerun()
                    else:
                        st.error("Email o contraseña incorrectos")
            else:
                st.warning("Por favor completa todos los campos")
        
        st.markdown("---")
        st.markdown("### 📝 Demo (credenciales de prueba)")
        st.info("""
        **Email:** demo@dolmen.com
        **Password:** demo123
        """)


# ===================== PÁGINA PRINCIPAL (CHAT) =====================
def show_chat():
    """Muestra la interfaz de chat para usuarios autenticados."""
    
    # Header con info del usuario
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        st.markdown(f"# 🏗️ DOLMEN - Asistente RAG")
        st.markdown(f"**Bienvenido:** {st.session_state.user_email}")
    
    with col3:
        if st.button("🚪 Cerrar sesión", use_container_width=True):
            logout_user()
            st.rerun()
    
    st.markdown("---")
    
    # Contenedor de chat
    chat_container = st.container()
    
    with chat_container:
        # Mostrar historial de chat
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.write(message["content"])
                
                # Mostrar PDF link si existe
                if message.get("pdf_link"):
                    st.markdown(
                        f"""
                        <div class='pdf-link'>
                        📄 <a href='{message['pdf_link']}' target='_blank'>Ver más en catálogo PDF</a>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                
                # Mostrar producto recomendado si existe
                if message.get("producto"):
                    prod = message["producto"]
                    with st.expander(f"📦 Producto recomendado: {prod['nombre']}"):
                        st.markdown(f"""
                        **Categoría:** {prod['categoria']}
                        
                        **Variantes:**
                        {', '.join(prod['variantes'][:3])}
                        
                        **Usos:**
                        {', '.join(prod['usos'])}
                        
                        **Beneficios:**
                        {', '.join(prod['beneficios'])}
                        """)
    
    # Input de usuario
    st.markdown("---")
    
    if pregunta := st.chat_input("💬 Haz tu pregunta sobre productos DOLMEN..."):
        # Agregar pregunta al historial
        st.session_state.chat_history.append({
            "role": "user",
            "content": pregunta
        })
        
        # Enviar al backend
        with st.spinner("🤔 Buscando respuesta..."):
            resultado = query_backend(pregunta)
        
        if "error" in resultado:
            st.error(f"❌ Error: {resultado['error']}")
        else:
            # Agregar respuesta al historial
            respuesta_data = {
                "role": "assistant",
                "content": resultado["respuesta"],
                "fuente": resultado.get("fuente", "rag"),
                "confianza": resultado.get("confianza", 0),
                "pdf_link": resultado.get("pdf_link"),
            }
            
            if resultado.get("producto_recomendado"):
                respuesta_data["producto"] = resultado["producto_recomendado"]
            
            st.session_state.chat_history.append(respuesta_data)
            st.rerun()
    
    # Sidebar con información
    with st.sidebar:
        st.markdown("### 📚 Información")
        st.markdown(f"""
        **Backend:** {BACKEND_URL}
        
        **Estado:** ✅ Conectado
        """)
        
        st.markdown("---")
        st.markdown("### 💡 Tips")
        st.markdown("""
        - Describe el tipo de material que necesitas
        - Menciona el uso específico
        - Pregunta sobre variantes y especificaciones
        - Consulta comparativas entre productos
        """)
        
        st.markdown("---")
        st.markdown("### 🎯 Categorías")
        st.markdown("""
        - **Aceromateriales:** Varillas, tuberías, mallas
        - **Pinturas:** Látex, esmaltes, selladores
        - **Grifería:** Llaves, inodoros, combos
        - **Morteros:** Adhesivos, pastas, morteros
        - **Bloques:** Ladrillos, adoquines, baldosas
        - **Materiales:** Cemento, plywood, madera
        """)


# ===================== ROUTER PRINCIPAL =====================
if __name__ == "__main__":
    if st.session_state.authenticated:
        show_chat()
    else:
        show_login()
