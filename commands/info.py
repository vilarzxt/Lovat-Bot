import discord

from discord.ext import commands
from discord import app_commands

from config.settings import (
    VERSION_NAME,
    VERSION_DESCRIPTION,
    PROJECT_NAME
)

from config.assets import (
    ASSETS,
    EMBED_COLOR
)

from systems.utils import create_embed

# =========================
# 📦 INFO COMMAND
# LOVAT BOT
# =========================

@app_commands.command(
    name="info",
    description="Exibe informações do sistema"
)
async def info(
    interaction: discord.Interaction
):

    embed = create_embed(
        title="📦 Lovat Bot",
        color=EMBED_COLOR
    )

    embed.add_field(
        name="🏷️ Projeto",
        value=PROJECT_NAME,
        inline=False
    )

    embed.add_field(
        name="📌 Versão",
        value=(
            f"{VERSION_NAME} | "
            f"{VERSION_DESCRIPTION}"
        ),
        inline=False
    )

    embed.add_field(
        name="🧠 Arquitetura",
        value="Sistema modular",
        inline=False
    )

    embed.set_image(
        url=ASSETS["banner_institucional"]
    )

    await interaction.response.send_message(
        embed=embed
    )

# =========================
# 🚀 SETUP
# =========================

async def setup(bot: commands.Bot):

    bot.tree.add_command(info)
