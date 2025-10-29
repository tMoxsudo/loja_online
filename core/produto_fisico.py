# Arquivo: core/produto_fisico.py
from .produto import Produto
from .avaliacao import Avaliacao # Importa a classe Avaliacao

class ProdutoFisico(Produto):
    """
    Subclasse de Produto. Demonstra HERANÇA e POLIMORFISMO (Frete).
    Agora também gerencia avaliações (COMPOSIÇÃO).
    """
    def __init__(self, nome, preco, peso, imagem_url, categoria="Físico"):
        super().__init__(nome, preco, categoria)
        self.peso = peso
        self.imagem_url = imagem_url
        self.avaliacoes = [] # Lista para COMPOSIÇÃO de Avaliacoes

    def calcular_frete(self):
        """Implementação Polimórfica 1: Frete baseado no peso."""
        return 10.0 + (self.peso * 0.5) 
        
    def adicionar_avaliacao(self, avaliacao: Avaliacao):
        """Adiciona uma nova avaliação ao produto."""
        if isinstance(avaliacao, Avaliacao):
            self.avaliacoes.append(avaliacao)

    def calcular_media_avaliacoes(self) -> float:
        """Calcula a média das notas das avaliações."""
        if not self.avaliacoes:
            return 0.0 # Retorna 0 se não houver avaliações
        
        soma_notas = sum(avl.nota for avl in self.avaliacoes)
        return round(soma_notas / len(self.avaliacoes), 1) # Arredonda para 1 casa decimal

    def to_json(self):
        """Serializa o Produto, incluindo a lista de avaliações."""
        data = super().to_json()
        data['peso'] = self.peso
        data['imagem_url'] = self.imagem_url
        # Serializa cada objeto Avaliacao na lista
        data['avaliacoes'] = [avl.to_json() for avl in self.avaliacoes] 
        return data
        
    @staticmethod
    def from_json(data):
        """Reconstrói a instância do ProdutoFisico, incluindo avaliações."""
        produto = ProdutoFisico(
            data['nome'], 
            data['preco'], 
            data.get('peso', 0.0), # Usa get com default para segurança
            data.get('imagem_url', ''), 
            data['categoria']
        )
        # Reconstrói a lista de avaliações
        for avl_data in data.get('avaliacoes', []):
            avaliacao_obj = Avaliacao.from_json(avl_data)
            if avaliacao_obj: # Adiciona apenas se a reconstrução for bem-sucedida
                produto.adicionar_avaliacao(avaliacao_obj)
        
        return produto