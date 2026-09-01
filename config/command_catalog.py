# =========================
# 📜 CATÁLOGO DE COMANDOS
# LOVAT BOT
# Fonte única usada pelo site (/comandos) para
# listar os comandos disponíveis, organizados por categoria.
#
# ⚠️ Isso é apenas metadado para exibição — não afeta o
# funcionamento real dos comandos no Discord. Se um comando
# for adicionado/removido/renomeado em commands/*.py, atualize
# aqui também para manter o site em dia.
# =========================

COMMAND_CATEGORIES = [
    {
        "id": "tickets",
        "label": "🎫 Tickets",
        "commands": [
            {"name": "ticket", "description": "Realiza o deploy do painel de tickets", "admin": True},
            {"name": "ticket-system", "description": "Painel principal de configuração do sistema de tickets", "admin": True},
        ],
    },
    {
        "id": "moderacao",
        "label": "🛡️ Moderação",
        "commands": [
            {"name": "ban", "description": "Bane um usuário do servidor", "admin": True},
            {"name": "kick", "description": "Expulsa um usuário do servidor", "admin": True},
            {"name": "warn", "description": "Aplica uma advertência", "admin": True},
            {"name": "mute", "description": "Silencia um usuário por um tempo determinado (ex: 10m, 1h, 1d)", "admin": True},
            {"name": "unmute", "description": "Remove o silêncio de um usuário", "admin": True},
            {"name": "clear", "description": "Limpa um determinado número de mensagens no canal (máximo 100)", "admin": True},
            {"name": "lock", "description": "Bloqueia o canal atual", "admin": True},
            {"name": "unlock", "description": "Desbloqueia o canal atual", "admin": True},
            {"name": "historico", "description": "Exibe o histórico recente de logs de moderação de um usuário", "admin": True},
        ],
    },
    {
        "id": "configuracao",
        "label": "⚙️ Configuração",
        "commands": [
            {"name": "config", "description": "Painel único de configurações gerais do servidor", "admin": True},
            {"name": "embed", "description": "Cria uma embed personalizada", "admin": True},
            {"name": "anuncio", "description": "Cria um anúncio oficial", "admin": True},
            {"name": "regras", "description": "Exibe as regras oficiais", "admin": False},
        ],
    },
    {
        "id": "economia",
        "label": "💰 Economia",
        "commands": [
            {"name": "saldo", "description": "Exibe o saldo de moedas de um usuário", "admin": False},
            {"name": "daily", "description": "Resgate sua recompensa diária de moedas", "admin": False},
            {"name": "apostar", "description": "Aposte moedas com 50% de chance de dobrar o valor", "admin": False},
            {"name": "raspadinha", "description": "Compre uma raspadinha por moedas", "admin": False},
        ],
    },
    {
        "id": "social",
        "label": "👤 Social",
        "commands": [
            {"name": "perfil ver", "description": "Exibe o perfil social e de economia de um usuário", "admin": False},
            {"name": "perfil editar", "description": "Edita a biografia do seu perfil", "admin": False},
            {"name": "rank", "description": "Exibe o Top 10 membros do servidor por XP", "admin": False},
            {"name": "rep", "description": "Dá um ponto de reputação a um usuário", "admin": False},
        ],
    },
    {
        "id": "diversao",
        "label": "🎉 Diversão",
        "commands": [
            {"name": "avatar", "description": "Exibe o avatar em tamanho grande de um usuário", "admin": False},
            {"name": "enquete", "description": "Cria uma enquete pública com opções", "admin": False},
            {"name": "moeda", "description": "Joga uma moeda (Cara ou Coroa)", "admin": False},
            {"name": "dado", "description": "Rola um dado de N lados", "admin": False},
            {"name": "ship", "description": "Calcula a compatibilidade entre dois usuários", "admin": False},
            {"name": "8ball", "description": "Pergunte algo à Bola 8 Mágica", "admin": False},
        ],
    },
    {
        "id": "musica",
        "label": "🎵 Música",
        "commands": [
            {"name": "tocar", "description": "Toca uma música no canal de voz", "admin": False},
            {"name": "pausar", "description": "Pausa a música atual", "admin": False},
            {"name": "pular", "description": "Pula a música atual", "admin": False},
            {"name": "parar", "description": "Para a reprodução de música", "admin": False},
            {"name": "fila", "description": "Exibe a fila de músicas", "admin": False},
        ],
    },
    {
        "id": "utilidades",
        "label": "🧰 Utilidades",
        "commands": [
            {"name": "serverinfo", "description": "Exibe informações sobre o servidor", "admin": False},
            {"name": "userinfo", "description": "Exibe informações sobre um usuário", "admin": False},
            {"name": "calcular", "description": "Calcula uma expressão matemática simples", "admin": False},
            {"name": "lembrete", "description": "Define um lembrete em tempo (ex: 10s, 5m, 1h)", "admin": False},
            {"name": "servidor", "description": "Exibe informações do servidor", "admin": False},
            {"name": "ping", "description": "Exibe a latência do bot", "admin": False},
            {"name": "info", "description": "Exibe informações do sistema", "admin": False},
            {"name": "status", "description": "Exibe o status do sistema", "admin": False},
        ],
    },
]


def get_total_command_count() -> int:
    return sum(len(cat["commands"]) for cat in COMMAND_CATEGORIES)
