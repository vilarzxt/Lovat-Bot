import discord

from discord.ext import commands
from discord import app_commands

from config.assets import (
    ASSETS,
    EMBED_COLOR,
    TICKET_FOOTER
)

from config.settings import (
    VERSION_NAME,
    TICKET_SYSTEM_ENABLED
)

from systems.utils import create_embed

from systems.views import (
    TicketPanelView
)

# =========================
# 🎫 TICKET COMMAND
# LOVAT BOT
# =========================

@app_commands.command(
    name="ticket",
    description="Realiza o deploy do painel de tickets"
)

async def ticket(
    interaction: discord.Interaction
):

    # =========================
    # 🔒 SYSTEM CHECK
    # =========================

    if not TICKET_SYSTEM_ENABLED:

        return await interaction.response.send_message(

            "❌ O sistema de tickets está desativado.",

            ephemeral=True
        )

    # =========================
    # 🧠 EMBED
    # =========================

    embed = create_embed(

        title="🎫 Central Oficial de Atendimento",

        description=(

            "Bem-vindo à Central de Atendimento "
            "do Lovat Bot.\n\n"

            "Selecione abaixo a categoria "
            "do seu atendimento."
        ),

        color=EMBED_COLOR
    )

    # =========================
    # 📂 CATEGORIAS
    # =========================

    embed.add_field(

        name="📂 Categorias",

        value=(

            "🛠️ Suporte Geral\n"
            "❓ Dúvidas\n"
            "💡 Sugestões\n"
            "🚨 Denúncia/Report\n"
            "💰 Financeiro/Colaboração"
        ),

        inline=False
    )

    # =========================
    # 🖼️ BANNER
    # =========================

    embed.set_image(
        url=ASSETS["banner_ticket"]
    )

    # =========================
    # 🏷️ FOOTER
    # =========================

    embed.set_footer(

        text=(
            f"{TICKET_FOOTER} • "
            f"{VERSION_NAME}"
        )
    )

    # =========================
    # 🚀 RESPONSE
    # =========================

    await interaction.response.send_message(

        embed=embed,

        view=TicketPanelView()
    )

# =========================
# 🚀 SETUP
# =========================

async def setup(bot: commands.Bot):

    bot.tree.add_command(ticket)

