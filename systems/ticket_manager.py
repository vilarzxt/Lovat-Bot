# =========================
# 🎫 TICKET MANAGER ENGINE
# LOVAT BOT
# =========================

import discord
import datetime

from systems.permissions import can_close_ticket
from systems.transcripts import TranscriptBuilder
from systems.utils import create_embed

from config.assets import (
    ASSETS,
    EMBED_COLOR,
    SUCCESS_COLOR,
    ERROR_COLOR
)

from systems.views import (
    TicketManagementView
)

# =========================
# 🧠 CORE MANAGER
# =========================

class TicketManager:

    def __init__(self, bot):

        self.bot = bot
        self.transcripts = TranscriptBuilder()

    # =========================
    # 🎫 CREATE TICKET
    # =========================

    async def create_ticket(

        self,
        interaction: discord.Interaction,
        category: str,
        subcategory: str

    ):

        guild = interaction.guild
        user = interaction.user

        # =========================
        # 📂 CATEGORY
        # =========================

        category_channel = discord.utils.get(
            guild.categories,
            name="TICKETS"
        )

        # =========================
        # 📁 AUTO CREATE CATEGORY
        # =========================

        if not category_channel:

            category_channel = await guild.create_category(
                name="TICKETS"
            )

        # =========================
        # 🏷️ CHANNEL NAME
        # =========================

        clean_name = (
            user.name
            .lower()
            .replace(" ", "-")
        )

        channel_name = (
            f"ticket-{clean_name}"
        )

        # =========================
        # 🚫 DUPLICATE CHECK
        # =========================

        existing_channel = discord.utils.get(
            guild.channels,
            name=channel_name
        )

        if existing_channel:

            return existing_channel

        # =========================
        # 🔐 PERMISSIONS
        # =========================

        overwrites = {

            guild.default_role: discord.PermissionOverwrite(
                view_channel=False
            ),

            user: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                attach_files=True,
                embed_links=True
            )
        }

        # =========================
        # 🎫 CREATE CHANNEL
        # =========================
        # 📌 TÓPICO: ID do dono vem PRIMEIRO,
        # separado por " | ", pra permitir
        # parsing seguro em get_ticket_owner_id()
        # =========================

        ticket_channel = await guild.create_text_channel(

            name=channel_name,

            category=category_channel,

            overwrites=overwrites,

            topic=(
                f"{user.id} | "
                f"{category} | "
                f"{subcategory}"
            )
        )

        # =========================
        # 📌 OPEN EMBED
        # =========================

        embed = create_embed(

            title="🎫 Ticket Criado",

            description=(

                f"Olá {user.mention}.\n\n"

                "Seu ticket foi criado "
                "com sucesso.\n\n"

                f"📂 Categoria: `{category}`\n"
                f"📌 Subcategoria: `{subcategory}`"
            ),

            color=EMBED_COLOR,

            image=ASSETS["banner_ticket"]
        )

        embed.timestamp = datetime.datetime.utcnow()

        embed.add_field(

            name="📋 Informações",

            value=(

                "• Descreva seu problema.\n"
                "• Envie provas se necessário.\n"
                "• Aguarde a equipe responsável."
            ),

            inline=False
        )

        # =========================
        # 📩 SEND PANEL
        # =========================

        await ticket_channel.send(

            content=user.mention,

            embed=embed,

            view=TicketManagementView()
        )

        # =========================
        # ✅ RETURN CHANNEL
        # =========================

        return ticket_channel

    # =========================
    # 📁 CHANGE CATEGORY
    # =========================

    async def change_category(

        self,
        channel: discord.TextChannel,
        new_category: str

    ):

        if not channel.topic:
            return False

        try:

            parts = channel.topic.split(" | ")

            owner_id = parts[0]

            subcategory = parts[2] if len(parts) > 2 else "geral"

        except IndexError:

            return False

        await channel.edit(

            topic=(
                f"{owner_id} | "
                f"{new_category} | "
                f"{subcategory}"
            )
        )

        return True

    # =========================
    # 🔒 CLOSE TICKET FLOW
    # =========================

    async def close_ticket(
        self,
        interaction: discord.Interaction,
        reason: str = "Não informado"
    ):

        channel = interaction.channel
        user = interaction.user
        guild = interaction.guild

        # =========================
        # 🔐 PERMISSION CHECK
        # =========================

        roles = [

            r.name.lower().replace(" ", "_")

            for r in user.roles
        ]

        if not can_close_ticket(
            roles,
            "generic"
        ):

            return await interaction.response.send_message(

                "❌ Você não tem permissão "
                "para fechar este ticket.",

                ephemeral=True
            )

        # =========================
        # 👤 IDENTIFICA DONO DO TICKET
        # =========================

        owner = None

        if channel.topic:

            try:

                owner_id = int(
                    channel.topic.split(" | ")[0]
                )

                owner = guild.get_member(owner_id)

            except (ValueError, IndexError):

                owner = None

        # =========================
        # 📌 FEEDBACK EMBED
        # =========================

        embed = create_embed(

            title="🔒 Ticket Encerrado",

            color=ERROR_COLOR
        )

        embed.timestamp = datetime.datetime.utcnow()

        embed.add_field(
            name="👤 Fechado por",
            value=user.mention,
            inline=False
        )

        embed.add_field(
            name="📌 Motivo",
            value=reason,
            inline=False
        )

        # =========================
        # 📤 DM USER (AVALIAÇÃO)
        # =========================

        if owner:

            try:

                dm_embed = create_embed(

                    title="📨 Seu ticket foi encerrado",

                    description=(

                        f"Seu atendimento em "
                        f"`{channel.name}` "
                        f"foi finalizado.\n\n"

                        f"📌 Motivo: {reason}\n\n"

                        "Agradecemos por utilizar "
                        "nossa central de atendimento!"
                    ),

                    color=SUCCESS_COLOR
                )

                await owner.send(
                    embed=dm_embed
                )

            except:
                pass

        # =========================
        # 📜 TRANSCRIPT (STAFF)
        # =========================

        try:

            await self.transcripts.send_transcript(

                channel=channel,
                guild=guild,
                user=owner if owner else user
            )

        except Exception as e:

            print(
                f"[TRANSCRIPT ERROR] {e}"
            )

        # =========================
        # 📊 LOG CHANNEL
        # =========================

        log_channel = discord.utils.get(
            guild.channels,
            name="logs-tickets"
        )

        if log_channel:

            await log_channel.send(
                embed=embed
            )

        # =========================
        # 🧹 FINALIZAÇÃO
        # =========================

        await interaction.response.send_message(

            "🔒 Ticket encerrado "
            "com sucesso.\n\n"

            "O canal será deletado em breve.",

            ephemeral=True
        )

        await channel.delete(
            reason=f"Ticket fechado: {reason}"
        )

