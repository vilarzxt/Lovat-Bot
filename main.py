import discord
from discord.ext import commands
import os
import asyncio

from dotenv import load_dotenv
load_dotenv()
from config.settings import PREFIX, GUILD_ID

from systems.views import (
    TicketPanelView,
    TicketManagementView
)


# =========================
# 🤖 INTENTS
# =========================

intents = discord.Intents.default()
intents.members = True
intents.message_content = True


# =========================
# 🤖 BOT CORE
# V1.3.2.9
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

        print("🎫 PERSISTENT VIEWS LOADED")

        try:

            guild = discord.Object(
                id=GUILD_ID
            )

            # =========================
            # 🌍 GLOBAL SYNC
            # =========================

            global_sync = await self.tree.sync()

            # =========================
            # 🏠 GUILD SYNC
            # =========================

            guild_sync = await self.tree.sync(
                guild=guild
            )

            print(
                f"🌍 GLOBAL SYNC: "
                f"{len(global_sync)}"
            )

            print(
                f"🏠 GUILD SYNC: "
                f"{len(guild_sync)}"
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
