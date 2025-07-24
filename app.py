import streamlit as st
import os
from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter
from datetime import datetime, time, timedelta

### ALTERAÇÃO: Importar bibliotecas de impressão ###
try:
    import win32print
    import win32api
    WINDOWS_PRINTING_ENABLED = True
except ImportError:
    WINDOWS_PRINTING_ENABLED = False

# --- FUNÇÕES DE IMPRESSÃO ---

### NOVO: Função para imprimir a comanda da cozinha ###
def formatar_comanda_cozinha(identificador, garcom, itens_novos):
    """Cria uma string formatada para a comanda da cozinha, com apenas os novos itens."""
    try:
        timestamp = datetime.now()
        texto = f"--- COZINHA/BAR - {timestamp.strftime('%H:%M:%S')} ---\n"
        texto += f"COMANDA: {identificador}\n"
        texto += f"GARCOM: {garcom}\n"
        texto += "--------------------------------------\n"
        
        for item in itens_novos:
            nome = item.get('nome', 'Item sem nome')
            qtd = item.get('quantidade', 1)
            texto += f"** {qtd}x {nome} **\n"
            if item.get('obs'):
                texto += f"  > Obs: {item.get('obs')}\n"
        
        texto += "--------------------------------------\n\n\n"
        return texto
    except Exception as e:
        st.warning(f"Não foi possível formatar a comanda da cozinha. Erro: {e}")
        return None

def formatar_cupom_para_impressao(pedido_dict):
    """Cria uma string formatada para o cupom de pagamento final."""
    try:
        # ... (Esta função permanece a mesma da resposta anterior) ...
        identificador = pedido_dict.get('identificador', 'N/A')
        garcom = pedido_dict.get('garcom', 'N/A')
        timestamp = pedido_dict.get('timestamp')
        
        texto = "--------- CUPOM DE PAGAMENTO ---------\n\n"
        texto += f"Comanda: {identificador}\n"
        texto += f"Garcom: {garcom}\n"
        if timestamp and isinstance(timestamp, datetime):
            texto += f"Horario Fechamento: {timestamp.strftime('%d/%m/%Y %H:%M:%S')}\n"
        texto += "--------------------------------------\n"
        
        for item in pedido_dict.get('itens', []):
            nome = item.get('nome', 'Item sem nome')
            qtd = item.get('quantidade', 1)
            preco_total_item = item.get('preco_unitario', 0) * qtd
            linha_item = f"{qtd}x {nome}"
            preco_str = f"R${preco_total_item:.2f}"
            texto += f"{linha_item.ljust(30)} {preco_str.rjust(10)}\n"
            if item.get('obs'):
                texto += f"  > Obs: {item.get('obs')}\n"
                
        texto += "--------------------------------------\n"
        texto += f"TOTAL:".ljust(30) + f"R$ {pedido_dict.get('total', 0):.2f}".rjust(10) + "\n\n"
        texto += "       Obrigado pela preferencia!     \n\n\n"
        return texto
    except Exception as e:
        st.warning(f"Não foi possível formatar o cupom de pagamento. Erro: {e}")
        return None

def enviar_para_impressora(texto_para_imprimir, nome_documento="Comanda"):
    """Envia um texto para a impressora padrão do Windows."""
    if not WINDOWS_PRINTING_ENABLED:
        st.warning("Impressão física não está disponível. (Biblioteca 'pywin32' não encontrada).")
        return False
        
    if not texto_para_imprimir:
        st.error("Texto para impressão está vazio. Impressão cancelada.")
        return False

    try:
        nome_impressora = win32print.GetDefaultPrinter()
        hPrinter = win32print.OpenPrinter(nome_impressora)
        try:
            hJob = win32print.StartDocPrinter(hPrinter, 1, (nome_documento, None, "RAW"))
            try:
                win32print.StartPagePrinter(hPrinter)
                win32print.WritePrinter(hPrinter, texto_para_imprimir.encode('cp850', errors='replace'))
                win32print.EndPagePrinter(hPrinter)
            finally:
                win32print.EndDocPrinter(hPrinter)
        finally:
            win32print.ClosePrinter(hPrinter)
        st.info(f"✅ '{nome_documento}' enviado para a impressora: {nome_impressora}")
        return True
    except Exception as e:
        st.error(f"🔴 Falha ao enviar para a impressora física: {e}")
        return False

