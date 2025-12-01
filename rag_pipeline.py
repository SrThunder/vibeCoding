"""
Módulo RAG con soporte para referencias a PDF.
Implementa pipeline híbrido: FAQ primero, luego búsqueda vectorial.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from supabase import create_client
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
import json


@dataclass
class RAGResponse:
    """Respuesta del pipeline RAG."""
    respuesta: str
    fuente: str  # "faq" o "rag"
    producto_recomendado: Optional[Dict] = None
    pdf_link: Optional[str] = None
    confianza: float = 0.0


class HybridRAGPipeline:
    """Pipeline RAG híbrido: FAQ + búsqueda vectorial."""
    
    def __init__(self, supabase_url: str, supabase_key: str, openai_api_key: str):
        self.supabase = create_client(supabase_url, supabase_key)
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    
    def _search_faqs(self, query: str, local_id: str, threshold: float = 0.75) -> Optional[Dict]:
        """
        Busca en FAQs usando similitud de embeddings.
        
        Args:
            query: Pregunta del usuario
            local_id: ID del local (multi-tenant)
            threshold: Mínimo de similitud (0-1)
        
        Returns:
            FAQ si se encuentra, None en caso contrario
        """
        query_embedding = self.embeddings.embed_query(query)
        
        # Intentar buscar en tabla faqs (Supabase). Si falla, usar fallback local (faq_poc.json)
        try:
            response = self.supabase.rpc(
                "search_faqs",
                {
                    "query_embedding": query_embedding,
                    "local_id": local_id,
                    "match_threshold": threshold,
                }
            ).execute()

            if response.data and len(response.data) > 0:
                return response.data[0]
        except Exception as e:
            # Fallback local: cargar faq_poc.json y hacer búsqueda por palabras clave
            try:
                with open("faq_poc.json", "r", encoding="utf-8") as f:
                    faqs = json.load(f).get("faqs", [])
                q = query.lower()
                # Mejor búsqueda por tokens: coincidir suficientes tokens en cualquier campo
                tokens = [t for t in q.split() if len(t) > 2]
                for faq in faqs:
                    text = " ".join([str(faq.get(k, "")) for k in ("pregunta", "respuesta", "categoria")]).lower()
                    matches = sum(1 for t in tokens if t in text)
                    # Considerar match si se encuentran al menos la mitad de los tokens (mínimo 1)
                    if matches >= max(1, len(tokens) // 2):
                        return {
                            "id": faq.get("id"),
                            "question": faq.get("pregunta"),
                            "answer": faq.get("respuesta"),
                            "category": faq.get("categoria"),
                            "pdf_link": faq.get("pdf_link"),
                        }
            except Exception:
                pass

        return None
    
    def _search_products(self, query: str, local_id: str, top_k: int = 3) -> List[Dict]:
        """
        Busca productos relevantes usando similitud vectorial.
        
        Args:
            query: Necesidad del usuario
            local_id: ID del local
            top_k: Número de resultados a retornar
        
        Returns:
            Lista de productos relevantes
        """
        query_embedding = self.embeddings.embed_query(query)
        
        # Intentar buscar en tabla products (Supabase). Si falla, usar fallback local (catalogo_jerarquia.json)
        try:
            response = self.supabase.rpc(
                "search_products",
                {
                    "query_embedding": query_embedding,
                    "local_id": local_id,
                    "match_count": top_k,
                }
            ).execute()

            return response.data if response.data else []
        except Exception:
            # Fallback local: cargar catalogo_jerarquia.json y hacer búsqueda por nombre/categoría
            try:
                with open("catalogo_jerarquia.json", "r", encoding="utf-8") as f:
                    catalog = json.load(f)
                    products = catalog.get("products", []) if isinstance(catalog, dict) else catalog
                q = query.lower()
                matches = []
                for p in products:
                    text = " ".join([str(p.get(k, "")) for k in ("nombre", "categoria", "descripcion")]).lower()
                    if q in text:
                        matches.append({
                            "id": p.get("id"),
                            "product_id": p.get("product_id") or p.get("id"),
                            "nombre": p.get("nombre") or p.get("id"),
                            "categoria": p.get("categoria"),
                            "descripcion": p.get("descripcion", ""),
                            "variantes": p.get("variantes", []),
                            "usos": p.get("usos", []),
                            "beneficios": p.get("beneficios", []),
                            "pdf_link": p.get("pdf_link"),
                            "stock": p.get("stock", True),
                        })
                    if len(matches) >= top_k:
                        break
                return matches
            except Exception:
                return []
    
    def _generate_response(
        self,
        query: str,
        context: str,
        productos: List[Dict],
        pdf_links: List[str]
    ) -> str:
        """
        Genera respuesta usando LLM con contexto RAG.
        """
        prompt = ChatPromptTemplate.from_template("""
