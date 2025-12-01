"""
Backend FastAPI - Sistema de Recomendación de Materiales (RAG)
Incluye: Autenticación JWT, Pipeline RAG, Logging
"""

import os
import json
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, List
from functools import lru_cache

from fastapi import FastAPI, Depends, HTTPException, status, Body
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import jwt
from passlib.context import CryptContext
from dotenv import load_dotenv

from supabase import create_client
from rag_pipeline import HybridRAGPipeline, RAGResponse

# Cargar variables de entorno
load_dotenv()

# ===================== CONFIGURACIÓN =====================
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "tu-clave-super-secreta-change-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRES_MINUTES = int(os.getenv("JWT_EXPIRES_MINUTES", "15"))
JWT_REFRESH_EXPIRES_DAYS = int(os.getenv("JWT_REFRESH_EXPIRES_DAYS", "7"))
CATALOG_PDF_URL = os.getenv("CATALOG_PDF_URL", "https://dolmen.com/catalogo.pdf")

# Contexto de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security
security = HTTPBearer()

# ===================== INICIALIZACIÓN =====================
app = FastAPI(
    title="DOLMEN - Sistema de Recomendación RAG",
    description="API para asistencia a vendedores usando RAG híbrido",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Clientes
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
rag_pipeline = HybridRAGPipeline(SUPABASE_URL, SUPABASE_KEY, OPENAI_API_KEY)

# ===================== MODELOS =====================
class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str


class QueryRequest(BaseModel):
    pregunta: str = Field(..., description="Pregunta del cliente sobre productos")


class ProductoRecomendado(BaseModel):
    id: str
    nombre: str
    categoria: str
    variantes: List[str]
    usos: List[str]
    beneficios: List[str]
    pdf_link: Optional[str] = None


class QueryResponse(BaseModel):
    respuesta: str
    fuente: str  # "faq" o "rag"
    producto_recomendado: Optional[ProductoRecomendado] = None
    pdf_link: Optional[str] = None
    confianza: float
    timestamp: str


class TokenPayload(BaseModel):
    sub: str  # user_id
    local_id: str
    iat: datetime
    exp: datetime


# ===================== FUNCIONES DE UTILIDAD =====================
def hash_password(password: str) -> str:
    """Hashea una contraseña."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica una contraseña."""
    return pwd_context.verify(plain_password, hashed_password)


def hash_token(token: str) -> str:
    """Hashea un token para almacenamiento seguro."""
    import hashlib
    return hashlib.sha256(token.encode()).hexdigest()


def create_access_token(user_id: str, local_id: str) -> str:
    """Crea un JWT access token."""
    payload = {
        "sub": user_id,
        "local_id": local_id,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRES_MINUTES),
    }
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token


def create_refresh_token(user_id: str, local_id: str) -> str:
    """Crea un JWT refresh token."""
    payload = {
        "sub": user_id,
        "local_id": local_id,
        "type": "refresh",
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(days=JWT_REFRESH_EXPIRES_DAYS),
    }
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token


def verify_token(token: str) -> TokenPayload:
    """Verifica y decodifica un JWT."""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        local_id = payload.get("local_id")
        
        if not user_id or not local_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido"
            )
        
        return TokenPayload(
            sub=user_id,
            local_id=local_id,
            iat=payload.get("iat"),
            exp=payload.get("exp"),
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )


async def get_current_user(credentials: HTTPAuthCredentials = Depends(security)) -> TokenPayload:
    """Dependency para obtener usuario actual del JWT."""
    return verify_token(credentials.credentials)


