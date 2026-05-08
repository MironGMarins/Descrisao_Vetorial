import pandas as pd
from sentence_transformers import SentenceTransformer
from sqlalchemy import create_engine
import sys

# --- 1. CONFIGURAÇÕES DE ACESSO ---
USUARIO = 'postgres'
SENHA = '2026'
HOST = 'localhost'
PORTA = '5432'
BANCO = 'cine_vector'

# Mudamos para 'pg8000'. Ele é imune aos erros de acento do Windows!
url_conexao = f"postgresql+pg8000://{USUARIO}:{SENHA}@{HOST}:{PORTA}/{BANCO}"
engine = create_engine(url_conexao)

# --- 2. CARREGANDO OS DADOS ---
caminho_arquivo = 'para vetores.xlsx' 

print(f"--- Lendo o arquivo: {caminho_arquivo} ---")
try:
    df = pd.read_excel(caminho_arquivo)
except Exception as e:
    print(f"Erro ao ler o Excel: {e}")
    sys.exit()

# Preencher vazios
df['overview'] = df['overview'].fillna('Sem descrição')

# --- 3. A INTELIGÊNCIA ARTIFICIAL ---
print("--- Gerando vetores (Sentence Transformers) ---")
modelo = SentenceTransformer('all-MiniLM-L6-v2')
vetores = modelo.encode(df['overview'].tolist(), show_progress_bar=True)
df['embedding'] = [list(v) for v in vetores]

# --- 4. TRATAMENTO DE TEXTO ---
# Transformamos tudo em string para garantir que acentos estrangeiros não quebrem
for col in df.columns:
    if df[col].dtype == 'object':
        df[col] = df[col].astype(str)

# --- 5. ENVIANDO PARA O POSTGRES ---
print("--- Enviando dados para o PostgreSQL via pg8000 ---")
try:
    # chunksize=500 ajuda a não travar a memória
    df.to_sql('filmes', engine, if_exists='append', index=False, chunksize=500)
    print("✅ FINALMENTE! Sucesso total. Seus filmes estão no banco.")
except Exception as e:
    print(f"❌ Erro ao salvar: {e}")
