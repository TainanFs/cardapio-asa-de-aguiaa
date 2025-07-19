import os
import time
from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter
from datetime import datetime, time as dt_time

# --- Configuração da Conexão com o Firestore ---
try:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    chave_path = os.path.join(script_dir, "firestore-chave.json")
    db = firestore.Client.from_service_account_json(chave_path)
    print("✅ Agente de impressão conectado ao Firestore.")
except Exception as e:
    print(f"❌ Falha na conexão com o banco de dados: {e}")
    exit()

# --- Função de Impressão (Nossa Impressora Falsa) ---
def formatar_e_imprimir_comanda(pedido_data):
    """
    Recebe os dados de um pedido e formata para 'imprimir' no console.
    """
    print("\n" + "="*30)
    print("      COMANDA - ASA DE ÁGUIA")
    print("="*30)
    
    identificador = pedido_data.get('identificador', 'N/A')
    garcom = pedido_data.get('garcom', 'N/A')
    timestamp = pedido_data.get('timestamp') 
    
    print(f"Comanda: {identificador}   |   Garçom: {garcom}")
    if timestamp:
        try:
            print(f"Horário do Pedido: {datetime.fromtimestamp(timestamp.timestamp()).strftime('%H:%M:%S')}")
        except:
            print(f"Horário do Pedido: {datetime.now().strftime('%H:%M:%S')}")

    print("-"*30)
    
    itens = pedido_data.get('itens', [])
    for item in itens:
        quantidade = item.get('quantidade', 1)
        nome = item.get('nome', 'Item desconhecido')
        print(f"{quantidade}x {nome}")
        
        obs = item.get('obs')
        if obs:
            print(f"  > Obs: {obs}")
            
    print("="*30 + "\n")

# --- O "Ouvinte" do Banco de Dados ---
def on_novo_pedido(col_snapshot, changes, read_time):
    """Função chamada quando um NOVO pedido chega."""
    for change in changes:
        # A lógica agora é simples: se um documento foi ADICIONADO, imprima.
        if change.type.name == 'ADDED':
            pedido_data = change.document.to_dict()
            print(f"🔔 NOVO PEDIDO DETECTADO [{pedido_data.get('identificador')}]! Imprimindo comanda...")
            formatar_e_imprimir_comanda(pedido_data)
            # O agente não muda mais o status. Seu trabalho está feito.

# --- Iniciar o Agente ---
# A consulta agora é direta: escute por pedidos com status 'novo'.
pedidos_ref = db.collection("pedidos").where(filter=FieldFilter("status", "==", "novo"))

# Inicia o "ouvinte" para novos pedidos.
query_watch = pedidos_ref.on_snapshot(on_novo_pedido)

print("🚀 Agente de impressão iniciado. Aguardando novos pedidos para imprimir...")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("🛑 Encerrando o agente de impressão.")
    query_watch.unsubscribe()