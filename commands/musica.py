import discord
from discord import app_commands
from discord.ext import commands

# Nota de dependência futura: descomentar discord.py[voice] / PyNaCl / wavelink no requirements.txt se integrar Lavalink
MUSIC_FALLBACK_MSG = "🎵 Sistema de música ainda não configurado neste servidor."

@app_commands.command(name="tocar", description="Toca uma música no canal de voz")
@app_commands.describe(busca="Nome ou link da música")
async def tocar(interaction: discord.Interaction, busca: str):
    await interaction.response.send_message(MUSIC_FALLBACK_MSG, ephemeral=True)

@app_commands.command(name="pausar", description="Pausa a música atual")
async def pausar(interaction: discord.Interaction):
    await interaction.response.send_message(MUSIC_FALLBACK_MSG, ephemeral=True)

@app_commands.command(name="pular", description="Pula a música atual")
async def pular(interaction: discord.Interaction):
    await interaction.response.send_message(MUSIC_FALLBACK_MSG, ephemeral=True)

@app_commands.command(name="parar", description="Para a reprodução de música")
async def parar(interaction: discord.Interaction):
    await interaction.response.send_message(MUSIC_FALLBACK_MSG, ephemeral=True)

@app_commands.command(name="fila", description="Exibe a fila de músicas")
async def fila(interaction: discord.Interaction):
    await interaction.response.send_message(MUSIC_FALLBACK_MSG, ephemeral=True)

async def setup(bot: commands.Bot):
    bot.tree.add_command(tocar)
    bot.tree.add_command(pausar)
    bot.tree.add_command(pular)
    bot.tree.add_command(parar)
    bot.tree.add_command(fila)
