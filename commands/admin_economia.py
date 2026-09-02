import os
import discord
from discord.ext import commands
from discord import app_commands

from config.assets import EMBED_COLOR
from systems.utils import create_embed
from systems.economy import get_saldo, set_saldo, add_saldo
from systems.social import get_user_social, set_xp

# =========================
# 👑 ADMIN ECONOMIA (SÓ O DONO)
#
# Funciona em QUALQUER servidor onde o bot esteja, mesmo que o dono
# não tenha permissão de administrador ali — a checagem é pelo ID
# fixo do dono (OWNER_DISCORD_ID), não por cargo/permissão do Discord.
# =========================

def is_bot_owner(interaction: discord.Interaction) -> bool:
    owner_id = os.getenv("OWNER_DISCORD_ID", "")
    return bool(owner_id) and str(interaction.user.id) == owner_id


async def _deny(interaction: discord.Interaction):
    await interaction.response.send_message(
        "❌ Esse comando é restrito ao dono do bot.", ephemeral=True
    )


admin_economia_group = app_commands.Group(
    name="admin-economia",
    description="[Dono] Ajusta saldo e XP de qualquer usuário"
)


@admin_economia_group.command(name="definir-saldo", description="[Dono] Define o saldo exato de um usuário")
@app_commands.describe(usuario="Usuário alvo", valor="Novo valor do saldo")
async def definir_saldo(interaction: discord.Interaction, usuario: discord.Member, valor: int):
    if not is_bot_owner(interaction):
        return await _deny(interaction)
    try:
        novo_saldo = set_saldo(interaction.guild_id, usuario.id, valor)
        embed = create_embed(
            title="👑 Saldo Ajustado",
            description=f"Saldo de {usuario.mention} definido para **{novo_saldo}** moedas.",
            color=EMBED_COLOR
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    except Exception as e:
        print(f"[ADMIN_ECONOMIA_ERROR] {e}", flush=True)
        if not interaction.response.is_done():
            await interaction.response.send_message("❌ Erro ao definir saldo.", ephemeral=True)


@admin_economia_group.command(name="adicionar-saldo", description="[Dono] Adiciona (ou remove, com valor negativo) moedas de um usuário")
@app_commands.describe(usuario="Usuário alvo", valor="Quantidade a adicionar (use negativo para remover)")
async def adicionar_saldo(interaction: discord.Interaction, usuario: discord.Member, valor: int):
    if not is_bot_owner(interaction):
        return await _deny(interaction)
    try:
        novo_saldo = add_saldo(interaction.guild_id, usuario.id, valor)
        embed = create_embed(
            title="👑 Saldo Ajustado",
            description=f"Saldo de {usuario.mention} agora é **{novo_saldo}** moedas.",
            color=EMBED_COLOR
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    except Exception as e:
        print(f"[ADMIN_ECONOMIA_ERROR] {e}", flush=True)
        if not interaction.response.is_done():
            await interaction.response.send_message("❌ Erro ao ajustar saldo.", ephemeral=True)


@admin_economia_group.command(name="definir-xp", description="[Dono] Define o XP exato de um usuário")
@app_commands.describe(usuario="Usuário alvo", valor="Novo valor de XP")
async def definir_xp(interaction: discord.Interaction, usuario: discord.Member, valor: int):
    if not is_bot_owner(interaction):
        return await _deny(interaction)
    try:
        set_xp(interaction.guild_id, usuario.id, valor)
        novo = get_user_social(interaction.guild_id, usuario.id)
        embed = create_embed(
            title="👑 XP Ajustado",
            description=f"XP de {usuario.mention} definido para **{novo['xp']}** (nível {novo['nivel']}).",
            color=EMBED_COLOR
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    except Exception as e:
        print(f"[ADMIN_ECONOMIA_ERROR] {e}", flush=True)
        if not interaction.response.is_done():
            await interaction.response.send_message("❌ Erro ao definir XP.", ephemeral=True)


@admin_economia_group.command(name="ver", description="[Dono] Vê saldo e XP de um usuário")
@app_commands.describe(usuario="Usuário alvo")
async def ver(interaction: discord.Interaction, usuario: discord.Member):
    if not is_bot_owner(interaction):
        return await _deny(interaction)
    try:
        saldo = get_saldo(interaction.guild_id, usuario.id)
        social = get_user_social(interaction.guild_id, usuario.id)
        embed = create_embed(
            title=f"👑 Dados de {usuario.display_name}",
            description=(
                f"**Saldo:** {saldo} moedas\n"
                f"**XP:** {social['xp']} (nível {social['nivel']})"
            ),
            color=EMBED_COLOR
        )
        embed.set_thumbnail(url=usuario.display_avatar.url)
        await interaction.response.send_message(embed=embed, ephemeral=True)
    except Exception as e:
        print(f"[ADMIN_ECONOMIA_ERROR] {e}", flush=True)
        if not interaction.response.is_done():
            await interaction.response.send_message("❌ Erro ao consultar dados.", ephemeral=True)


async def setup(bot: commands.Bot):
    bot.tree.add_command(admin_economia_group)
