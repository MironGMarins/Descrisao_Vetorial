import pandas as pd
from sentence_transformers import SentenceTransformer
from deep_translator import GoogleTranslator
from sqlalchemy import create_engine, text
import psycopg2

# --- 1. CONFIGURAÇÃO IGUAL AO QUE FUNCIONOU ---
USUARIO = 'postgres'
SENHA = '2026' 
HOST = '127.0.0.1'
PORTA = '5432'
BANCO = 'cine_vector'

# Usamos a função que deu certo no outro script
def abrir_conexao():
    return psycopg2.connect(
        user=USUARIO,
        password=SENHA,
        host=HOST,
        port=PORTA,
        database=BANCO,
        client_encoding='utf8' # Isso resolve o erro de Unicode
    )

# Criamos o motor usando o 'creator'
conexao = create_engine("postgresql://", creator=abrir_conexao)

# --- 2. CARREGA O MODELO ---
print("Carregando inteligência artificial...")
modelo = SentenceTransformer('all-MiniLM-L6-v2')

def buscar_filmes():
    print("\n" + "="*30)
    pergunta = input("🤖 O que você procura hoje? ")
    
    print("✨ Traduzindo e processando...")
    # A tradução do GoogleTranslator pode retornar o 'Valentine's Day' com aspas
    pergunta_en = GoogleTranslator(source='pt', target='en').translate(pergunta)
    print(f"🔎 Buscando por: '{pergunta_en}'")

    vetor_pergunta = modelo.encode(pergunta_en).tolist()

    # Usamos :vetor (parâmetro) para evitar erros com aspas da tradução
    query = text("""
        SELECT title, overview, vote_average,
               embedding <=> :vetor AS distancia
        FROM filmes
        ORDER BY distancia ASC
        LIMIT 5;
    """)
    
    # Passamos o vetor com params
    resultados = pd.read_sql(query, conexao, params={"vetor": str(vetor_pergunta)})

    print("\n🍿 Talvez você goste dessas opções:")
    for i, linha in resultados.iterrows():
        print(f"\n🎬 {linha['title']} (Nota: {linha['vote_average']})")
        print(f"📖 {linha['overview'][:150]}...")
        print("-" * 20)

while True:
    try:
        buscar_filmes()
    except Exception as e:
        print(f"❌ Ocorreu um erro: {e}")
    
    continuar = input("\nQuer buscar outro? (s/n): ")
    if continuar.lower() != 's':
        break