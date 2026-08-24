import discord

from discord.ui import (
    View,
    Select,
    Button
)

from systems.permissions import is_ticket_staff
from systems.utils import create_embed
from config.assets import ASSETS

# =========================
# 🔐 STAFF CHECK HELPER
# =========================

def is_staff(interaction: discord.Interaction) -> bool:
    if not interaction.guild:
        return False

    roles = [
        r.name.lower()
        for r in interaction.user.roles
    ]

    return is_ticket_staff(interaction.guild.id, roles)

# =========================
# 🎫 TICKET CATEGORY SELECT
# LOVAT BOT
# =========================

class TicketCategorySelect(Select):

    def __init__(self, guild_id: int = None):
        from config.guild_config import get_ticket_categories

        options = []
        if guild_id:
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
            placeholder="Selecione a categoria do atendimento...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="ticket_category_select"
        )

    async def callback(
        self,
        interaction: discord.Interaction
    ):
        from systems.dropdowns import TicketSubCategoryView

        category = self.values[0]

        embed = create_embed(
            title="📂 Categoria Selecionada",
            description=(
                f"Categoria: `{category}`\n\n"
                "Selecione abaixo a subcategoria do atendimento."
            ),
            color=discord.Color.blurple(),
            image=ASSETS["banner_ticket"]
        )

        await interaction.response.send_message(
            embed=embed,
            view=TicketSubCategoryView(
                category,
                guild_id=interaction.guild.id if interaction.guild else None
            ),
            ephemeral=True
        )

# =========================
# 🎫 MAIN PANEL VIEW
# =========================

# Nota: O registro estático via bot.add_view() usa uma instância sem guild_id (padrão).
# Instâncias dinâmicas enviadas via /ticket passam o guild_id real da guilda.
class TicketPanelView(View):

    def __init__(self, guild_id: int = None):
        super().__init__(timeout=None)
        self.add_item(
            TicketCategorySelect(guild_id=guild_id)
        )

# =========================
# 🔒 FECHAMENTO — MOTIVO (3 BOTÕES)
# =========================

class TicketCloseReasonView(View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Realizado",
        emoji="✅",
        style=discord.ButtonStyle.success,
        custom_id="ticket_close_reason_realizado"
    )
    async def realizado(
        self,
        interaction: discord.Interaction,
        button: Button
    ):
        from systems.ticket_manager import close_ticket

        if not is_staff(interaction):
            return await interaction.response.send_message(
                "❌ Você não tem permissão para fechar este ticket.",
                ephemeral=True
            )

        await close_ticket(
            interaction=interaction,
            reason="Atendimento realizado com sucesso"
        )

    @discord.ui.button(
        label="Ticket Spam",
        emoji="❌",
        style=discord.ButtonStyle.danger,
        custom_id="ticket_close_reason_spam"
    )
    async def spam(
        self,
        interaction: discord.Interaction,
        button: Button
    ):
        from systems.ticket_manager import close_ticket

        if not is_staff(interaction):
            return await interaction.response.send_message(
                "❌ Você não tem permissão para fechar este ticket.",
                ephemeral=True
            )

        await close_ticket(
            interaction=interaction,
            reason="Ticket aberto indevidamente (spam)"
        )

    @discord.ui.button(
        label="Outros",
        emoji="📝",
        style=discord.ButtonStyle.secondary,
        custom_id="ticket_close_reason_outros"
    )
    async def outros(
        self,
        interaction: discord.Interaction,
        button: Button
    ):
        if not is_staff(interaction):
            return await interaction.response.send_message(
                "❌ Você não tem permissão para fechar este ticket.",
                ephemeral=True
            )

        from systems.modals import CloseReasonModal

        await interaction.response.send_modal(
            CloseReasonModal()
        )

# =========================
# 🔒 CLOSE TICKET BUTTON
# =========================

class CloseTicketButton(Button):

    def __init__(self):
        super().__init__(
            label="Fechar Ticket",
            emoji="🔒",
            style=discord.ButtonStyle.danger,
            custom_id="close_ticket_button"
        )

    async def callback(
        self,
        interaction: discord.Interaction
    ):
        if not is_staff(interaction):
            return await interaction.response.send_message(
                "❌ Você não tem permissão para fechar este ticket.",
                ephemeral=True
            )

        embed = create_embed(
            title="🔒 | Fechar Ticket",
            description=(
                "Selecione o motivo do fechamento do ticket:\n\n"
                "**Realizado:** O atendimento foi concluído com sucesso\n"
                "**Ticket Spam:** O ticket foi aberto indevidamente\n"
                "**Outros:** Especifique um motivo personalizado"
            ),
            color=discord.Color.red(),
            image=ASSETS["banner_ticket"]
        )

        await interaction.response.send_message(
            embed=embed,
            view=TicketCloseReasonView(),
            ephemeral=True
        )

# =========================
# 🤝 CLAIM TICKET BUTTON
# =========================