# --- IMAGEM DE FUNDO E CONEXÃO COM BANCO (sem alterações) ---
page_bg_img = """
<style>
/* --- ESTILO PADRÃO (Para telas largas como PC e tablet deitado) --- */
[data-testid="stAppViewContainer"] {
    background-image: url("https://github.com/TainanFs/cardapio-asa-de-aguiaa/blob/main/background.jpg?raw=true");
    background-size: cover;
    background-position: center center;
    background-repeat: no-repeat;
}

/* --- CÓDIGO INTELIGENTE (Apenas para telas com largura máxima de 768px) --- */
@media (max-width: 768px) {
    [data-testid="stAppViewContainer"] {
        background-image: url("https://github.com/TainanFs/cardapio-asa-de-aguiaa/blob/main/background.jpg?raw=true") !important;
        background-size: 120% auto !important; 
        background-position: center 40px !important; 
    }
}

/* --- Estilos que valem para ambas as telas --- */
[data-testid="stHeader"] {
    background-color: rgba(0, 0, 0, 0);
}

/* --- NOVO CÓDIGO PARA CENTRALIZAR O CONTEÚDO --- */
[data-testid="stAppViewContainer"] > .main {
    display: flex; /* Ativa o modo Flexbox */
    flex-direction: column; /* Organiza os itens em coluna (um abaixo do outro) */
    justify-content: center; /* Centraliza o conteúdo verticalmente */
}
</style>
"""
st.markdown(page_bg_img, unsafe_allow_html=True)

try:
    if hasattr(st, 'secrets') and "firestore_credentials" in st.secrets:
        db = firestore.Client.from_service_account_info(st.secrets["firestore_credentials"])
    else:
        chave_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "firestore-chave.json")
        db = firestore.Client.from_service_account_json(chave_path)
except Exception as e:
    st.error(f"🔴 Falha na conexão com o banco de dados: {e}")
    st.stop()

# --- ESTADO DA SESSÃO (sem alterações) ---
default_values = {'logged_in': False, 'role': None, 'username': None, 'cart': [], 'table_number': 1, 'client_name': "", 'editing_product_id': None, 'editing_option_id': None, 'editing_user_id': None}
for key, value in default_values.items():
    if key not in st.session_state: st.session_state[key] = value

# --- FUNÇÃO DE LOGIN (sem alterações) ---
def check_login(username, password):
    query = db.collection("usuarios").where(filter=FieldFilter("nome_usuario", "==", username)).limit(1).stream()
    user_list = [user.to_dict() for user in query]
    if user_list and user_list[0].get("senha") == password: return True, user_list[0].get("cargo")
    return False, None


