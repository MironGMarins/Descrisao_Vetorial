import pandas as pd
from sentence_transformers import SentenceTransformer
from sqlalchemy import create_engine

# --- 1. CONFIGURAÇÃO DE ACESSO ---
# Aqui você diz ao Python como entrar no seu banco de dados.
# Substitua 'sua_senha' pela senha que você definiu no PostgreSQL.
USUARIO = 'postgres'
SENHA = 'sua_senha'
HOST = 'localhost'
PORTA = '5432'
BANCO = 'Meu Projeto Vetorial'

# Criamos o "motor" de conexão
conexao = create_engine(f'postgresql://{USUARIO}:{SENHA}@{HOST}:{PORTA}/{BANCO}')

# --- 2. CARREGANDO OS DADOS ---
# O Pandas abre o Excel. O 'r' antes do caminho ajuda o Windows a não se confundir com as barras \
caminho_arquivo = r'C:\Caminho\Para\Seu\Arquivo_10000.csv'
df = pd.read_csv(caminho_arquivo)

# Se alguma sinopse estiver vazia, preenchemos com um texto padrão para a IA não travar
df['overview'] = df['overview'].fillna('Sem descrição')

# --- 3. A INTELIGÊNCIA ARTIFICIAL ---
print("Iniciando a IA... Na primeira vez, ela fará um download de 80MB.")
# Aqui carregamos o 'cérebro' pronto que vai traduzir texto em números.
modelo = SentenceTransformer('all-MiniLM-L6-v2')

# A IA lê a coluna 'overview' e cria a lista de 384 números (vetor) para cada filme
print("A IA está lendo as sinopses e gerando os vetores. Aguarde...")
vetores = modelo.encode(df['overview'].tolist(), show_progress_bar=True)

# Guardamos esses números em uma nova coluna no nosso DataFrame
df['embedding'] = [list(v) for v in vetores]

# --- 4. SALVANDO NO POSTGRES ---
print("Enviando tudo para o PostgreSQL...")
# 'if_exists=append' significa: coloque os dados na tabela 'filmes' que já criamos
# 'index=False' evita que o Python crie uma coluna extra de contagem
df.to_sql('filmes', conexao, if_exists='append', index=False)

print("✅ Tudo pronto! Seu banco de dados agora é inteligente.")