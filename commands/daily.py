import discord
from datetime import datetime, timezone, timedelta
from discord.ext import commands
from discord import app_commands

from config.assets import EMBED_COLOR
from systems.utils import create_embed
from systems.economy import get_ultimo_daily, set_ultimo_daily, add_saldo

DAILY_REWARD = 100

@app_commands.command(
    name="daily",
    description="Resgate sua recompensa diária de moedas"
)
async def daily(interaction: discord.Interaction):
    try:
        guild_id = interaction.guild_id
        user_id = interaction.user.id
        now = datetime.now(timezone.utc)

        last_daily_str = get_ultimo_daily(guild_id, user_id)
        if last_daily_str:
            last_daily = datetime.fromisoformat(last_daily_str)
            if now - last_daily < timedelta(hours=24):
                remaining = timedelta(hours=24) - (now - last_daily)
                hours, remainder = divmod(int(remaining.total_seconds()), 3600)
                minutes, _ = divmod(remainder, 60)
                return await interaction.response.send_message(
                    f"⏰ Você já resgatou seu daily hoje! Tente novamente em **{hours}h {minutes}m**.",
                    ephemeral=True
                )

        novo_saldo = add_saldo(guild_id, user_id, DAILY_REWARD)
        set_ultimo_daily(guild_id, user_id, now.isoformat())

        embed = create_embed(
            title="🎉 Recompensa Diária",
            description=f"Você resgatou **{DAILY_REWARD}** moedas com sucesso!\nSeu novo saldo é: **{novo_saldo}** moedas.",
            color=EMBED_COLOR
        )
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        print(f"[DAILY_ERROR] {e}", flush=True)
        if not interaction.response.is_done():
            await interaction.response.send_message("❌ Erro ao resgatar daily.", ephemeral=True)

async def setup(bot: commands.Bot):
    bot.tree.add_command(daily)
