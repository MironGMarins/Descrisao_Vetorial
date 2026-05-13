import pandas as pd
from sentence_transformers import SentenceTransformer
from sqlalchemy import create_engine, Text
import psycopg2
from urllib.parse import quote_plus

# --- 1. CONFIGURAÇÃO DE ACESSO (BLINDADA) ---
USUARIO = 'postgres'
SENHA = '2026'  # <-- COLOQUE SUA SENHA REAL AQUI
HOST = '127.0.0.1'        # Usar 127.0.0.1 é mais seguro que 'localhost'
PORTA = '5432'
BANCO = 'cine_vector'

# Função especial para evitar o erro de 'utf-8' (o tal do ç escondido)
def minha_conexao():
    return psycopg2.connect(
        user=USUARIO,
        password=SENHA,
        host=HOST,
        port=PORTA,
        database=BANCO,
        client_encoding='utf8'
    )

# Criamos o motor usando a função acima
conexao = create_engine("postgresql://", creator=minha_conexao)

# --- 2. CARREGAMENTO E LIMPEZA (O FILTRO DE DUPLICADAS) ---
print("Lendo o arquivo Excel...")
df = pd.read_excel('para vetores.xlsx', engine='openpyxl')

print(f"Total de linhas no Excel: {len(df)}")

# A MÁGICA ESTÁ AQUI: 
# Remove linhas onde o Título e a Sinopse são idênticos.
df = df.drop_duplicates(subset=['title', 'overview'], keep='first')

# Remove também se houver IDs repetidos (por precaução)
if 'id' in df.columns:
    df = df.drop_duplicates(subset=['id'], keep='first')

print(f"Total de linhas após a limpeza: {len(df)}")

# Preenche vazios
df['overview'] = df['overview'].fillna('No description available')

# --- 3. VETORIZAÇÃO (MODELO AFIADO EM INGLÊS) ---
print("Criando 'sopa de dados' para a IA (Título + Sinopse + Keywords + Tagline)...")

# Combinamos as colunas em uma única frase de contexto
# O .astype(str) garante que tudo seja lido como texto
df['contexto_completo'] = (
    "Title: " + df['title'].astype(str) + ". " +
    "Description: " + df['overview'].fillna('') + ". " +
    "Keywords: " + df['keywords'].fillna('') + ". " +
    "Tagline: " + df['tagline'].fillna('')
)

print("Iniciando o modelo all-MiniLM-L6-v2...")
modelo = SentenceTransformer('all-MiniLM-L6-v2')

print("Gerando vetores de alta precisão... Isso pode demorar um pouco mais agora.")
# Agora a IA lê a coluna combinada!
vetores = modelo.encode(df['contexto_completo'].tolist(), show_progress_bar=True)

# Transforma os vetores em string para o formato do pgvector
df['embedding'] = [f"[{','.join(map(str, v))}]" for v in vetores]

# --- 4. ENVIO PARA O BANCO ---
print("Enviando dados limpos para o PostgreSQL...")

# Definimos apenas as colunas que REALMENTE existem na tabela do banco
# Note que NÃO incluímos 'contexto_completo' aqui, pois ela só serviu para a IA ler
colunas_para_salvar = [
    'id', 'title', 'genres', 'original_language', 'overview', 
    'popularity', 'production_companies', 'release_date', 'budget', 
    'revenue', 'runtime', 'status', 'tagline', 'vote_average', 
    'vote_count', 'credits', 'keywords', 'poster_path', 
    'backdrop_path', 'recommendations', 'embedding'
]

try:
    # Filtramos o DataFrame para levar só o que o banco aceita
    # O .intersection garante que só pegaremos colunas que existem no seu Excel
    colunas_finais = [c for c in colunas_para_salvar if c in df.columns]
    df_final = df[colunas_finais]
    
    # Lembre-se de dar TRUNCATE na tabela no pgAdmin antes!
    df_final.to_sql('filmes', conexao, if_exists='append', index=False, dtype={'embedding': Text})
    print(f"✅ SUCESSO! {len(df_final)} filmes processados com contexto completo.")
except Exception as e:
    print(f"❌ Erro: {e}")
