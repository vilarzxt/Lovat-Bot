import discord
from discord.ext import commands
import os
import asyncio

from dotenv import load_dotenv
load_dotenv()
from config.settings import PREFIX
from config.guild_config import get_guild_config

from systems.views import (
    TicketPanelView,
    TicketManagementView,
    DynamicPanelPublicView
)
from commands.config import CaptchaVerifyView, log_action

# =========================
# 🤖 INTENTS
# =========================

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

# =========================
# 🤖 BOT CORE
# =========================

class BotClient(commands.Bot):

    def __init__(self):

        super().__init__(
            command_prefix=PREFIX,
            intents=intents,
            help_command=None
        )

        self.auto_close_manager = None

    # =========================
    # 📦 COMMAND LOADER
    # =========================

    COMMAND_FILES = [
        "commands.ping",
        "commands.info",
        "commands.status",
        "commands.ticket",
        "commands.ticket_system",
        "commands.config",
        "commands.embed",
        "commands.anuncio",
        "commands.regras",
        "commands.servidor",
        "commands.warn",
        "commands.kick",
        "commands.ban",
        "commands.lock",
        "commands.unlock"
    ]

    # =========================
    # 🚀 SETUP HOOK
    # =========================

    async def setup_hook(self):

        print("🔁 CARREGANDO COMANDOS...")

        for command in self.COMMAND_FILES:

            try:
                module = __import__(
                    command,
                    fromlist=["setup"]
                )

                if hasattr(module, "setup"):
                    await module.setup(self)

                print(f"[OK] {command}")

            except Exception as e:
                print(f"[ERRO] {command}")
                print(e)

    # =========================
    # 🔁 READY EVENT
    # =========================

    async def on_ready(self):

        print("========================")
        print("🤖 BOT ONLINE")
        print(self.user)
        print("========================")

        # =========================
        # 🎫 PERSISTENT VIEWS
        # =========================

        self.add_view(TicketPanelView())
        self.add_view(TicketManagementView())
        self.add_view(DynamicPanelPublicView())
        self.add_view(CaptchaVerifyView())

        print("🎫 PERSISTENT VIEWS LOADED")

        try:
            # =========================
            # 🌍 GLOBAL SYNC
            # =========================

            global_sync = await self.tree.sync()

            print(
                f"🌍 GLOBAL SYNC: "
                f"{len(global_sync)} comandos sincronizados"
            )

        except Exception as e:
            print("❌ SYNC ERROR:")
            print(e)

        # =========================
        # 🔥 SYSTEMS INIT
        # =========================

        from systems.auto_close import (
            setup_auto_close
        )

        from systems.ticket_manager import (
            setup_ticket_manager
        )

        from systems.events.ticket_events import (
            init_events
        )

        # =========================
        # ⚙️ AUTO CLOSE
        # =========================

        self.auto_close_manager = (
            setup_auto_close(self)
        )

        # =========================
        # 🎫 TICKET MANAGER
        # =========================

        setup_ticket_manager(self)

        # =========================
        # 📩 EVENTS
        # =========================

        init_events(
            self,
            self.auto_close_manager
        )

        print("⚙️ SYSTEMS LOADED")

    # =========================
    # 📥 MEMBER JOIN EVENT
    # =========================

    async def on_member_join(self, member: discord.Member):
        guild = member.guild
        cfg = get_guild_config(guild.id)

        # Auto-role (se ativado e captcha não for obrigatório para o cargo)
        auto_role_id = cfg.get("auto_role_id")
        if auto_role_id:
            role = guild.get_role(auto_role_id)
            if role:
                try:
                    await member.add_roles(role, reason="Auto-role de entrada")
                except Exception as e:
                    print(f"[AUTO_ROLE_ERROR] {e}", flush=True)

        # Boas-vindas
        welcome_channel_id = cfg.get("welcome_channel_id")
        welcome_msg = cfg.get("welcome_message")
        if welcome_channel_id and welcome_msg:
            channel = guild.get_channel(welcome_channel_id)
            if channel:
                formatted_msg = welcome_msg.format(
                    user=member.name,
                    mention=member.mention,
                    server=guild.name,
                    count=guild.member_count
                )
                try:
                    await channel.send(formatted_msg)
                except Exception as e:
                    print(f"[WELCOME_ERROR] {e}", flush=True)

        # Log
        await log_action(
            guild,
            "📥 Membro Entrou",
            f"O membro {member.mention} (`{member.id}`) entrou no servidor.",
            color=0x2ECC71
        )

    # =========================
    # 📤 MEMBER REMOVE EVENT
    # =========================

    async def on_member_remove(self, member: discord.Member):
        guild = member.guild
        cfg = get_guild_config(guild.id)

        # Despedida
        goodbye_channel_id = cfg.get("goodbye_channel_id")
        goodbye_msg = cfg.get("goodbye_message")
        if goodbye_channel_id and goodbye_msg:
            channel = guild.get_channel(goodbye_channel_id)
            if channel:
                formatted_msg = goodbye_msg.format(
                    user=member.name,
                    server=guild.name,
                    count=guild.member_count
                )
                try:
                    await channel.send(formatted_msg)
                except Exception as e:
                    print(f"[GOODBYE_ERROR] {e}", flush=True)

        # Log
        await log_action(
            guild,
            "📤 Membro Saiu",
            f"O membro **{member.name}** (`{member.id}`) saiu do servidor.",
            color=0xE74C3C
        )

    # =========================
    # 📩 MESSAGE EVENT
    # =========================

    async def on_message(self, message):

        await self.process_commands(
            message
        )

        if message.author.bot:
            return

        if not message.guild:
            return

        from systems.events.ticket_events import (
            handle_message
        )

        await handle_message(message)

# =========================
# 🚀 STARTUP
# =========================

async def main():

    async with BotClient() as bot:

        await bot.start(
            os.getenv("TOKEN")
        )

# =========================
# ▶️ RUNTIME
# =========================

asyncio.run(main())
