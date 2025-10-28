# app.py
import random
import os
from flask import Flask, render_template
from flask_socketio import SocketIO, emit, join_room

# --- Configuração Inicial ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'seu_segredo_super_secreto!'
socketio = SocketIO(app)

# --- Lógica do Jogo (Quase idêntica à sua) ---
# Você copiaria todas as suas constantes aqui:
# NOME_CARTAS_AMIGAVEL, CARTAS_PROPRIEDADES, etc.
CARTAS_PROPRIEDADES = {
    "jogada_hacker": {"duração": 1},
    "oitava_vida": {"efeito": "recupera_vida"},
    "miaudicao": {"duração": 2},
    "garra_feroz": {"duração": 1},
    "roubo_felino": {"duração": 0},
    "arranhao_sorte": {"duração": 2}
}
cartas_disponiveis_para_sorteio = list(CARTAS_PROPRIEDADES.keys())
opcoes = ["pedra", "papel", "tesoura"]

# O estado do jogo agora é global no servidor.
# Em um app real, você gerenciaria "salas" de jogo.
# Vamos manter um estado global para simplificar (similar ao seu original)
estado_jogo = {}

def sortear_carta():
    return random.choice(cartas_disponiveis_para_sorteio)

# Você copiaria sua função resetar_jogo() aqui
def resetar_jogo():
    global estado_jogo
    estado_jogo = {
        "vidas": {"jogador1": 7, "jogador2": 7},
        "rodada": 1,
        "modo": "menu", # Começa no menu
        "jogada_jogador1": None,
        "jogada_jogador2": None,
        "vencedor_final": None,
        "cartas_jogador1": [sortear_carta() for _ in range(3)],
        "cartas_jogador2": [sortear_carta() for _ in range(3)],
        "efeitos_ativos": {"jogador1": {}, "jogador2": {}},
        "mao_invencivel_j1": None,
        "mao_invencivel_j2": None,
        "carta_especial_usada_jogador1": False,
        "carta_especial_usada_jogador2": False,
        "vidas_perdidas_acumuladas_jogador1": 0,
        "vidas_perdidas_acumuladas_jogador2": 0,
        "empates_seguidos": 0,
        "mensagem_rodada": None # Mensagem para exibir (ex: "Jogador 1 venceu!")
    }

# Copie suas funções de lógica pura para cá:
# aplicar_efeito_carta(jogador, carta_nome)
# calcular_resultado_rodada()
# avancar_rodada()
# decidir_jogada_cpu()
# ... etc.

# Exemplo simplificado de calcular_resultado_rodada
def calcular_resultado_rodada():
    global estado_jogo
    j1 = estado_jogo["jogada_jogador1"]
    j2 = estado_jogo["jogada_jogador2"]
    
    if not j1 or not j2:
        return

    # --- (Toda a sua lógica de cartas especiais iria aqui) ---
    # ... (ex: garra_feroz, miaudicao, etc.) ...
    
    tipo_j1 = j1.split('_')[0]
    tipo_j2 = j2.split('_')[0]

    vencedor = None
    if tipo_j1 == tipo_j2:
        vencedor = "empate"
        estado_jogo["mensagem_rodada"] = "Empate!"
    elif (tipo_j1 == "pedra" and tipo_j2 == "tesoura") or \
         (tipo_j1 == "papel" and tipo_j2 == "pedra") or \
         (tipo_j1 == "tesoura" and tipo_j2 == "papel"):
        vencedor = "jogador1"
        estado_jogo["vidas"]["jogador2"] -= 1
        estado_jogo["mensagem_rodada"] = "Jogador 1 venceu a rodada!"
    else:
        vencedor = "jogador2"
        estado_jogo["vidas"]["jogador1"] -= 1
        estado_jogo["mensagem_rodada"] = "Jogador 2 venceu a rodada!"
        
    # --- (Sua lógica de fim de jogo iria aqui) ---
    if estado_jogo["vidas"]["jogador1"] <= 0:
        estado_jogo["vencedor_final"] = "Jogador 2"
        estado_jogo["modo"] = "fim_jogo"
    elif estado_jogo["vidas"]["jogador2"] <= 0:
        estado_jogo["vencedor_final"] = "Jogador 1"
        estado_jogo["modo"] = "fim_jogo"


