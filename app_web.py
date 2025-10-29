# Arquivo: app_web.py - Servidor Flask (COMPLETO E FINAL)

from flask import Flask, render_template, request, redirect, url_for, session
import database 
from core.cliente import Cliente 
from core.carrinho import Carrinho
from core.item_carrinho import ItemCarrinho
from core.produto_fisico import ProdutoFisico
from core.avaliacao import Avaliacao 
from pagamentos.pagamento_pix import PagamentoPix
from pagamentos.pagamento_cartao import PagamentoCartao
from pagamentos.pagamento_boleto import PagamentoBoleto
import os
from pathlib import Path
import sys
from datetime import timedelta 

# --- INICIALIZAÇÃO DO FLASK E SESSÃO ---
basedir = Path(os.path.dirname(os.path.abspath(__file__)))
app = Flask(__name__, 
            template_folder=str(basedir / 'templates'))

app.secret_key = 'chave_muito_secreta_para_oo_unb' 
app.permanent_session_lifetime = timedelta(minutes=15) 
app.config.update(SESSION_PERMANENT=True)

sys.path.append(str(basedir))

# Carrega os dados
DB = database.carregar_dados_json()
Cliente.db_ref = DB['clientes'] 

# Função de ajuda para obter o cliente logado
def get_current_user():
    user_id = session.get('user_id')
    return DB['clientes'].get(user_id) if user_id else None


# --- ROTA DE AUTENTICAÇÃO/LOGIN/LOGOUT ---

@app.route('/auth', methods=['GET', 'POST'])
def login_cadastro():
    """Lida com a rota de Login/Cadastro."""
    if request.method == 'POST':
        acao = request.form.get('acao')
        
        if acao == 'cadastro':
            return redirect(url_for('cadastrar_cliente_web'))
            
        elif acao == 'login':
            cpf_login = request.form.get('cpf_login')
            senha = request.form.get('senha_login')
            
            cliente_logado = next((c for c in DB['clientes'].values() if c.cpf == cpf_login), None)
            
            if cliente_logado and cliente_logado.senha == senha:
                cliente_id_logado = next((key for key, client in DB['clientes'].items() if client.cpf == cpf_login), None)

                if cliente_id_logado:
                    session['logged_in'] = True
                    session['user_name'] = cliente_logado.nome
                    session['is_admin'] = cliente_logado.is_admin
                    session['user_id'] = cliente_id_logado 
                    session.permanent = True 
                    
                    return redirect(url_for('index'))
                else:
                    return render_template('login_cadastro.html', erro_login="Erro interno ao buscar ID do cliente.")
            else:
                return render_template('login_cadastro.html', erro_login="CPF ou Senha incorretos.")

    return render_template('login_cadastro.html')

@app.route('/logout')
def logout():
    """Função para terminar a sessão do usuário."""
    session.clear() 
    return redirect(url_for('index'))


# --- ROTAS DE VISUALIZAÇÃO PRINCIPAIS ---

@app.route('/')
def index():
    """Rota principal. Exibe o Dashboard."""
    erro_carrinho = request.args.get('erro_carrinho')
    
    return render_template(
        'index.html',
        is_admin=session.get('is_admin', False),
        user_name=session.get('user_name', 'Visitante'),
        clientes=DB['clientes'].items(),
        produtos=DB['produtos'].items(),
        carrinhos=DB['carrinhos'].items(),
        erro_carrinho=erro_carrinho 
    )

@app.route('/cadastrar_cliente', methods=['GET', 'POST'])
def cadastrar_cliente_web():
    """Demonstra Herança e Persistência."""
    if request.method == 'POST':
        nome = request.form['nome']
        cpf = request.form['cpf']
        endereco = request.form['endereco']
        senha = request.form['senha']
        
        novo_cliente = Cliente(nome, cpf, endereco, senha=senha, is_admin=False)
        
        cliente_id = str(DB['next_ids']['cliente'])
        DB['clientes'][cliente_id] = novo_cliente
        DB['next_ids']['cliente'] += 1
        database.salvar_dados_json(DB)
        
        session['logged_in'] = True
        session['user_name'] = novo_cliente.nome
        session['is_admin'] = False
        session['user_id'] = cliente_id 
        session.permanent = True
        
        return redirect(url_for('index'))
    
    return render_template('cadastro.html')


