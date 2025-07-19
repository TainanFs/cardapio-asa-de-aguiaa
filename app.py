import streamlit as st
import os
from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter
from datetime import datetime, time

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Cardápio Asa de Águia",
    page_icon="🔥",
    layout="centered",
    initial_sidebar_state="auto"
)

# --- LÓGICA DE CONEXÃO COM O BANCO DE DADOS ---
try:
    if hasattr(st, 'secrets') and "firestore_credentials" in st.secrets:
        creds_dict = st.secrets["firestore_credentials"]
        db = firestore.Client.from_service_account_info(creds_dict)
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        chave_path = os.path.join(script_dir, "firestore-chave.json")
        db = firestore.Client.from_service_account_json(chave_path)
except Exception as e:
    st.error("🔴 Falha na conexão com o banco de dados.")
    st.error(f"Ocorreu um erro: {e}")
    st.stop()

# --- INICIALIZAÇÃO DO ESTADO DA SESSÃO ---
if 'logged_in' not in st.session_state:
    st.session_state.update({
        'logged_in': False, 'role': None, 'username': None, 'cart': [],
        'table_number': 1, 'client_name': ""
    })

# --- FUNÇÕES DE LÓGICA E TELAS ---
def check_login(username, password):
    users_ref = db.collection("usuarios")
    query = users_ref.where(filter=FieldFilter("nome_usuario", "==", username)).limit(1).stream()
    user_list = [user.to_dict() for user in query]
    if user_list and user_list[0].get("senha") == password:
        return True, user_list[0].get("cargo")
    return False, None