# =========================
# 🚀 GLOBAL INSTANCE
# =========================

ticket_manager = None

# =========================
# 🚀 SETUP MANAGER
# =========================

def setup_ticket_manager(bot):

    global ticket_manager

    ticket_manager = TicketManager(bot)

    return ticket_manager

# =========================
# 🎫 GLOBAL CREATE FUNCTION
# =========================

async def create_ticket(

    interaction: discord.Interaction,
    category: str,
    subcategory: str

):

    if not ticket_manager:

        return None

    return await ticket_manager.create_ticket(

        interaction=interaction,

        category=category,

        subcategory=subcategory
    )

# =========================
# 🔒 GLOBAL CLOSE FUNCTION
# =========================

async def close_ticket(

    interaction: discord.Interaction,
    reason: str = "Não informado"

):

    if not ticket_manager:

        return await interaction.response.send_message(

            "❌ Sistema de tickets indisponível.",

            ephemeral=True
        )

    return await ticket_manager.close_ticket(

        interaction=interaction,

        reason=reason
    )

# =========================
# 📁 GLOBAL CHANGE CATEGORY
# =========================

async def change_ticket_category(

    channel: discord.TextChannel,
    new_category: str

):

    if not ticket_manager:

        return False

    return await ticket_manager.change_category(

        channel=channel,

        new_category=new_category
    )

