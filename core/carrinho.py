# Arquivo: core/carrinho.py

import random
import string
from .cliente import Cliente
from .item_carrinho import ItemCarrinho
from pagamentos.pagamento import Pagamento 
from core.produto_fisico import ProdutoFisico # Para type hinting e from_json

class Carrinho:
    """
    Demonstra Associação, Composição e Status de Entrega.
    Contém o método 'adicionar_item' que faltava.
    """
    def __init__(self, cliente: Cliente):
        self.cliente = cliente
        self.itens = []      
        self.status = "ABERTO" # Status do pagamento
        self.status_entrega = None # Ex: Preparando, Enviado, Entregue
        self.codigo_rastreio = None 

    # --- MÉTODO CRÍTICO QUE ESTAVA FALTANDO ---
    def adicionar_item(self, item: ItemCarrinho):
        """Adiciona ItemCarrinho."""
        self.itens.append(item)

    def calcular_total(self):
        """Calcula o valor total."""
        return sum(item.calcular_subtotal() for item in self.itens)

    def finalizar_compra(self, forma_pagamento: Pagamento):
        """Processa o pagamento e define o status inicial de entrega."""
        total = self.calcular_total()
        
        print(f"\n--- INICIANDO PROCESSAMENTO DE PAGAMENTO (Total: R$ {total}) ---")
        forma_pagamento.valor = total
        forma_pagamento.processar() # Chamada POLIMÓRFICA
        
        self.status = "PROCESSADO"
        
        # Define um status inicial de entrega aleatório
        status_possiveis = ["Pedido recebido", "Preparando envio", "Aguardando coleta"]
        self.status_entrega = random.choice(status_possiveis)
        
        # Gera um código de rastreio aleatório
        if self.status_entrega in ["Aguardando coleta", "Enviado"]: 
             self.codigo_rastreio = 'BR' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=11)) + 'BR'
        
        print(f"--- COMPRA FINALIZADA (Status Entrega: {self.status_entrega}) ---")

    # --- MÉTODOS DE SERIALIZAÇÃO JSON ---
    def to_json(self):
        """Serializa o Carrinho, incluindo status de entrega."""
        cliente_id = next((cid for cid, c in Cliente.db_ref.items() if c is self.cliente), None)
        
        return {
            'cliente_id': cliente_id,
            'itens': [item.to_json() for item in self.itens], 
            'status': self.status,
            'status_entrega': self.status_entrega, 
            'codigo_rastreio': self.codigo_rastreio 
        }

    @staticmethod
    def from_json(data, cliente_ref, produtos_db):
        """Reconstrói o Carrinho, incluindo status de entrega."""
        from core.item_carrinho import ItemCarrinho # Evita import circular

        carrinho = Carrinho(cliente_ref)
        carrinho.status = data.get('status', 'ABERTO')
        carrinho.status_entrega = data.get('status_entrega') 
        carrinho.codigo_rastreio = data.get('codigo_rastreio') 
        
        for item_data in data.get('itens', []):
            try:
                # Usa o from_json do ItemCarrinho
                item = ItemCarrinho.from_json(item_data)
                carrinho.itens.append(item)
            except Exception as e:
                print(f"Erro ao reconstruir item do carrinho no from_json: {e}")
            
        return carrinho