import time

# =========================
# 🔗 ESTADO COMPARTILHADO
# BOT <-> DASHBOARD
#
# O bot roda na thread principal (event loop do discord.py)
# e o Flask roda em uma thread separada (ver main.py).
# Este módulo é o ponto de contato entre os dois: guarda uma
# referência ao objeto `bot` e o horário de início, para que
# as rotas do site possam ler dados básicos (servidores,
# usuários, uptime) sem precisar acessar o event loop do bot.
#
# Apenas LEITURA de atributos simples (bot.guilds, bot.user,
# bot.latency) é feita a partir da thread do Flask — nenhuma
# escrita ou chamada assíncrona é feita por aqui.
# =========================

bot_instance = None
start_time = None


def register_bot(bot):
    global bot_instance, start_time
    bot_instance = bot
    start_time = time.time()


def get_bot():
    return bot_instance


def get_uptime_seconds() -> float:
    if start_time is None:
        return 0.0
    return time.time() - start_time


def is_bot_online() -> bool:
    return bot_instance is not None and bot_instance.is_ready()


def get_guild_count() -> int:
    if bot_instance is None:
        return 0
    return len(bot_instance.guilds)


def get_user_count() -> int:
    if bot_instance is None:
        return 0
    return sum(g.member_count or 0 for g in bot_instance.guilds)


def get_latency_ms() -> float:
    if bot_instance is None:
        return 0.0
    return round(bot_instance.latency * 1000, 1)


def get_bot_guild(guild_id: int):
    """Retorna o objeto discord.Guild se o bot estiver presente nele, senão None."""
    if bot_instance is None:
        return None
    return bot_instance.get_guild(guild_id)
