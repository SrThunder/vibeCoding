#!/usr/bin/env python3
"""
Script para ingerir catálogo de productos DOLMEN en Supabase.
Versión simplificada usando REST API directamente.
"""

import json
import os
import requests
from typing import Dict, List
import hashlib
from datetime import datetime

from dotenv import load_dotenv
from openai import OpenAI

# Cargar variables de entorno
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not all([SUPABASE_URL, SUPABASE_KEY, OPENAI_API_KEY]):
    print("❌ Error: Faltan variables de entorno")
    exit(1)

# Inicializar cliente OpenAI
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# Headers para Supabase REST API
HEADERS = {
    "apikey": SUPABASE_KEY,
    "Content-Type": "application/json",
    "Authorization": f"Bearer {SUPABASE_KEY}"
}


def generate_embedding(text: str) -> List[float]:
    """Genera embedding usando OpenAI text-embedding-3-small."""
    try:
        response = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"❌ Error generando embedding: {e}")
        return None


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 100) -> List[str]:
    """Divide un texto en chunks con overlap."""
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        start = end - overlap
        if start < 0:
            start = 0
    
    return chunks


def ingest_faqs():
    """Ingesta las FAQs del archivo JSON."""
    print("\n📚 Ingestando FAQs...")
    
    try:
        with open("faq_poc.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        
        faqs = data.get("faqs", [])
        print(f"   Leyendo {len(faqs)} FAQs del archivo")
        
        for faq in faqs:
            try:
                faq_id = faq["id"]
                pregunta = faq["pregunta"]
                respuesta = faq["respuesta"]
                
                # Generar embedding
                text_to_embed = f"{pregunta} {respuesta}"
                embedding = generate_embedding(text_to_embed)
                
                if embedding is None:
                    print(f"   ⚠️  Saltando {faq_id} - error con embedding")
                    continue
                
                # Preparar datos para Supabase
                faq_data = {
                    "faq_id": faq_id,
                    "pregunta": pregunta,
                    "respuesta": respuesta,
                    "categoria": faq.get("categoria", ""),
                    "palabras_clave": faq.get("palabras_clave", []),
                    "productos_relacionados": faq.get("productos_relacionados", []),
                    "pdf_link": faq.get("pdf_link", ""),
                    "embedding": embedding,
                    "created_at": datetime.now().isoformat()
                }
                
                # Insertar en Supabase
                response = requests.post(
                    f"{SUPABASE_URL}/rest/v1/faqs",
                    headers=HEADERS,
                    json=faq_data
                )
                
                if response.status_code in [200, 201]:
                    print(f"   ✅ {faq_id} ingestado")
                else:
                    print(f"   ❌ {faq_id}: {response.status_code} - {response.text[:100]}")
                    
            except Exception as e:
                print(f"   ❌ Error con FAQ: {e}")
                continue
        
        print(f"✅ FAQs ingestadas")
        
    except FileNotFoundError:
        print("❌ Error: faq_poc.json no encontrado")
    except Exception as e:
        print(f"❌ Error ingestando FAQs: {e}")


def ingest_catalog():
    """Ingesta el catálogo del archivo JSON."""
    print("\n📦 Ingestando Catálogo...")
    
    try:
        with open("catalogo_jerarquia.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        
        products = data.get("productos", [])
        print(f"   Leyendo {len(products)} productos del archivo")
        
        for product in products:
            try:
                product_id = product["id"]
                nombre = product["nombre"]
                descripcion = product.get("descripcion", "")
                
                # Dividir descripción en chunks
                chunks = chunk_text(descripcion)
                
                for chunk_idx, chunk in enumerate(chunks):
                    # Generar embedding para el chunk
                    embedding = generate_embedding(chunk)
                    
                    if embedding is None:
                        continue
                    
                    # Preparar datos
                    product_data = {
                        "product_id": product_id,
                        "nombre": nombre,
                        "categoria": product.get("categoria", ""),
                        "subcategoria": product.get("subcategoria", ""),
                        "descripcion": descripcion[:500],  # Solo primeros 500 chars
                        "variantes": product.get("variantes", []),
                        "usos": product.get("usos", []),
                        "beneficios": product.get("beneficios", []),
                        "chunk_index": chunk_idx,
                        "chunk_text": chunk,
                        "embedding": embedding,
                        "created_at": datetime.now().isoformat()
                    }
                    
                    # Insertar
                    response = requests.post(
                        f"{SUPABASE_URL}/rest/v1/products",
                        headers=HEADERS,
                        json=product_data
                    )
                    
                    if response.status_code not in [200, 201]:
                        print(f"   ❌ {product_id} chunk {chunk_idx}: {response.status_code}")
                
                print(f"   ✅ {product_id} ingestado ({len(chunks)} chunks)")
                        
            except Exception as e:
                print(f"   ❌ Error con producto: {e}")
                continue
        
        print(f"✅ Catálogo ingestado")
        
    except FileNotFoundError:
        print("❌ Error: catalogo_jerarquia.json no encontrado")
    except Exception as e:
        print(f"❌ Error ingestando catálogo: {e}")


def main():
    print("🚀 Iniciando ingesta de datos...")
    print(f"📍 Supabase: {SUPABASE_URL}")
    
    ingest_faqs()
    ingest_catalog()
    
    print("\n✅ Ingesta completada")


if __name__ == "__main__":
    main()
