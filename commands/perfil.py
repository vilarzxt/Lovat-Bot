import discord
from discord.ext import commands
from discord import app_commands

from config.assets import EMBED_COLOR
from config.bot_settings import is_system_enabled
from systems.utils import create_embed
from systems.social import get_user_social, set_bio, xp_progress
from systems.economy import get_saldo

profile_group = app_commands.Group(
    name="perfil",
    description="Comandos de perfil de usuário"
)

def _build_progress_bar(percent: float, length: int = 10) -> str:
    filled_count = int(round((percent / 100.0) * length))
    filled_count = max(0, min(length, filled_count))
    empty_count = length - filled_count
    return ("▰" * filled_count) + ("▱" * empty_count)

def _get_level_color(nivel: int) -> int:
    if nivel >= 10:
        return 0x7B2FF7
    elif nivel >= 5:
        return 0xF1C40F
    return EMBED_COLOR

@profile_group.command(
    name="ver",
    description="Exibe o perfil social e de economia de um usuário"
)
@app_commands.describe(usuario="Usuário para visualizar (opcional)")
async def perfil_ver(
    interaction: discord.Interaction,
    usuario: discord.Member = None
):
    if not is_system_enabled("social"):
        return await interaction.response.send_message(
            "⚠️ Esse sistema está temporariamente desativado pelo administrador do bot.",
            ephemeral=True
        )

    try:
        target = usuario or interaction.user
        soc = get_user_social(interaction.guild_id, target.id)
        saldo = get_saldo(interaction.guild_id, target.id)

        bio = soc.get("bio") or "*Nenhuma biografia definida.*"
        xp = soc.get("xp", 0)
        nivel = soc.get("nivel", 1)
        rep = soc.get("reputacao", 0)

        current_in_level, needed_in_level, percentual = xp_progress(xp)
        bar = _build_progress_bar(percentual, length=10)
        color = _get_level_color(nivel)

        embed = create_embed(
            title=f"Perfil de {target.display_name} — Nível {nivel}",
            description=f"📝 **Bio:** {bio}\n\n**Progresso de Nível:**\n{bar} `{current_in_level}/{needed_in_level} XP` ({percentual:.1f}%)",
            color=color
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="⭐ Nível", value=f"`{nivel}`", inline=True)
        embed.add_field(name="✨ XP Total", value=f"`{xp}`", inline=True)
        embed.add_field(name="⭐ Reputação", value=f"`+{rep}`", inline=True)
        embed.add_field(name="💰 Saldo", value=f"`{saldo}` moedas", inline=True)

        await interaction.response.send_message(embed=embed)
    except Exception as e:
        print(f"[PERFIL_ERROR] {e}", flush=True)
        if not interaction.response.is_done():
            await interaction.response.send_message("❌ Erro ao exibir perfil.", ephemeral=True)

@profile_group.command(
    name="editar",
    description="Edita a biografia do seu perfil"
)
@app_commands.describe(bio="Texto da sua nova biografia (máx 200 caracteres)")
async def perfil_editar(
    interaction: discord.Interaction,
    bio: str
):
    if not is_system_enabled("social"):
        return await interaction.response.send_message(
            "⚠️ Esse sistema está temporariamente desativado pelo administrador do bot.",
            ephemeral=True
        )

    try:
        set_bio(interaction.guild_id, interaction.user.id, bio)
        await interaction.response.send_message("✅ Sua biografia foi atualizada com sucesso!", ephemeral=True)
    except Exception as e:
        print(f"[PERFIL_EDITAR_ERROR] {e}", flush=True)
        if not interaction.response.is_done():
            await interaction.response.send_message("❌ Erro ao editar perfil.", ephemeral=True)

async def setup(bot: commands.Bot):
    bot.tree.add_command(profile_group)
