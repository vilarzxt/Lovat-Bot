import discord

from discord.ui import (
    View,
    Select,
    Button
)

from systems.permissions import is_ticket_staff
from systems.utils import create_embed
from config.assets import ASSETS, EMBED_COLOR

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
# 🎫 DYNAMIC PUBLIC PANEL VIEWS (ETAPA 8 / 9)
# =========================

class DynamicPanelSelect(Select):
    def __init__(self, panel: dict):
        self.panel_id = panel["id"]
        cs = panel.get("component_settings", {})
        placeholder = cs.get("placeholder", "Selecione o tipo do atendimento...")
        min_v = cs.get("min_values", 1)
        max_v = cs.get("max_values", 1)

        options = []
        for opt in panel.get("options", []):
            emoji = opt.get("emoji") or "📄"
            desc = opt.get("description") or None
            options.append(
                discord.SelectOption(
                    label=opt["label"][:100],
                    emoji=emoji,
                    description=desc[:100] if desc else None,
                    value=str(opt["id"])
                )
            )

        if not options:
            options = [discord.SelectOption(label="Padrão", emoji="📁", value="default")]

        super().__init__(
            placeholder=placeholder,
            min_values=min_v,
            max_values=min_v if min_v > max_v else max_v,
            options=options,
            custom_id=f"ticket_panel_{self.panel_id}_select"
        )

    async def callback(self, interaction: discord.Interaction):
        try:
            from systems.ticket_manager import create_ticket
            from config.guild_config import get_panel

            panel = get_panel(interaction.guild_id, self.panel_id)
            selected_opt_id = self.values[0]

            linked_cat = "suporte_geral"
            subcat = "geral"

            if panel and selected_opt_id != "default":
                for o in panel.get("options", []):
                    if str(o["id"]) == str(selected_opt_id):
                        if o.get("categoria_vinculada"):
                            linked_cat = o["categoria_vinculada"]
                        subcat = o["label"]
                        break

            await interaction.response.defer(ephemeral=True)

            ticket_channel = await create_ticket(
                interaction=interaction,
                category=linked_cat,
                subcategory=subcat,
                panel_id=self.panel_id
            )

            if ticket_channel:
                await interaction.followup.send(
                    f"✅ Ticket criado com sucesso.\n\n📂 Canal: {ticket_channel.mention}",
                    ephemeral=True
                )
            else:
                await interaction.followup.send(
                    "❌ O sistema não conseguiu criar o ticket.",
                    ephemeral=True
                )
        except Exception as e:
            print(f"[DYNAMIC_PANEL] Erro no callback de seleção: {e}", flush=True)

class DynamicPanelPublicView(View):
    def __init__(self, panel: dict = None):
        super().__init__(timeout=None)
        if panel:
            if panel["tipo_componente"] == "dropdown":
                self.add_item(DynamicPanelSelect(panel))
            else:
                for opt in panel.get("options", []):
                    btn = DynamicPanelButton(panel["id"], opt)
                    self.add_item(btn)

class DynamicPanelButton(Button):
    def __init__(self, panel_id: int, option_data: dict):
        self.panel_id = panel_id
        self.option_data = option_data
        emoji = option_data.get("emoji") or None
        super().__init__(
            label=option_data["label"][:80],
            emoji=emoji,
            style=discord.ButtonStyle.primary,
            custom_id=f"ticket_panel_{panel_id}_btn_{option_data['id']}"
        )

    async def callback(self, interaction: discord.Interaction):
        try:
            from systems.ticket_manager import create_ticket

            linked_cat = self.option_data.get("categoria_vinculada") or "suporte_geral"
            subcat = self.option_data.get("label", "geral")

            await interaction.response.defer(ephemeral=True)

            ticket_channel = await create_ticket(
                interaction=interaction,
                category=linked_cat,
                subcategory=subcat,
                panel_id=self.panel_id
            )

            if ticket_channel:
                await interaction.followup.send(
                    f"✅ Ticket criado com sucesso.\n\n📂 Canal: {ticket_channel.mention}",
                    ephemeral=True
                )
            else:
                await interaction.followup.send(
                    "❌ O sistema não conseguiu criar o ticket.",
                    ephemeral=True
                )
        except Exception as e:
            print(f"[DYNAMIC_PANEL] Erro no callback do botao: {e}", flush=True)

