-- 1. Habilitar a extensão pgvector (Obrigatório antes de criar a tabela)
-- Lembre-se de colar a DLL na pasta lib antes de rodar este comando
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Criar a tabela 'filmes' com todas as colunas do seu dataset
-- Nota: Usei TEXT para datas e campos complexos para evitar erros de importação
CREATE TABLE filmes (
    id INTEGER PRIMARY KEY,
    title TEXT,
    genres TEXT,
    original_language VARCHAR(10),
    overview TEXT,
    popularity FLOAT,
    production_companies TEXT,
    release_date TEXT, 
    budget BIGINT,
    revenue BIGINT,
    runtime FLOAT,
    status TEXT,
    tagline TEXT,
    vote_average FLOAT,
    vote_count INTEGER,
    credits TEXT,
    keywords TEXT,
    poster_path TEXT,
    backdrop_path TEXT,
    recommendations TEXT,
    embedding vector(384) -- Onde a IA vai guardar os vetores de 384 dimensões
);

-- 3. Query de Teste (Para usar depois que importar os dados)
-- Esta query lista os 5 filmes mais parecidos com uma sinopse específica
-- Substitua '[...]' pelo vetor gerado pela IA
-- SELECT title, overview FROM filmes 
-- ORDER BY embedding <=> '[...]' 
-- LIMIT 5;