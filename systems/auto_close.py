# =========================
# ⏰ AUTO CLOSE ENGINE
# V1.3.2 - FINAL (PRODUCTION)
# =========================

import asyncio
import datetime
import discord
from config.guild_config import get_guild_config
from systems.utils import create_embed


# =========================
# 🧠 ACTIVE TIMERS REGISTRY
# =========================

ACTIVE_TIMERS = {}


# =========================
# ⏰ AUTO CLOSE MANAGER
# =========================

class AutoCloseManager:

    def __init__(self, bot):
        self.bot = bot


    # =========================
    # 🔍 CHECK ACTIVE TIMER
    # =========================

    def is_active(self, channel_id: int) -> bool:
        return channel_id in ACTIVE_TIMERS


    # =========================
    # 🚀 START TIMER
    # =========================

    async def start_timer(
        self,
        channel: discord.TextChannel,
        user: discord.Member,
        timeout_seconds: int
    ):

        # cancela timer anterior se existir
        if channel.id in ACTIVE_TIMERS:

            ACTIVE_TIMERS[channel.id].cancel()
            del ACTIVE_TIMERS[channel.id]

        task = asyncio.create_task(
            self._run_timer(channel, user, timeout_seconds)
        )

        ACTIVE_TIMERS[channel.id] = task


    # =========================
    # 🔄 RESET TIMER (ACTIVITY)
    # =========================

    async def reset_timer(self, channel: discord.TextChannel):

        if channel.id in ACTIVE_TIMERS:

            try:
                ACTIVE_TIMERS[channel.id].cancel()
            except Exception:
                pass

            del ACTIVE_TIMERS[channel.id]


    # =========================
    # ⏳ TIMER CORE LOOP
    # =========================

    async def _run_timer(
        self,
        channel: discord.TextChannel,
        user: discord.Member,
        timeout_seconds: int
    ):
        try:
            await asyncio.sleep(timeout_seconds)

            guild = channel.guild
            cfg = get_guild_config(guild.id)

            embed = create_embed(
                title="⏰ Ticket Fechado Automaticamente",
                description=f"Este ticket foi fechado automaticamente após {timeout_seconds // 60} minutos de inatividade.",
                color=0xE74C3C
            )

            try:
                await channel.send(embed=embed)
            except Exception:
                pass

            # Notificar canal de logs de ticket se configurado
            log_ch_id = cfg.get("ticket_log_channel_id")
            if log_ch_id:
                log_ch = guild.get_channel(log_ch_id)
                if log_ch:
                    log_embed = discord.Embed(
                        title="⏰ Ticket Auto-Fechado",
                        description=f"O canal `{channel.name}` foi fechado automaticamente por inatividade.",
                        color=0xE74C3C,
                        timestamp=datetime.datetime.utcnow()
                    )
                    log_embed.add_field(name="Membro", value=user.mention if user else "Desconhecido")
                    try:
                        await log_ch.send(embed=log_embed)
                    except Exception as e:
                        print(f"[AUTO_CLOSE_LOG_ERROR] {e}", flush=True)

            await asyncio.sleep(5)
            await channel.delete(reason="Auto-close por inatividade")

        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"[AUTO_CLOSE_ERROR] {e}", flush=True)
        finally:
            if channel.id in ACTIVE_TIMERS:
                del ACTIVE_TIMERS[channel.id]


def setup_auto_close(bot):
    return AutoCloseManager(bot)
