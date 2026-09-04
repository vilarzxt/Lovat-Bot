import discord
import random
from discord.ext import commands
from discord import app_commands

from config.assets import EMBED_COLOR
from config.bot_settings import is_system_enabled
from systems.utils import create_embed
from systems.economy import get_saldo, add_saldo, remove_saldo

@app_commands.command(
    name="apostar",
    description="Aposte moedas com 50% de chance de dobrar o valor"
)
@app_commands.describe(valor="Quantidade de moedas a apostar")
async def apostar(
    interaction: discord.Interaction,
    valor: int
):
    if not is_system_enabled("economia"):
        return await interaction.response.send_message(
            "⚠️ Esse sistema está temporariamente desativado pelo administrador do bot.",
            ephemeral=True
        )

    try:
        if valor <= 0:
            return await interaction.response.send_message("❌ O valor da aposta deve ser maior que 0.", ephemeral=True)

        guild_id = interaction.guild_id
        user_id = interaction.user.id
        saldo_atual = get_saldo(guild_id, user_id)

        if saldo_atual < valor:
            return await interaction.response.send_message(f"❌ Saldo insuficiente! Você possui apenas **{saldo_atual}** moedas.", ephemeral=True)

        remove_saldo(guild_id, user_id, valor)
        ganhou = random.choice([True, False])

        if ganhou:
            lucro = valor * 2
            novo_saldo = add_saldo(guild_id, user_id, lucro)
            embed = create_embed(
                title="🎲 Aposta — Vitória!",
                description=f"🎉 **Parabéns!** Você apostou **{valor}** e ganhou **{lucro}** moedas!\nSeu saldo atual é **{novo_saldo}**.",
                color=0x2ECC71
            )
        else:
            novo_saldo = get_saldo(guild_id, user_id)
            embed = create_embed(
                title="🎲 Aposta — Derrota",
                description=f"💸 **Que azar!** Você perdeu **{valor}** moedas.\nSeu saldo atual é **{novo_saldo}**.",
                color=0xE74C3C
            )

        await interaction.response.send_message(embed=embed)
    except Exception as e:
        print(f"[APOSTAR_ERROR] {e}", flush=True)
        if not interaction.response.is_done():
            await interaction.response.send_message("❌ Erro ao realizar aposta.", ephemeral=True)

async def setup(bot: commands.Bot):
    bot.tree.add_command(apostar)
