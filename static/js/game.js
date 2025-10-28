// static/js/game.js

// Conecta ao servidor WebSocket
const socket = io();

// --- Mapeamento de Teclas (similar ao seu) ---
const teclas_jogador1 = {
    's': 'pedra_branco',
    'd': 'papel_branco',
    'a': 'tesoura_branco'
};
const teclas_jogador2 = {
    'k': 'pedra_cinza',
    'l': 'papel_cinza',
    'j': 'tesoura_cinza'
};

// --- Elementos do DOM ---
const menuScreen = document.getElementById('menu-screen');
const gameScreen = document.getElementById('game-screen');
const endScreen = document.getElementById('end-screen');

const playLocalBtn = document.getElementById('play-local-btn');
const playCpuBtn = document.getElementById('play-cpu-btn');

const p1Health = document.getElementById('player1-health');
const p2Health = document.getElementById('player2-health');
const roundNumber = document.getElementById('round-number');
const p1Move = document.getElementById('player1-move');
const p2Move = document.getElementById('player2-move');
const roundMessage = document.getElementById('round-message');
const p1Cards = document.getElementById('player1-cards');
const p2Cards = document.getElementById('player2-cards');
const winnerText = document.getElementById('winner-text');
const revancheBtn = document.getElementById('revanche-btn');

// --- Estado local (para saber quem é este jogador) ---
// Em um jogo real, o servidor te diria se você é P1 or P2.
// Para modo local, vamos assumir que este navegador controla os dois.
let modoJogo = 'menu';

// --- (1) Manipuladores de Eventos (Input do Usuário) ---

// Cliques nos botões do Menu
playLocalBtn.addEventListener('click', () => {
    socket.emit('start_game', { mode: 'local' });
});

playCpuBtn.addEventListener('click', () => {
    socket.emit('start_game', { mode: 'cpu' });
});

revancheBtn.addEventListener('click', () => {
    // Pede ao servidor para resetar (no nosso caso, apenas reconectar)
    window.location.reload();
});


// Eventos de Teclado para Jogadas
document.addEventListener('keydown', (event) => {
    const key = event.key.toLowerCase();
    
    // Jogador 1
    if (key in teclas_jogador1) {
        socket.emit('make_move', {
            jogador: 'jogador1',
            jogada: teclas_jogador1[key]
        });
    }

    // Jogador 2 (apenas se for modo local)
    if (modoJogo === 'local' && key in teclas_jogador2) {
        socket.emit('make_move', {
            jogador: 'jogador2',
            jogada: teclas_jogador2[key]
        });
    }
});

// Cliques nas Cartas
function onCardClick(jogador, cartaNome) {
    // (Seu popup_carta iria aqui)
    const querUsar = confirm(`Você quer usar a carta "${cartaNome}"?`);
    if (querUsar) {
        socket.emit('use_card', {
            jogador: jogador,
            carta: cartaNome
        });
    }
}


// --- (2) Manipulador de Estado (Renderização) ---
// Esta é a função mais importante! Ela substitui TODAS as suas funções "desenhar_".
socket.on('update_state', (estado) => {
    console.log("Novo estado recebido:", estado);
    modoJogo = estado.modo;

    // --- Atualiza as Telas ---
    menuScreen.style.display = (estado.modo === 'menu') ? 'flex' : 'none';
    gameScreen.style.display = (estado.modo === 'local' || estado.modo === 'cpu') ? 'flex' : 'none';
    endScreen.style.display = (estado.modo === 'fim_jogo') ? 'flex' : 'none';

    if (estado.modo === 'fim_jogo') {
        winnerText.innerText = `${estado.vencedor_final} VENCEU!`;
        return;
    }

    if (estado.modo === 'local' || estado.modo === 'cpu') {
        // --- Atualiza o HUD (Vidas) ---
        p1Health.innerHTML = ''; // Limpa vidas antigas
        for (let i = 0; i < estado.vidas.jogador1; i++) {
            p1Health.innerHTML += `<img src="/static/images/coracao_red.png">`;
        }
        for (let i = 0; i < (7 - estado.vidas.jogador1); i++) {
            p1Health.innerHTML += `<img src="/static/images/coracao_branco.png">`;
        }
        
        p2Health.innerHTML = ''; // Limpa vidas antigas
        for (let i = 0; i < estado.vidas.jogador2; i++) {
            p2Health.innerHTML += `<img src="/static/images/coracao_red.png">`;
        }
        for (let i = 0; i < (7 - estado.vidas.jogador2); i++) {
            p2Health.innerHTML += `<img src="/static/images/coracao_branco.png">`;
        }

        // --- Atualiza a Rodada ---
        roundNumber.innerText = estado.rodada;

        // --- Atualiza as Jogadas na Tela ---
        p1Move.className = 'move-display'; // Reseta a classe
        if (estado.jogada_jogador1) {
            p1Move.classList.add(estado.jogada_jogador1);
            p1Move.innerText = '';
        } else {
            p1Move.innerText = '?';
        }
        
        p2Move.className = 'move-display'; // Reseta a classe
        if (estado.jogada_jogador2) {
            p2Move.classList.add(estado.jogada_jogador2);
            p2Move.innerText = '';
        } else {
            p2Move.innerText = '?';
        }

        // --- Atualiza a Mensagem da Rodada ---
        roundMessage.innerText = estado.mensagem_rodada || '';

        // --- Atualiza as Cartas (Mão) ---
        p1Cards.innerHTML = '';
        estado.cartas_jogador1.forEach(carta => {
            const cardDiv = document.createElement('div');
            cardDiv.className = `card ${carta}`;
            cardDiv.onclick = () => onCardClick('jogador1', carta);
            p1Cards.appendChild(cardDiv);
        });

        p2Cards.innerHTML = '';
        estado.cartas_jogador2.forEach(carta => {
            const cardDiv = document.createElement('div');
            cardDiv.className = `card ${carta}`;
            // Em modo CPU, o jogador não pode clicar nas cartas da CPU
            if (modoJogo === 'local') {
                cardDiv.onclick = () => onCardClick('jogador2', carta);
            }
            p2Cards.appendChild(cardDiv);
        });
    }
});