# --- ROTA CRÍTICA: PROCESSA ADIÇÃO DE ITEM (POST) ---

@app.route('/carrinho/adicionar_item', methods=['POST'])
def adicionar_item_processa():
    """
    Processa a adição de item vindo da página de Detalhes.
    """
    # CORREÇÃO: Pega o usuário da sessão.
    cliente_atual = get_current_user() 
    
    # Se não houver usuário logado, força o login.
    if not cliente_atual:
        return redirect(url_for('login_cadastro', erro="Você precisa estar logado para comprar."))
    
    if request.method == 'POST':
        produto_id = request.form.get('produto_id')
        quantidade = request.form.get('quantidade', type=int)
        acao_compra = request.form.get('acao_compra') 
        produto_obj = DB['produtos'].get(produto_id)
        
        if not produto_obj or not quantidade or quantidade < 1:
            return redirect(url_for('index', erro_carrinho="Dados de compra inválidos."))

        # Lógica de Carrinho Existente
        carrinhos = DB['carrinhos']
        carrinho_keys = [int(k) for k in carrinhos.keys()]
        ultimo_id = max(carrinho_keys) if carrinho_keys else 0 
        ultimo_carrinho = carrinhos.get(str(ultimo_id))

        carrinho_atual = None
        
        # Decide qual carrinho usar baseado na ação
        if acao_compra == 'compra_imediata':
            novo_id = str(ultimo_id + 1)
            carrinho_atual = Carrinho(cliente_atual) # Usa o cliente da sessão
            carrinhos[novo_id] = carrinho_atual
            DB['next_ids']['carrinho'] = int(novo_id) + 1 
        
        elif acao_compra == 'adicionar_carrinho':
            if ultimo_carrinho and ultimo_carrinho.status == 'ABERTO' and ultimo_carrinho.cliente == cliente_atual:
                carrinho_atual = ultimo_carrinho
            else:
                novo_id = str(ultimo_id + 1)
                carrinho_atual = Carrinho(cliente_atual) # Usa o cliente da sessão
                carrinhos[novo_id] = carrinho_atual
                DB['next_ids']['carrinho'] = int(novo_id) + 1 
        
        if carrinho_atual:
            item = ItemCarrinho(produto_obj, quantidade)
            carrinho_atual.adicionar_item(item) 
            database.salvar_dados_json(DB)
        
        if acao_compra == 'compra_imediata':
            return redirect(url_for('checkout_web')) 
        
        return redirect(url_for('index')) 

    return redirect(url_for('index'))


# --- ROTA DE CHECKOUT (VISUALIZAÇÃO DE CARRINHO E BLOQUEIO) ---

@app.route('/checkout', methods=['GET', 'POST'])
def checkout_web():
    """
    Simula o checkout. Esta é a rota acessada pelo ícone do carrinho (🛒).
    """
    
    carrinho_keys = [int(k) for k in DB['carrinhos'].keys()]
    carrinho_id = max(carrinho_keys) if carrinho_keys else None
    ultimo_carrinho = DB['carrinhos'].get(str(carrinho_id))
    
    # LÓGICA DE BLOQUEIO CRÍTICA: Se vazio, redireciona para a home com erro (Pop-up).
    if not ultimo_carrinho or ultimo_carrinho.calcular_total() == 0 or ultimo_carrinho.status == "PROCESSADO":
        return redirect(url_for('index', erro_carrinho="Seu carrinho está vazio. Adicione itens primeiro!"))

    if request.method == 'POST':
        forma_escolhida = request.form['pagamento']
        total = ultimo_carrinho.calcular_total()
        parcelas = request.form.get('parcelas', type=int) 
        
        pix_info = None
        
        if forma_escolhida == 'pix':
            forma_pagamento = PagamentoPix(total, "UNB.PIX@000")
            pix_info = {
                'code': "00020126360014BR.GOV.BCB.PIX0114...",
                'qr_url': 'https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=' + str(total)
            }
        elif forma_escolhida == 'cartao':
            forma_pagamento = PagamentoCartao(total, "**** 4444", parcelas=parcelas)
        elif forma_escolhida == 'boleto':
            forma_pagamento = PagamentoBoleto(total)
        else:
            return redirect(url_for('index'))

        # Lógica POO
        ultimo_carrinho.finalizar_compra(forma_pagamento) 
        database.salvar_dados_json(DB)
        
        return render_template('confirmacao.html', forma=forma_escolhida, total=total, pix_info=pix_info)
    
    return render_template('checkout.html', carrinho=ultimo_carrinho)


