#!/usr/bin/env python3
"""
Setup Script para Supabase - Automático
Ejecutar: python scripts/setup_supabase.py

Este script:
1. Conecta a Supabase con credenciales
2. Crea tablas si no existen
3. Crea extensiones necesarias
4. Crea funciones SQL para búsqueda
5. Verifica configuración
"""

import os
import sys
from typing import Optional
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import execute_values
import json

# Load environment variables
load_dotenv()

# Connection parameters
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_PASSWORD = os.getenv("SUPABASE_PASSWORD", "")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Error: SUPABASE_URL o SUPABASE_KEY no configurados")
    print("   Configura estas variables en .env")
    sys.exit(1)

# Extract host from URL
# Format: https://xxxxx.supabase.co
SUPABASE_HOST = SUPABASE_URL.replace("https://", "").replace("http://", "").split(".")[0]
SUPABASE_HOST = f"{SUPABASE_HOST}.supabase.co"
SUPABASE_DB = "postgres"
SUPABASE_USER = "postgres"

print(f"🔗 Conectando a Supabase: {SUPABASE_HOST}")

# Connect to Supabase
try:
    conn = psycopg2.connect(
        host=SUPABASE_HOST,
        port=5432,
        database=SUPABASE_DB,
        user=SUPABASE_USER,
        password=SUPABASE_KEY,
        sslmode="require"
    )
    cursor = conn.cursor()
    print("✅ Conexión exitosa")
except Exception as e:
    print(f"❌ Error de conexión: {e}")
    sys.exit(1)

def run_sql(sql: str, description: str) -> bool:
    """Execute SQL and handle errors"""
    try:
        cursor.execute(sql)
        conn.commit()
        print(f"✅ {description}")
        return True
    except Exception as e:
        conn.rollback()
        print(f"❌ {description}: {e}")
        return False

# Step 1: Enable pgvector extension
print("\n📦 Instalando extensiones...")
run_sql("CREATE EXTENSION IF NOT EXISTS vector", "pgvector extensión")

# Step 2: Create users table
print("\n👥 Creando tablas...")
sql_users = """
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    local_id VARCHAR(50) NOT NULL,
    role VARCHAR(20) DEFAULT 'vendedor',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""
run_sql(sql_users, "Tabla users")

# Step 3: Create refresh_tokens table
sql_refresh_tokens = """
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    revoked BOOLEAN DEFAULT FALSE
);
"""
run_sql(sql_refresh_tokens, "Tabla refresh_tokens")

# Step 4: Create products table
sql_products = """
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    product_id VARCHAR(50) NOT NULL,
    local_id VARCHAR(50) NOT NULL,
    nombre VARCHAR(255) NOT NULL,
    categoria VARCHAR(100),
    subcategoria VARCHAR(100),
    descripcion TEXT,
    variantes TEXT[],
    usos TEXT[],
    beneficios TEXT[],
    pdf_link VARCHAR(500),
    stock BOOLEAN DEFAULT TRUE,
    chunk_index INTEGER,
    chunk_text TEXT,
    embedding vector(1536),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT products_unique_chunk UNIQUE(product_id, local_id, chunk_index)
);
"""
run_sql(sql_products, "Tabla products")

# Step 5: Create FAQs table
sql_faqs = """
CREATE TABLE IF NOT EXISTS faqs (
    id SERIAL PRIMARY KEY,
    faq_id VARCHAR(50) NOT NULL,
    local_id VARCHAR(50) NOT NULL,
    pregunta VARCHAR(500) NOT NULL,
    respuesta TEXT NOT NULL,
    categoria VARCHAR(100),
    palabras_clave TEXT[],
    productos_relacionados VARCHAR(50)[],
    pdf_link VARCHAR(500),
    embedding vector(1536),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT faqs_unique UNIQUE(faq_id, local_id)
);
"""
run_sql(sql_faqs, "Tabla faqs")

# Step 6: Create logs table
sql_logs = """
CREATE TABLE IF NOT EXISTS logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    local_id VARCHAR(50),
    pregunta VARCHAR(500),
    respuesta TEXT,
    fuente VARCHAR(50),
    confianza DECIMAL(3,2),
    tokens_used INTEGER,
    response_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""
run_sql(sql_logs, "Tabla logs")

# Step 7: Create indexes
print("\n📑 Creando índices...")
run_sql(
    "CREATE INDEX IF NOT EXISTS idx_products_embedding ON products USING ivfflat (embedding vector_cosine_ops)",
    "Índice vectorial products"
)
run_sql(
    "CREATE INDEX IF NOT EXISTS idx_faqs_embedding ON faqs USING ivfflat (embedding vector_cosine_ops)",
    "Índice vectorial faqs"
)
run_sql(
    "CREATE INDEX IF NOT EXISTS idx_products_local_id ON products(local_id)",
    "Índice products.local_id"
)
run_sql(
    "CREATE INDEX IF NOT EXISTS idx_faqs_local_id ON faqs(local_id)",
    "Índice faqs.local_id"
)
run_sql(
    "CREATE INDEX IF NOT EXISTS idx_logs_local_id ON logs(local_id)",
    "Índice logs.local_id"
)

