# --- INÍCIO DO CÓDIGO DE IMPRESSÃO ---

# ATENÇÃO: Adapte esta função para buscar dados do seu sistema real.
def buscar_dados_do_pedido(id_pedido):
    """
    Esta função simula a busca de dados de um pedido.
    Adapte-a para o seu sistema real.
    """
    print(f"DEBUG: Buscando dados para o pedido de ID: {id_pedido}")
    
    # Adicionei um creme e mais um item para um teste melhor.
    dados_ficticios = {
        "id": "123",
        "cliente": "Mesa 05",
        "itens": [
            {"qtd": 2, "nome": "Coca-Cola Lata", "preco_unit": 5.00},
            {"qtd": 1, "nome": "Porcao de Fritas G", "preco_unit": 25.00},
            {"qtd": 1, "nome": "Creme de Acai 500ml", "preco_unit": 18.00}, # ITEM TIPO CREME
            {"qtd": 1, "nome": "X-Burger Especial", "preco_unit": 20.00},
        ],
        "data_hora": "21/07/2025 02:28" # Data/hora atualizada
    }
    
    if str(id_pedido) == dados_ficticios["id"]:
        return dados_ficticios
    
    return None

@app.route('/imprimir/pedido/<id_pedido>')
def imprimir_pedido(id_pedido):
    """
    Esta rota busca os dados de um pedido e formata como um cupom de texto
    com duas seções: uma geral e uma para cremes.
    """
    pedido = buscar_dados_do_pedido(id_pedido)

    if not pedido:
        return "Pedido nao encontrado!", 404

    # --- 1. SEPARAÇÃO DOS ITENS ---
    itens_gerais = []
    itens_creme = []
    
    # Assumimos que um item é creme se a palavra "creme" estiver no nome.
    # Você pode criar uma lógica mais robusta se tiver categorias de produtos.
    for item in pedido['itens']:
        itens_gerais.append(item) # A primeira via tem TUDO.
        if 'creme' in item['nome'].lower():
            itens_creme.append(item)

    # --- 2. MONTAGEM DO CUPOM ---
    LARGURA_CUPOM = 32
    
    # --- PARTE 1: VIA COMPLETA (COZINHA GERAL) ---
    cupom_texto = "       ASA DE AGUIA\n"
    cupom_texto += "       VIA COZINHA\n"
    cupom_texto += "--------------------------------\n"
    cupom_texto += f"PEDIDO: {pedido['id']} | CLIENTE: {pedido['cliente']}\n"
    cupom_texto += f"DATA: {pedido['data_hora']}\n"
    cupom_texto += "--------------------------------\n"
    
    total_pedido = 0.0
    for item in itens_gerais: # Usamos a lista com todos os itens
        preco_total_item = item['qtd'] * item['preco_unit']
        total_pedido += preco_total_item
        
        linha_item = f"{item['qtd']}x {item['nome']}"
        preco_str = f"R${preco_total_item:7.2f}"
        
        espacos = LARGURA_CUPOM - len(linha_item) - len(preco_str)
        linha_formatada = linha_item + ("." * espacos) + preco_str
        
        cupom_texto += linha_formatada[:LARGURA_CUPOM] + "\n"

    cupom_texto += "--------------------------------\n"
    
    texto_total = "TOTAL:"
    valor_total_str = f"R${total_pedido:7.2f}"
    espacos = LARGURA_CUPOM - len(texto_total) - len(valor_total_str)
    linha_total_formatada = texto_total + (" " * espacos) + valor_total_str
    
    cupom_texto += linha_total_formatada + "\n"
    
    # --- PARTE 2: VIA DE CREMES (SÓ SE EXISTIR) ---
    if itens_creme: # Este bloco só executa se a lista 'itens_creme' não estiver vazia
        cupom_texto += "\n"
        cupom_texto += "--------------------------------\n"
        cupom_texto += "        VIA CREMES\n"
        cupom_texto += "--------------------------------\n"
        cupom_texto += f"PEDIDO: {pedido['id']} | CLIENTE: {pedido['cliente']}\n"
        cupom_texto += "--------------------------------\n"
        
        for item in itens_creme:
            linha_item = f"{item['qtd']}x {item['nome']}"
            cupom_texto += linha_item + "\n"
            
        cupom_texto += "--------------------------------\n"

    cupom_texto += "\n\n\n" # Pulos de linha para ejetar o papel
    
    return Response(cupom_texto, mimetype='text/plain; charset=utf-8')

# --- FIM DO CÓDIGO DE IMPRESSÃO ---
