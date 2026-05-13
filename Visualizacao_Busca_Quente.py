import pandas as pd
import numpy as np
import plotly.express as px
from sklearn.manifold import TSNE
from sqlalchemy import create_engine, text
from sentence_transformers import SentenceTransformer
from deep_translator import GoogleTranslator
import psycopg2
import ast

# --- 1. CONFIGURAÇÃO E CONEXÃO ---
USUARIO, SENHA, HOST, PORTA, BANCO = 'postgres', '2026', '127.0.0.1', '5432', 'cine_vector'

def abrir_conexao():
    return psycopg2.connect(user=USUARIO, password=SENHA, host=HOST, port=PORTA, database=BANCO, client_encoding='utf8')

conexao = create_engine("postgresql://", creator=abrir_conexao)
modelo = SentenceTransformer('all-MiniLM-L6-v2')

# --- 2. ENTRADA E TRADUÇÃO ---
pergunta = "Um filme triste onde um cachorro morre"
print(f"🔎 Processando busca: '{pergunta}'")
pergunta_en = GoogleTranslator(source='pt', target='en').translate(pergunta)
vetor_pergunta = modelo.encode(pergunta_en).tolist()

# --- 3. BUSCA NO BANCO ---
print("🔥 Buscando dados e calculando similaridade...")
query = text("SELECT title, genres, embedding, (embedding <=> :vetor) AS distancia FROM filmes")
df = pd.read_sql(query, conexao, params={"vetor": str(vetor_pergunta)})

# Criamos o score de "Calor" (quanto menor a distância, maior o calor)
df['calor'] = 1 - df['distancia']

# --- 4. REDUÇÃO DE DIMENSIONALIDADE (t-SNE para criar as Ilhas) ---
print("📍 Criando ilhas de proximidade com t-SNE (isso pode levar 1 minuto)...")
X = np.array([ast.literal_eval(v) for v in df['embedding']])

# O t-SNE agrupa melhor que o PCA
tsne = TSNE(n_components=2, perplexity=30, random_state=42, init='pca', learning_rate='auto')
coords = tsne.fit_transform(X)
df['x'], df['y'] = coords[:, 0], coords[:, 1]

# --- 5. GRÁFICO INTERATIVO (PLOTLY) ---
print("✨ Gerando mapa interativo...")

# Garantimos que o tamanho seja sempre positivo para o Plotly não reclamar
# Criamos uma coluna de tamanho que vai de 5 (frio) a 20 (quente)
df['tamanho_ponto'] = np.interp(df['calor'], (df['calor'].min(), df['calor'].max()), [5, 25])

fig = px.scatter(
    df, x='x', y='y',
    color='calor',
    size='tamanho_ponto',    # <-- Usamos a nova coluna garantida positiva
    hover_name='title',
    hover_data={
        'genres': True,
        'calor': ':.4f',
        'tamanho_ponto': False, # Esconde a coluna técnica de tamanho
        'x': False, 'y': False
    },
    color_continuous_scale='RdBu_r', 
    title=f'Mapa Semântico Interativo - Busca: "{pergunta}"'
)

# Ajustes de layout
fig.update_layout(template='plotly_dark', paper_bgcolor='#111', plot_bgcolor='#111')

print("✅ Tudo certo! Abrindo o navegador...")
fig.show()