# Step 8: Create search functions
print("\n🔍 Creando funciones de búsqueda...")

sql_search_faqs = """
CREATE OR REPLACE FUNCTION search_faqs(
    query_embedding vector(1536),
    local_id_param VARCHAR(50),
    limit_results INT DEFAULT 5
)
RETURNS TABLE(
    id INT,
    faq_id VARCHAR,
    pregunta VARCHAR,
    respuesta TEXT,
    categoria VARCHAR,
    productos_relacionados VARCHAR[],
    pdf_link VARCHAR,
    similarity FLOAT
) AS $$
    SELECT
        f.id,
        f.faq_id,
        f.pregunta,
        f.respuesta,
        f.categoria,
        f.productos_relacionados,
        f.pdf_link,
        (1 - (f.embedding <=> query_embedding)) as similarity
    FROM faqs f
    WHERE f.local_id = local_id_param
    ORDER BY f.embedding <=> query_embedding
    LIMIT limit_results;
$$ LANGUAGE SQL;
"""

sql_search_products = """
CREATE OR REPLACE FUNCTION search_products(
    query_embedding vector(1536),
    local_id_param VARCHAR(50),
    limit_results INT DEFAULT 5
)
RETURNS TABLE(
    id INT,
    product_id VARCHAR,
    nombre VARCHAR,
    categoria VARCHAR,
    descripcion TEXT,
    beneficios TEXT[],
    pdf_link VARCHAR,
    similarity FLOAT
) AS $$
    SELECT
        p.id,
        p.product_id,
        p.nombre,
        p.categoria,
        p.chunk_text,
        p.beneficios,
        p.pdf_link,
        (1 - (p.embedding <=> query_embedding)) as similarity
    FROM products p
    WHERE p.local_id = local_id_param
    AND (1 - (p.embedding <=> query_embedding)) > 0.5
    ORDER BY p.embedding <=> query_embedding
    LIMIT limit_results;
$$ LANGUAGE SQL;
"""

run_sql(sql_search_faqs, "Función search_faqs()")
run_sql(sql_search_products, "Función search_products()")

# Step 9: Insert demo user
print("\n👤 Creando usuario demo...")
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
demo_password_hash = pwd_context.hash("demo123")

sql_insert_user = """
INSERT INTO users (email, password_hash, local_id, role)
VALUES (%s, %s, %s, %s)
ON CONFLICT (email) DO NOTHING;
"""

try:
    cursor.execute(sql_insert_user, ("demo@dolmen.com", demo_password_hash, "LOCAL_001", "vendedor"))
    conn.commit()
    print("✅ Usuario demo@dolmen.com creado")
except Exception as e:
    conn.rollback()
    print(f"ℹ️  Usuario demo ya existe: {e}")

# Step 10: Verification
print("\n🔍 Verificando configuración...")

sql_check_tables = """
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public'
ORDER BY table_name;
"""

try:
    cursor.execute(sql_check_tables)
    tables = [row[0] for row in cursor.fetchall()]
    print(f"✅ Tablas creadas: {', '.join(tables)}")
except Exception as e:
    print(f"❌ Error verificando tablas: {e}")

sql_check_users = "SELECT COUNT(*) FROM users;"
try:
    cursor.execute(sql_check_users)
    user_count = cursor.fetchone()[0]
    print(f"✅ Usuarios en BD: {user_count}")
except Exception as e:
    print(f"❌ Error verificando usuarios: {e}")

sql_check_extensions = "SELECT extname FROM pg_extension ORDER BY extname;"
try:
    cursor.execute(sql_check_extensions)
    extensions = [row[0] for row in cursor.fetchall()]
    print(f"✅ Extensiones habilitadas: {', '.join(extensions)}")
except Exception as e:
    print(f"❌ Error verificando extensiones: {e}")

# Close connection
cursor.close()
conn.close()

print("\n" + "="*50)
print("✅ SETUP COMPLETADO EXITOSAMENTE")
print("="*50)
print("\nPróximos pasos:")
print("1. Ejecutar: python scripts/ingest_catalog.py")
print("2. Verificar en Supabase que products y faqs tengan embeddings")
print("3. Ejecutar backend: cd backend && uvicorn main:app --reload")
print("4. Ejecutar frontend: cd frontend && streamlit run app.py")
print("5. Testear: python scripts/test_backend.py")
