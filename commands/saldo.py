import discord
from discord.ext import commands
from discord import app_commands

from config.assets import EMBED_COLOR
from config.bot_settings import is_system_enabled
from systems.utils import create_embed
from systems.economy import get_saldo

@app_commands.command(
    name="saldo",
    description="Exibe o saldo de moedas de um usuário"
)
@app_commands.describe(usuario="Usuário para verificar o saldo (opcional)")
async def saldo(
    interaction: discord.Interaction,
    usuario: discord.Member = None
):
    if not is_system_enabled("economia"):
        return await interaction.response.send_message(
            "⚠️ Esse sistema está temporariamente desativado pelo administrador do bot.",
            ephemeral=True
        )

    try:
        target = usuario or interaction.user
        val = get_saldo(interaction.guild_id, target.id)

        embed = create_embed(
            title="💰 Carteira de Moedas",
            description=f"O saldo atual de {target.mention} é **{val}** moedas.",
            color=EMBED_COLOR
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        print(f"[SALDO_ERROR] {e}", flush=True)
        if not interaction.response.is_done():
            await interaction.response.send_message("❌ Erro ao consultar saldo.", ephemeral=True)

async def setup(bot: commands.Bot):
    bot.tree.add_command(saldo)
