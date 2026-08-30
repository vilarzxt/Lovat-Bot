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
            except:
                pass

            del ACTIVE_TIMERS[channel.id]


    # =========================
    # ⏳ TIMER CORE LOOP
    # =========================

    async def _run_timer