import discord
import os
import json
from discord.ext import commands
from discord import app_commands

from config.assets import EMBED_COLOR
from systems.utils import create_embed
from systems.permissions import is_ticket_staff

def is_staff_member(interaction: discord.Interaction) -> bool:
    if not interaction.guild:
        return False
    if interaction.user.guild_permissions.moderate_members or interaction.user.guild_permissions.administrator:
        return True
    roles = [r.name.lower() for r in interaction.user.roles]
    return is_ticket_staff(interaction.guild_id, roles)

@app_commands.command(
    name="historico",
    description="Exibe o histórico recente de logs de moderação de um usuário"
)
@app_commands.describe(usuario="Usuário para consultar o histórico")
async def historico(
    interaction: discord.Interaction,
    usuario: discord.Member
):
    try:
        if not is_staff_member(interaction):
            return await interaction.response.send_message("❌ Permissão insuficiente.", ephemeral=True)

        guild_id = interaction.guild_id
        file_path = f"data/guilds/{guild_id}/logs.json"

        registros = []
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for entry in reversed(data):
                        if str(entry.get("alvo_id")) == str(usuario.id):
                            registros.append(entry)
                        if len(registros) >= 15:
                            break
            except Exception as e:
                print(f"[HISTORICO_READ_ERROR] {e}", flush=True)

        if not registros:
            embed = create_embed(
                title=f"📜 Histórico — {usuario.name}",
                description="Nenhum registro de log encontrado para este usuário.",
                color=EMBED_COLOR
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        desc = f"Últimos {len(registros)} registros para {usuario.mention}:\n\n"
        for idx, item in enumerate(registros, 1):
            tipo = item.get("tipo", "Geral")
            autor = item.get("autor_nome", "Sistema")
            motivo = item.get("motivo") or "Sem motivo declarado"
            ts = item.get("timestamp", "")[:10]
            desc += f"**{idx}. [{tipo}]** — `{ts}`\n• Autor: {autor}\n• Motivo: {motivo}\n\n"

        embed = create_embed(
            title=f"📜 Histórico de Moderação — {usuario.name}",
            description=desc,
            color=EMBED_COLOR
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    except Exception as e:
        print(f"[HISTORICO_ERROR] {e}", flush=True)
        if not interaction.response.is_done():
            await interaction.response.send_message("❌ Erro ao consultar histórico.", ephemeral=True)

async def setup(bot: commands.Bot):
    bot.tree.add_command(historico)
