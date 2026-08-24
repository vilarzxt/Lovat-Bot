import discord

from discord.ui import (
    View,
    Select
)

# =========================
# 🎫 SUBCATEGORY SELECT
# =========================

class TicketSubCategorySelect(Select):

    def __init__(
        self,
        category: str,
        guild_id: int = None
    ):
        self.category = category
        self.guild_id = guild_id

        options = self.get_options()

        if not options:
            options = [
                discord.SelectOption(
                    label="Geral",
                    emoji="❓",
                    value="geral"
                )
            ]

        super().__init__(
            placeholder="Selecione o tipo do atendimento...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id=f"ticket_subcategory_{category}"
        )

    def get_options(self):
        if not self.guild_id:
            return []

        from config.guild_config import get_ticket_categories
        categories = get_ticket_categories(self.guild_id)
        cat_data = categories.get(self.category, {})
        subcats = cat_data.get("subcategories", {})

        options = []
        for sub_key, sub_data in subcats.items():
            options.append(
                discord.SelectOption(
                    label=sub_data.get("label", sub_key),
                    emoji=sub_data.get("emoji", "📄"),
                    value=sub_key
                )
            )

        return options

    async def callback(
        self,
        interaction: discord.Interaction
    ):
        import traceback

        try:
            from systems.ticket_manager import create_ticket

            subcategory = self.values[0]

            await interaction.response.defer(
                ephemeral=True
            )

            ticket_channel = await create_ticket(
                interaction=interaction,
                category=self.category,
                subcategory=subcategory
            )

            if ticket_channel:
                await interaction.followup.send(
                    (
                        "✅ Ticket criado com sucesso.\n\n"
                        f"📂 Canal: {ticket_channel.mention}"
                    ),
                    ephemeral=True
                )
            else:
                await interaction.followup.send(
                    (
                        "❌ O sistema não conseguiu criar o ticket."
                    ),
                    ephemeral=True
                )

        except Exception as e:
            print("❌ ERRO NO CALLBACK DE SUBCATEGORIA:", flush=True)
            traceback.print_exc()

            try:
                if interaction.response.is_done():
                    await interaction.followup.send(
                        f"❌ Erro: {e}",
                        ephemeral=True
                    )
                else:
                    await interaction.response.send_message(
                        f"❌ Erro: {e}",
                        ephemeral=True
                    )
            except:
                pass

# =========================
# 🎫 SUBCATEGORY VIEW
# =========================

# Nota: O registro estático usa guild_id=None; envio dinâmico via /ticket passa o guild_id real.
class TicketSubCategoryView(View):

    def __init__(
        self,
        category: str,
        guild_id: int = None
    ):
        super().__init__(timeout=None)
        self.add_item(
            TicketSubCategorySelect(
                category,
                guild_id=guild_id
            )
        )

    async def on_error(
        self,
        interaction: discord.Interaction,
        error: Exception,
        item
    ):
        import traceback
        print("❌ ERRO NA VIEW DE SUBCATEGORIA:", flush=True)
        traceback.print_exc()

        try:
            if interaction.response.is_done():
                await interaction.followup.send(
                    f"❌ Erro: {error}",
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    f"❌ Erro: {error}",
                    ephemeral=True
                )
        except:
            pass

# =========================
# ⏰ AUTO CLOSE SELECT
# =========================

class TicketAutoCloseSelect(Select):

    def __init__(self):
        options = [
            discord.SelectOption(
                label="30 minutos",
                emoji="⏰",
                value="1800"
            ),
            discord.SelectOption(
                label="1 hora",
                emoji="⏰",
                value="3600"
            ),
            discord.SelectOption(
                label="2 horas",
                emoji="⏰",
                value="7200"
            ),
            discord.SelectOption(
                label="4 horas",
                emoji="⏰",
                value="14400"
            ),
            discord.SelectOption(
                label="8 horas",
                emoji="⏰",
                value="28800"
            ),
            discord.SelectOption(
                label="12 horas",
                emoji="⏰",
                value="43200"
            ),
            discord.SelectOption(
                label="24 horas",
                emoji="⏰",
                value="86400"
            )
        ]

        super().__init__(
            placeholder="Selecione o tempo de inatividade...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="ticket_autoclose_select"
        )

    async def callback(
        self,
        interaction: discord.Interaction
    ):
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

# =========================
# 📁 CHANGE CATEGORY SELECT
# =========================

class TicketChangeCategorySelect(Select):

    def __init__(self, guild_id: int = None):
        options = []
        if guild_id:
            from config.guild_config import get_ticket_categories
            categories = get_ticket_categories(guild_id)
            for key, cat in categories.items():
                options.append(
                    discord.SelectOption(
                        label=cat.get("label", key),
                        emoji=cat.get("emoji", "📁"),
                        value=key
                    )
                )

        if not options:
            options = [
                discord.SelectOption(
                    label="Padrão",
                    emoji="📁",
                    value="suporte_geral"
                )
            ]

        super().__init__(
            placeholder="Selecione a nova categoria...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="ticket_change_category_select"
        )

    async def callback(
        self,
        interaction: discord.Interaction
    ):
        from systems.views import is_staff

        if not is_staff(interaction):
            return await interaction.response.send_message(
                "❌ Você não tem permissão para alterar a categoria.",
                ephemeral=True
            )

        from systems.ticket_manager import change_ticket_category

        new_category = self.values[0]

        success = await change_ticket_category(
            channel=interaction.channel,
            new_category=new_category
        )

        if not success:
            return await interaction.response.send_message(
                "❌ Não foi possível alterar a categoria deste ticket.",
                ephemeral=True
            )

        await interaction.channel.send(
            f"📁 Categoria alterada para `{new_category}` por {interaction.user.mention}."
        )

        await interaction.response.send_message(
            f"✅ Categoria alterada para `{new_category}`.",
            ephemeral=True
        )

class TicketChangeCategoryView(View):

    def __init__(self, guild_id: int = None):
        super().__init__(timeout=None)
        self.add_item(
            TicketChangeCategorySelect(guild_id=guild_id)
        )