def render_order_placement_screen(db, all_products, all_opcoes):
    st.title(f"👨‍🍳 Lançar Pedido - {st.session_state.get('username')}")
    tipo_comanda = st.radio("Tipo de Comanda:", ["Mesa", "Cliente"], horizontal=True, key="tipo_comanda_launcher")
    identificador_comanda = ""
    if tipo_comanda == "Mesa":
        st.session_state.table_number = st.number_input("Número da Mesa:", min_value=1, step=1, value=st.session_state.get('table_number', 1), key="table_num_launcher")
        identificador_comanda = f"Mesa {st.session_state.table_number}"
    else:
        st.session_state.client_name = st.text_input("Nome do Cliente:", value=st.session_state.get('client_name', ''), key="client_name_launcher")
        identificador_comanda = st.session_state.client_name

    st.write("---")
    tab_sanduiches, tab_cremes, tab_bebidas = st.tabs(["🍔 Sanduíches", "🍨 Cremes", "🥤 Bebidas"])

    with tab_sanduiches:
        st.subheader("Montar Sanduíche")
        sanduiches_base = [p for p in all_products if p.get('categoria') == 'Sanduíches']
        if not sanduiches_base:
            st.info("Nenhum 'Sanduíche' cadastrado.")
        else:
            base_nome = st.selectbox("Escolha o sanduíche:", [s['nome'] for s in sanduiches_base], key="sb_base_launcher")
            base_selecionada = next((s for s in sanduiches_base if s['nome'] == base_nome), None)
            if base_selecionada:
                nome_final_sb = base_selecionada['nome']
                preco_final_sb = base_selecionada.get('preco_base', 0)
                if base_selecionada.get('permite_carne'):
                    carnes_disponiveis = [o for o in all_opcoes if o.get('tipo') == 'Carne']
                    if carnes_disponiveis:
                        nomes_carnes = [c['nome_opcao'] for c in carnes_disponiveis]
                        opcoes_carne_primaria = ["Nenhuma"] + nomes_carnes
                        carne_primaria_nome = st.selectbox("Escolha a carne principal:", opcoes_carne_primaria, key="sb_carne_primaria_launcher")
                        if carne_primaria_nome != "Nenhuma":
                            carne_primaria_info = next((c for c in carnes_disponiveis if c['nome_opcao'] == carne_primaria_nome), None)
                            if carne_primaria_info:
                                preco_final_sb += carne_primaria_info.get('preco_adicional', 0)
                                nome_final_sb += f" com {carne_primaria_nome}"
                            st.write("---")
                            nomes_carnes_secundarias = [c for c in nomes_carnes if c != carne_primaria_nome]
                            opcoes_carne_secundaria = ["Nenhuma"] + nomes_carnes_secundarias
                            carne_secundaria_nome = st.selectbox("Adicionar uma segunda carne? (Opcional)", opcoes_carne_secundaria, key="sb_carne_secundaria_launcher")
                            if carne_secundaria_nome != "Nenhuma":
                                carne_secundaria_info = next((c for c in carnes_disponiveis if c['nome_opcao'] == carne_secundaria_nome), None)
                                if carne_secundaria_info:
                                    preco_final_sb += carne_secundaria_info.get('preco_adicional', 0)
                                    nome_final_sb += f" e {carne_secundaria_nome}"
                quantidade_sb = st.number_input("Quantidade:", min_value=1, value=1, step=1, key="sb_qty_launcher")
                obs_sb = st.text_input("Observações:", key="sb_obs_launcher")
                if st.button("Adicionar Sanduíche ao Pedido", key="sb_add_launcher"):
                    st.session_state.cart.append({"nome": nome_final_sb, "preco_unitario": preco_final_sb, "quantidade": quantidade_sb, "obs": obs_sb})
                    st.success(f"Adicionado: {quantidade_sb}x {nome_final_sb}!")
                    st.rerun()

    with tab_cremes:
        st.subheader("Montar Creme")
        cremes_base = [p for p in all_products if p.get('categoria') == 'Cremes']
        if not cremes_base:
            st.info("Nenhum 'Creme' cadastrado.")
        else:
            creme_nome = st.selectbox("Escolha o creme:", [c['nome'] for c in cremes_base], key="cr_base_launcher")
            creme_selecionado = next((c for c in cremes_base if c['nome'] == creme_nome), None)
            if creme_selecionado:
                nome_final_cr = creme_nome
                preco_final_cr = creme_selecionado.get('preco_base', 0)
                if creme_selecionado.get('permite_adicional'):
                    adicionais_disponiveis = [o for o in all_opcoes if o.get('tipo') == 'Polpa']
                    if adicionais_disponiveis:
                        nomes_adicionais = st.multiselect("Escolha os adicionais:", [a['nome_opcao'] for a in adicionais_disponiveis], key="cr_adicionais_launcher")
                        if nomes_adicionais:
                            adicionais_info = [a for a in adicionais_disponiveis if a['nome_opcao'] in nomes_adicionais]
                            for add_info in adicionais_info:
                                preco_final_cr += add_info.get('preco_adicional', 0)
                            nome_final_cr += f" com {' e '.join(nomes_adicionais)}"
                quantidade_cr = st.number_input("Quantidade:", min_value=1, value=1, step=1, key="cr_qty_launcher")
                obs_cr = st.text_input("Observações:", key="cr_obs_launcher")
                if st.button("Adicionar Creme ao Pedido", key="cr_add_launcher"):
                    st.session_state.cart.append({"nome": nome_final_cr, "preco_unitario": preco_final_cr, "quantidade": quantidade_cr, "obs": obs_cr})
                    st.success(f"Adicionado: {quantidade_cr}x {nome_final_cr}!")
                    st.rerun()

    with tab_bebidas:
        st.subheader("Escolher Bebida")
        bebidas = [p for p in all_products if p.get('categoria') == 'Bebidas']
        if not bebidas:
            st.info("Nenhuma 'Bebida' cadastrada.")
        else:
            bebida_nome = st.selectbox("Escolha a bebida:", [b['nome'] for b in bebidas], key="bb_base_launcher")
            bebida_selecionada = next((b for b in bebidas if b['nome'] == bebida_nome), None)
            if bebida_selecionada:
                preco_bebida = bebida_selecionada.get('preco_base', 0)
                quantidade_bb = st.number_input("Quantidade:", min_value=1, value=1, step=1, key="bb_qty_launcher")
                obs_bb = st.text_input("Observações (ex: com gelo e limão):", key="bb_obs_launcher")
                if st.button("Adicionar Bebida ao Pedido", key="bb_add_launcher"):
                    st.session_state.cart.append({"nome": bebida_nome, "preco_unitario": preco_bebida, "quantidade": quantidade_bb, "obs": obs_bb})
                    st.success(f"Adicionado: {quantidade_bb}x {bebida_nome}!")
                    st.rerun()

    st.write("---")
    st.header(f"Itens a Adicionar na Comanda de: {identificador_comanda}")
    if st.session_state.cart:
        total_a_adicionar = sum(item.get('preco_unitario', 0) * item.get('quantidade', 1) for item in st.session_state.cart)
        for i, item in enumerate(st.session_state.cart):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"- **{item.get('quantidade')}x {item['nome']}** (R$ {item.get('preco_unitario', 0) * item.get('quantidade', 1):.2f})")
                if item.get('obs'):
                    st.markdown(f"  > *Obs: {item['obs']}*")
            with col2:
                if st.button("🗑️", key=f"del_cart_{i}_launcher", help="Remover item"):
                    st.session_state.cart.pop(i)
                    st.rerun()
        st.subheader(f"Total a ser adicionado: R$ {total_a_adicionar:.2f}")
        
        if st.button("✅ Adicionar à Comanda / Abrir Nova", type="primary", key="send_order_launcher"):
            if not identificador_comanda.strip():
                st.warning("Por favor, preencha o número da Mesa ou o nome do Cliente.")
            else:
                query = db.collection("pedidos").where(filter=FieldFilter("identificador", "==", identificador_comanda)).where(filter=FieldFilter("status", "==", "novo")).limit(1)
                comandas_abertas = list(query.stream())
                if comandas_abertas:
                    comanda_existente_doc = comandas_abertas[0]
                    dados_comanda_antiga = comanda_existente_doc.to_dict()
                    novos_itens = dados_comanda_antiga.get('itens', []) + st.session_state.cart
                    novo_total = dados_comanda_antiga.get('total', 0) + total_a_adicionar
                    comanda_existente_doc.reference.update({"itens": novos_itens, "total": novo_total})
                    st.success(f"Itens adicionados à comanda da(o) {identificador_comanda}!")
                else:
                    pedido_final = {"identificador": identificador_comanda, "tipo_identificador": tipo_comanda, "garcom": st.session_state.username, "itens": st.session_state.cart, "total": total_a_adicionar, "status": "novo", "timestamp": firestore.SERVER_TIMESTAMP}
                    db.collection("pedidos").add(pedido_final)
                    st.success(f"Nova comanda aberta para {identificador_comanda}!")
                
                st.session_state.cart = []
                st.balloons()
                st.rerun()
    else:
        st.info("O carrinho está vazio. Adicione itens para enviar à comanda.")

