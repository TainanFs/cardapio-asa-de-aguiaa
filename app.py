import streamlit as st
import base64
import os
from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA (Deve ser o primeiro comando Streamlit) ---
st.set_page_config(
    page_title="Cardápio Asa de Águia",
    page_icon="🔥",
    layout="centered",
    initial_sidebar_state="auto"
)


# --- LÓGICA DE CONEXÃO "INTELIGENTE" E MAIS ROBUSTA COM O BANCO DE DADOS ---
try:
    # Verificação mais direta: se o objeto 'secrets' existe e contém nossas credenciais
    if hasattr(st, 'secrets') and "firestore_credentials" in st.secrets:
        # Mensagem de diagnóstico para sabermos que este bloco foi executado
        st.success("✅ Tentando conectar usando as credenciais do Streamlit Secrets...") 
        creds_dict = st.secrets["firestore_credentials"]
        db = firestore.Client.from_service_account_info(creds_dict)
    
    # Se a verificação acima falhar, ele tentará o método local
    else:
        # Mensagem de diagnóstico para sabermos que este bloco foi executado
        st.info("ℹ️ Secrets não encontrados. Tentando conectar usando o arquivo local 'firestore-chave.json'...")
        script_dir = os.path.dirname(os.path.abspath(__file__))
        chave_path = os.path.join(script_dir, "firestore-chave.json")
        db = firestore.Client.from_service_account_json(chave_path)

except Exception as e:
    st.error("🔴 Falha na conexão com o banco de dados.")
    st.error(f"Ocorreu um erro: {e}")
    st.info("Verifique se o arquivo 'firestore-chave.json' está na pasta correta (para execução local) ou se os 'Secrets' foram configurados corretamente no Streamlit Cloud.")
    st.stop()