# --- ROTA CRÍTICA: LIMPAR CARRINHO ---

@app.route('/carrinho/limpar', methods=['POST'])
def limpar_carrinho():
    """Função para apagar todos os itens do carrinho atual."""
    carrinho_keys = [int(k) for k in DB['carrinhos'].keys()]
    carrinho_id = max(carrinho_keys) if carrinho_keys else None
    ultimo_carrinho = DB['carrinhos'].get(str(carrinho_id))
    
    if ultimo_carrinho and ultimo_carrinho.status == 'ABERTO':
        cliente_ref = ultimo_carrinho.cliente
        novo_carrinho_vazio = Carrinho(cliente_ref)
        DB['carrinhos'][str(carrinho_id)] = novo_carrinho_vazio
        database.salvar_dados_json(DB)
        
    return redirect(url_for('checkout_web'))


# --- NOVAS ROTAS DO MENU DE USUÁRIO ---

@app.route('/perfil', methods=['GET', 'POST'])
def perfil_usuario():
    """Permite ao usuário visualizar e editar suas informações."""
    cliente = get_current_user()
    if not cliente:
        return redirect(url_for('login_cadastro', erro="Acesso negado. Faça login."))
        
    if request.method == 'POST':
        cliente.nome = request.form['nome']
        cliente.endereco = request.form['endereco']
        
        nova_senha = request.form.get('senha')
        if nova_senha:
            cliente.senha = nova_senha 
            
        DB['clientes'][session['user_id']] = cliente 
        database.salvar_dados_json(DB)
        session['user_name'] = cliente.nome 
        
        return redirect(url_for('perfil_usuario', sucesso="Perfil atualizado com sucesso!"))
        
    sucesso = request.args.get('sucesso')
    return render_template('perfil.html', cliente=cliente, sucesso=sucesso)

@app.route('/pedidos')
def pedidos_prontos():
    """Exibe os pedidos que já foram finalizados com status de entrega."""
    cliente = get_current_user()
    if not cliente:
        return redirect(url_for('login_cadastro', erro="Acesso negado. Faça login."))
        
    # --- CORREÇÃO DO FILTRO: Usa o objeto cliente para comparação ---
    pedidos_finalizados = []
    for pid, c in DB['carrinhos'].items():
        # Compara o objeto cliente do carrinho com o objeto cliente da sessão
        if c.status == 'PROCESSADO' and c.cliente == cliente:
            pedidos_finalizados.append((pid, c))

    return render_template('pedidos.html', cliente=cliente, pedidos=pedidos_finalizados)


# --- ROTAS ADMINISTRATIVAS ---

@app.route('/admin')
def admin_dashboard():
    """Exibe o painel de administração."""
    if not session.get('is_admin'):
        return redirect(url_for('index')) 
    return render_template('admin_dashboard.html', 
                           clientes=DB['clientes'].items(),
                           produtos=DB['produtos'].items())

@app.route('/admin/editar/<pid>', methods=['GET', 'POST'])
def admin_editar_produto(pid):
    """Permite alterar informações de um produto existente."""
    if not session.get('is_admin'):
        return redirect(url_for('index')) 
    produto = DB['produtos'].get(pid)
    if not produto:
        return "Produto não encontrado.", 404
    if request.method == 'POST':
        produto.nome = request.form['nome']
        produto.preco = float(request.form['preco'])
        produto.categoria = request.form['categoria']
        produto.imagem_url = request.form['imagem_url']
        produto.peso = float(request.form['peso'])
        database.salvar_dados_json(DB)
        return redirect(url_for('admin_dashboard'))
    return render_template('admin_editar_produto.html', produto=produto, pid=pid)


