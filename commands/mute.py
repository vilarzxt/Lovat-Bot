import discord
import re
from datetime import timedelta
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

def parse_duration(time_str: str) -> timedelta | None:
    match = re.match(r"^(\d+)\s*([s|m|h|d|w])$", time_str.lower().strip())
    if not match:
        return None
    val, unit = int(match.group(1)), match.group(2)
    if unit == 's':
        return timedelta(seconds=val)
    elif unit == 'm':
        return timedelta(minutes=val)
    elif unit == 'h':
        return timedelta(hours=val)
    elif unit == 'd':
        return timedelta(days=val)
    elif unit == 'w':
        return timedelta(weeks=val)
    return None

@app_commands.command(
    name="mute",
    description="Silencia um usuário por um tempo determinado (ex: 10m, 1h, 1d)"
)
@app_commands.describe(
    usuario="Membro a ser silenciado",
    duracao="Duração do castigo (ex: 10m, 1h, 1d)",
    motivo="Motivo do silenciamento (opcional)"
)
async def mute(
    interaction: discord.Interaction,
    usuario: discord.Member,
    duracao: str,
    motivo: str = "Não informado"
):
    try:
        if not is_staff_member(interaction):
            return await interaction.response.send_message("❌ Permissão insuficiente para silenciar membros.", ephemeral=True)

        td = parse_duration(duracao)
        if not td or td.total_seconds() <= 0:
            return await interaction.response.send_message("❌ Formato de duração inválido! Use algo como `10m`, `1h`, `1d`.", ephemeral=True)

        if td > timedelta(days=28):
            return await interaction.response.send_message("❌ O tempo máximo de silêncio permitido pelo Discord é de 28 dias.", ephemeral=True)

        await usuario.timeout(td, reason=motivo)

        embed = create_embed(
            title="🔇 Usuário Silenciado",
            color=EMBED_COLOR
        )
        embed.add_field(name="👤 Usuário", value=f"{usuario.mention} (`{usuario.id}`)", inline=False)
        embed.add_field(name="⏱️ Duração", value=duracao, inline=True)
        embed.add_field(name="📝 Motivo", value=motivo, inline=False)
        embed.add_field(name="🛡️ Moderador", value=interaction.user.mention, inline=False)

        await interaction.response.send_message(embed=embed)

        await log_action(
            interaction.guild,
            "🔇 Silenciamento",
            f"O membro {usuario.mention} (`{usuario.id}`) foi silenciado por **{duracao}** por {interaction.user.mention}.\n**Motivo:** {motivo}",
            color=0xF1C40F
        )
    except Exception as e:
        print(f"[MUTE_ERROR] {e}", flush=True)
        if not interaction.response.is_done():
            await interaction.response.send_message("❌ Ocorreu um erro ao aplicar o silêncio no usuário.", ephemeral=True)

async def setup(bot: commands.Bot):
    bot.tree.add_command(mute)