# --- INICIALIZAÇÃO DO ESTADO DA SESSÃO ---
if 'logged_in' not in st.session_state:
    st.session_state.update({
        'logged_in': False,
        'role': None,
        'username': None,
        'cart': [],
        'table_number': 1,
        'client_name': ""
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
    """Renderiza a tela completa de lançamento de pedidos."""
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
                nome_final_sb = base_nome
                preco_final_sb = base_selecionada.get('preco_base', 0)

                # Lógica para seleção de carnes
                if base_selecionada.get('permite_carne'):
                    carnes_disponiveis = [o for o in all_opcoes if o.get('tipo') == 'Carne']
                    if carnes_disponiveis:
                        nomes_carnes_selecionadas = st.multiselect("Escolha as carnes:", [c['nome_opcao'] for c in carnes_disponiveis], key="sb_carnes_launcher")
                        if nomes_carnes_selecionadas:
                            carnes_selecionadas_info = [c for c in carnes_disponiveis if c['nome_opcao'] in nomes_carnes_selecionadas]
                            for carne_info in carnes_selecionadas_info:
                                preco_final_sb += carne_info.get('preco_adicional', 0)
                            nomes_formatados = " e ".join(nomes_carnes_selecionadas)
                            nome_final_sb += f" com {nomes_formatados}"
                    else:
                        st.warning("Nenhuma opção de 'Carne' cadastrada pelo admin.")

                quantidade_sb = st.number_input("Quantidade:", min_value=1, value=1, step=1, key="sb_qty_launcher")
                obs_sb = st.text_input("Observações:", key="sb_obs_launcher")

                if st.button("Adicionar Sanduíche ao Pedido", key="sb_add_launcher"):
                    st.session_state.cart.append({"nome": nome_final_sb, "preco_unitario": preco_final_sb, "quantidade": quantidade_sb, "obs": obs_sb})
                    st.success(f"Adicionado: {quantidade_sb}x {nome_final_sb}!")
                    st.rerun()

    with tab_cremes:
        st.subheader("Montar Creme")
        cremes_base = [p for p in all_products if p.get('categoria') == 'Cremes']
        if cremes_base:
            # Lógica completa para cremes aqui...
            st.info("Lógica de Cremes a ser implementada.")
        else:
            st.info("Nenhum 'Creme' cadastrado.")

    with tab_bebidas:
        st.subheader("Escolher Bebida")
        bebidas = [p for p in all_products if p.get('categoria') == 'Bebidas']
        if bebidas:
            # Lógica completa para bebidas aqui...
            st.info("Lógica de Bebidas a ser implementada.")
        else:
            st.info("Nenhuma 'Bebida' cadastrada.")

    st.write("---")
    st.header(f"Revisão da Comanda para: {identificador_comanda}")

    if st.session_state.cart:
        total_comanda = sum(item.get('preco_unitario', 0) * item.get('quantidade', 1) for item in st.session_state.cart)
        for i, item in enumerate(st.session_state.cart):
            preco_total_item = item.get('preco_unitario', 0) * item.get('quantidade', 1)
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"- **{item.get('quantidade')}x {item['nome']}** (R$ {preco_total_item:.2f})")
                if item.get('obs'):
                    st.markdown(f"  > *Obs: {item['obs']}*")
            with col2:
                if st.button("🗑️", key=f"del_cart_{i}_launcher", help="Remover item"):
                    st.session_state.cart.pop(i)
                    st.rerun()

        st.subheader(f"Total da Comanda: R$ {total_comanda:.2f}")

        # O BOTÃO DE ENVIAR O PEDIDO
        if st.button("✅ Enviar Pedido para Cozinha", type="primary", key="send_order_launcher"):
            if tipo_comanda == "Cliente" and not identificador_comanda.strip():
                st.warning("Por favor, insira o nome do cliente.")
            else:
                pedido_final = {
                    "identificador": identificador_comanda,
                    "tipo_identificador": tipo_comanda,
                    "garcom": st.session_state.username,
                    "itens": st.session_state.cart,
                    "total": total_comanda,
                    "status": "novo",
                    "timestamp": firestore.SERVER_TIMESTAMP
                }
                db.collection("pedidos").add(pedido_final)
                st.success("Pedido enviado para a Cozinha!")
                st.session_state.cart = [] # Limpa o carrinho
                st.balloons()
                st.rerun()
    else:
        st.info("A comanda está vazia. Adicione itens para continuar.")

# --- LÓGICA PRINCIPAL DA APLICAÇÃO ---

# TELA DE LOGIN
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

# TELAS PÓS-LOGIN
else:
    # Sidebar comum a todos os usuários logados
    st.sidebar.write(f"Logado como: **{st.session_state.get('username')}**")
    st.sidebar.write(f"Cargo: **{st.session_state.get('role')}**")
    def logout():
        # Limpa todo o session_state para garantir um logout limpo
        st.session_state.clear()
        st.rerun()
    st.sidebar.button("Sair", on_click=logout)
    
    # Carrega dados que todos os painéis (exceto admin, talvez) usarão
    try:
        all_products_query = db.collection("produtos").where(filter=FieldFilter("disponivel", "==", True)).stream()
        all_products = [p.to_dict() | {'id': p.id} for p in all_products_query]
        
        all_opcoes_query = db.collection("opcoes").stream()
        all_opcoes = [o.to_dict() | {'id': o.id} for o in all_opcoes_query]
    except Exception as e:
        st.error(f"Erro ao carregar dados do cardápio: {e}")
        st.stop()

    # PAINEL DO ADMIN
    if st.session_state.get('role') == 'admin':
        st.title("⚙️ Painel do Administrador")
        # Implementar a lógica do painel de admin aqui
        st.write("Bem-vindo, admin! Funcionalidades de gerenciamento de produtos e usuários a serem implementadas.")

    # PAINEL DO GARÇOM
    elif st.session_state.get('role') == 'garcom':
        render_order_placement_screen(db, all_products, all_opcoes)

    # PAINEL DO CAIXA
    elif st.session_state.get('role') == 'caixa':
        st.title("💰 Painel do Caixa")
        tab_ver_contas, tab_lancar_pedido = st.tabs(["Ver Contas Abertas", "Lançar Novo Pedido"])

        with tab_ver_contas:
            st.header("Contas Pendentes de Pagamento")
            try:
                # Busca pedidos com status 'novo' para o caixa
                pedidos_ref = db.collection("pedidos").where(filter=FieldFilter("status", "==", "novo")).order_by("timestamp", direction=firestore.Query.ASCENDING).stream()
                pedidos_a_pagar = [doc.to_dict() | {'id': doc.id} for doc in pedidos_ref]

                if not pedidos_a_pagar:
                    st.success("Nenhuma conta pendente de pagamento. Tudo em dia! ✅")
                else:
                    for pedido in pedidos_a_pagar:
                        identificador_label = f"**{pedido.get('identificador')}**"
                        with st.expander(f"{identificador_label} - Total: R$ {pedido.get('total', 0):.2f}"):
                            # Detalhes do pedido...
                            if st.button("Marcar como Pago", key=f"pay_{pedido['id']}", type="primary"):
                                db.collection("pedidos").document(pedido['id']).update({"status": "pago"})
                                st.success(f"Pedido de {identificador_label} marcado como pago!")
                                st.rerun()
            except Exception as e:
                st.error(f"Ocorreu um erro ao buscar contas: {e}")

        with tab_lancar_pedido:
            render_order_placement_screen(db, all_products, all_opcoes)

    # PAINEL DA COZINHA
    elif st.session_state.get('role') == 'cozinha':
        st.title("🍳 Cozinha - Fila de Preparo")
        st.info("Aqui aparecerão os pedidos que foram pagos e estão prontos para o preparo.")
        try:
            pedidos_pagos_ref = db.collection("pedidos").where(filter=FieldFilter("status", "==", "pago")).order_by("timestamp", direction=firestore.Query.ASCENDING).stream()
            pedidos_para_preparar = [doc.to_dict() | {'id': doc.id} for doc in pedidos_pagos_ref]
            if not pedidos_para_preparar:
                st.success("Nenhum pedido na fila. Bom trabalho! 👍")
            else:
                for pedido in pedidos_para_preparar:
                    with st.container(border=True):
                        st.subheader(f"Pedido para: {pedido.get('identificador')}")
                        for item in pedido.get('itens', []):
                            st.write(f" - {item.get('quantidade')}x **{item['nome']}**")
                            if item.get('obs'):
                                st.warning(f"   > Obs: {item['obs']}")
                        
                        if st.button("Marcar como Pronto", key=f"done_{pedido['id']}", type="primary"):
                            db.collection("pedidos").document(pedido['id']).update({"status": "pronto"})
                            st.toast(f"Pedido de {pedido.get('identificador')} finalizado!")
                            st.rerun()

        except Exception as e:
            st.error(f"Ocorreu um erro ao buscar os pedidos: {e}")

    # Fallback para cargos não reconhecidos
    else:
        st.error("Seu cargo não foi reconhecido ou não possui um painel definido.")
