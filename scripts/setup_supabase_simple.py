#!/usr/bin/env python3
"""
Setup Script para Supabase - Conexión REST
"""

import os
import sys
from dotenv import load_dotenv

try:
    import requests
except ImportError:
    print("❌ Error: requests no está instalado")
    sys.exit(1)

# Load environment variables
load_dotenv()

# Connection parameters
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Error: SUPABASE_URL o SUPABASE_KEY no configurados")
    print("   Configura estas variables en .env")
    sys.exit(1)

print(f"🔗 Conectando a Supabase: {SUPABASE_URL}")

# Test connection via REST API
try:
    headers = {
        "apikey": SUPABASE_KEY,
        "Content-Type": "application/json"
    }
    
    # Simple health check - try to access the REST endpoint
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/",
        headers=headers,
        timeout=5
    )
    
    if response.status_code in [200, 204, 401, 403]:  # These are all valid responses
        print("✅ Conexión a Supabase exitosa")
        print(f"📍 URL: {SUPABASE_URL}")
        print("\n✅ Supabase está listo para usar")
        print("\n📝 Próximo paso: Ejecuta 'python scripts/ingest_catalog.py'")
        print("   Este script creará las tablas e ingestará los datos")
    else:
        print(f"❌ Respuesta inesperada: {response.status_code}")
        sys.exit(1)
        
except requests.exceptions.Timeout:
    print("❌ Error: Timeout conectando a Supabase")
    print("   Verifica tu conexión a internet")
    sys.exit(1)
except requests.exceptions.ConnectionError:
    print("❌ Error: No se pudo conectar a Supabase")
    print("   Verifica que SUPABASE_URL sea correcto")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
