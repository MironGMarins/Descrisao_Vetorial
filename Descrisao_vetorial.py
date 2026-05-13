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
print("Iniciando o modelo all-MiniLM-L6-v2 (O mais preciso)...")
modelo = SentenceTransformer('all-MiniLM-L6-v2')

print("Gerando vetores... Isso será rápido.")
vetores = modelo.encode(df['overview'].tolist(), show_progress_bar=True)
df['embedding'] = [f"[{','.join(map(str, v))}]" for v in vetores]

# --- 4. ENVIO PARA O BANCO ---
print("Enviando dados limpos para o PostgreSQL...")
try:
    # Lembre-se de dar TRUNCATE na tabela no pgAdmin antes de rodar!
    df.to_sql('filmes', conexao, if_exists='append', index=False, dtype={'embedding': Text})
    print(f"✅ SUCESSO! {len(df)} filmes únicos foram processados e salvos.")
except Exception as e:
    print(f"❌ Erro: {e}")
