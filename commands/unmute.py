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
    if interaction.user.guild_permissions.moderate_members or interaction.user.guild_permissions.administrator:
        return True
    roles = [r.name.lower() for r in interaction.user.roles]
    return is_ticket_staff(interaction.guild_id, roles)

@app_commands.command(
    name="unmute",
    description="Remove o silêncio de um usuário"
)
@app_commands.describe(
    usuario="Membro para remover o castigo",
    motivo="Motivo da remoção do castigo (opcional)"
)
async def unmute(
    interaction: discord.Interaction,
    usuario: discord.Member,
    motivo: str = "Não informado"
):
    try:
        if not is_staff_member(interaction):
            return await interaction.response.send_message("❌ Permissão insuficiente.", ephemeral=True)

        if not usuario.is_timed_out():
            return await interaction.response.send_message("ℹ️ Este usuário não está silenciado atualmente.", ephemeral=True)

        await usuario.timeout(None, reason=motivo)

        embed = create_embed(
            title="🔊 Silêncio Removido",
            color=EMBED_COLOR
        )
        embed.add_field(name="👤 Usuário", value=f"{usuario.mention} (`{usuario.id}`)", inline=False)
        embed.add_field(name="📝 Motivo", value=motivo, inline=False)
        embed.add_field(name="🛡️ Moderador", value=interaction.user.mention, inline=False)

        await interaction.response.send_message(embed=embed)

        await log_action(
            interaction.guild,
            "🔊 Remoção de Silêncio",
            f"O silêncio do membro {usuario.mention} (`{usuario.id}`) foi removido por {interaction.user.mention}.\n**Motivo:** {motivo}",
            color=0x2ECC71
        )
    except Exception as e:
        print(f"[UNMUTE_ERROR] {e}", flush=True)
        if not interaction.response.is_done():
            await interaction.response.send_message("❌ Ocorreu um erro ao remover o silêncio do usuário.", ephemeral=True)

async def setup(bot: commands.Bot):
    bot.tree.add_command(unmute)
