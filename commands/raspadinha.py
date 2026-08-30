import discord
import random
from discord.ext import commands
from discord import app_commands

from config.assets import EMBED_COLOR
from systems.utils import create_embed
from systems.economy import get_saldo, add_saldo, remove_saldo

CUSTO_RASPADINHA = 20

@app_commands.command(
    name="raspadinha",
    description=f"Compre uma raspadinha por {CUSTO_RASPADINHA} moedas"
)
async def raspadinha(interaction: discord.Interaction):
    try:
        guild_id = interaction.guild_id
        user_id = interaction.user.id

        if not remove_saldo(guild_id, user_id, CUSTO_RASPADINHA):
            saldo_atual = get_saldo(guild_id, user_id)
            return await interaction.response.send_message(
                f"❌ Saldo insuficiente! A raspadinha custa **{CUSTO_RASPADINHA}** moedas e você tem **{saldo_atual}**.",
                ephemeral=True
            )

        rand = random.random()
        if rand < 0.70:
            premio = 0
            resultado_txt = "❌ NENHUM PRÊMIO"
        elif rand < 0.90:
            premio = CUSTO_RASPADINHA * 2
            resultado_txt = f"🎉 2x O CUSTO ({premio} moedas)"
        else:
            premio = CUSTO_RASPADINHA * 5
            resultado_txt = f"🌟 SUPER PRÊMIO 5x ({premio} moedas)"

        if premio > 0:
            add_saldo(guild_id, user_id, premio)

        novo_saldo = get_saldo(guild_id, user_id)
        embed = create_embed(
            title="🎟️ Raspadinha da Sorte",
            description=f"Você pagou **{CUSTO_RASPADINHA}** moedas para raspar...\n\nResultado: **{resultado_txt}**\n\nSeu saldo atual: **{novo_saldo}** moedas.",
            color=0xF1C40F if premio > 0 else EMBED_COLOR
        )
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        print(f"[RASPADINHA_ERROR] {e}", flush=True)
        if not interaction.response.is_done():
            await interaction.response.send_message("❌ Erro ao jogar raspadinha.", ephemeral=True)

async def setup(bot: commands.Bot):
    bot.tree.add_command(raspadinha)
