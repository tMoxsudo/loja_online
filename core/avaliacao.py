# Arquivo: core/avaliacao.py

class Avaliacao:
    """Representa uma avaliação (nota e comentário) feita por um cliente."""
    def __init__(self, cliente_id, nota, comentario):
        # Validação básica da nota
        if not 1 <= nota <= 5:
            raise ValueError("A nota da avaliação deve estar entre 1 e 5.")
        
        self.cliente_id = cliente_id # ID do cliente que avaliou (Associação)
        self.nota = nota
        self.comentario = comentario

    def to_json(self):
        """Serializa a Avaliação para JSON."""
        return {
            'cliente_id': self.cliente_id,
            'nota': self.nota,
            'comentario': self.comentario
        }
    
    @staticmethod
    def from_json(data):
        """Reconstrói a Avaliação a partir do JSON."""
        # Adiciona tratamento de erro se os dados estiverem incompletos
        try:
            return Avaliacao(
                data['cliente_id'],
                data['nota'],
                data.get('comentario', '') # Comentário é opcional
            )
        except KeyError:
            print("AVISO: Dados de avaliação incompletos. Ignorando.")
            return None # Retorna None se os dados essenciais faltarem