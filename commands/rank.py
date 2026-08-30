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
        for idx, (uid, udata) in enumerate(sorted_users, 1):
            xp = udata.get("xp", 0)
            lvl = udata.get("nivel", 1)
            desc += f"**{idx}.** <@{uid}> — Nível `{lvl}` | `{xp}` XP\n"

        embed = create_embed(
            title="🏆 Ranking de XP — Top 10",
            description=desc,
            color=EMBED_COLOR
        )
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        print(f"[RANK_ERROR] {e}", flush=True)
        if not interaction.response.is_done():
            await interaction.response.send_message("❌ Erro ao exibir o ranking.", ephemeral=True)

async def setup(bot: commands.Bot):
    bot.tree.add_command(rank)
