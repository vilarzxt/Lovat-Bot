import discord
from discord import app_commands
from discord.ext import commands
from systems.social import add_rep
from systems.utils import create_embed
from config.assets import SUCCESS_COLOR, ERROR_COLOR

@app_commands.command(
    name="rep",
    description="Dá um ponto de reputação a um usuário"
)
@app_commands.describe(usuario="Usuário que receberá a reputação")
async def rep(interaction: discord.Interaction, usuario: discord.Member):
    try:
        if not interaction.guild:
            return await interaction.response.send_message("❌ Comando apenas para servidores.", ephemeral=True)

        if usuario.bot:
            return await interaction.response.send_message("❌ Você não pode dar reputação a bots.", ephemeral=True)

        success, msg = add_rep(interaction.guild_id, usuario.id, interaction.user.id)
        if success:
            embed = create_embed(
                title="⭐ Reputação Concedida",
                description=f"Você deu 1 ponto de reputação para {usuario.mention}!",
                color=SUCCESS_COLOR
            )
            await interaction.response.send_message(embed=embed)
        else:
            embed = create_embed(
                title="⚠️ Reputação Não Concedida",
                description=msg,
                color=ERROR_COLOR
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    except Exception as e:
        print(f"[REP_CMD_ERROR] {e}", flush=True)
        await interaction.response.send_message("❌ Erro ao processar reputação.", ephemeral=True)

async def setup(bot: commands.Bot):
    bot.tree.add_command(rep)