# ===================== ENDPOINTS DE AUTENTICACIÓN =====================
@app.post("/auth/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """
    Login de usuario.
    
    Args:
        request: email y password
    
    Returns:
        Tokens de acceso y refresh + info de expiración
    """
    # Buscar usuario en BD
    response = supabase.table("users").select("*").eq("email", request.email).execute()
    
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas"
        )
    
    user = response.data[0]
    
    # Verificar contraseña
    if not verify_password(request.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas"
        )
    
    # Crear tokens
    access_token = create_access_token(user["id"], user["local_id"])
    refresh_token = create_refresh_token(user["id"], user["local_id"])
    
    # Guardar refresh token hasheado en BD
    token_hash = hash_token(refresh_token)
    expires_at = (datetime.now(timezone.utc) + timedelta(days=JWT_REFRESH_EXPIRES_DAYS)).isoformat()
    
    supabase.table("refresh_tokens").insert({
        "user_id": user["id"],
        "token_hash": token_hash,
        "expires_at": expires_at,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }).execute()
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=JWT_EXPIRES_MINUTES * 60,  # en segundos
    )


@app.post("/auth/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshRequest):
    """
    Refresca el access token usando un refresh token válido.
    """
    # Verificar refresh token
    payload = verify_token(request.refresh_token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido"
        )
    
    # Verificar que exista en BD
    token_hash = hash_token(request.refresh_token)
    response = supabase.table("refresh_tokens").select("*").eq(
        "token_hash", token_hash
    ).eq("user_id", payload.sub).execute()
    
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token no encontrado o revocado"
        )
    
    # Crear nuevo access token
    new_access_token = create_access_token(payload.sub, payload.local_id)
    
    return TokenResponse(
        access_token=new_access_token,
        refresh_token=request.refresh_token,
        expires_in=JWT_EXPIRES_MINUTES * 60,
    )


@app.post("/auth/logout")
async def logout(current_user: TokenPayload = Depends(get_current_user)):
    """
    Logout: invalida todos los refresh tokens del usuario.
    """
    supabase.table("refresh_tokens").delete().eq(
        "user_id", current_user.sub
    ).execute()
    
    return {"message": "Logout exitoso"}


# ===================== ENDPOINTS RAG =====================
@app.post("/query", response_model=QueryResponse)
async def query(
    request: QueryRequest,
    current_user: TokenPayload = Depends(get_current_user)
):
    """
    Procesa una pregunta del cliente usando pipeline RAG híbrido.
    
    Args:
        request: pregunta del cliente
        current_user: usuario autenticado (extraído del JWT)
    
    Returns:
        Respuesta RAG con referencias a PDF
    """
    try:
        # Ejecutar pipeline RAG
        rag_response = rag_pipeline.query(request.pregunta, current_user.local_id)
        
        # Preparar respuesta con producto recomendado
        producto_recomendado = None
        if rag_response.producto_recomendado:
            producto_recomendado = ProductoRecomendado(
                id=rag_response.producto_recomendado["product_id"],
                nombre=rag_response.producto_recomendado["nombre"],
                categoria=rag_response.producto_recomendado["categoria"],
                variantes=rag_response.producto_recomendado.get("variantes", []),
                usos=rag_response.producto_recomendado.get("usos", []),
                beneficios=rag_response.producto_recomendado.get("beneficios", []),
                pdf_link=rag_response.producto_recomendado.get("pdf_link"),
            )
        
        # Guardar log en Supabase
        log_entry = {
            "user_id": current_user.sub,
            "local_id": current_user.local_id,
            "query": request.pregunta,
            "response": rag_response.respuesta,
            "product_recommended": rag_response.producto_recomendado.get("id") if rag_response.producto_recomendado else None,
            "pdf_link_sent": rag_response.pdf_link,
            "confidence": rag_response.confianza,
            "source": rag_response.fuente,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        
        supabase.table("logs").insert(log_entry).execute()
        
        return QueryResponse(
            respuesta=rag_response.respuesta,
            fuente=rag_response.fuente,
            producto_recomendado=producto_recomendado,
            pdf_link=rag_response.pdf_link or CATALOG_PDF_URL,
            confianza=rag_response.confianza,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    
    except Exception as e:
        print(f"Error en query: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error procesando la pregunta: {str(e)}"
        )


# ===================== ENDPOINTS DE UTILIDAD =====================
@app.get("/health")
async def health_check():
    """Health check del backend."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "DOLMEN RAG Backend",
    }


@app.get("/me")
async def get_current_user_info(current_user: TokenPayload = Depends(get_current_user)):
    """
    Obtiene info del usuario actual.
    """
    response = supabase.table("users").select("*").eq("id", current_user.sub).execute()
    
    if not response.data:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    user = response.data[0]
    return {
        "id": user["id"],
        "email": user["email"],
        "local_id": user["local_id"],
        "role": user["role"],
        "created_at": user["created_at"],
    }


@app.get("/catalog/pdf")
async def get_catalog_pdf_url():
    """
    Retorna la URL del catálogo PDF completo.
    """
    return {
        "pdf_url": CATALOG_PDF_URL,
        "descripcion": "Catálogo completo de productos DOLMEN"
    }


# ===================== ERROR HANDLERS =====================
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handler personalizado para HTTPExceptions."""
    return {
        "error": exc.detail,
        "status_code": exc.status_code,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ===================== STARTUP =====================
@app.on_event("startup")
async def startup_event():
    """Ejecutarse al iniciar el servidor."""
    print("🚀 Backend RAG iniciado")
    print(f"📍 Supabase: {SUPABASE_URL}")
    print(f"🤖 OpenAI: {OPENAI_API_KEY[:10]}...")
    print(f"📄 Catálogo PDF: {CATALOG_PDF_URL}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
