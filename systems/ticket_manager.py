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
    EMBED_COLOR,
    SUCCESS_COLOR,
    ERROR_COLOR
)

from config.guild_config import (
    get_panel,
    get_global_ticket_settings,
    get_guild_config
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

    async def _log_ticket_event(self, guild: discord.Guild, title: str, description: str, color: int):
        try:
            cfg = get_guild_config(guild.id)
            log_ch_id = cfg.get("ticket_log_channel_id")
            if not log_ch_id:
                return
            log_ch = guild.get_channel(log_ch_id)
            if log_ch:
                embed = discord.Embed(
                    title=title,
                    description=description,
                    color=color,
                    timestamp=datetime.datetime.utcnow()
                )
                await log_ch.send(embed=embed)
        except Exception as e:
            print(f"[TICKET_LOG_EVENT_ERROR] {e}", flush=True)

    # =========================
    # 🎫 CREATE TICKET
    # =========================

    async def create_ticket(
        self,
        interaction: discord.Interaction,
        category: str,
        subcategory: str,
        panel_id: int = None
    ):
        guild = interaction.guild
        user = interaction.user

        # Obter configurações do painel e fallback global
        panel = get_panel(guild.id, panel_id) if panel_id else None
        glob_settings = get_global_ticket_settings(guild.id)

        target_category_id = None
        staff_roles = []
        mentions = []

        if panel:
            ps = panel.get("settings", {})
            target_category_id = ps.get("ticket_category_channel_id") or glob_settings.get("ticket_category_channel_id")
            staff_roles = ps.get("staff_role_ids") or glob_settings.get("staff_role_ids", [])
            mentions = ps.get("mention_role_ids") or glob_settings.get("mention_role_ids", [])
        else:
            target_category_id = glob_settings.get("ticket_category_channel_id")
            staff_roles = glob_settings.get("staff_role_ids", [])
            mentions = glob_settings.get("mention_role_ids", [])

        category_channel = None
        if target_category_id:
            category_channel = guild.get_channel(target_category_id)

        if not category_channel:
            category_channel = discord.utils.get(
                guild.categories,
                name="TICKETS"
            )

        if not category_channel:
            category_channel = await guild.create_category(
                name="TICKETS"
            )

        clean_name = (
            user.name
            .lower()
            .replace(" ", "-")
        )

        channel_name = f"ticket-{clean_name}"

        existing_channel = discord.utils.get(
            guild.channels,
            name=channel_name
        )

        if existing_channel:
            return existing_channel

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

        # Conceder permissão aos cargos de staff configurados
        for rid in staff_roles:
            role = guild.get_role(rid)
            if role:
                overwrites[role] = discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True,
                    attach_files=True,
                    embed_links=True
                )

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

        from systems.templates import get_ticket_template

        embed = get_ticket_template(
            subcategory=subcategory,
            guild_id=guild.id,
            category_key=category
        )

        mention_content = f"{user.mention}"
        if mentions:
            mention_str = " ".join([f"<@&{m}>" for m in mentions])
            mention_content += f" {mention_str}"

        await ticket_channel.send(
            content=mention_content,
            embed=embed,
            view=TicketManagementView()
        )

        await self._log_ticket_event(
            guild,
            "🎫 Ticket Criado",
            f"**Usuário:** {user.mention} (`{user.id}`)\n**Canal:** {ticket_channel.mention}\n**Categoria/Opção:** {category} / {subcategory}",
            color=0x2ECC71
        )

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

        roles = [
            r.name.lower()
            for r in user.roles
        ]

        if not can_close_ticket(
            guild.id,
            roles,
            "generic"
        ):
            return await interaction.response.send_message(
                "❌ Você não tem permissão para fechar este ticket.",
                ephemeral=True
            )

        owner = None
        if channel.topic:
            try:
                owner_id = int(channel.topic.split(" | ")[0])
                owner = guild.get_member(owner_id)
            except (ValueError, IndexError):
                owner = None

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

        if owner:
            try:
                dm_embed = create_embed(
                    title="📨 Seu ticket foi encerrado",
                    description=(
                        f"Seu atendimento em `{channel.name}` foi finalizado.\n\n"
                        f"📌 Motivo: {reason}\n\n"
                        "Agradecemos por utilizar nossa central de atendimento!"
                    ),
                    color=SUCCESS_COLOR
                )
                await owner.send(embed=dm_embed)
            except Exception:
                pass

        try:
            await self.transcripts.send_transcript(
                channel=channel,
                guild=guild,
                user=owner if owner else user
            )
        except Exception as e:
            print(f"[TRANSCRIPT ERROR] {e}", flush=True)

        await self._log_ticket_event(
            guild,
            "🔒 Ticket Fechado",
            f"**Canal:** `{channel.name}`\n**Fechado por:** {user.mention}\n**Dono do Ticket:** {owner.mention if owner else 'Desconhecido'}\n**Motivo:** {reason}",
            color=0xE74C3C
        )

        await interaction.response.send_message(
            "🔒 Ticket encerrado com sucesso.\n\nO canal será deletado em breve.",
            ephemeral=True
        )

        await channel.delete(
            reason=f"Ticket fechado: {reason}"
        )

# =========================
# 🚀 GLOBAL INSTANCE
# =========================

ticket_manager = None

def setup_ticket_manager(bot):
    global ticket_manager
    ticket_manager = TicketManager(bot)
    return ticket_manager

async def create_ticket(
    interaction: discord.Interaction,
    category: str,
    subcategory: str,
    panel_id: int = None
):
    if not ticket_manager:
        return None

    return await ticket_manager.create_ticket(
        interaction=interaction,
        category=category,
        subcategory=subcategory,
        panel_id=panel_id
    )

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
