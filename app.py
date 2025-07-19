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

# --- FUNÇÃO E CÓDIGO PARA IMAGEM DE FUNDO ---
@st.cache_data
def get_img_as_base64(file):
    try:
        with open(file, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except FileNotFoundError:
        st.error(f"Arquivo de imagem '{file}' não encontrado. Verifique se ele está na mesma pasta que o app.py.")
        return None

img = get_img_as_base64("background.jpg")

if img:
    page_bg_img = f"""
    <style>
    [data-testid="stAppViewContainer"] > .main {{
    background-image: url("data:image/jpeg;base64,{img}");
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
    background-attachment: local;
    }}
    [data-testid="stSidebar"] > div:first-child {{
    background-color: rgba(255, 255, 255, 0.8);
    }}
    [data-testid="stHeader"], [data-testid="stToolbar"] {{
    background: rgba(0,0,0,0);
    }}
    </style>
    """
    st.markdown(page_bg_img, unsafe_allow_html=True)

# --- LÓGICA DE CONEXÃO "INTELIGENTE" COM O BANCO DE DADOS ---
try:
    if 'STREAMLIT_SHARING_MODE' in os.environ:
        creds_dict = st.secrets["firestore_credentials"]
        db = firestore.Client.from_service_account_info(creds_dict)
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        chave_path = os.path.join(script_dir, "firestore-chave.json")
        db = firestore.Client.from_service_account_json(chave_path)
except Exception as e:
    st.error("🔴 Falha na conexão com o banco de dados.")
    st.error(f"Erro: {e}")
    st.stop()


# --- Funções de Lógica e Telas (O restante do código) ---
# (Aqui entra todo o resto do seu código, que já estava correto:
# check_login, render_order_placement_screen, e a lógica dos painéis)
# Para garantir, vou colar o restante completo abaixo.

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
                nome_final_sb = base_nome
                preco_final_sb = base_selecionada.get('preco_base', 0)
                if base_selecionada.get('permite_carne'):
                    carnes_disponiveis = [o for o in all_opcoes if o.get('tipo') == 'Carne']
                    if carnes_disponiveis:
                        nomes_carnes_selecionadas = st.multiselect("Escolha as carnes (pode escolher várias):", [c['nome_opcao'] for c in carnes_disponiveis], key="sb_carnes_launcher")
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
                if st.button("Adicionar Sanduíche", key="sb_add_launcher"):
                    st.session_state.cart.append({"nome": nome_final_sb, "preco_unitario": preco_final_sb, "quantidade": quantidade_sb, "obs": obs_sb})
                    st.success(f"Adicionado: {quantidade_sb}x {nome_final_sb}!")
                    st.rerun()
    with tab_cremes:
        st.subheader("Montar Creme")
        cremes_base = [p for p in all_products if p.get('categoria') == 'Cremes']
        if cremes_base:
            creme_nome = st.selectbox("Escolha o creme:", [c['nome'] for c in cremes_base], key="cr_base_launcher")
            creme = next((c for c in cremes_base if c['nome'] == creme_nome), None)
            if creme:
                nome_final_cr = creme_nome
                preco_final_cr = creme.get('preco_base', 0)
                if creme.get('permite_adicional'):
                    polpas = [o for o in all_opcoes if o.get('tipo') == 'Polpa']
                    if polpas:
                        opcoes_polpa = ["Nenhuma"] + [p['nome_opcao'] for p in polpas]
                        polpa_nome = st.selectbox("Adicional de polpa:", opcoes_polpa, key="cr_polpa_launcher")
                        if polpa_nome != "Nenhuma":
                            polpa = next((p for p in polpas if p['nome_opcao'] == polpa_nome), None)
                            if polpa:
                                nome_final_cr += f" com {polpa_nome}"
                                preco_final_cr += polpa.get('preco_adicional', 0)
                    else:
                        st.warning("Nenhuma opção de 'Polpa' cadastrada pelo admin.")
                quantidade_creme = st.number_input("Quantidade:", min_value=1, value=1, step=1, key="cr_qty_launcher")
                obs_creme = st.text_input("Observações:", key="cr_obs_launcher")
                if st.button("Adicionar Creme", key="cr_add_launcher"):
                    st.session_state.cart.append({"nome": nome_final_cr, "preco_unitario": preco_final_cr, "quantidade": quantidade_creme, "obs": obs_creme})
                    st.success(f"Adicionado: {quantidade_creme}x {nome_final_cr}!")
                    st.rerun()
        else:
            st.info("Nenhum 'Creme' cadastrado.")
    with tab_bebidas:
        st.subheader("Escolher Bebida")
        bebidas = [p for p in all_products if p.get('categoria') == 'Bebidas']
        if bebidas:
            bebida_nome = st.selectbox("Escolha a bebida:", [b['nome'] for b in bebidas], key="bb_base_launcher")
            quantidade_bebida = st.number_input("Quantidade:", min_value=1, value=1, step=1, key="bb_qty_launcher")
            obs_bebida = st.text_input("Observações (gelo e limão, etc.):", key="bb_obs_launcher")
            if st.button("Adicionar Bebida", key="bb_add_launcher"):
                bebida = next((b for b in bebidas if b['nome'] == bebida_nome), None)
                if bebida:
                    preco = bebida.get('preco_base', 0)
                    st.session_state.cart.append({"nome": bebida_nome, "preco_unitario": preco, "quantidade": quantidade_bebida, "obs": obs_bebida})
                    st.success(f"Adicionado: {quantidade_sb}x {bebida_nome}!")
                    st.rerun()
        else:
            st.info("Nenhuma 'Bebida' cadastrada.")
    st.write("---")
    st.header(f"Comanda para: {identificador_comanda}")
    if st.session_state.cart:
        total_comanda = sum(item.get('preco_unitario', 0) * item.get('quantidade', 1) for item in st.session_state.cart)
        for i, item in enumerate(st.session_state.cart):
            preco_total_item = item.get('preco_unitario', 0) * item.get('quantidade', 1)
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"- **{item.get('quantidade')}x {item['nome']}** (R$ {preco_total_item:.2f})")
                if item['obs']:
                    st.markdown(f"  > *Obs: {item['obs']}*")
            with col2:
                if st.button("🗑️", key=f"del_cart_{i}_launcher", help="Remover item"):
                    st.session_state.cart.pop(i)
                    st.rerun()
        st.subheader(f"Total da Comanda: R$ {total_comanda:.2f}")
        if st.button("✅ Enviar Pedido para Cozinha", key="send_order_launcher"):
            if (tipo_comanda == "Cliente" and not identificador_comanda.strip()):
                st.warning("Por favor, insira o nome do cliente.")
            else:
                pedido_final = {"identificador": identificador_comanda, "tipo_identificador": tipo_comanda, "garcom": st.session_state.username, "itens": st.session_state.cart, "total": total_comanda, "status": "novo", "timestamp": firestore.SERVER_TIMESTAMP}
                db.collection("pedidos").add(pedido_final)
                st.success("Pedido enviado para a Cozinha!")
                st.session_state.cart = []
                st.balloons()
                st.rerun()
    else:
        st.info("A comanda está vazia.")