# Legacy Static Fallback Views
class TicketCategorySelect(Select):
    def __init__(self, guild_id: int = None):
        options = [discord.SelectOption(label="Padrão", emoji="📁", value="suporte_geral")]
        super().__init__(
            placeholder="Selecione a categoria do atendimento...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="ticket_category_select"
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message("Por favor, utilize os novos painéis configurados via `/ticket-system`.", ephemeral=True)

class TicketPanelView(View):
    def __init__(self, guild_id: int = None):
        super().__init__(timeout=None)
        self.add_item(TicketCategorySelect(guild_id=guild_id))

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
    async def realizado(self, interaction: discord.Interaction, button: Button):
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
    async def spam(self, interaction: discord.Interaction, button: Button):
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
    async def outros(self, interaction: discord.Interaction, button: Button):
        if not is_staff(interaction):
            return await interaction.response.send_message(
                "❌ Você não tem permissão para fechar este ticket.",
                ephemeral=True
            )

        from systems.modals import CloseReasonModal

        await interaction.response.send_modal(CloseReasonModal())

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

    async def callback(self, interaction: discord.Interaction):
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
            image=ASSETS.get("banner_ticket")
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

    async def callback(self, interaction: discord.Interaction):
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
# ⚙️ CONFIG BUTTON & SELECT
# =========================

class ConfigTicketButton(Button):
    def __init__(self):
        super().__init__(
            label="Configurações",
            emoji="⚙️",
            style=discord.ButtonStyle.secondary,
            custom_id="ticket_config_button"
        )

    async def callback(self, interaction: discord.Interaction):
        if not is_staff(interaction):
            return await interaction.response.send_message(
                "❌ Você não tem permissão para configurar este ticket.",
                ephemeral=True
            )

        embed = create_embed(
            title="⚙️ | Configurações do Ticket",
            description="Selecione uma opção abaixo para começar:",
            color=discord.Color.blurple(),
            image=ASSETS.get("banner_ticket")
        )

        await interaction.response.send_message(
            embed=embed,
            view=TicketConfigView(),
            ephemeral=True
        )

class TicketConfigSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Configurar Auto-Close", description="Fechamento automático por inatividade", emoji="⏰", value="auto_close"),
            discord.SelectOption(label="Chamar Usuário", description="Envie uma mensagem no privado do usuário", emoji="📢", value="chamar_usuario"),
            discord.SelectOption(label="Adicionar Membro ao Ticket", description="Adicione um usuário ao ticket", emoji="➕", value="add_member"),
            discord.SelectOption(label="Remover Membro do Ticket", description="Remova um usuário do ticket", emoji="➖", value="remove_member"),
            discord.SelectOption(label="Adicionar Notas Privadas", description="Anotações visíveis apenas para staff", emoji="📝", value="private_notes"),
            discord.SelectOption(label="Renomear Ticket", description="Altere o nome do canal", emoji="✏️", value="rename_ticket"),
            discord.SelectOption(label="Gerar Transcript", description="Gera um transcript para a staff", emoji="📄", value="generate_transcript")
        ]

        super().__init__(
            placeholder="Selecione o que deseja configurar...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="ticket_config_select"
        )

    async def callback(self, interaction: discord.Interaction):
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
                image=ASSETS.get("banner_ticket")
            )
            return await interaction.response.send_message(embed=embed, view=TicketAutoCloseView(), ephemeral=True)

        if action == "chamar_usuario":
            from systems.actions import call_ticket_user
            return await call_ticket_user(interaction)

        if action == "add_member":
            from systems.modals import AddMemberModal
            return await interaction.response.send_modal(AddMemberModal())

        if action == "remove_member":
            from systems.modals import RemoveMemberModal
            return await interaction.response.send_modal(RemoveMemberModal())

        if action == "private_notes":
            from systems.modals import PrivateNoteModal
            return await interaction.response.send_modal(PrivateNoteModal())

        if action == "rename_ticket":
            from systems.modals import RenameTicketModal
            return await interaction.response.send_modal(RenameTicketModal())

        if action == "generate_transcript":
            from systems.actions import generate_ticket_transcript
            return await generate_ticket_transcript(interaction)

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