### ALTERAÇÃO PRINCIPAL: LÓGICA DE IMPRESSÃO MOVIDA PARA CÁ ###
def render_order_placement_screen(db, products, options):
    st.write("\n")
    st.write("\n")
    st.write("\n")
    st.write("\n")
    st.write("\n")
    st.write("\n")
    st.write("\n")
    st.write("\n")
    st.write("\n")
    st.write("\n")
    st.title(f"🤵- {st.session_state.get('username')}")
    # ... (toda a lógica de seleção de itens permanece a mesma) ...
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

    # ... (código das abas de produtos omitido para brevidade, ele não muda) ...
    with tab_sanduiches:
        st.subheader("Montar Sanduíche")
        sanduiches_base = [p for p in products if p.get('categoria') == 'Sanduíches']
        if not sanduiches_base:
            st.info("Nenhum 'Sanduíche' disponível no momento.")
        else:
            base_nome = st.selectbox("Escolha o sanduíche:", [s['nome'] for s in sanduiches_base], key="sb_base_launcher")
            base_selecionada = next((s for s in sanduiches_base if s['nome'] == base_nome), None)
            if base_selecionada:
                nome_final_sb = base_selecionada['nome']
                preco_final_sb = base_selecionada.get('preco_base', 0)
                if base_selecionada.get('permite_carne'):
                    carnes_disponiveis = [o for o in options if o.get('tipo') == 'Carne']
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
        cremes_base = [p for p in products if p.get('categoria') == 'Cremes']
        if not cremes_base:
            st.info("Nenhum 'Creme' disponível no momento.")
        else:
            creme_nome = st.selectbox("Escolha o creme:", [c['nome'] for c in cremes_base], key="cr_base_launcher")
            creme_selecionado = next((c for c in cremes_base if c['nome'] == creme_nome), None)
            if creme_selecionado:
                nome_final_cr = creme_nome
                preco_final_cr = creme_selecionado.get('preco_base', 0)
                if creme_selecionado.get('permite_adicional'):
                    adicionais_disponiveis = [o for o in options if o.get('tipo') == 'Polpa']
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
        bebidas = [p for p in products if p.get('categoria') == 'Bebidas']
        if not bebidas:
            st.info("Nenhuma 'Bebida' disponível no momento.")
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
        # ... (lógica de exibição do carrinho permanece a mesma) ...
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
                # Salva os itens do carrinho em uma variável temporária antes de limpar
                itens_para_imprimir = list(st.session_state.cart)

                query = db.collection("pedidos").where(filter=FieldFilter("identificador", "==", identificador_comanda)).where(filter=FieldFilter("status", "==", "novo")).limit(1)
                comandas_abertas = list(query.stream())
                
                if comandas_abertas:
                    comanda_existente_doc = comandas_abertas[0]
                    dados_comanda_antiga = comanda_existente_doc.to_dict()
                    novos_itens = dados_comanda_antiga.get('itens', []) + st.session_state.cart
                    novo_total = dados_comanda_antiga.get('total', 0) + total_a_adicionar
                    comanda_existente_doc.reference.update({"itens": novos_itens, "total": novo_total, "timestamp": firestore.SERVER_TIMESTAMP})
                    st.success(f"Itens adicionados à comanda da(o) {identificador_comanda}!")
                else:
                    pedido_final = {"identificador": identificador_comanda, "tipo_identificador": tipo_comanda, "garcom": st.session_state.username, "itens": st.session_state.cart, "total": total_a_adicionar, "status": "novo", "timestamp": firestore.SERVER_TIMESTAMP}
                    db.collection("pedidos").add(pedido_final)
                    st.success(f"Nova comanda aberta para {identificador_comanda}!")
                
                ### INÍCIO DA LÓGICA DE IMPRESSÃO AUTOMÁTICA ###
                comanda_cozinha_texto = formatar_comanda_cozinha(
                    identificador=identificador_comanda, 
                    garcom=st.session_state.username, 
                    itens_novos=itens_para_imprimir
                )
                enviar_para_impressora(comanda_cozinha_texto, nome_documento="Comanda para Cozinha")
                ### FIM DA LÓGICA DE IMPRESSÃO AUTOMÁTICA ###

                st.session_state.cart = []
                st.balloons()
                st.rerun()
    else:
        st.info("O carrinho está vazio. Adicione itens para enviar à comanda.")

