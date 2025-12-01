-- Script SQL para crear las tablas en Supabase
-- Ejecuta esto en: https://app.supabase.com → SQL Editor

-- 1. Habilitar extensión pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Crear tabla FAQs
CREATE TABLE IF NOT EXISTS faqs (
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
);

-- 3. Crear tabla Products
CREATE TABLE IF NOT EXISTS products (
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
);

-- 4. Crear índices para búsqueda vectorial rápida
CREATE INDEX IF NOT EXISTS idx_faqs_embedding ON faqs USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_products_embedding ON products USING ivfflat (embedding vector_cosine_ops);

-- 5. Habilitar RLS (Row Level Security)
ALTER TABLE faqs ENABLE ROW LEVEL SECURITY;
ALTER TABLE products ENABLE ROW LEVEL SECURITY;

-- 6. Crear políticas para acceso anónimo (lectura)
CREATE POLICY "Allow anonymous read" ON faqs FOR SELECT USING (true);
CREATE POLICY "Allow anonymous read" ON products FOR SELECT USING (true);

-- Confirmar que se creó todo correctamente
SELECT 
    'faqs' as table_name, 
    COUNT(*) as row_count 
FROM faqs
UNION ALL
SELECT 
    'products' as table_name, 
    COUNT(*) as row_count 
FROM products;