# --- Rotas da Aplicação Web ---

# 1. Rota para servir o HTML principal
@app.route('/')
def index():
    return render_template('index.html')

# --- Eventos do Jogo (WebSockets) ---

@socketio.on('connect')
def handle_connect():
    # Quando um novo usuário se conecta, reseta o jogo
    # (Em um app real, você o colocaria em uma sala)
    print("Cliente conectado!")
    resetar_jogo()
    # Envia o estado inicial para o cliente que acabou de conectar
    emit('update_state', estado_jogo)

@socketio.on('start_game')
def handle_start_game(data):
    # O usuário clicou em "Jogar Local" ou "Jogar CPU"
    global estado_jogo
    estado_jogo["modo"] = data['mode']
    estado_jogo["rodada"] = 1
    # Envia o novo estado para TODOS os clientes
    emit('update_state', estado_jogo, broadcast=True)

@socketio.on('make_move')
def handle_make_move(data):
    # data = { "jogador": "jogador1", "jogada": "pedra_branco" }
    global estado_jogo
    
    jogador = data['jogador']
    jogada = data['jogada']
    
    if estado_jogo[f"jogada_{jogador}"] is None:
        estado_jogo[f"jogada_{jogador}"] = jogada
        print(f"{jogador} jogou: {jogada}")

    # Lógica para jogo local (espera os dois)
    if estado_jogo["modo"] == 'local':
        if estado_jogo["jogada_jogador1"] and estado_jogo["jogada_jogador2"]:
            # Os dois jogaram, calcula o resultado
            calcular_resultado_rodada()
            # Envia o resultado
            emit('update_state', estado_jogo, broadcast=True)
            
            # Prepara a próxima rodada após um tempo
            socketio.sleep(3) # Espera 3 segundos (como seu `tempo_de_exibicao`)
            # avancar_rodada() # (Você chamaria sua função aqui)
            estado_jogo["jogada_jogador1"] = None
            estado_jogo["jogada_jogador2"] = None
            estado_jogo["mensagem_rodada"] = None
            estado_jogo["rodada"] += 1
            emit('update_state', estado_jogo, broadcast=True)
            
    # Lógica para jogo contra CPU
    elif estado_jogo["modo"] == 'cpu':
        if estado_jogo["jogada_jogador1"]:
            # Jogador 1 jogou, agora a CPU joga
            # (Você chamaria sua `decidir_jogada_cpu()` aqui)
            estado_jogo["jogada_jogador2"] = random.choice(["pedra_cinza", "papel_cinza", "tesoura_cinza"])
            
            calcular_resultado_rodada()
            emit('update_state', estado_jogo, broadcast=True)

            socketio.sleep(3)
            # avancar_rodada() # (Você chamaria sua função aqui)
            estado_jogo["jogada_jogador1"] = None
            estado_jogo["jogada_jogador2"] = None
            estado_jogo["mensagem_rodada"] = None
            estado_jogo["rodada"] += 1
            emit('update_state', estado_jogo, broadcast=True)

@socketio.on('use_card')
def handle_use_card(data):
    # data = { "jogador": "jogador1", "carta": "jogada_hacker" }
    global estado_jogo
    # (Você chamaria sua função aplicar_efeito_carta() aqui)
    print(f"{data['jogador']} usou a carta {data['carta']}")
    # ... lógica para aplicar efeito ...
    # Remove a carta da mão
    estado_jogo[f"cartas_{data['jogador']}"].remove(data['carta'])
    emit('update_state', estado_jogo, broadcast=True)


if __name__ == '__main__':
    print("Servidor iniciado em http://127.0.0.1:5000")
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)