class ClaimTicketButton(Button):

    def __init__(self):
        super().__init__(
            label="Atender Ticket",
            emoji="🤝",
            style=discord.ButtonStyle.primary,
            custom_id="ticket_claim_button"
        )

    async def callback(
        self,
        interaction: discord.Interaction
    ):
        if not is_staff(interaction):
            return await interaction.response.send_message(
                "❌ Você não tem permissão para atender este ticket.",
                ephemeral=True
            )

        await interaction.channel.send(
            f"🤝 Ticket assumido por {interaction.user.mention}."
        )

        await interaction.response.send_message(
            "✅ Você reivindicou este ticket com sucesso!",
            ephemeral=True
        )

# =========================
# ⚙️ CONFIG BUTTON
# =========================

class ConfigTicketButton(Button):

    def __init__(self):
        super().__init__(
            label="Configurações",
            emoji="⚙️",
            style=discord.ButtonStyle.secondary,
            custom_id="ticket_config_button"
        )

    async def callback(
        self,
        interaction: discord.Interaction
    ):
        if not is_staff(interaction):
            return await interaction.response.send_message(
                "❌ Você não tem permissão para configurar este ticket.",
                ephemeral=True
            )

        embed = create_embed(
            title="⚙️ | Configurações do Ticket",
            description="Selecione uma opção abaixo para começar:",
            color=discord.Color.blurple(),
            image=ASSETS["banner_ticket"]
        )

        await interaction.response.send_message(
            embed=embed,
            view=TicketConfigView(),
            ephemeral=True
        )

# =========================
# ⚙️ CONFIG SELECT
# =========================

class TicketConfigSelect(Select):

    def __init__(self):
        options = [
            discord.SelectOption(
                label="Configurar Auto-Close",
                description="Fechamento automático por inatividade",
                emoji="⏰",
                value="auto_close"
            ),
            discord.SelectOption(
                label="Chamar Usuário",
                description="Envie uma mensagem no privado do usuário",
                emoji="📢",
                value="chamar_usuario"
            ),
            discord.SelectOption(
                label="Adicionar Membro ao Ticket",
                description="Adicione um usuário ao ticket",
                emoji="➕",
                value="add_member"
            ),
            discord.SelectOption(
                label="Remover Membro do Ticket",
                description="Remova um usuário do ticket",
                emoji="➖",
                value="remove_member"
            ),
            discord.SelectOption(
                label="Alterar Categoria do Ticket",
                description="Mova o ticket para outra categoria",
                emoji="📁",
                value="change_category"
            ),
            discord.SelectOption(
                label="Adicionar Notas Privadas",
                description="Anotações visíveis apenas para staff",
                emoji="📝",
                value="private_notes"
            ),
            discord.SelectOption(
                label="Renomear Ticket",
                description="Altere o nome do canal",
                emoji="✏️",
                value="rename_ticket"
            ),
            discord.SelectOption(
                label="Gerar Transcript",
                description="Gera um transcript para a staff",
                emoji="📄",
                value="generate_transcript"
            )
        ]

        super().__init__(
            placeholder="Selecione o que deseja configurar...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="ticket_config_select"
        )

    async def callback(
        self,
        interaction: discord.Interaction
    ):
        action = self.values[0]

        if action == "auto_close":
            from systems.dropdowns import TicketAutoCloseView
            embed = create_embed(
                title="⏰ | Configurar Fechamento Automático",
                description=(
                    "**Como funciona?**\n\n"
                    "• Se o usuário que abriu o ticket não enviar nenhuma mensagem no tempo configurado, o ticket será fechado automaticamente\n\n"
                    "• Se o usuário enviar uma mensagem, o temporizador será cancelado\n\n"
                    "• A equipe será notificada sobre o fechamento automático"
                ),
                color=discord.Color.orange(),
                image=ASSETS["banner_ticket"]
            )
            return await interaction.response.send_message(
                embed=embed,
                view=TicketAutoCloseView(),
                ephemeral=True
            )

        if action == "chamar_usuario":
            from systems.actions import call_ticket_user
            return await call_ticket_user(interaction)

        if action == "add_member":
            from systems.modals import AddMemberModal
            return await interaction.response.send_modal(AddMemberModal())

        if action == "remove_member":
            from systems.modals import RemoveMemberModal
            return await interaction.response.send_modal(RemoveMemberModal())

        if action == "change_category":
            from systems.dropdowns import TicketChangeCategoryView
            return await interaction.response.send_message(
                "📁 Selecione a nova categoria do ticket:",
                view=TicketChangeCategoryView(guild_id=interaction.guild.id if interaction.guild else None),
                ephemeral=True
            )

        if action == "private_notes":
            from systems.modals import PrivateNoteModal
            return await interaction.response.send_modal(PrivateNoteModal())

        if action == "rename_ticket":
            from systems.modals import RenameTicketModal
            return await interaction.response.send_modal(RenameTicketModal())

        if action == "generate_transcript":
            from systems.actions import generate_ticket_transcript
            return await generate_ticket_transcript(interaction)

# =========================
# ⚙️ CONFIG VIEW
# =========================

class TicketConfigView(View):

    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketConfigSelect())

# =========================
# ⚙️ MANAGEMENT VIEW (PAINEL DENTRO DO TICKET)
# =========================

class TicketManagementView(View):

    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(CloseTicketButton())
        self.add_item(ClaimTicketButton())
        self.add_item(ConfigTicketButton())