# --- LÓGICA PRINCIPAL DA APLICAÇÃO (sem alterações) ---
if not st.session_state.get('logged_in', False):
    # ... (código de login sem alterações) ...
   st.title("\n")
   st.write("\n")
   st.write("\n")
   st.write("\n")
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
        all_products_docs = db.collection("produtos").stream()
        all_products = [p.to_dict() | {'id': p.id} for p in all_products_docs]
        all_opcoes_docs = db.collection("opcoes").stream()
        all_opcoes = [o.to_dict() | {'id': o.id} for o in all_opcoes_docs]
    except Exception as e:
        st.error(f"Erro ao carregar dados do cardápio: {e}")
        st.stop()
    
    # PAINEL DO ADMIN (sem alterações)
    if st.session_state.get('role') == 'admin':
        st.write("\n")
        st.write("\n")
        st.write("\n")
        st.write("\n")
        st.write("\n")
        st.write("\n")
        st.write("\n")
        st.write("\n")
        st.write("\n")
        st.write("\n")
        st.write("\n")
        st.title("⚙️ Painel do Administrador")
        try:
            all_users_docs = db.collection("usuarios").stream()
            all_users = [u.to_dict() | {'id': u.id} for u in all_users_docs]
        except Exception as e:
            st.error(f"Erro ao carregar usuários: {e}")
            all_users = []

        tab_produtos, tab_opcoes, tab_usuarios = st.tabs(["Produtos", "Opções", "Usuários"])

        with tab_produtos:
            if st.session_state.get('editing_product_id'):
                product_ref = db.collection("produtos").document(st.session_state.editing_product_id)
                product_data = product_ref.get().to_dict()
                st.header(f"✏️ Editando: {product_data.get('nome')}")
                with st.form(key="edit_product_form"):
                    novo_nome = st.text_input("Nome do Produto", value=product_data.get("nome"))
                    novo_preco = st.number_input("Preço Base (R$)", value=product_data.get("preco_base"), format="%.2f")
                    categorias = ["Sanduíches", "Bebidas", "Cremes"]
                    try:
                        indice_cat = categorias.index(product_data.get("categoria"))
                    except (ValueError, TypeError):
                        indice_cat = 0
                    nova_categoria = st.selectbox("Categoria", categorias, index=indice_cat)
                    novo_permite_carne = st.checkbox("Permite escolher carnes?", value=product_data.get("permite_carne"))
                    novo_permite_adicional = st.checkbox("Permite adicionais (polpa)?", value=product_data.get("permite_adicional"))
                    
                    save_btn, cancel_btn = st.columns(2)
                    if save_btn.form_submit_button("Salvar Alterações", type="primary"):
                        update_data = {"nome": novo_nome, "preco_base": novo_preco, "categoria": nova_categoria, "permite_carne": novo_permite_carne, "permite_adicional": novo_permite_adicional}
                        product_ref.update(update_data)
                        st.session_state.editing_product_id = None
                        st.success("Produto atualizado!")
                        st.rerun()
                    if cancel_btn.form_submit_button("Cancelar"):
                        st.session_state.editing_product_id = None
                        st.rerun()
            else:
                st.header("Gerenciamento de Produtos")
                with st.expander("➕ Adicionar Novo Produto"):
                    with st.form(key="add_product_form", clear_on_submit=True):
                        st.subheader("Novo Produto")
                        nome_prod = st.text_input("Nome do Produto")
                        preco_prod = st.number_input("Preço Base (R$)", format="%.2f", min_value=0.0)
                        cat_prod = st.selectbox("Categoria", ["Sanduíches", "Bebidas", "Cremes"])
                        perm_carne = st.checkbox("Permite carnes?")
                        perm_adic = st.checkbox("Permite adicionais?")
                        if st.form_submit_button("Adicionar"):
                            if nome_prod and cat_prod:
                                db.collection("produtos").add({"nome": nome_prod, "preco_base": preco_prod, "categoria": cat_prod, "permite_carne": perm_carne, "permite_adicional": perm_adic, "disponivel": True})
                                st.success("Produto adicionado!")
                                st.rerun()
                st.header("Lista de Produtos")
                for prod_data in all_products:
                    p_id = prod_data.get('id')
                    cols = st.columns([3, 1, 1, 1])
                    cols[0].subheader(prod_data.get('nome'))
                    cols[0].caption(f"Categoria: {prod_data.get('categoria')} | Preço: R$ {prod_data.get('preco_base', 0):.2f}")
                    if cols[1].button("Editar", key=f"edit_{p_id}"):
                        st.session_state.editing_product_id = p_id
                        st.rerun()
                    disponivel = prod_data.get("disponivel", True)
                    if disponivel:
                        if cols[2].button("Pausar", key=f"off_{p_id}"):
                            db.collection("produtos").document(p_id).update({"disponivel": False})
                            st.rerun()
                    else:
                        if cols[2].button("Ativar", key=f"on_{p_id}", type="primary"):
                            db.collection("produtos").document(p_id).update({"disponivel": True})
                            st.rerun()
                    if cols[3].button("Apagar", key=f"del_{p_id}"):
                        db.collection("produtos").document(p_id).delete()
                        st.rerun()

        with tab_opcoes:
            if st.session_state.get('editing_option_id'):
                option_ref = db.collection("opcoes").document(st.session_state.editing_option_id)
                option_data = option_ref.get().to_dict()
                st.header(f"✏️ Editando Opção: {option_data.get('nome_opcao')}")
                with st.form(key="edit_option_form"):
                    novo_nome_op = st.text_input("Nome da Opção", value=option_data.get("nome_opcao"))
                    novo_preco_op = st.number_input("Preço Adicional (R$)", value=option_data.get("preco_adicional"), format="%.2f")
                    tipos = ["Carne", "Polpa", "Outro Adicional"]
                    try:
                        indice_tipo = tipos.index(option_data.get("tipo"))
                    except (ValueError, TypeError):
                        indice_tipo = 0
                    novo_tipo = st.selectbox("Tipo de Opção", tipos, index=indice_tipo)
                    save_btn, cancel_btn = st.columns(2)
                    if save_btn.form_submit_button("Salvar Alterações", type="primary"):
                        option_ref.update({"nome_opcao": novo_nome_op, "preco_adicional": novo_preco_op, "tipo": novo_tipo})
                        st.session_state.editing_option_id = None
                        st.success("Opção atualizada!")
                        st.rerun()
                    if cancel_btn.form_submit_button("Cancelar"):
                        st.session_state.editing_option_id = None
                        st.rerun()
            else:
                st.header("Gerenciamento de Opções")
                with st.expander("➕ Adicionar Nova Opção"):
                    with st.form(key="add_option_form", clear_on_submit=True):
                        st.subheader("Nova Opção")
                        nome_op = st.text_input("Nome da Opção")
                        preco_op = st.number_input("Preço Adicional (R$)", format="%.2f", min_value=0.0)
                        tipo_op = st.selectbox("Tipo", ["Carne", "Polpa", "Outro Adicional"])
                        if st.form_submit_button("Adicionar"):
                            if nome_op and tipo_op:
                                db.collection("opcoes").add({"nome_opcao": nome_op, "preco_adicional": preco_op, "tipo": tipo_op})
                                st.success("Opção adicionada!")
                                st.rerun()
                st.header("Lista de Opções")
                for opt_data in all_opcoes:
                    o_id = opt_data.get('id')
                    cols = st.columns([3, 1, 1])
                    cols[0].subheader(opt_data.get('nome_opcao'))
                    cols[0].caption(f"Tipo: {opt_data.get('tipo')} | Preço Adic.: R$ {opt_data.get('preco_adicional', 0):.2f}")
                    if cols[1].button("Editar", key=f"edit_op_{o_id}"):
                        st.session_state.editing_option_id = o_id
                        st.rerun()
                    if cols[2].button("Apagar", key=f"del_op_{o_id}"):
                        db.collection("opcoes").document(o_id).delete()
                        st.rerun()

        with tab_usuarios:
            st.header("Gerenciamento de Usuários")
            if st.session_state.get('editing_user_id'):
                user_ref = db.collection("usuarios").document(st.session_state.editing_user_id)
                user_data = user_ref.get().to_dict()
                st.header(f"✏️ Editando Usuário: {user_data.get('nome_usuario')}")
                with st.form(key="edit_user_form"):
                    st.text_input("Nome de Usuário (não pode ser alterado)", value=user_data.get('nome_usuario'), disabled=True)
                    cargos = ["garcom", "caixa", "cozinha", "admin"]
                    try:
                        indice_cargo = cargos.index(user_data.get("cargo"))
                    except (ValueError, TypeError):
                        indice_cargo = 0
                    novo_cargo = st.selectbox("Cargo", cargos, index=indice_cargo)
                    nova_senha = st.text_input("Nova Senha (deixe em branco para não alterar)", type="password")
                    
                    save_btn, cancel_btn = st.columns(2)
                    if save_btn.form_submit_button("Salvar Alterações", type="primary"):
                        update_data = {"cargo": novo_cargo}
                        if nova_senha:
                            update_data["senha"] = nova_senha
                        user_ref.update(update_data)
                        st.session_state.editing_user_id = None
                        st.success("Usuário atualizado!")
                        st.rerun()
                    if cancel_btn.form_submit_button("Cancelar"):
                        st.session_state.editing_user_id = None
                        st.rerun()
            else:
                with st.expander("➕ Adicionar Novo Usuário"):
                    with st.form(key="add_user_form", clear_on_submit=True):
                        st.subheader("Novo Usuário")
                        novo_user_nome = st.text_input("Nome de Usuário")
                        novo_user_senha = st.text_input("Senha", type="password")
                        novo_user_cargo = st.selectbox("Cargo", ["garcom", "caixa", "cozinha", "admin"])
                        if st.form_submit_button("Criar Usuário"):
                            if novo_user_nome and novo_user_senha and novo_user_cargo:
                                db.collection("usuarios").add({"nome_usuario": novo_user_nome, "senha": novo_user_senha, "cargo": novo_user_cargo})
                                st.success(f"Usuário '{novo_user_nome}' criado!")
                                st.rerun()
                st.header("Lista de Usuários")
                for user_data in all_users:
                    u_id = user_data.get('id')
                    cols = st.columns([3, 1, 1])
                    cols[0].subheader(user_data.get('nome_usuario'))
                    cols[0].caption(f"Cargo: {user_data.get('cargo')}")
                    if cols[1].button("Editar", key=f"edit_user_{u_id}"):
                        st.session_state.editing_user_id = u_id
                        st.rerun()
                    if cols[2].button("Apagar", key=f"del_user_{u_id}"):
                        if user_data.get('nome_usuario') == st.session_state.username:
                            st.warning("Não é possível apagar o próprio usuário.")
                        else:
                            db.collection("usuarios").document(u_id).delete()
                            st.rerun()

    # PAINEL DO GARÇOM (chama a função de renderização que agora imprime)
    elif st.session_state.get('role') == 'garcom':
        products_disponiveis = [p for p in all_products if p.get("disponivel", True)]
        render_order_placement_screen(db, products_disponiveis, all_opcoes)

    # PAINEL DO CAIXA (imprime o cupom de pagamento final)
    elif st.session_state.get('role') == 'caixa':
        st.title("💰 Caixa \n")
        tab_ver_contas, tab_lancar_pedido = st.tabs(["Ver Contas Abertas", "Lançar Novo Pedido"])
        with tab_ver_contas:
            st.header("Contas Pendentes de Pagamento")
            if st.button("Atualizar Comandas 🔄"): st.rerun()
            pedidos_ref = db.collection("pedidos").where(filter=FieldFilter("status", "==", "novo")).order_by("timestamp", direction=firestore.Query.ASCENDING).stream()
            pedidos_a_pagar = [doc.to_dict() | {'id': doc.id} for doc in pedidos_ref]
            if not pedidos_a_pagar:
                st.success("Nenhuma conta pendente de pagamento. Tudo em dia! ✅")
            else:
                for pedido in pedidos_a_pagar:
                    identificador_label = f"**{pedido.get('identificador')}**"
                    with st.expander(f"{identificador_label} - Total: R$ {pedido.get('total', 0):.2f}"):
                        # ... (código de exibição dos itens sem alterações) ...
                        st.subheader("Itens Consumidos:")
                        for item in pedido.get('itens', []):
                            st.write(f" - {item.get('quantidade')}x **{item['nome']}**")
                            if item.get('obs'):
                                st.info(f"   > Obs: {item['obs']}")
                        st.write("---")
                        if st.button("Confirmar Pagamento e Imprimir Cupom", key=f"pay_{pedido['id']}", type="primary"):
                            db.collection("pedidos").document(pedido['id']).update({"status": "pago"})
                            cupom_texto = formatar_cupom_para_impressao(pedido)
                            enviar_para_impressora(cupom_texto, nome_documento="Cupom de Pagamento")
                            st.success(f"Pedido de {identificador_label} pago!")
                            st.balloons()
                            st.rerun()
        with tab_lancar_pedido:
            products_disponiveis = [p for p in all_products if p.get("disponivel", True)]
            render_order_placement_screen(db, products_disponiveis, all_opcoes)
    
    # PAINEL DA COZINHA 
    elif st.session_state.get('role') == 'cozinha':
        st.write("\n")
        st.write("\n")
        st.write("\n")
        st.write("\n")
        st.write("\n")
        st.write("\n")
        st.write("\n")
        st.write("\n")
        st.write("\n")
        st.write("\n")
        st.title("🔎 Histórico de Vendas")

        # --- 1. SELETOR DE DATA ---
        opcoes_data = ("Hoje", "Ontem", "Anteontem")
        data_selecionada_str = st.radio(
            "Selecione o dia para o relatório:",
            opcoes_data,
            horizontal=True,
            key="date_selector_cozinha"
        )

        st.write("---")

        # --- 2. LÓGICA PARA CALCULAR O INTERVALO DE DATA ---
        hoje = datetime.now().date()
        if data_selecionada_str == "Hoje":
            data_alvo = hoje
        elif data_selecionada_str == "Ontem":
            data_alvo = hoje - timedelta(days=1)
        else:  # Anteontem
            data_alvo = hoje - timedelta(days=2)
            
        # Definimos o início do dia selecionado e o início do dia seguinte
        start_of_day_dt = datetime.combine(data_alvo, time.min)
        start_of_next_day_dt = datetime.combine(data_alvo + timedelta(days=1), time.min)

        try:
            # --- 3. CONSULTA AO BANCO DE DADOS ATUALIZADA ---
            pedidos_ref = db.collection("pedidos") \
                .where(filter=FieldFilter("status", "==", "pago")) \
                .where(filter=FieldFilter("timestamp", ">=", start_of_day_dt)) \
                .where(filter=FieldFilter("timestamp", "<", start_of_next_day_dt)) \
                .order_by("timestamp", direction=firestore.Query.DESCENDING) \
                .stream()

            pedidos_pagos_do_dia = list(pedidos_ref)
            
            # Título dinâmico que mostra a data selecionada
            st.header(f"Relatório de {data_selecionada_str} ({data_alvo.strftime('%d/%m/%Y')})")

            if not pedidos_pagos_do_dia:
                st.success(f"Nenhum pedido pago registrado no dia {data_alvo.strftime('%d/%m/%Y')}.")
            else:
                total_faturado = sum(p.to_dict().get('total', 0) for p in pedidos_pagos_do_dia)
                num_pedidos = len(pedidos_pagos_do_dia)
                
                col1, col2 = st.columns(2)
                col1.metric(label="Faturamento Total do Dia", value=f"R$ {total_faturado:.2f}")
                col2.metric(label="Total de Pedidos Pagos", value=num_pedidos)
                
                st.write("---")
                st.subheader("Lista de Pedidos Pagos")
                for pedido_doc in pedidos_pagos_do_dia:
                    pedido = pedido_doc.to_dict()
                    identificador_label = f"**{pedido.get('identificador')}**"
                    # Verifica se o timestamp não é nulo antes de formatar
                    horario = pedido.get('timestamp').strftime('%H:%M:%S') if pedido.get('timestamp') else 'N/A'
                    
                    with st.expander(f"{identificador_label} às {horario} - Total: R$ {pedido.get('total', 0):.2f}"):
                        for item in pedido.get('itens', []):
                            st.write(f" - {item.get('quantidade')}x **{item['nome']}**")
                            if item.get('obs'):
                                st.info(f"   > Obs: {item['obs']}")

        except Exception as e:
            st.error(f"Ocorreu um erro ao gerar o relatório: {e}")
            st.warning("Se o erro mencionar um 'índice', por favor, clique no link na mensagem de erro para criá-lo no Firebase e tente novamente. Isso pode ser necessário devido à nova consulta de data.")
