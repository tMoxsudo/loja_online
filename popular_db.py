import requests
import json
import random

# O arquivo de banco de dados que seu app usa
DB_FILE = 'data.json'
# A API que vamos usar
API_URL = 'https://fakestoreapi.com/products?limit=10' # Vamos buscar 10 produtos

def fetch_new_products():
    """Busca novos produtos da API."""
    print("Buscando novos produtos da FakeStoreAPI...")
    try:
        response = requests.get(API_URL)
        response.raise_for_status() # Lança um erro se a requisição falhar
        return response.json()
    except Exception as e:
        print(f"ERRO ao buscar produtos: {e}")
        return None

def format_product(api_product, new_id):
    """Converte o formato da API para o formato do nosso DB."""
    return {
        "nome": api_product['title'],
        "preco": float(api_product['price']),
        "categoria": api_product['category'],
        "peso": round(random.uniform(0.2, 5.0), 1), # A API não tem peso, então vamos simular
        "imagem_url": api_product['image'] # A API JÁ NOS DÁ A IMAGEM!
    }

def main():
    """Função principal para carregar, atualizar e salvar o DB."""
    
    # Carrega o data.json existente
    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Erro: Arquivo {DB_FILE} não encontrado.")
        return
    except json.JSONDecodeError:
        print(f"Erro: Arquivo {DB_FILE} está corrompido ou vazio.")
        return

    # Busca os produtos novos
    new_products_api = fetch_new_products()
    if not new_products_api:
        print("Nenhum produto foi buscado. Saindo.")
        return

    # Acha o último ID de produto para continuar a contagem
    existing_product_keys = [int(k) for k in data['produtos'].keys()]
    next_id = max(existing_product_keys) + 1
    
    count = 0
    for product in new_products_api:
        # Formata o produto para o nosso padrão
        formatted = format_product(product, next_id)
        
        # Adiciona ao dicionário de produtos
        product_id_str = str(next_id)
        data['produtos'][product_id_str] = formatted
        
        print(f"Adicionando ID {product_id_str}: {formatted['nome'][:30]}...")
        
        next_id += 1
        count += 1

    # Salva o arquivo data.json de volta no disco
    try:
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"ERRO ao salvar o arquivo: {e}")
        return

    print(f"\nSUCESSO! {count} novos produtos foram adicionados ao {DB_FILE}.")

if __name__ == "__main__":
    main()