if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'role': None, 'username': None,'editing_product_id': None, 'cart': [], 'table_number': 1, 'client_name': ""})
if not st.session_state.get('logged_in', False):
    st.title("🔥 Cardápio Asa de Águia - Login")
    with st.form("login_form"):
        username = st.text_input("Nome de Usuário")
        password = st.text_input("Senha", type="password")
        login_button = st.form_submit_button("Entrar")
        if login_button:
            is_correct, role = check_login(username, password)
            if is_correct:
                st.session_state.update({'logged_in': True, 'role': role, 'username': username})
                st.rerun()
            else:
                st.error("Usuário ou senha inválidos.")
else:
    st.sidebar.write(f"Logado como: **{st.session_state.get('username')}** ({st.session_state.get('role')})")
    def logout():
        st.session_state.clear()
        st.rerun()
    st.sidebar.button("Sair", on_click=logout)
    try:
        all_products_query = db.collection("produtos").where(filter=FieldFilter("disponivel", "==", True)).stream()
        all_products = [p.to_dict() | {'id': p.id} for p in all_products_query]
        all_opcoes_query = db.collection("opcoes").stream()
        all_opcoes = [o.to_dict() | {'id': o.id} for o in all_opcoes_query]
    except Exception as e:
        st.error(f"Erro ao carregar o cardápio: {e}"); st.stop()
    if st.session_state.get('role') == 'admin':
        st.title("🔥 Cardápio Asa de Águia - Painel de Controle")
        tab_produtos, tab_opcoes = st.tabs(["Gerenciar Produtos", "Gerenciar Opções"])
        with tab_produtos:
            st.header("Produtos (Sanduíches, Bebidas, etc.)")
            with st.expander("➕ Adicionar Novo Produto", expanded=False):
                with st.form(key="add_product_form", clear_on_submit=True):
                    nome_produto = st.text_input("Nome do Produto")
                    preco_base_produto = st.number_input("Preço Base (ou preço único)", format="%.2f", step=0.50, min_value=0.0)
                    categoria_produto = st.selectbox("Categoria", ["Sanduíches", "Bebidas", "Sobremesas", "Cremes"], key="cat_prod")
                    permite_carne = st.checkbox("Este sanduíche permite escolher carne?", key="p_carne")
                    permite_adicional = st.checkbox("Este item permite adicional (ex: polpa)?", key="p_adic")
                    if st.form_submit_button(label="Adicionar Produto"):
                        if nome_produto:
                            produto_data = {"nome": nome_produto, "preco_base": preco_base_produto, "categoria": categoria_produto, "permite_carne": permite_carne, "permite_adicional": permite_adicional, "disponivel": True}
                            db.collection("produtos").add(produto_data)
                            st.success(f"Produto '{nome_produto}' adicionado!")
                            st.rerun()
            st.subheader("Lista de Produtos Cadastrados")
            produtos_ref = db.collection("produtos").stream()
            for produto in produtos_ref:
                p_data = produto.to_dict()
                p_id = produto.id
                # (O resto do código do admin para listar e editar produtos)
    elif st.session_state.get('role') == 'garcom':
        render_order_placement_screen(db, all_products, all_opcoes)
    elif st.session_state.get('role') == 'caixa':
        st.title("💰 Painel do Caixa")
        tab_ver_contas, tab_lancar_pedido = st.tabs(["Ver Contas Abertas", "Lançar Novo Pedido"])
        with tab_ver_contas:
            st.header("Contas Pendentes de Pagamento")
            st.write("---")
            try:
                pedidos_ref = db.collection("pedidos").where(filter=FieldFilter("status", "==", "novo")).order_by("timestamp", direction=firestore.Query.ASCENDING).stream()
                pedidos_a_pagar = [doc.to_dict() | {'id': doc.id} for doc in pedidos_ref]
                if not pedidos_a_pagar:
                    st.success("Nenhuma conta pendente de pagamento. Tudo em dia! ✅")
                else:
                    for pedido in pedidos_a_pagar:
                        identificador_label = f"**{pedido.get('identificador')}**"
                        with st.expander(f"{identificador_label} - Total: R$ {pedido.get('total', 0):.2f}"):
                            for item in pedido.get('itens', []):
                                st.write(f"- {item.get('quantidade')}x {item['nome']}")
                                if item['obs']:
                                    st.info(f"  > Obs: {item['obs']}")
                            if st.button("Confirmar Pagamento e Enviar para Cozinha", key=f"pay_{pedido['id']}"):
                                db.collection("pedidos").document(pedido['id']).update({"status": "pago"})
                                st.balloons()
                                st.rerun()
            except Exception as e:
                st.error(f"Ocorreu um erro: {e}")
        with tab_lancar_pedido:
            render_order_placement_screen(db, all_products, all_opcoes)
    elif st.session_state.get('role') == 'cozinha':
        st.title("🍳 Cozinha - Fila de Preparo (Pedidos Pagos)")
        # (O resto do código da tela da cozinha)
    else:
        st.error("Cargo não reconhecido ou sem painel definido.")