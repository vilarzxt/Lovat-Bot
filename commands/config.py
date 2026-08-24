import discord
from discord import app_commands
from discord.ext import commands

from config.guild_config import get_guild_config, save_guild_config

config_group = app_commands.Group(
    name="config",
    description="Configurações gerais do servidor"
)

def is_admin_or_founder(interaction: discord.Interaction) -> bool:
    if not interaction.guild:
        return False
    if interaction.user.guild_permissions.administrator:
        return True
    roles = [r.name.lower() for r in interaction.user.roles]
    return "fundador" in roles

# =========================
# 📋 CANAL DE LOGS - DEFINIR
# =========================

@config_group.command(
    name="canal-logs-definir",
    description="Define o canal onde os logs de moderação/sistema serão enviados"
)
@app_commands.describe(
    canal="Canal de texto para os registros"
)
async def canal_logs_definir(
    interaction: discord.Interaction,
    canal: discord.TextChannel
):
    try:
        if not is_admin_or_founder(interaction):
            return await interaction.response.send_message("❌ Permissão insuficiente.", ephemeral=True)

        guild_id = interaction.guild_id
        cfg = get_guild_config(guild_id)
        cfg["log_channel_id"] = canal.id
        save_guild_config(guild_id, cfg)

        await interaction.response.send_message(
            f"✅ Canal de logs definido para {canal.mention} com sucesso!",
            ephemeral=True
        )
    except Exception as e:
        print(f"[CONFIG] Erro em canal_logs_definir: {e}", flush=True)
        await interaction.response.send_message("❌ Ocorreu um erro ao definir o canal de logs.", ephemeral=True)

# =========================
# 🚀 SETUP
# =========================

async def setup(bot: commands.Bot):
    bot.tree.add_command(config_group)