# --- LÓGICA PRINCIPAL DA APLICAÇÃO ---
if not st.session_state.get('logged_in', False):
    st.title("🔥 Cardápio Asa de Águia - Login")
    with st.form("login_form"):
        username = st.text_input("Nome de Usuário")
        password = st.text_input("Senha", type="password")
        login_button = st.form_submit_button("Entrar", type="primary")
        if login_button:
            is_correct, role = check_login(username, password)
            if is_correct:
                st.session_state.logged_in = True
                st.session_state.role = role
                st.session_state.username = username
                st.rerun()
            else:
                st.error("Usuário ou senha inválidos.")
else:
    st.sidebar.write(f"Logado como: **{st.session_state.get('username')}**")
    st.sidebar.write(f"Cargo: **{st.session_state.get('role')}**")
    st.sidebar.button("Sair", on_click=lambda: st.session_state.clear() or st.rerun())

    try:
        all_products_query = db.collection("produtos").where(filter=FieldFilter("disponivel", "==", True)).stream()
        all_products = [p.to_dict() | {'id': p.id} for p in all_products_query]
        all_opcoes_query = db.collection("opcoes").stream()
        all_opcoes = [o.to_dict() | {'id': o.id} for o in all_opcoes_query]
    except Exception as e:
        st.error(f"Erro ao carregar dados do cardápio: {e}")
        st.stop()

        # PAINEL DO ADMIN (SUBSTITUA POR ESTE BLOCO COMPLETO E CORRIGIDO)
    if st.session_state.get('role') == 'admin':
        st.title("⚙️ Painel do Administrador")

        # Inicializa o estado de edição se não existir
        if 'editing_product_id' not in st.session_state:
            st.session_state.editing_product_id = None
        if 'editing_option_id' not in st.session_state:
            st.session_state.editing_option_id = None

        tab_produtos, tab_opcoes, tab_usuarios = st.tabs(["Produtos", "Opções", "Usuários"])

        # --- ABA DE PRODUTOS ---
        with tab_produtos:
            # Se estamos editando um produto, mostra o formulário de edição
            if st.session_state.editing_product_id:
                product_to_edit_ref = db.collection("produtos").document(st.session_state.editing_product_id)
                product_to_edit = product_to_edit_ref.get().to_dict()
                
                st.header(f"✏️ Editando: {product_to_edit.get('nome')}")
                with st.form(key="edit_product_form_main"):
                    novo_nome = st.text_input("Nome do Produto", value=product_to_edit.get("nome"))
                    novo_preco = st.number_input("Preço Base (R$)", value=product_to_edit.get("preco_base"), format="%.2f")
                    nova_categoria = st.selectbox("Categoria", ["Sanduíches", "Bebidas", "Cremes"], index=["Sanduíches", "Bebidas", "Cremes"].index(product_to_edit.get("categoria")))
                    novo_permite_carne = st.checkbox("Permite escolher carnes?", value=product_to_edit.get("permite_carne"))
                    novo_permite_adicional = st.checkbox("Permite adicionais (polpa)?", value=product_to_edit.get("permite_adicional"))
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.form_submit_button("Salvar Alterações", type="primary"):
                            update_data = {"nome": novo_nome, "preco_base": novo_preco, "categoria": nova_categoria, "permite_carne": novo_permite_carne, "permite_adicional": novo_permite_adicional}
                            product_to_edit_ref.update(update_data)
                            st.session_state.editing_product_id = None
                            st.success("Produto atualizado!")
                            st.rerun()
                    with col2:
                        if st.form_submit_button("Cancelar"):
                            st.session_state.editing_product_id = None
                            st.rerun()
            
            # Se não estamos editando, mostra a lista e o form de adicionar
            else:
                st.header("Gerenciamento de Produtos")
                with st.expander("➕ Adicionar Novo Produto"):
                    with st.form(key="add_product_form", clear_on_submit=True):
                        # ... (código do formulário de adicionar produto que já funcionava) ...
                
                st.write("---")
                st.header("Lista de Produtos Cadastrados")
                try:
                    produtos_ref = db.collection("produtos").stream()
                    for produto in produtos_ref:
                        p_data = produto.to_dict()
                        p_id = produto.id
                        col1, col2, col3, col4 = st.columns([2, 0.5, 0.8, 0.8])
                        with col1:
                            st.subheader(p_data.get("nome"))
                            st.caption(f"Categoria: {p_data.get('categoria')} | Preço: R$ {p_data.get('preco_base', 0):.2f}")
                        with col2:
                            if st.button("Editar", key=f"edit_{p_id}"):
                                st.session_state.editing_product_id = p_id
                                st.rerun()
                        with col3:
                            disponivel = p_data.get("disponivel", True)
                            if disponivel:
                                if st.button("Indisponível", key=f"off_{p_id}"):
                                    db.collection("produtos").document(p_id).update({"disponivel": False})
                                    st.rerun()
                            else:
                                if st.button("Disponível", key=f"on_{p_id}", type="primary"):
                                    db.collection("produtos").document(p_id).update({"disponivel": True})
                                    st.rerun()
                        with col4:
                            if st.button("Apagar", key=f"del_{p_id}"):
                                db.collection("produtos").document(p_id).delete()
                                st.rerun()
                except Exception as e:
                    st.error(f"Erro ao buscar produtos: {e}")

        # --- ABA DE OPÇÕES (REPLICANDO O MESMO PADRÃO) ---
        with tab_opcoes:
            if st.session_state.editing_option_id:
                option_to_edit_ref = db.collection("opcoes").document(st.session_state.editing_option_id)
                option_to_edit = option_to_edit_ref.get().to_dict()
                st.header(f"✏️ Editando Opção: {option_to_edit.get('nome_opcao')}")
                with st.form(key="edit_option_form_main"):
                    # ... (formulário de edição de opção) ...
            else:
                st.header("Gerenciamento de Opções")
                with st.expander("➕ Adicionar Nova Opção"):
                    with st.form(key="add_option_form", clear_on_submit=True):
                        # ... (formulário de adicionar opção) ...
                st.write("---")
                st.header("Lista de Opções Cadastradas")
                try:
                    opcoes_ref = db.collection("opcoes").stream()
                    for opcao in opcoes_ref:
                        # ... (lógica de listar e botões para opções) ...
                except Exception as e:
                    st.error(f"Erro ao buscar opções: {e}")

        with tab_usuarios:
            st.info("A funcionalidade de gerenciamento de Usuários será implementada aqui.")

        # --- ABA DE OPÇÕES (CÓDIGO COMPLETO) ---
        with tab_opcoes:
            st.header("Gerenciamento de Opções")
            with st.expander("➕ Adicionar Nova Opção", expanded=False):
                with st.form(key="add_option_form", clear_on_submit=True):
                    st.subheader("Detalhes da Nova Opção")
                    nome_opcao = st.text_input("Nome da Opção (Ex: Bacon, Polpa de Morango)")
                    preco_adicional = st.number_input("Preço Adicional (R$)", format="%.2f", step=0.50, min_value=0.0)
                    tipo_opcao = st.selectbox("Tipo de Opção", ["Carne", "Polpa", "Outro Adicional"])
                    if st.form_submit_button("Adicionar Opção"):
                        if nome_opcao and tipo_opcao:
                            opcao_data = {"nome_opcao": nome_opcao, "preco_adicional": preco_adicional, "tipo": tipo_opcao}
                            db.collection("opcoes").add(opcao_data)
                            st.success(f"Opção '{nome_opcao}' adicionada!")
                            st.rerun()
                        else:
                            st.warning("O Nome e o Tipo são obrigatórios.")
            st.write("---")
            st.header("Lista de Opções Cadastradas")
            try:
                todas_opcoes_ref = db.collection("opcoes").stream()
                lista_opcoes = list(todas_opcoes_ref)
                if not lista_opcoes:
                    st.info("Nenhuma opção cadastrada ainda.")
                else:
                    for opcao in lista_opcoes:
                        o_data = opcao.to_dict()
                        o_id = opcao.id
                        col1, col2 = st.columns([2, 1.2])
                        with col1:
                            st.subheader(o_data.get("nome_opcao", "Nome não encontrado"))
                            st.write(f"Tipo: **{o_data.get('tipo')}** | Preço Adicional: **R$ {o_data.get('preco_adicional', 0):.2f}**")
                        with col2:
                            botoes_col1, botoes_col2 = st.columns(2)
                            with botoes_col1:
                                with st.popover("✏️"):
                                    with st.form(key=f"edit_op_{o_id}"):
                                        st.subheader(f"Editando: {o_data.get('nome_opcao')}")
                                        novo_nome_op = st.text_input("Novo nome", value=o_data.get("nome_opcao"), key=f"name_op_{o_id}")
                                        novo_preco_op = st.number_input("Novo Preço", value=o_data.get("preco_adicional"), format="%.2f", key=f"price_op_{o_id}")
                                        if st.form_submit_button("Salvar"):
                                            db.collection("opcoes").document(o_id).update({"nome_opcao": novo_nome_op, "preco_adicional": novo_preco_op})
                                            st.rerun()
                            with botoes_col2:
                                with st.popover("🗑️"):
                                    st.write(f"Apagar '{o_data.get('nome_opcao')}' permanentemente?")
                                    if st.button("Confirmar Exclusão", key=f"del_op_{o_id}", type="primary"):
                                        db.collection("opcoes").document(o_id).delete()
                                        st.rerun()
            except Exception as e:
                st.error(f"Erro ao buscar opções: {e}")

        with tab_usuarios:
            st.info("A funcionalidade de gerenciamento de Usuários será implementada aqui.")

            # Lógica para Listar, Editar e Apagar Opções
            try:
                todas_opcoes_ref = db.collection("opcoes").stream()
                lista_opcoes = list(todas_opcoes_ref)

                if not lista_opcoes:
                    st.info("Nenhuma opção cadastrada ainda.")
                else:
                    for opcao in lista_opcoes:
                        o_data = opcao.to_dict()
                        o_id = opcao.id

                        col1, col2 = st.columns([2, 1.2])

                        with col1:
                            st.subheader(o_data.get("nome_opcao", "Nome não encontrado"))
                            st.write(f"Tipo: **{o_data.get('tipo')}** | Preço Adicional: **R$ {o_data.get('preco_adicional', 0):.2f}**")
                        
                        with col2:
                            botoes_col1, botoes_col2 = st.columns(2)

                            # Botão Editar
                            with botoes_col1:
                                with st.popover("✏️"):
                                    with st.form(key=f"edit_op_{o_id}"):
                                        st.subheader(f"Editando: {o_data.get('nome_opcao')}")
                                        novo_nome_op = st.text_input("Novo nome", value=o_data.get("nome_opcao"), key=f"name_op_{o_id}")
                                        novo_preco_op = st.number_input("Novo Preço", value=o_data.get("preco_adicional"), format="%.2f", key=f"price_op_{o_id}")
                                        if st.form_submit_button("Salvar"):
                                            db.collection("opcoes").document(o_id).update({"nome_opcao": novo_nome_op, "preco_adicional": novo_preco_op})
                                            st.rerun()

                            # Botão de Apagar com Confirmação
                            with botoes_col2:
                                with st.popover("🗑️"):
                                    st.write(f"Apagar '{o_data.get('nome_opcao')}' permanentemente?")
                                    if st.button("Confirmar Exclusão", key=f"del_op_{o_id}", type="primary"):
                                        db.collection("opcoes").document(o_id).delete()
                                        st.rerun()
            except Exception as e:
                st.error(f"Erro ao buscar opções: {e}")

        with tab_usuarios:
            st.info("A funcionalidade de gerenciamento de Usuários será implementada aqui.")
            # --- Lógica para Listar e Editar Produtos ---
            try:
                todos_produtos_ref = db.collection("produtos").stream()
                lista_produtos = [p for p in todos_produtos_ref] # Materializa a lista

                if not lista_produtos:
                    st.info("Nenhum produto cadastrado ainda.")
                else:
                    for produto in lista_produtos:
                        p_data = produto.to_dict()
                        p_id = produto.id

                        col1, col2, col3 = st.columns([2, 1, 1])
                        
                        with col1:
                            st.subheader(p_data.get("nome", "Nome não encontrado"))
                            st.write(f"Categoria: **{p_data.get('categoria')}** | Preço: **R$ {p_data.get('preco_base', 0):.2f}**")

                        with col2:
                            # Lógica para editar - aqui usamos um formulário dentro de um st.popover
                            with st.popover("✏️ Editar"):
                                with st.form(key=f"edit_{p_id}"):
                                    st.subheader(f"Editando: {p_data.get('nome')}")
                                    novo_nome = st.text_input("Novo nome", value=p_data.get("nome"), key=f"name_{p_id}")
                                    novo_preco = st.number_input("Novo Preço Base (R$)", value=p_data.get("preco_base"), format="%.2f", step=0.50, min_value=0.0, key=f"price_{p_id}")
                                    
                                    if st.form_submit_button("Salvar Alterações"):
                                        update_data = {"nome": novo_nome, "preco_base": novo_preco}
                                        db.collection("produtos").document(p_id).update(update_data)
                                        st.success("Produto atualizado!")
                                        st.rerun()
                        
                        with col3:
                            # Lógica para ativar/desativar
                            disponivel = p_data.get("disponivel", True)
                            if disponivel:
                                if st.button("Tornar Indisponível", key=f"off_{p_id}", type="secondary"):
                                    db.collection("produtos").document(p_id).update({"disponivel": False})
                                    st.rerun()
                            else:
                                if st.button("✅ Tornar Disponível", key=f"on_{p_id}", type="primary"):
                                    db.collection("produtos").document(p_id).update({"disponivel": True})
                                    st.rerun()

            except Exception as e:
                st.error(f"Erro ao buscar produtos: {e}")

        with tab_opcoes:
            st.info("A funcionalidade de gerenciamento de Opções (carnes, polpas) será implementada aqui.")

        with tab_usuarios:
            st.info("A funcionalidade de gerenciamento de Usuários (garçom, caixa) será implementada aqui.")
    elif st.session_state.get('role') == 'garcom':
        render_order_placement_screen(db, all_products, all_opcoes)

    elif st.session_state.get('role') == 'caixa':
        st.title("💰 Painel do Caixa")
        tab_ver_contas, tab_lancar_pedido = st.tabs(["Ver Contas Abertas", "Lançar Novo Pedido"])
        with tab_ver_contas:
            st.header("Contas Pendentes de Pagamento")
            try:
                pedidos_ref = db.collection("pedidos").where(filter=FieldFilter("status", "==", "novo")).order_by("timestamp", direction=firestore.Query.ASCENDING).stream()
                pedidos_a_pagar = [doc.to_dict() | {'id': doc.id} for doc in pedidos_ref]
                if not pedidos_a_pagar:
                    st.success("Nenhuma conta pendente de pagamento. Tudo em dia! ✅")
                else:
                    for pedido in pedidos_a_pagar:
                        identificador_label = f"**{pedido.get('identificador')}**"
                        with st.expander(f"{identificador_label} - Total: R$ {pedido.get('total', 0):.2f}"):
                            st.subheader("Itens Consumidos:")
                            for item in pedido.get('itens', []):
                                st.write(f" - {item.get('quantidade')}x **{item['nome']}**")
                                if item.get('obs'):
                                    st.info(f"   > Obs: {item['obs']}")
                            st.write("---")
                            if st.button("Confirmar Pagamento e Enviar para Cozinha", key=f"pay_{pedido['id']}", type="primary"):
                                db.collection("pedidos").document(pedido['id']).update({"status": "pago"})
                                st.success(f"Pedido de {identificador_label} pago e enviado para a cozinha!")
                                st.balloons()
                                st.rerun()
            except Exception as e:
                st.error(f"Ocorreu um erro ao buscar contas: {e}")
        with tab_lancar_pedido:
            render_order_placement_screen(db, all_products, all_opcoes)

    elif st.session_state.get('role') == 'cozinha':
        st.title("📈 Relatório de Pedidos do Dia")
        try:
            today = datetime.now().date()
            start_of_day = datetime.combine(today, time.min)
            pedidos_ref = db.collection("pedidos").where(filter=FieldFilter("status", "==", "pago")).where(filter=FieldFilter("timestamp", ">=", start_of_day)).order_by("timestamp", direction=firestore.Query.DESCENDING).stream()
            pedidos_pagos_hoje = list(pedidos_ref)
            if not pedidos_pagos_hoje:
                st.success("Nenhum pedido pago registrado hoje.")
            else:
                total_faturado = sum(p.to_dict().get('total', 0) for p in pedidos_pagos_hoje)
                num_pedidos = len(pedidos_pagos_hoje)
                st.metric(label="Faturamento Total do Dia", value=f"R$ {total_faturado:.2f}")
                st.metric(label="Total de Pedidos Pagos", value=num_pedidos)
                st.write("---")
                st.subheader("Lista de Pedidos Pagos Hoje")
                for pedido_doc in pedidos_pagos_hoje:
                    pedido = pedido_doc.to_dict()
                    identificador_label = f"**{pedido.get('identificador')}**"
                    horario = pedido.get('timestamp').strftime('%H:%M:%S') if pedido.get('timestamp') else 'N/A'
                    with st.expander(f"{identificador_label} às {horario} - Total: R$ {pedido.get('total', 0):.2f}"):
                        for item in pedido.get('itens', []):
                            st.write(f" - {item.get('quantidade')}x **{item['nome']}**")
                            if item.get('obs'):
                                st.info(f"   > Obs: {item['obs']}")
        except Exception as e:
            st.error(f"Ocorreu um erro ao gerar o relatório: {e}")
            st.warning("Se o erro mencionar um 'índice', por favor, clique no link na mensagem de erro para criá-lo no Firebase e tente novamente.")

    else:
        st.error("Seu cargo não foi reconhecido ou não possui um painel definido.")
