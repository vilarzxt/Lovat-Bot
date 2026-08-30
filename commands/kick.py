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
    if interaction.user.guild_permissions.kick_members or interaction.user.guild_permissions.administrator:
        return True
    roles = [r.name.lower() for r in interaction.user.roles]
    return is_ticket_staff(interaction.guild_id, roles)

# =========================
# 👢 KICK COMMAND
# V1.3.1
# =========================

@app_commands.command(
    name="kick",
    description="Expulsa um usuário do servidor"
)
async def kick(
    interaction: discord.Interaction,
    usuario: discord.Member,
    motivo: str
):
    try:
        if not is_staff_member(interaction):
            return await interaction.response.send_message("❌ Permissão insuficiente para expulsar membros.", ephemeral=True)

        await usuario.kick(
            reason=motivo
        )

        embed = create_embed(
            title="👢 Usuário Expulso",
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
            "👢 Expulsão",
            f"O membro {usuario.mention} (`{usuario.id}`) foi expulsar por {interaction.user.mention}.\n**Motivo:** {motivo}",
            color=0xE67E22
        )
    except Exception as e:
        print(f"[KICK_ERROR] {e}", flush=True)
        if not interaction.response.is_done():
            await interaction.response.send_message("❌ Não foi possível expulsar o usuário. Verifique minhas permissões e a hierarquia de cargos.", ephemeral=True)

# =========================
# 🚀 SETUP
# =========================

async def setup(bot: commands.Bot):
    bot.tree.add_command(kick)
