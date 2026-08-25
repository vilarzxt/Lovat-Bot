import discord

from discord.ui import (
    View,
    Select
)

# =========================
# 🎫 SUBCATEGORY SELECT & VIEWS (RETENÇÃO / ADAPTAÇÃO)
# =========================

class TicketSubCategorySelect(Select):
    def __init__(self, category: str, guild_id: int = None):
        self.category = category
        self.guild_id = guild_id

        options = [discord.SelectOption(label="Geral", emoji="❓", value="geral")]

        super().__init__(
            placeholder="Selecione o tipo do atendimento...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id=f"ticket_subcategory_{category}"
        )

    async def callback(self, interaction: discord.Interaction):
        try:
            from systems.ticket_manager import create_ticket

            subcategory = self.values[0]
            await interaction.response.defer(ephemeral=True)

            ticket_channel = await create_ticket(
                interaction=interaction,
                category=self.category,
                subcategory=subcategory
            )

            if ticket_channel:
                await interaction.followup.send(
                    f"✅ Ticket criado com sucesso.\n\n📂 Canal: {ticket_channel.mention}",
                    ephemeral=True
                )
            else:
                await interaction.followup.send("❌ O sistema não conseguiu criar o ticket.", ephemeral=True)

        except Exception as e:
            print(f"[DROPDOWNS] erro em subcategory select: {e}", flush=True)

class TicketSubCategoryView(View):
    def __init__(self, category: str, guild_id: int = None):
        super().__init__(timeout=None)
        self.add_item(TicketSubCategorySelect(category, guild_id=guild_id))

# =========================
# ⏰ AUTO CLOSE SELECT
# =========================

class TicketAutoCloseSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="30 minutos", emoji="⏰", value="1800"),
            discord.SelectOption(label="1 hora", emoji="⏰", value="3600"),
            discord.SelectOption(label="2 horas", emoji="⏰", value="7200"),
            discord.SelectOption(label="4 horas", emoji="⏰", value="14400"),
            discord.SelectOption(label="8 horas", emoji="⏰", value="28800"),
            discord.SelectOption(label="12 horas", emoji="⏰", value="43200"),
            discord.SelectOption(label="24 horas", emoji="⏰", value="86400")
        ]

        super().__init__(
            placeholder="Selecione o tempo de inatividade...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="ticket_autoclose_select"
        )

    async def callback(self, interaction: discord.Interaction):
        from systems.views import is_staff
        from systems.actions import get_ticket_owner_id

        if not is_staff(interaction):
            return await interaction.response.send_message(
                "❌ Você não tem permissão para configurar o auto-close.",
                ephemeral=True
            )

        channel = interaction.channel
        guild = interaction.guild

        owner_id = get_ticket_owner_id(channel)
        owner = guild.get_member(owner_id) if owner_id else None

        if not owner:
            return await interaction.response.send_message(
                "❌ Não foi possível identificar o autor deste ticket.",
                ephemeral=True
            )

        timeout_seconds = int(self.values[0])
        auto_close_manager = interaction.client.auto_close_manager

        await auto_close_manager.start_timer(
            channel=channel,
            user=owner,
            timeout_seconds=timeout_seconds
        )

        hours = timeout_seconds / 3600
        label = (
            f"{int(timeout_seconds / 60)} minutos"
            if timeout_seconds < 3600 else
            f"{hours:g} horas"
        )

        await channel.send(
            f"⏰ Fechamento automático configurado por {interaction.user.mention}: "
            f"o ticket será fechado após **{label}** de inatividade do usuário."
        )

        await interaction.response.send_message(
            f"✅ Auto-close configurado para {label}.",
            ephemeral=True
        )

class TicketAutoCloseView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketAutoCloseSelect())
