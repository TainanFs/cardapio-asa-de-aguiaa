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
    """Verifica as credenciais do usuário no Firestore."""
    users_ref = db.collection("usuarios")
    query = users_ref.where(filter=FieldFilter("nome_usuario", "==", username)).limit(1).stream()
    user_list = [user.to_dict() for user in query]
    if user_list and user_list[0].get("senha") == password:
        return True, user_list[0].get("cargo")
    return False, None

def render_order_placement_screen(db, all_products, all_opcoes):
    """Renderiza a tela de lançamento de pedidos com a lógica de 'Comandas Abertas'."""
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
        # Lógica completa para Sanduíches... (O código aqui não muda)
        st.subheader("Montar Sanduíche")
        # ... (código omitido para brevidade, mas deve ser o mesmo da versão anterior)

    with tab_cremes:
        # Lógica completa para Cremes... (O código aqui não muda)
        st.subheader("Montar Creme")
        # ... (código omitido para brevidade, mas deve ser o mesmo da versão anterior)

    with tab_bebidas:
        # Lógica completa para Bebidas... (O código aqui não muda)
        st.subheader("Escolher Bebida")
        # ... (código omitido para brevidade, mas deve ser o mesmo da versão anterior)

    st.write("---")
    st.header(f"Itens a Adicionar na Comanda de: {identificador_comanda}")
    if st.session_state.cart:
        total_a_adicionar = sum(item.get('preco_unitario', 0) * item.get('quantidade', 1) for item in st.session_state.cart)
        # Lógica de exibição do carrinho... (O código aqui não muda)
        
        # --- LÓGICA DE ATUALIZAÇÃO MANUAL (SEM FIELDVALUE) ---
        if st.button("✅ Adicionar à Comanda / Abrir Nova", type="primary", key="send_order_launcher"):
            if not identificador_comanda.strip():
                st.warning("Por favor, preencha o número da Mesa ou o nome do Cliente.")
            else:
                query = db.collection("pedidos").where(filter=FieldFilter("identificador", "==", identificador_comanda)).where(filter=FieldFilter("status", "==", "novo")).limit(1)
                comandas_abertas = list(query.stream())
                if comandas_abertas:
                    comanda_existente_doc = comandas_abertas[0]
                    dados_comanda_antiga = comanda_existente_doc.to_dict()
                    
                    # Passo 2: Modificar os dados em Python
                    novos_itens = dados_comanda_antiga.get('itens', []) + st.session_state.cart
                    novo_total = dados_comanda_antiga.get('total', 0) + total_a_adicionar
                    
                    # Passo 3: Escrever os dados modificados de volta
                    comanda_existente_doc.reference.update({
                        "itens": novos_itens,
                        "total": novo_total
                    })
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

    if st.session_state.get('role') == 'admin':
        st.title("⚙️ Painel do Administrador")
        st.write("Bem-vindo, admin! Funcionalidades de gerenciamento de produtos e usuários a serem implementadas.")

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
