import discord
from discord.ext import commands
from discord import app_commands

from config.assets import EMBED_COLOR
from systems.utils import create_embed
from systems.social import load_social

@app_commands.command(
    name="rank",
    description="Exibe o Top 10 membros do servidor por XP"
)
async def rank(interaction: discord.Interaction):
    try:
        soc_data = load_social(interaction.guild_id)
        sorted_users = sorted(
            soc_data.items(),
            key=lambda item: item[1].get("xp", 0),
            reverse=True
        )[:10]

        if not sorted_users:
            embed = create_embed(
                title="🏆 Ranking de XP",
                description="Nenhum registro de XP encontrado no servidor.",
                color=EMBED_COLOR
            )
            return await interaction.response.send_message(embed=embed)

        desc = ""
        for idx, (uid,