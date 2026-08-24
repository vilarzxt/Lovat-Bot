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

from config.guild_config import get_ticket_categories
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

    if not TICKET_SYSTEM_ENABLED:
        return await interaction.response.send_message(
            "❌ O sistema de tickets está desativado.",
            ephemeral=True
        )

    guild_id = interaction.guild_id if interaction.guild else None
    categories = get_ticket_categories(guild_id) if guild_id else {}

    categories_text = ""
    for key, cat in categories.items():
        emoji = cat.get("emoji", "📂")
        label = cat.get("label", key)
        categories_text += f"{emoji} {label}\n"

    if not categories_text:
        categories_text = "Nenhuma categoria configurada."

    embed = create_embed(
        title="🎫 Central Oficial de Atendimento",
        description=(
            "Bem-vindo à Central de Atendimento.\n\n"
            "Selecione abaixo a categoria do seu atendimento."
        ),
        color=EMBED_COLOR
    )

    embed.add_field(
        name="📂 Categorias",
        value=categories_text,
        inline=False
    )

    embed.set_image(
        url=ASSETS["banner_ticket"]
    )

    embed.set_footer(
        text=(
            f"{TICKET_FOOTER} • "
            f"{VERSION_NAME}"
        )
    )

    await interaction.response.send_message(
        embed=embed,
        view=TicketPanelView(guild_id=guild_id)
    )

async def setup(bot: commands.Bot):
    bot.tree.add_command(ticket)
