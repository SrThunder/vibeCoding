#!/usr/bin/env python3
"""
Script para ingerir catálogo de productos DOLMEN en Supabase.
Genera embeddings y popula las tablas de Supabase.
"""

import json
import os
from typing import Dict, List
import hashlib
from datetime import datetime

from dotenv import load_dotenv
from supabase import create_client
from openai import OpenAI

# Cargar variables de entorno
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Inicializar clientes
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
openai_client = OpenAI(api_key=OPENAI_API_KEY)


def generate_embedding(text: str) -> List[float]:
    """Genera embedding usando OpenAI text-embedding-3-small."""
    response = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 100) -> List[str]:
    """
    Divide un texto en chunks con overlap.
    
    Args:
        text: Texto a dividir
        chunk_size: Tamaño de cada chunk (caracteres)
        overlap: Caracteres de solapamiento entre chunks
    
    Returns:
        Lista de chunks
    """
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    step = chunk_size - overlap
    start = 0
    
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        start += step
        
        if end == len(text):
            break
    
    return chunks


def prepare_product_text(product: Dict) -> str:
    """Prepara texto para embedding a partir de un producto."""
    parts = [
        f"Producto: {product['nombre']}",
        f"Categoría: {product['categoria']}",
        f"Descripción: {product.get('descripcion', '')}",
        f"Usos: {', '.join(product.get('usos', []))}",
        f"Beneficios: {', '.join(product.get('beneficios', []))}",
    ]
    
    if product.get('variantes'):
        parts.append(f"Variantes: {', '.join(product['variantes'][:3])}")
    
    return " ".join(parts)


def ingest_products(catalog_path: str, local_id: str = "LOCAL_001"):
    """
    Ingesta productos del catálogo en Supabase.
    
    Args:
        catalog_path: Ruta al archivo JSON del catálogo
        local_id: ID del local (para multi-tenant)
    """
    print(f"[INFO] Cargando catálogo desde {catalog_path}...")
    
    with open(catalog_path, 'r', encoding='utf-8') as f:
        catalog = json.load(f)
    
    print(f"[INFO] Encontrados {len(catalog['productos'])} productos")
    
    for idx, product in enumerate(catalog['productos'], 1):
        try:
            print(f"[{idx}/{len(catalog['productos'])}] Procesando {product['nombre']}...")
            
            # Preparar texto para embedding
            product_text = prepare_product_text(product)
            
            # Dividir en chunks
            chunks = chunk_text(product_text, chunk_size=500, overlap=100)
            
            # Generar embedding para cada chunk
            for chunk_idx, chunk in enumerate(chunks):
                print(f"  → Chunk {chunk_idx + 1}/{len(chunks)}")
                
                # Generar embedding
                embedding = generate_embedding(chunk)
                
                # Preparar datos para Supabase
                product_data = {
                    "id": f"{product['id']}_chunk_{chunk_idx}",
                    "product_id": product['id'],
                    "nombre": product['nombre'],
                    "categoria": product['categoria'],
                    "subcategoria": product.get('subcategoria', ''),
                    "descripcion": product.get('descripcion', ''),
                    "contenido": chunk,
                    "variantes": product.get('variantes', []),
                    "usos": product.get('usos', []),
                    "beneficios": product.get('beneficios', []),
                    "pdf_link": product.get('pdf_link', ''),
                    "stock": product.get('stock', True),
                    "local_id": local_id,
                    "vector": embedding,
                    "created_at": datetime.now().isoformat(),
                }
                
                # Insertar en Supabase (tabla: products)
                response = supabase.table("products").insert(product_data).execute()
                
                if response.data:
                    print(f"  ✓ Insertado: {product_data['id']}")
                else:
                    print(f"  ✗ Error al insertar: {product['nombre']}")
        
        except Exception as e:
            print(f"  ✗ Error procesando {product['nombre']}: {str(e)}")
            continue
    
    print("\n[INFO] Ingesta completada!")


def create_faqs(local_id: str = "LOCAL_001"):
    """
    Ingesta FAQs en Supabase.
    """
    faqs = [
        {
            "id": "FAQ_001",
            "question": "¿Cuál es la diferencia entre varilla corrugada y malla electrosoldada?",
            "answer": "La varilla corrugada se usa para refuerzo en columnas y vigas no sismorresistentes, mientras que la malla electrosoldada es mejor para aplicaciones que requieren menor personal y menos espacio en obra.",
            "category": "Aceromateriales",
            "pdf_link": "https://dolmen.com/catalogo/aceromateriales.pdf",
        },
        {
            "id": "FAQ_002",
            "question": "¿Qué pintura debo usar para exterior?",
            "answer": "Recomendamos Látex Supremo para paredes exteriores. Es resistente al clima, tiene buen rendimiento y ofrece un acabado liso duradero.",
            "category": "Pinturas",
            "pdf_link": "https://dolmen.com/catalogo/pinturas.pdf",
        },
        {
            "id": "FAQ_003",
            "question": "¿El Combo Max incluye todo para instalar un baño?",
            "answer": "Sí, el Combo Max incluye inodoro (Milán HET), lavabo (Alpes) y llave (Capri). Es una solución integral para baños.",
            "category": "Grifería",
            "pdf_link": "https://dolmen.com/catalogo/griferia.pdf",
        },
        {
            "id": "FAQ_004",
            "question": "¿Cuál es el mejor mortero para pegado de cerámicas?",
            "answer": "Maxibond Standard es el indicado para pegado de cerámicas y azulejos. Tiene buena adherencia y es fácil de mezclar.",
            "category": "Morteros_Pegantes",
            "pdf_link": "https://dolmen.com/catalogo/morteros.pdf",
        },
        {
            "id": "FAQ_005",
            "question": "¿Qué bloque recomiendan para muros divisorios?",
            "answer": "Para muros divisorios recomendamos Bloque Rojo Rayado en dimensión 07x30x41. Es económico, duradero y fácil de trabajar.",
            "category": "Bloques_Acabados",
            "pdf_link": "https://dolmen.com/catalogo/bloques.pdf",
        },
    ]
    
    print(f"[INFO] Ingestion {len(faqs)} FAQs...")
    
    for faq in faqs:
        try:
            # Generar embedding para la pregunta
            embedding = generate_embedding(faq["question"])
            
            faq_data = {
                "id": faq["id"],
                "question": faq["question"],
                "answer": faq["answer"],
                "category": faq["category"],
                "pdf_link": faq["pdf_link"],
                "vector": embedding,
                "local_id": local_id,
                "created_at": datetime.now().isoformat(),
            }
            
            # Insertar en tabla faqs
            response = supabase.table("faqs").insert(faq_data).execute()
            
            if response.data:
                print(f"  ✓ FAQ insertada: {faq['id']}")
            else:
                print(f"  ✗ Error al insertar FAQ: {faq['id']}")
        
        except Exception as e:
            print(f"  ✗ Error con FAQ {faq['id']}: {str(e)}")
            continue
    
    print("[INFO] FAQs ingestion completada!")


if __name__ == "__main__":
    catalog_path = "/Users/jorgec/Documents/1-PORTAFOLIO/DOLMEN/catalogo_jerarquia.json"
    
    print("=" * 60)
    print("INGESTA DE CATÁLOGO DOLMEN EN SUPABASE")
    print("=" * 60)
    
    # Ingestar productos
    ingest_products(catalog_path)
    
    # Ingestar FAQs
    create_faqs()
    
    print("\n✓ ¡Proceso completado!")