# --- ROTAS DE DETALHES DO PRODUTO E BUSCA ---

@app.route('/produto/<pid>')
def detalhe_produto(pid):
    """Exibe a página de detalhes do produto."""
    produto = DB['produtos'].get(pid)
    if not produto:
        return "Produto não encontrado.", 404
        
    # Lógica para buscar o nome do cliente da avaliação
    avaliacoes_enriquecidas = []
    for avl in produto.avaliacoes:
        cliente_avaliador = DB['clientes'].get(avl.cliente_id)
        nome_avaliador = cliente_avaliador.nome if cliente_avaliador else "Usuário Anônimo"
        
        avaliacoes_enriquecidas.append({
            'nome': nome_avaliador,
            'nota': avl.nota,
            'comentario': avl.comentario
        })

    return render_template(
        'detalhe_produto.html',
        produto=produto,
        pid=pid,
        frete=produto.calcular_frete(), # Polimorfismo
        avaliacoes=avaliacoes_enriquecidas # Passa a lista com nomes
    )

@app.route('/produto/<pid>/avaliar', methods=['POST']) 
def avaliar_produto(pid):
    """Processa o formulário de avaliação do produto."""
    cliente = get_current_user()
    if not cliente:
        return redirect(url_for('login_cadastro', erro="Faça login para avaliar."))
        
    produto = DB['produtos'].get(pid)
    if not produto:
        return "Produto não encontrado.", 404
        
    if request.method == 'POST':
        try:
            nota = request.form.get('nota', type=int)
            comentario = request.form.get('comentario', '')
            
            nova_avaliacao = Avaliacao(cliente_id=session['user_id'], nota=nota, comentario=comentario)
            
            produto.adicionar_avaliacao(nova_avaliacao)
            database.salvar_dados_json(DB) 
            
            return redirect(url_for('detalhe_produto', pid=pid))
            
        except ValueError as e: 
            return render_template(
                'detalhe_produto.html',
                produto=produto, pid=pid, frete=produto.calcular_frete(),
                avaliacoes=produto.avaliacoes, 
                erro_avaliacao=str(e) 
            )
        except Exception as e:
            return f"Erro ao processar avaliação: {e}", 500

    return redirect(url_for('detalhe_produto', pid=pid))


@app.route('/busca')
def busca():
    """
    Exibe a página de busca, permitindo filtros por termo, categoria e preço.
    """
    termo = request.args.get('termo', '')
    categoria_filtro = request.args.get('categoria', '') 
    preco_max_filtro_str = request.args.get('preco_max', '') 
    avaliacao_min_filtro = request.args.get('avaliacao_min', type=int, default=1) 

    preco_max_filtro = None
    if preco_max_filtro_str:
        try:
            preco_max_filtro = float(preco_max_filtro_str)
        except ValueError:
            pass 

    produtos_filtrados = []
    for pid, p in DB['produtos'].items():
        match_termo = termo.lower() in p.nome.lower() or not termo
        match_categoria = p.categoria.lower() == categoria_filtro.lower() if categoria_filtro else True
        match_preco = p.preco <= preco_max_filtro if preco_max_filtro is not None else True
        media_avaliacao = p.calcular_media_avaliacoes()
        match_avaliacao = media_avaliacao >= avaliacao_min_filtro
        
        if match_termo and match_categoria and match_preco and match_avaliacao:
            produtos_filtrados.append((pid, p))
            
    
    return render_template(
        'busca.html',
        produtos=produtos_filtrados,
        categorias=['Eletrônico', 'Livro', 'Vestuário', 'Móveis', 'Acessório', 'Informática'], 
        termo=termo,
        categoria_selecionada=categoria_filtro,
        preco_max_selecionado=preco_max_filtro_str,
        avaliacao_min_selecionada=avaliacao_min_filtro
    )


if __name__ == '__main__':
    app.run(debug=True)