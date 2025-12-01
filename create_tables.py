#!/usr/bin/env python3
"""
Script para crear las tablas en Supabase automáticamente
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Error: SUPABASE_URL o SUPABASE_KEY no configurados")
    exit(1)

print(f"🔗 Conectando a Supabase: {SUPABASE_URL}")

# SQL para crear las tablas
SQL_COMMANDS = [
    # Habilitar extensión pgvector
    "CREATE EXTENSION IF NOT EXISTS vector",
    
    # Tabla FAQs
    """CREATE TABLE IF NOT EXISTS faqs (
    id BIGSERIAL PRIMARY KEY,
    faq_id VARCHAR(50) NOT NULL UNIQUE,
    pregunta VARCHAR(500) NOT NULL,
    respuesta TEXT NOT NULL,
    categoria VARCHAR(100),
    palabras_clave TEXT[],
    productos_relacionados VARCHAR(50)[],
    pdf_link VARCHAR(500),
    embedding VECTOR(1536),
    created_at TIMESTAMP DEFAULT NOW()
)""",
    
    # Tabla Products
    """CREATE TABLE IF NOT EXISTS products (
    id BIGSERIAL PRIMARY KEY,
    product_id VARCHAR(50) NOT NULL,
    nombre VARCHAR(255) NOT NULL,
    categoria VARCHAR(100),
    subcategoria VARCHAR(100),
    descripcion TEXT,
    variantes TEXT[],
    usos TEXT[],
    beneficios TEXT[],
    chunk_index INTEGER,
    chunk_text TEXT,
    embedding VECTOR(1536),
    created_at TIMESTAMP DEFAULT NOW()
)""",
    
    # Índices
    "CREATE INDEX IF NOT EXISTS idx_faqs_embedding ON faqs USING ivfflat (embedding vector_cosine_ops)",
    "CREATE INDEX IF NOT EXISTS idx_products_embedding ON products USING ivfflat (embedding vector_cosine_ops)",
]

headers = {
    "apikey": SUPABASE_KEY,
    "Content-Type": "application/json",
    "Authorization": f"Bearer {SUPABASE_KEY}"
}

def execute_sql(sql):
    """Ejecuta SQL en Supabase"""
    try:
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/rpc/sql",
            headers=headers,
            json={"sql": sql},
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            return True, "OK"
        else:
            return False, response.text[:200]
    except Exception as e:
        return False, str(e)

print("\n📦 Creando tablas y extensiones...\n")

for i, sql in enumerate(SQL_COMMANDS, 1):
    sql_short = sql.split('\n')[0][:50]
    success, msg = execute_sql(sql)
    
    if success:
        print(f"  ✅ {i}. {sql_short}...")
    else:
        # No es error crítico si ya existen
        if "already exists" in msg or "EXTENSION" in sql:
            print(f"  ⚠️  {i}. {sql_short}... (ya existe o no disponible)")
        else:
            print(f"  ❌ {i}. {sql_short}...\n     Error: {msg}")

print("\n✅ Intento de creación completado")
print("\n📝 Alternativa: Si los comandos SQL no funcionaron,")
print("   ve a https://app.supabase.com → SQL Editor")
print("   y copia-pega este SQL manualmente:")
print("\n" + "="*60)
for sql in SQL_COMMANDS[1:]:
    print(sql + ";")
print("="*60)
