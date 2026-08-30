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
    if interaction.user.guild_permissions.ban_members or interaction.user.guild_permissions.administrator:
        return True
    roles = [r.name.lower() for r in interaction.user.roles]
    return is_ticket_staff(interaction.guild_id, roles)

# =========================
# 🔨 BAN COMMAND
# V1.3.1
# =========================

@app_commands.command(
    name="ban",
    description="Bane um usuário do servidor"
)
async def ban(
    interaction: discord.Interaction,
    usuario: discord.Member,
    motivo: str
):
    try:
        if not is_staff_member(interaction):
            return await interaction.response.send_message("❌ Permissão insuficiente para banir membros.", ephemeral=True)

        await usuario.ban(
            reason=motivo
        )

        embed = create_embed(
            title="🔨 Usuário Banido",
            color=EMBED_COLOR
        )

        embed.add_field(
            name="👤 Usuário",
            value=f"{usuario.mention} (`{usuario.id}`)",
            inline=False
        )

        embed.add_field(
            name="📝 Motivo",
            value=motivo,
            inline=False
        )

        embed.add_field(
            name="🛡️ Moderador",
            value=interaction.user.mention,
            inline=False
        )

        await interaction.response.send_message(
            embed=embed
        )

        await log_action(
            interaction.guild,
            "🔨 Banimento",
            f"O membro {usuario.mention} (`{usuario.id}`) foi banido por {interaction.user.mention}.\n**Motivo:** {motivo}",
            color=0xE74C3C
        )
    except Exception as e:
        print(f"[BAN_ERROR] {e}", flush=True)
        if not interaction.response.is_done():
            await interaction.response.send_message("❌ Não foi possível banir o usuário. Verifique minhas permissões e a hierarquia de cargos.", ephemeral=True)

# =========================
# 🚀 SETUP
# =========================

async def setup(bot: commands.Bot):
    bot.tree.add_command(ban)
