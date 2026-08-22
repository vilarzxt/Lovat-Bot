# =========================
# 🧭 TICKET ROUTER ENGINE
# LOVAT BOT
# =========================

import discord

from systems.permissions import (
    TICKET_RULES,
    can_access_ticket,
    get_user_highest_level
)

from systems.utils import create_embed

from config.assets import (
    ASSETS,
    SUCCESS_COLOR
)


# =========================
# 🧠 SQUADS (CATEGORIAS INTERNAS)
# =========================

SQUADS = {

    "FOUNDER_TEAM": "fundador",
    "MOD_TEAM": "moderador",
    "STAFF_TEAM": "staff"
}


# =========================
# 🧭 ROUTER PRINCIPAL
# =========================

class TicketRouter:

    def __init__(self, bot):
        self.bot = bot


    # =========================
    # 🔍 RESOLVE TICKET RULE
    # =========================

    def resolve_rule(self, ticket_key: str) -> dict:
        return TICKET_RULES.get(ticket_key, None)


    # =========================
    # 👥 RESOLVE SQUAD
    # =========================

    def resolve_squad(self, ticket_key: str) -> str:

        rule = self.resolve_rule(ticket_key)

        if not rule:
            return SQUADS["STAFF_TEAM"]

        return SQUADS.get(rule["route"], SQUADS["STAFF_TEAM"])


    # =========================
    # 🔐 CHECK ACCESS
    # =========================

    def can_user_access(self, member: discord.Member, ticket_key: str) -> bool:

        roles = [r.name.lower().replace(" ", "_") for r in member.roles]

        return can_access_ticket(roles, ticket_key)


    # =========================
    # 🧠 CREATE TICKET CHANNEL
    # =========================

    async def create_ticket_channel(
        self,
        interaction: discord.Interaction,
        ticket_key: str,
        category: discord.CategoryChannel,
        ticket_id: int
    ):

        guild = interaction.guild

        rule = self.resolve_rule(ticket_key)

        squad = self.resolve_squad(ticket_key)

        channel_name = f"🎫-{ticket_key}-{ticket_id}"


        # =========================
        # 🔐 PERMISSION OVERLAY
        # =========================

        overwrites = {

            guild.default_role: discord.PermissionOverwrite(
                view_channel=False
            ),

            interaction.user: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True
            )
        }


        # =========================
        # 👥 SQUAD ACCESS (STAFF)
        # =========================

        staff_role = discord.utils.get(
            guild.roles,
            name=squad
        )

        if staff_role:

            overwrites[staff_role] = discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True
            )


        # =========================
        # 🔥 FOUNDER OVERRIDE
        # =========================

        founder_role = discord.utils.get(
            guild.roles,
            name=SQUADS["FOUNDER_TEAM"]
        )

        if founder_role:

            overwrites[founder_role] = discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True
            )


        # =========================
        # 🎫 CHANNEL CREATE
        # =========================

        channel = await guild.create_text_channel(
            name=channel_name,
            category=category,
            overwrites=overwrites,
            reason=f"Ticket created: {ticket_key}"
        )


        # =========================
        # 📌 INITIAL STATE MESSAGE
        # =========================

        await channel.send(
            embed=create_embed(
                title="🎫 Ticket Aberto",
                description=(
                    f"**Categoria:** `{ticket_key}`\n"
                    f"**Responsável inicial:** {interaction.user.mention}\n"
                    f"**Squad designado:** `{squad}`"
                ),
                color=SUCCESS_COLOR,
                image=ASSETS["banner_ticket"]
            )
        )

        return channel


    # =========================
    # 🔄 MOVE TICKET (ALTERAR SETOR)
    # =========================

    async def move_ticket(
        self,
        channel: discord.TextChannel,
        new_category: discord.CategoryChannel,
        ticket_key: str
    ):

        await channel.edit(
            category=new_category,
            reason=f"Ticket moved to new category: {ticket_key}"
        )


    # =========================
    # 🧠 ROUTE DECISION (CORE)
    # =========================

    def route_ticket(self, ticket_key: str) -> dict:

        rule = self.resolve_rule(ticket_key)

        if not rule:
            return {
                "squad": SQUADS["STAFF_TEAM"],
                "min_level": 0
            }

        return {
            "squad": SQUADS.get(rule["route"], SQUADS["STAFF_TEAM"]),
            "min_level": rule["min_level"]
        }


# =========================
# 🚀 FACTORY
# =========================

def setup_router(bot):
    return TicketRouter(bot)