Eres un vendedor experto en materiales de construcción DOLMEN.
Responde la pregunta del cliente usando el contexto disponible.

CONTEXTO DE PRODUCTOS:
{context}

PREGUNTA DEL CLIENTE:
{query}

INSTRUCCIONES:
1. Responde de forma clara y concisa (máximo 3 oraciones)
2. Recomenda productos específicos si es relevante
3. Menciona variantes o especificaciones técnicas
4. Sé amable y profesional

RESPUESTA:
""")
        
        chain = prompt | self.llm
        response = chain.invoke({
            "context": context,
            "query": query,
        })
        
        return response.content
    
    def query(self, pregunta: str, local_id: str) -> RAGResponse:
        """
        Pipeline completo: FAQ → Búsqueda Vectorial → Generación
        
        Args:
            pregunta: Pregunta del usuario
            local_id: ID del local (multi-tenant)
        
        Returns:
            RAGResponse con respuesta, fuente y referencias
        """
        # 1. Buscar en FAQs (rápido y preciso)
        faq = self._search_faqs(pregunta, local_id)
        if faq:
            return RAGResponse(
                respuesta=faq["answer"],
                fuente="faq",
                pdf_link=faq.get("pdf_link"),
                confianza=0.95,
            )
        
        # 2. Buscar productos relevantes
        productos = self._search_products(pregunta, local_id, top_k=3)
        
        if not productos:
            return RAGResponse(
                respuesta="No encontré productos relevantes. Por favor, contacta con nuestro equipo de soporte.",
                fuente="rag",
                confianza=0.0,
            )
        
        # 3. Construir contexto
        context_parts = []
        for prod in productos:
            part = f"""
Producto: {prod['nombre']}
Descripción: {prod['descripcion']}
Usos: {', '.join(prod['usos'])}
Variantes: {', '.join(prod['variantes'][:2])}
Beneficios: {', '.join(prod['beneficios'])}
"""
            context_parts.append(part)
        
        context = "\n---\n".join(context_parts)
        pdf_links = [p.get("pdf_link") for p in productos if p.get("pdf_link")]
        
        # 4. Generar respuesta con LLM
        respuesta = self._generate_response(
            pregunta,
            context,
            productos,
            pdf_links,
        )
        
        return RAGResponse(
            respuesta=respuesta,
            fuente="rag",
            producto_recomendado=productos[0],
            pdf_link=pdf_links[0] if pdf_links else None,
            confianza=0.85,
        )


# SQL Functions para Supabase (ejecutar en SQL Editor)
SUPABASE_SQL = """
-- Crear función de búsqueda en FAQs
CREATE OR REPLACE FUNCTION search_faqs(
    query_embedding vector,
    local_id text,
    match_threshold float DEFAULT 0.75
)
RETURNS TABLE (
    id text,
    question text,
    answer text,
    category text,
    pdf_link text,
    similarity float
) LANGUAGE sql STABLE AS $$
    SELECT
        faqs.id,
        faqs.question,
        faqs.answer,
        faqs.category,
        faqs.pdf_link,
        1 - (faqs.vector <=> query_embedding) AS similarity
    FROM faqs
    WHERE faqs.local_id = local_id
    AND 1 - (faqs.vector <=> query_embedding) > match_threshold
    ORDER BY similarity DESC
    LIMIT 1;
$$;

-- Crear función de búsqueda en Productos
CREATE OR REPLACE FUNCTION search_products(
    query_embedding vector,
    local_id text,
    match_count int DEFAULT 3
)
RETURNS TABLE (
    id text,
    product_id text,
    nombre text,
    categoria text,
    descripcion text,
    variantes text[],
    usos text[],
    beneficios text[],
    pdf_link text,
    stock boolean,
    similarity float
) LANGUAGE sql STABLE AS $$
    SELECT
        products.id,
        products.product_id,
        products.nombre,
        products.categoria,
        products.descripcion,
        products.variantes,
        products.usos,
        products.beneficios,
        products.pdf_link,
        products.stock,
        1 - (products.vector <=> query_embedding) AS similarity
    FROM products
    WHERE products.local_id = local_id
    AND products.stock = true
    ORDER BY similarity DESC
    LIMIT match_count;
$$;
"""

print("Módulo RAG cargado correctamente")
