// Configuração
// TODO: Em produção, o ID viria do login ou da URL
const GUILD_ID = "1057379243249635459"; // Coloque o ID do seu servidor aqui para testar
const API_URL = `/api/guild/${GUILD_ID}`;

// Elementos DOM
const contentDiv = document.getElementById('dashboard-content');
const loadingDiv = document.getElementById('loading');
const toastDiv = document.getElementById('toast');

// Estado da Aplicação
let currentConfig = {};

// --- Funções de API ---

async def fetchConfig() {
    try {
        const response = await fetch(API_URL);
        currentConfig = await response.json();
        renderModules();
    } catch (error) {
        console.error("Erro ao carregar config:", error);
        contentDiv.innerHTML = `<div style="color:red">Erro ao carregar configurações. O servidor está rodando?</div>`;
    } finally {
        loadingDiv.style.display = 'none';
    }
}

async def saveConfig() {
    try {
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(currentConfig)
        });
        
        if (response.ok) {
            showToast();
        }
    } catch (error) {
        console.error("Erro ao salvar:", error);
        alert("Erro ao salvar alterações.");
    }
}

// --- Funções de Interface (Renderização) ---

function renderModules() {
    // Aqui desenhamos o HTML dinamicamente baseado no JSON
    contentDiv.innerHTML = `
        <div class="grid">
            <!-- Módulo Boas-Vindas (Destaque) -->
            <div class="card" style="grid-column: 1 / -1;">
                <div class="card-header">
                    <div class="card-title">
                        <i class="fa-solid fa-door-open" style="color: var(--success)"></i> Boas-Vindas
                    </div>
                    <label class="switch">
                        <input type="checkbox" onchange="toggleModule('module_welcome', this.checked)" ${currentConfig.module_welcome ? 'checked' : ''}>
                        <span class="slider"></span>
                    </label>
                </div>
                <div class="form-group">
                    <label>Mensagem de Entrada</label>
                    <textarea rows="3" oninput="updateText('welcome_message_text', this.value)" onblur="saveConfig()">${currentConfig.welcome_message_text || ''}</textarea>
                </div>
            </div>

            ${renderCard('module_economy', 'fa-coins', 'Economia', 'Sistema de DreamCoins e Loja.')}
            ${renderCard('module_music', 'fa-music', 'Música', 'Player Lavalink de alta qualidade.')}
            ${renderCard('module_tickets', 'fa-ticket', 'Tickets', 'Suporte privado via botão.')}
            ${renderCard('module_automod', 'fa-robot', 'AutoMod', 'Proteção automática contra spam.')}
            ${renderCard('module_levels', 'fa-chart-line', 'Níveis', 'XP e recompensas por atividade.')}
            ${renderCard('module_fun', 'fa-gamepad', 'Diversão', 'Quiz, 8Ball e outros jogos.')}
        </div>
    `;
}

function renderCard(key, icon, title, desc) {
    return `
        <div class="card">
            <div class="card-header">
                <div class="card-title"><i class="fa-solid ${icon}"></i> ${title}</div>
                <label class="switch">
                    <input type="checkbox" onchange="toggleModule('${key}', this.checked)" ${currentConfig[key] ? 'checked' : ''}>
                    <span class="slider"></span>
                </label>
            </div>
            <div class="card-desc">${desc}</div>
        </div>
    `;
}

// --- Lógica de Negócio ---

// Torna as funções globais para o HTML acessar
window.toggleModule = (key, value) => {
    currentConfig[key] = value;
    saveConfig(); // Salva instantaneamente ao clicar
};

window.updateText = (key, value) => {
    currentConfig[key] = value;
    // Nota: Não salvamos no 'input' (a cada letra), mas sim no 'blur' (quando sai do campo)
};

// --- Utilitários ---

function showToast() {
    toastDiv.classList.add('show');
    setTimeout(() => toastDiv.classList.remove('show'), 3000);
}

// Inicialização
document.addEventListener('DOMContentLoaded', fetchConfig);