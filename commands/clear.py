import discord
from discord.ext import commands
from discord import app_commands

from config.assets import EMBED_COLOR
from systems.utils import create_embed
from systems.permissions import is_ticket_staff
from commands.config import log_action

def is_staff_member(interaction: discord.Interaction) -> bool:
    if not interaction.guild:
        return False
    if interaction.user.guild_permissions.manage_messages or interaction.user.guild_permissions.administrator:
        return True
    roles = [r.name.lower() for r in interaction.user.roles]
    return is_ticket_staff(interaction.guild_id, roles)

@app_commands.command(
    name="clear",
    description="Limpa um determinado número de mensagens no canal (máximo 100)"
)
@app_commands.describe(quantidade="Quantidade de mensagens a apagar (1-100)")
async def clear(
    interaction: discord.Interaction,
    quantidade: int
):
    try:
        if not is_staff_member(interaction):
            return await interaction.response.send_message("❌ Permissão insuficiente para limpar mensagens.", ephemeral=True)

        if quantidade < 1 or quantidade > 100:
            return await interaction.response.send_message("❌ A quantidade deve estar entre 1 e 100.", ephemeral=True)

        await interaction.response.defer(ephemeral=True)

        deleted = await interaction.channel.purge(limit=quantidade)

        embed = create_embed(
            title="🧹 Limpeza Concluída",
            description=f"Foram removidas **{len(deleted)}** mensagens do canal {interaction.channel.mention}.",
            color=EMBED_COLOR
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

        await log_action(
            interaction.guild,
            "🧹 Limpeza de Chat",
            f"Foram apagadas **{len(deleted)}** mensagens no canal {interaction.channel.mention} por {interaction.user.mention}.",
            color=0x95A5A6
        )
    except Exception as e:
        print(f"[CLEAR_ERROR] {e}", flush=True)
        if not interaction.response.is_done():
            await interaction.response.send_message("❌ Ocorreu um erro ao apagar as mensagens.", ephemeral=True)

async def setup(bot: commands.Bot):
    bot.tree.add_command(clear)
