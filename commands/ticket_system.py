import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Select, Button, Modal, TextInput, RoleSelect, ChannelSelect

from config.guild_config import (
    get_panels,
    get_panel,
    create_panel,
    update_panel,
    delete_panel,
    get_global_ticket_settings,
    update_global_ticket_settings,
    get_guild_config,
    update_guild_config
)
from systems.permissions import is_ticket_staff
from systems.utils import create_embed
from config.assets import EMBED_COLOR, SUCCESS_COLOR, ERROR_COLOR

# Helper de permissão
def is_admin_or_staff(interaction: discord.Interaction) -> bool:
    if not interaction.guild:
        return False
    if interaction.user.guild_permissions.administrator:
        return True
    roles = [r.name.lower() for r in interaction.user.roles]
    return is_ticket_staff(interaction.guild_id, roles)

# Helper para converter HEX string para discord.Color
def parse_hex_color(hex_str: str) -> discord.Color:
    try:
        hex_str = hex_str.lstrip("#")
        return discord.Color(int(hex_str, 16))
    except Exception:
        return discord.Color.blurple()

# Helper para construir Discord Embed a partir do dict do painel
def build_panel_embed(conteudo: dict) -> discord.Embed:
    title = conteudo.get("title") or "Sem Título"
    desc = conteudo.get("description") or None
    color = parse_hex_color(conteudo.get("color", "#3D5A80"))
    url = conteudo.get("url") or None

    embed = discord.Embed(title=title, description=desc, color=color, url=url)

    if conteudo.get("timestamp"):
        embed.timestamp = discord.utils.utcnow()

    author = conteudo.get("author", {})
    if author and author.get("name"):
        embed.set_author(name=author["name"], icon_url=author.get("icon_url"), url=author.get("url"))

    if conteudo.get("thumbnail_url"):
        embed.set_thumbnail(url=conteudo["thumbnail_url"])

    if conteudo.get("image_url"):
        embed.set_image(url=conteudo["image_url"])

    footer = conteudo.get("footer", {})
    if footer and footer.get("text"):
        embed.set_footer(text=footer["text"], icon_url=footer.get("icon_url"))

    for f in conteudo.get("fields", []):
        embed.add_field(name=f.get("name", "Field"), value=f.get("value", "-"), inline=f.get("inline", False))

    return embed

# ============================================================
# ETAPA 2 — COMANDO RAIZ /ticket-system & MENU INICIAL
# ============================================================

class RootMenuView(View):
    def __init__(self, guild_id: int):
        super().__init__(timeout=300)
        self.guild_id = guild_id

    @discord.ui.select(
        placeholder="Selecione uma opção para começar...",
        min_values=1,
        max_values=1,
        options=[
            discord.SelectOption(label="Criar ou Editar Painéis", description="Gerencie painéis de ticket", emoji="🛠️", value="panels"),
            discord.SelectOption(label="Editar Configurações Globais", description="Configurações padrões do servidor", emoji="⚙️", value="globals"),
            discord.SelectOption(label="Enviar Painéis", description="Envia ou reenvia um painel em um canal", emoji="📢", value="send"),
            discord.SelectOption(label="Estatísticas dos Tickets", description="Ver relatório de atendimento", emoji="📊", value="stats")
        ]
    )
    async def menu_callback(self, interaction: discord.Interaction, select: Select):
        try:
            val = select.values[0]
            if val == "panels":
                view = PanelListView(self.guild_id)
                embed = view.get_embed()
                await interaction.response.edit_message(embed=embed, view=view)

            elif val == "globals":
                view = GlobalSettingsView(self.guild_id)
                embed = view.get_embed()
                await interaction.response.edit_message(embed=embed, view=view)

            elif val == "send":
                view = SendPanelView(self.guild_id)
                embed = view.get_embed()
                await interaction.response.edit_message(embed=embed, view=view)

            elif val == "stats":
                embed = create_embed(
                    title="📊 Estatísticas dos Tickets",
                    description="📊 **Relatório Geral (Últimos 30 dias)**\n\n*(Recurso em breve: Histórico detalhado de atendimento e métricas por categoria)*",
                    color=discord.Color.blue()
                )
                view = SingleBackButton(parent_view_factory=lambda: RootMenuView(self.guild_id))
                await interaction.response.edit_message(embed=embed, view=view)

        except Exception as e:
            print(f"[TICKET_SYSTEM] erro no menu raiz: {e}", flush=True)

class SingleBackButton(View):
    def __init__(self, parent_view_factory):
        super().__init__(timeout=300)
        self.parent_view_factory = parent_view_factory

    @discord.ui.button(label="< Voltar", style=discord.ButtonStyle.secondary)
    async def back_button(self, interaction: discord.Interaction, button: Button):
        try:
            parent_view = self.parent_view_factory()
            embed = getattr(parent_view, "get_embed", lambda: create_embed(title="⚙️ Painel do Sistema de Tickets", description="Selecione uma opção para configurar.", color=EMBED_COLOR))()
            await interaction.response.edit_message(embed=embed, view=parent_view)
        except Exception as e:
            print(f"[TICKET_SYSTEM] erro ao voltar: {e}", flush=True)

# ============================================================
# ETAPA 3 — CRIAR OU EDITAR PAINÉIS
# ============================================================

class PanelListView(View):
    def __init__(self, guild_id: int):
        super().__init__(timeout=300)
        self.guild_id = guild_id
        self._build_components()

    def get_embed(self) -> discord.Embed:
        panels = get_panels(self.guild_id)
        desc = "Bora configurar?\n\nSelecione um painel abaixo para editar ou clique em **Criar Novo**." if panels else "Nenhum painel cadastrado. Clique em **Criar Novo** para começar!"
        return create_embed(title="🛠️ Gerenciar Painéis", description=desc, color=EMBED_COLOR)

    def _build_components(self):
        self.clear_items()
        panels = get_panels(self.guild_id)

        if panels:
            options = []
            for p in panels:
                title = p["conteudo"].get("title") or p["conteudo"].get("texto") or f"Painel #{p['id']}"
                options.append(
                    discord.SelectOption(
                        label=f"{title[:90]}",
                        description=f"Painel ID: {p['id']} | Tipo: {p['tipo_conteudo']}",
                        value=str(p["id"]),
                        emoji="📋"
                    )
                )
            select = Select(placeholder="Selecione um painel...", options=options, custom_id="panel_select_item")
            select.callback = self.on_select_panel
            self.add_item(select)

        create_btn = Button(label="➕ Criar Novo", style=discord.ButtonStyle.success)
        create_btn.callback = self.on_create_new
        self.add_item(create_btn)

        back_btn = Button(label="< Voltar", style=discord.ButtonStyle.secondary)
        back_btn.callback = self.on_back
        self.add_item(back_btn)

    async def on_select_panel(self, interaction: discord.Interaction):
        try:
            panel_id = int(interaction.data["values"][0])
            view = PanelOptionsMenuView(self.guild_id, panel_id)
            embed = view.get_embed()
            await interaction.response.edit_message(embed=embed, view=view)
        except Exception as e:
            print(f"[TICKET_SYSTEM] erro ao selecionar painel: {e}", flush=True)

    async def on_create_new(self, interaction: discord.Interaction):
        try:
            view = CreatePanelContentTypeView(self.guild_id)
            embed = create_embed(
                title="Escolha o Tipo de Painel",
                description="**Embed:** Exibe uma mensagem enriquecida com título, descrição, imagem, footer, etc.\n\n**Mensagem:** Exibe uma mensagem simples de texto sem formatação em caixa de embed.",
                color=EMBED_COLOR
            )
            await interaction.response.edit_message(embed=embed, view=view)
        except Exception as e:
            print(f"[TICKET_SYSTEM] erro ao iniciar criação: {e}", flush=True)

    async def on_back(self, interaction: discord.Interaction):
        view = RootMenuView(self.guild_id)
        embed = create_embed(title="⚙️ Painel do Sistema de Tickets", description="Selecione uma opção para configurar.", color=EMBED_COLOR)
        await interaction.response.edit_message(embed=embed, view=view)

class CreatePanelContentTypeView(View):
    def __init__(self, guild_id: int):
        super().__init__(timeout=300)
        self.guild_id = guild_id

    @discord.ui.button(label="Embed", style=discord.ButtonStyle.primary, emoji="🖼️")
    async def embed_type(self, interaction: discord.Interaction, button: Button):
        await self._next_step(interaction, "embed")

    @discord.ui.button(label="Mensagem Simples", style=discord.ButtonStyle.secondary, emoji="💬")
    async def message_type(self, interaction: discord.Interaction, button: Button):
        await self._next_step(interaction, "mensagem")

    @discord.ui.button(label="< Voltar", style=discord.ButtonStyle.secondary)
    async def back_button(self, interaction: discord.Interaction, button: Button):
        view = PanelListView(self.guild_id)
        await interaction.response.edit_message(embed=view.get_embed(), view=view)

    async def _next_step(self, interaction: discord.Interaction, tipo_conteudo: str):
        view = CreatePanelComponentTypeView(self.guild_id, tipo_conteudo)
        embed = create_embed(
            title="Tipo de Componente",
            description="**Dropdown:** Menu de seleção com opções suspensas.\n\n**Botão:** Botões individuais diretamente sob a mensagem.",
            color=EMBED_COLOR
        )
        await interaction.response.edit_message(embed=embed, view=view)

class CreatePanelComponentTypeView(View):
    def __init__(self, guild_id: int, tipo_conteudo: str):
        super().__init__(timeout=300)
        self.guild_id = guild_id
        self.tipo_conteudo = tipo_conteudo

    @discord.ui.button(label="Dropdown (Menu de Seleção) (Recomendado)", style=discord.ButtonStyle.primary, emoji="🔽")
    async def dropdown_type(self, interaction: discord.Interaction, button: Button):
        await self._finish_create(interaction, "dropdown")

    @discord.ui.button(label="Botão", style=discord.ButtonStyle.secondary, emoji="🔘")
    async def button_type(self, interaction: discord.Interaction, button: Button):
        await self._finish_create(interaction, "botao")

    @discord.ui.button(label="< Voltar", style=discord.ButtonStyle.secondary)
    async def back_button(self, interaction: discord.Interaction, button: Button):
        view = CreatePanelContentTypeView(self.guild_id)
        embed = create_embed(title="Escolha o Tipo de Painel", description="Selecione o tipo de conteúdo.", color=EMBED_COLOR)
        await interaction.response.edit_message(embed=embed, view=view)

    async def _finish_create(self, interaction: discord.Interaction, tipo_componente: str):
        new_panel = create_panel(self.guild_id, self.tipo_conteudo, tipo_componente)
        embed = create_embed(
            title="✅ Painel Criado com Sucesso!",
            description=f"Painel Criado com Sucesso! ID: `{new_panel['id']}`.\n\nAgora você pode personalizá-lo e depois enviá-lo ao canal desejado!",
            color=SUCCESS_COLOR
        )
        view = SingleBackButton(parent_view_factory=lambda: PanelListView(self.guild_id))
        await interaction.response.edit_message(embed=embed, view=view)

# ============================================================
# ETAPA 4 — ESCOLHA O QUE CONFIGURAR NESTE PAINEL
# ============================================================

class PanelOptionsMenuView(View):
    def __init__(self, guild_id: int, panel_id: int):
        super().__init__(timeout=300)
        self.guild_id = guild_id
        self.panel_id = panel_id

    def get_embed(self) -> discord.Embed:
        panel = get_panel(self.guild_id, self.panel_id)
        name = panel["conteudo"].get("title") or panel["conteudo"].get("texto") or f"Painel #{self.panel_id}"
        return create_embed(
            title=f"⚙️ Configurando Painel (ID: {self.panel_id})",
            description=f"**Painel:** `{name}`\n**Tipo:** {panel['tipo_conteudo'].upper()} | **Componente:** {panel['tipo_componente'].upper()}\n\nEscolha o que configurar neste painel:",
            color=EMBED_COLOR
        )

    @discord.ui.select(
        placeholder="Selecione a ação...",
        options=[
            discord.SelectOption(label="Configurar Conteúdo/Embed", description="Editar textos, imagens e formato do painel", emoji="📝", value="content"),
            discord.SelectOption(label="Configurar Componentes", description="Gerenciar opções de botões ou dropdown", emoji="🔘", value="components"),
            discord.SelectOption(label="Outras Configurações", description="Cargos de suporte, categorias e regras do painel", emoji="⚙️", value="other"),
            discord.SelectOption(label="Deletar Painel", description="Excluir este painel permanentemente", emoji="🗑️", value="delete")
        ]
    )
    async def select_option(self, interaction: discord.Interaction, select: Select):
        try:
            val = select.values[0]
            panel = get_panel(self.guild_id, self.panel_id)

            if val == "content":
                if panel["tipo_conteudo"] == "mensagem":
                    modal = SimpleMessageModal(self.guild_id, self.panel_id, panel["conteudo"].get("texto", ""))
                    await interaction.response.send_modal(modal)
                else:
                    view = EmbedEditorView(self.guild_id, self.panel_id)
                    await interaction.response.edit_message(embed=view.get_embed(), view=view)

            elif val == "components":
                view = OptionsManagerView(self.guild_id, self.panel_id)
                await interaction.response.edit_message(embed=view.get_embed(), view=view)

            elif val == "other":
                view = PanelSettingsView(self.guild_id, self.panel_id)
                await interaction.response.edit_message(embed=view.get_embed(), view=view)

            elif val == "delete":
                view = ConfirmDeletePanelView(self.guild_id, self.panel_id)
                embed = create_embed(
                    title="⚠️ Confirmação de Exclusão",
                    description=f"Você tem certeza que deseja excluir o painel **ID: {self.panel_id}**? Essa ação não pode ser desfeita.",
                    color=ERROR_COLOR
                )
                await interaction.response.edit_message(embed=embed, view=view)

        except Exception as e:
            print(f"[TICKET_SYSTEM] erro em panel options menu: {e}", flush=True)

    @discord.ui.button(label="< Voltar", style=discord.ButtonStyle.secondary, row=1)
    async def back_button(self, interaction: discord.Interaction, button: Button):
        view = PanelListView(self.guild_id)
        await interaction.response.edit_message(embed=view.get_embed(), view=view)

class SimpleMessageModal(Modal, title="Editar Texto da Mensagem"):
    texto = TextInput(label="Conteúdo da Mensagem", style=discord.TextStyle.paragraph, max_length=2000, required=True)

    def __init__(self, guild_id: int, panel_id: int, current_text: str):
        super().__init__()
        self.guild_id = guild_id
        self.panel_id = panel_id
        self.texto.default = current_text

    async def on_submit(self, interaction: discord.Interaction):
        try:
            panel = get_panel(self.guild_id, self.panel_id)
            panel["conteudo"]["texto"] = self.texto.value
            update_panel(self.guild_id, self.panel_id, panel)
            view = PanelOptionsMenuView(self.guild_id, self.panel_id)
            await interaction.response.edit_message(embed=view.get_embed(), view=view)
        except Exception as e:
            print(f"[TICKET_SYSTEM] erro ao salvar modal de texto: {e}", flush=True)

class ConfirmDeletePanelView(View):
    def __init__(self, guild_id: int, panel_id: int):
        super().__init__(timeout=300)
        self.guild_id = guild_id
        self.panel_id = panel_id

    @discord.ui.button(label="Sim, Excluir", style=discord.ButtonStyle.danger, emoji="🗑️")
    async def confirm(self, interaction: discord.Interaction, button: Button):
        delete_panel(self.guild_id, self.panel_id)
        view = PanelListView(self.guild_id)
        embed = create_embed(title="✅ Painel Excluído", description=f"O painel ID {self.panel_id} foi removido.", color=SUCCESS_COLOR)
        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(label="< Cancelar", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: Button):
        view = PanelOptionsMenuView(self.guild_id, self.panel_id)
        await interaction.response.edit_message(embed=view.get_embed(), view=view)

# ============================================================
# ETAPA 5 — CONFIGURAR EMBED (EDITOR COMPLETO)
# ============================================================

class EmbedEditorView(View):
    def __init__(self, guild_id: int, panel_id: int):
        super().__init__(timeout=300)
        self.guild_id = guild_id
        self.panel_id = panel_id

    def get_embed(self) -> discord.Embed:
        panel = get_panel(self.guild_id, self.panel_id)
        c = panel["conteudo"]

        def check(val):
            return "✅" if val else "❌"

        def trunc(val, limit=30):
            if not val:
                return "*Não configurado*"
            s = str(val)
            return f"`{s[:limit]}...`" if len(s) > limit else f"`{s}`"

        status_text = (
            f"📌 **Geral**\n"
            f"• Título: {check(c.get('title'))} {trunc(c.get('title'))}\n"
            f"• Descrição: {check(c.get('description'))} {trunc(c.get('description'))}\n"
            f"• Cor Hex: `#{c.get('color', '3D5A80').lstrip('#')}`\n"
            f"• Link Título: {check(c.get('url'))} {trunc(c.get('url'))}\n"
            f"• Timestamp: {check(c.get('timestamp'))}\n\n"
            f"👤 **Autor**\n"
            f"• Nome: {check(c.get('author', {}).get('name'))} {trunc(c.get('author', {}).get('name'))}\n"
            f"• Ícone: {check(c.get('author', {}).get('icon_url'))} {trunc(c.get('author', {}).get('icon_url'))}\n"
            f"• URL: {check(c.get('author', {}).get('url'))} {trunc(c.get('author', {}).get('url'))}\n\n"
            f"🖼️ **Mídia & Rodapé**\n"
            f"• Thumbnail: {check(c.get('thumbnail_url'))} {trunc(c.get('thumbnail_url'))}\n"
            f"• Imagem: {check(c.get('image_url'))} {trunc(c.get('image_url'))}\n"
            f"• Rodapé: {check(c.get('footer', {}).get('text'))} {trunc(c.get('footer', {}).get('text'))}\n\n"
            f"📑 **Campos (Fields)**: `{len(c.get('fields', []))}/25`"
        )

        return create_embed(title=f"🖼️ Editor de Embed — Painel ID: {self.panel_id}", description=status_text, color=EMBED_COLOR)

    @discord.ui.button(label="Título", style=discord.ButtonStyle.secondary, row=0)
    async def edit_title(self, interaction: discord.Interaction, button: Button):
        c = get_panel(self.guild_id, self.panel_id)["conteudo"]
        await interaction.response.send_modal(EmbedFieldModal(self.guild_id, self.panel_id, "title", "Editar Título", c.get("title", "")))

    @discord.ui.button(label="Descrição", style=discord.ButtonStyle.secondary, row=0)
    async def edit_desc(self, interaction: discord.Interaction, button: Button):
        c = get_panel(self.guild_id, self.panel_id)["conteudo"]
        await interaction.response.send_modal(EmbedFieldModal(self.guild_id, self.panel_id, "description", "Editar Descrição", c.get("description", ""), multiline=True))

    @discord.ui.button(label="Link Título (URL)", style=discord.ButtonStyle.secondary, row=0)
    async def edit_url(self, interaction: discord.Interaction, button: Button):
        c = get_panel(self.guild_id, self.panel_id)["conteudo"]
        await interaction.response.send_modal(EmbedFieldModal(self.guild_id, self.panel_id, "url", "Link do Título", c.get("url", "")))

    @discord.ui.button(label="Cor (HEX)", style=discord.ButtonStyle.secondary, row=0)
    async def edit_color(self, interaction: discord.Interaction, button: Button):
        c = get_panel(self.guild_id, self.panel_id)["conteudo"]
        await interaction.response.send_modal(EmbedFieldModal(self.guild_id, self.panel_id, "color", "Cor da Embed (ex: #3D5A80)", c.get("color", "#3D5A80")))

    @discord.ui.button(label="Timestamp (Toggle)", style=discord.ButtonStyle.secondary, row=0)
    async def toggle_timestamp(self, interaction: discord.Interaction, button: Button):
        panel = get_panel(self.guild_id, self.panel_id)
        panel["conteudo"]["timestamp"] = not panel["conteudo"].get("timestamp", False)
        update_panel(self.guild_id, self.panel_id, panel)
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

    @discord.ui.button(label="Thumbnail URL", style=discord.ButtonStyle.secondary, row=1)
    async def edit_thumb(self, interaction: discord.Interaction, button: Button):
        c = get_panel(self.guild_id, self.panel_id)["conteudo"]
        await interaction.response.send_modal(EmbedFieldModal(self.guild_id, self.panel_id, "thumbnail_url", "URL da Miniatura", c.get("thumbnail_url", "")))

    @discord.ui.button(label="Imagem URL", style=discord.ButtonStyle.secondary, row=1)
    async def edit_image(self, interaction: discord.Interaction, button: Button):
        c = get_panel(self.guild_id, self.panel_id)["conteudo"]
        await interaction.response.send_modal(EmbedFieldModal(self.guild_id, self.panel_id, "image_url", "URL da Imagem Principal", c.get("image_url", "")))

    @discord.ui.button(label="Texto Autor", style=discord.ButtonStyle.secondary, row=1)
    async def edit_author_name(self, interaction: discord.Interaction, button: Button):
        c = get_panel(self.guild_id, self.panel_id)["conteudo"]
        await interaction.response.send_modal(EmbedFieldModal(self.guild_id, self.panel_id, "author_name", "Nome do Autor", c.get("author", {}).get("name", "")))

    @discord.ui.button(label="Ícone Autor", style=discord.ButtonStyle.secondary, row=1)
    async def edit_author_icon(self, interaction: discord.Interaction, button: Button):
        c = get_panel(self.guild_id, self.panel_id)["conteudo"]
        await interaction.response.send_modal(EmbedFieldModal(self.guild_id, self.panel_id, "author_icon_url", "URL do Ícone do Autor", c.get("author", {}).get("icon_url", "")))

    @discord.ui.button(label="URL Autor", style=discord.ButtonStyle.secondary, row=1)
    async def edit_author_url(self, interaction: discord.Interaction, button: Button):
        c = get_panel(self.guild_id, self.panel_id)["conteudo"]
        await interaction.response.send_modal(EmbedFieldModal(self.guild_id, self.panel_id, "author_url", "URL do Autor", c.get("author", {}).get("url", "")))

    @discord.ui.button(label="Texto Rodapé", style=discord.ButtonStyle.secondary, row=2)
    async def edit_footer_text(self, interaction: discord.Interaction, button: Button):
        c = get_panel(self.guild_id, self.panel_id)["conteudo"]
        await interaction.response.send_modal(EmbedFieldModal(self.guild_id, self.panel_id, "footer_text", "Texto do Rodapé", c.get("footer", {}).get("text", "")))

    @discord.ui.button(label="Gerenciar Fields", style=discord.ButtonStyle.primary, row=2)
    async def manage_fields(self, interaction: discord.Interaction, button: Button):
        view = ManageFieldsView(self.guild_id, self.panel_id)
        await interaction.response.edit_message(embed=view.get_embed(), view=view)

    @discord.ui.button(label="Ver Prévia", style=discord.ButtonStyle.secondary, row=2)
    async def preview(self, interaction: discord.Interaction, button: Button):
        panel = get_panel(self.guild_id, self.panel_id)
        embed = build_panel_embed(panel["conteudo"])
        await interaction.response.send_message("🔍 **Prévia do Embed:**", embed=embed, ephemeral=True)

    @discord.ui.button(label="Salvar Configuração", style=discord.ButtonStyle.success, row=2)
    async def save(self, interaction: discord.Interaction, button: Button):
        view = PanelOptionsMenuView(self.guild_id, self.panel_id)
        await interaction.response.edit_message(embed=view.get_embed(), view=view)

    @discord.ui.button(label="< Voltar", style=discord.ButtonStyle.secondary, row=2)
    async def back(self, interaction: discord.Interaction, button: Button):
        view = PanelOptionsMenuView(self.guild_id, self.panel_id)
        await interaction.response.edit_message(embed=view.get_embed(), view=view)

class EmbedFieldModal(Modal):
    def __init__(self, guild_id: int, panel_id: int, field_key: str, title: str, current_value: str = "", multiline: bool = False):
        super().__init__(title=title[:45])
        self.guild_id = guild_id
        self.panel_id = panel_id
        self.field_key = field_key

        style = discord.TextStyle.paragraph if multiline else discord.TextStyle.short
        self.val_input = TextInput(label=title[:45], style=style, required=False, max_length=4000 if multiline else 256)
        self.val_input.default = current_value or ""
        self.add_item(self.val_input)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            panel = get_panel(self.guild_id, self.panel_id)
            c = panel["conteudo"]
            val = self.val_input.value.strip() or None

            if self.field_key in ["title", "description", "color", "url", "thumbnail_url", "image_url"]:
                c[self.field_key] = val
            elif self.field_key.startswith("author_"):
                k = self.field_key.replace("author_", "")
                if "author" not in c or not isinstance(c["author"], dict):
                    c["author"] = {}
                c["author"][k] = val
            elif self.field_key.startswith("footer_"):
                k = self.field_key.replace("footer_", "")
                if "footer" not in c or not isinstance(c["footer"], dict):
                    c["footer"] = {}
                c["footer"][k] = val

            panel["conteudo"] = c
            update_panel(self.guild_id, self.panel_id, panel)
            view = EmbedEditorView(self.guild_id, self.panel_id)
            await interaction.response.edit_message(embed=view.get_embed(), view=view)
        except Exception as e:
            print(f"[TICKET_SYSTEM] erro ao salvar embed field modal: {e}", flush=True)

class ManageFieldsView(View):
    def __init__(self, guild_id: int, panel_id: int):
        super().__init__(timeout=300)
        self.guild_id = guild_id
        self.panel_id = panel_id
        self._build_select()

    def get_embed(self) -> discord.Embed:
        panel = get_panel(self.guild_id, self.panel_id)
        fields = panel["conteudo"].get("fields", [])
        text = f"Total de Fields: `{len(fields)}/25`\n\n"
        for i, f in enumerate(fields, 1):
            inline_str = " (Inline)" if f.get("inline") else ""
            text += f"**{i}. {f.get('name')}**{inline_str}: `{f.get('value')[:40]}`\n"
        if not fields:
            text += "*Nenhum field configurado.*"
        return create_embed(title="📑 Gerenciar Fields", description=text, color=EMBED_COLOR)

    def _build_select(self):
        panel = get_panel(self.guild_id, self.panel_id)
        fields = panel["conteudo"].get("fields", [])
        if fields:
            options = [discord.SelectOption(label=f"{i+1}. {f['name'][:50]}", value=str(i)) for i, f in enumerate(fields)]
            select = Select(placeholder="Selecione um field para remover...", options=options, custom_id="field_remove_select")
            select.callback = self.on_remove_field
            self.add_item(select)

    async def on_remove_field(self, interaction: discord.Interaction):
        try:
            idx = int(interaction.data["values"][0])
            panel = get_panel(self.guild_id, self.panel_id)
            fields = panel["conteudo"].get("fields", [])
            if 0 <= idx < len(fields):
                fields.pop(idx)
                panel["conteudo"]["fields"] = fields
                update_panel(self.guild_id, self.panel_id, panel)
            view = ManageFieldsView(self.guild_id, self.panel_id)
            await interaction.response.edit_message(embed=view.get_embed(), view=view)
        except Exception as e:
            print(f"[TICKET_SYSTEM] erro ao remover field: {e}", flush=True)

    @discord.ui.button(label="➕ Adicionar Field", style=discord.ButtonStyle.success)
    async def add_field(self, interaction: discord.Interaction, button: Button):
        panel = get_panel(self.guild_id, self.panel_id)
        if len(panel["conteudo"].get("fields", [])) >= 25:
            return await interaction.response.send_message("❌ Máximo de 25 fields atingido.", ephemeral=True)
        await interaction.response.send_modal(AddFieldModal(self.guild_id, self.panel_id))

    @discord.ui.button(label="< Voltar", style=discord.ButtonStyle.secondary)
    async def back(self, interaction: discord.Interaction, button: Button):
        view = EmbedEditorView(self.guild_id, self.panel_id)
        await interaction.response.edit_message(embed=view.get_embed(), view=view)

class AddFieldModal(Modal, title="Adicionar Field"):
    name = TextInput(label="Nome do Field", max_length=256, required=True)
    value = TextInput(label="Valor do Field", style=discord.TextStyle.paragraph, max_length=1024, required=True)
    inline = TextInput(label="Inline? (sim/nao)", max_length=5, required=False, default="nao")

    def __init__(self, guild_id: int, panel_id: int):
        super().__init__()
        self.guild_id = guild_id
        self.panel_id = panel_id

    async def on_submit(self, interaction: discord.Interaction):
        try:
            panel = get_panel(self.guild_id, self.panel_id)
            fields = panel["conteudo"].get("fields", [])
            is_inline = self.inline.value.strip().lower() in ["sim", "true", "s", "1"]
            fields.append({"name": self.name.value, "value": self.value.value, "inline": is_inline})
            panel["conteudo"]["fields"] = fields
            update_panel(self.guild_id, self.panel_id, panel)
            view = ManageFieldsView(self.guild_id, self.panel_id)
            await interaction.response.edit_message(embed=view.get_embed(), view=view)
        except Exception as e:
            print(f"[TICKET_SYSTEM] erro ao adicionar field: {e}", flush=True)

# ============================================================
# ETAPA 6 — CONFIGURAR COMPONENTES (OPÇÕES)
# ============================================================

class OptionsManagerView(View):
    def __init__(self, guild_id: int, panel_id: int):
        super().__init__(timeout=300)
        self.guild_id = guild_id
        self.panel_id = panel_id
        self._build_components()

    def get_embed(self) -> discord.Embed:
        panel = get_panel(self.guild_id, self.panel_id)
        options = panel.get("options", [])
        title_comp = "Componentes" if panel["tipo_componente"] == "botao" else "Dropdown"
        text = f"Gerenciar Opções do Painel ({len(options)}/25 configuradas):\n\n"
        for o in options:
            emoji_str = f"{o.get('emoji')} " if o.get('emoji') else ""
            cat_str = f" | Cat: `{o.get('categoria_vinculada')}`" if o.get('categoria_vinculada') else ""
            text += f"• **ID {o['id']}**: {emoji_str}`{o['label']}`{cat_str}\n"
        if not options:
            text += "*Nenhuma opção configurada ainda. Clique em Criar Nova Opção.*"
        return create_embed(title=f"🔘 Gerenciar Opções ({title_comp})", description=text, color=EMBED_COLOR)

    def _build_components(self):
        self.clear_items()
        panel = get_panel(self.guild_id, self.panel_id)
        options = panel.get("options", [])

        if options:
            select_options = [
                discord.SelectOption(label=f"ID {o['id']}: {o['label'][:50]}", value=str(o["id"]), emoji=o.get("emoji") or "📄", description=o.get("description") or None)
                for o in options
            ]
            select = Select(placeholder="Editar Opção (N/25)...", options=select_options, custom_id="option_edit_select")
            select.callback = self.on_select_option
            self.add_item(select)

        create_btn = Button(label="➕ Criar Nova Opção", style=discord.ButtonStyle.success)
        create_btn.callback = self.on_create_option
        self.add_item(create_btn)

        if options:
            delete_btn = Button(label="🗑️ Excluir Opções", style=discord.ButtonStyle.danger)
            delete_btn.callback = self.on_delete_options_screen
            self.add_item(delete_btn)

            reorder_btn = Button(label="↕️ Organizar", style=discord.ButtonStyle.secondary)
            reorder_btn.callback = self.on_reorder_screen
            self.add_item(reorder_btn)

        save_btn = Button(label="💾 Salvar Componentes", style=discord.ButtonStyle.primary)
        save_btn.callback = self.on_save
        self.add_item(save_btn)

        back_btn = Button(label="< Voltar", style=discord.ButtonStyle.secondary)
        back_btn.callback = self.on_back
        self.add_item(back_btn)

    async def on_select_option(self, interaction: discord.Interaction):
        try:
            opt_id = int(interaction.data["values"][0])
            view = EditOptionView(self.guild_id, self.panel_id, opt_id)
            await interaction.response.edit_message(embed=view.get_embed(), view=view)
        except Exception as e:
            print(f"[TICKET_SYSTEM] erro ao selecionar opcao: {e}", flush=True)

    async def on_create_option(self, interaction: discord.Interaction):
        try:
            panel = get_panel(self.guild_id, self.panel_id)
            options = panel.get("options", [])
            if len(options) >= 25:
                return await interaction.response.send_message("❌ Máximo de 25 opções atingido.", ephemeral=True)
            next_id = max([o["id"] for o in options], default=0) + 1
            new_opt = {
                "id": next_id,
                "label": f"Nova Opção {next_id}",
                "emoji": "📄",
                "description": None,
                "categoria_vinculada": None
            }
            options.append(new_opt)
            panel["options"] = options
            update_panel(self.guild_id, self.panel_id, panel)

            view = EditOptionView(self.guild_id, self.panel_id, next_id)
            await interaction.response.edit_message(embed=view.get_embed(), view=view)
        except Exception as e:
            print(f"[TICKET_SYSTEM] erro ao criar opcao: {e}", flush=True)

    async def on_delete_options_screen(self, interaction: discord.Interaction):
        view = DeleteOptionsView(self.guild_id, self.panel_id)
        await interaction.response.edit_message(embed=view.get_embed(), view=view)

    async def on_reorder_screen(self, interaction: discord.Interaction):
        view = ReorderOptionsView(self.guild_id, self.panel_id)
        await interaction.response.edit_message(embed=view.get_embed(), view=view)

    async def on_save(self, interaction: discord.Interaction):
        embed = create_embed(title="✅ Sucesso", description="Componentes salvos com sucesso!", color=SUCCESS_COLOR)
        view = SingleBackButton(parent_view_factory=lambda: PanelOptionsMenuView(self.guild_id, self.panel_id))
        await interaction.response.edit_message(embed=embed, view=view)

    async def on_back(self, interaction: discord.Interaction):
        view = PanelOptionsMenuView(self.guild_id, self.panel_id)
        await interaction.response.edit_message(embed=view.get_embed(), view=view)

class EditOptionView(View):
    def __init__(self, guild_id: int, panel_id: int, option_id: int):
        super().__init__(timeout=300)
        self.guild_id = guild_id
        self.panel_id = panel_id
        self.option_id = option_id

    def get_embed(self) -> discord.Embed:
        panel = get_panel(self.guild_id, self.panel_id)
        opt = next((o for o in panel.get("options", []) if o["id"] == self.option_id), None)
        if not opt:
            return create_embed(title="❌ Erro", description="Opção não encontrada.", color=ERROR_COLOR)

        emoji_str = opt.get("emoji") or "*Nenhum*"
        desc_str = opt.get("description") or "*Nenhuma*"
        cat_str = opt.get("categoria_vinculada") or "*Nenhuma*"

        return create_embed(
            title=f"✏️ Editando Opção (ID: {self.option_id})",
            description=f"**Label:** `{opt.get('label')}`\n**Emoji:** {emoji_str}\n**Descrição:** `{desc_str}`\n**Categoria Vinculada:** `{cat_str}`",
            color=EMBED_COLOR
        )

    @discord.ui.button(label="Alterar Label", style=discord.ButtonStyle.secondary)
    async def edit_label(self, interaction: discord.Interaction, button: Button):
        panel = get_panel(self.guild_id, self.panel_id)
        opt = next((o for o in panel.get("options", []) if o["id"] == self.option_id), {})
        await interaction.response.send_modal(EditOptionModal(self.guild_id, self.panel_id, self.option_id, "label", "Novo Label", opt.get("label", "")))

    @discord.ui.button(label="Alterar Emoji", style=discord.ButtonStyle.secondary)
    async def edit_emoji(self, interaction: discord.Interaction, button: Button):
        panel = get_panel(self.guild_id, self.panel_id)
        opt = next((o for o in panel.get("options", []) if o["id"] == self.option_id), {})
        await interaction.response.send_modal(EditOptionModal(self.guild_id, self.panel_id, self.option_id, "emoji", "Emoji (Unicode ou Nome)", opt.get("emoji", "")))

    @discord.ui.button(label="Alterar Descrição", style=discord.ButtonStyle.secondary)
    async def edit_desc(self, interaction: discord.Interaction, button: Button):
        panel = get_panel(self.guild_id, self.panel_id)
        opt = next((o for o in panel.get("options", []) if o["id"] == self.option_id), {})
        await interaction.response.send_modal(EditOptionModal(self.guild_id, self.panel_id, self.option_id, "description", "Descrição", opt.get("description", "")))

    @discord.ui.button(label="< Voltar", style=discord.ButtonStyle.secondary)
    async def back(self, interaction: discord.Interaction, button: Button):
        view = OptionsManagerView(self.guild_id, self.panel_id)
        await interaction.response.edit_message(embed=view.get_embed(), view=view)

class EditOptionModal(Modal):
    def __init__(self, guild_id: int, panel_id: int, option_id: int, key: str, title: str, current_value: str = ""):
        super().__init__(title=title[:45])
        self.guild_id = guild_id
        self.panel_id = panel_id
        self.option_id = option_id
        self.key = key

        self.input_val = TextInput(label=title[:45], required=False, max_length=100)
        self.input_val.default = current_value or ""
        self.add_item(self.input_val)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            panel = get_panel(self.guild_id, self.panel_id)
            for o in panel.get("options", []):
                if o["id"] == self.option_id:
                    o[self.key] = self.input_val.value.strip() or None
                    break
            update_panel(self.guild_id, self.panel_id, panel)
            view = EditOptionView(self.guild_id, self.panel_id, self.option_id)
            await interaction.response.edit_message(embed=view.get_embed(), view=view)
        except Exception as e:
            print(f"[TICKET_SYSTEM] erro ao salvar edit option modal: {e}", flush=True)

class DeleteOptionsView(View):
    def __init__(self, guild_id: int, panel_id: int):
        super().__init__(timeout=300)
        self.guild_id = guild_id
        self.panel_id = panel_id
        self._build_select()

    def get_embed(self) -> discord.Embed:
        return create_embed(title="🗑️ Selecione a Opção para excluir", description="Escolha uma opção no menu abaixo:", color=ERROR_COLOR)

    def _build_select(self):
        panel = get_panel(self.guild_id, self.panel_id)
        options = panel.get("options", [])
        if options:
            select_options = [discord.SelectOption(label=f"ID {o['id']}: {o['label'][:50]}", value=str(o["id"])) for o in options]
            select = Select(placeholder="Selecione para excluir...", options=select_options, custom_id="delete_opt_select")
            select.callback = self.on_delete_select
            self.add_item(select)
        back_btn = Button(label="< Voltar", style=discord.ButtonStyle.secondary)
        back_btn.callback = self.on_back
        self.add_item(back_btn)

    async def on_delete_select(self, interaction: discord.Interaction):
        try:
            opt_id = int(interaction.data["values"][0])
            panel = get_panel(self.guild_id, self.panel_id)
            panel["options"] = [o for o in panel.get("options", []) if o["id"] != opt_id]
            update_panel(self.guild_id, self.panel_id, panel)

            view = OptionsManagerView(self.guild_id, self.panel_id)
            await interaction.response.edit_message(embed=view.get_embed(), view=view)
        except Exception as e:
            print(f"[TICKET_SYSTEM] erro ao deletar opcao: {e}", flush=True)

    async def on_back(self, interaction: discord.Interaction):
        view = OptionsManagerView(self.guild_id, self.panel_id)
        await interaction.response.edit_message(embed=view.get_embed(), view=view)

class ReorderOptionsView(View):
    def __init__(self, guild_id: int, panel_id: int, selected_idx: int = 0):
        super().__init__(timeout=300)
        self.guild_id = guild_id
        self.panel_id = panel_id
        self.selected_idx = selected_idx
        self._build_components()

    def get_embed(self) -> discord.Embed:
        panel = get_panel(self.guild_id, self.panel_id)
        options = panel.get("options", [])
        text = "Use os botões para mover a opção selecionada para cima ou para baixo:\n\n"
        for i, o in enumerate(options):
            pointer = "➡️ " if i == self.selected_idx else "   "
            text += f"{pointer}**{i+1}.** `{o['label']}` (ID: {o['id']})\n"
        return create_embed(title="↕️ Organizar Componentes", description=text, color=EMBED_COLOR)

    def _build_components(self):
        self.clear_items()
        panel = get_panel(self.guild_id, self.panel_id)
        options = panel.get("options", [])

        if options:
            select_options = [discord.SelectOption(label=f"{i+1}. {o['label'][:50]}", value=str(i), default=(i == self.selected_idx)) for i, o in enumerate(options)]
            select = Select(placeholder="Selecione um item para mover...", options=select_options, custom_id="reorder_select")
            select.callback = self.on_select_item
            self.add_item(select)

        up_btn = Button(label="▲ Mover Para Cima", style=discord.ButtonStyle.primary)
        up_btn.callback = self.on_move_up
        self.add_item(up_btn)

        down_btn = Button(label="▼ Mover Para Baixo", style=discord.ButtonStyle.primary)
        down_btn.callback = self.on_move_down
        self.add_item(down_btn)

        back_btn = Button(label="< Voltar", style=discord.ButtonStyle.secondary)
        back_btn.callback = self.on_back
        self.add_item(back_btn)

    async def on_select_item(self, interaction: discord.Interaction):
        self.selected_idx = int(interaction.data["values"][0])
        self._build_components()
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

    async def on_move_up(self, interaction: discord.Interaction):
        if self.selected_idx > 0:
            panel = get_panel(self.guild_id, self.panel_id)
            opts = panel.get("options", [])
            opts[self.selected_idx], opts[self.selected_idx - 1] = opts[self.selected_idx - 1], opts[self.selected_idx]
            panel["options"] = opts
            update_panel(self.guild_id, self.panel_id, panel)
            self.selected_idx -= 1
        self._build_components()
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

    async def on_move_down(self, interaction: discord.Interaction):
        panel = get_panel(self.guild_id, self.panel_id)
        opts = panel.get("options", [])
        if self.selected_idx < len(opts) - 1:
            opts[self.selected_idx], opts[self.selected_idx + 1] = opts[self.selected_idx + 1], opts[self.selected_idx]
            panel["options"] = opts
            update_panel(self.guild_id, self.panel_id, panel)
            self.selected_idx += 1
        self._build_components()
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

    async def on_back(self, interaction: discord.Interaction):
        view = OptionsManagerView(self.guild_id, self.panel_id)
        await interaction.response.edit_message(embed=view.get_embed(), view=view)

# ============================================================
# ETAPA 7 — CONFIGURAÇÕES GLOBAIS
# ============================================================

class GlobalSettingsView(View):
    def __init__(self, guild_id: int):
        super().__init__(timeout=300)
        self.guild_id = guild_id

    def get_embed(self) -> discord.Embed:
        glob = get_global_ticket_settings(self.guild_id)
        cfg = get_guild_config(self.guild_id)
        staff_roles = ", ".join([f"<@&{r}>" for r in glob.get("staff_role_ids", [])]) or "*Nenhum*"
        cat_ch = f"<#{glob.get('ticket_category_channel_id')}>" if glob.get("ticket_category_channel_id") else "*Nenhuma*"
        tlog_ch = f"<#{cfg.get('ticket_log_channel_id')}>" if cfg.get("ticket_log_channel_id") else "*Não configurado*"

        text = (
            "Aqui você pode configurar as configurações globais do sistema de tickets! "
            "Essas configurações serão aplicadas para todos os painéis do servidor.\n\n"
            f"• **Cargos de Staff Global:** {staff_roles}\n"
            f"• **Categoria de Canal Global:** {cat_ch}\n"
            f"• **Canal de Logs de Ticket:** {tlog_ch}"
        )
        return create_embed(title="⚙️ Configurações Globais", description=text, color=EMBED_COLOR)

    @discord.ui.select(
        placeholder="Selecione uma categoria para começar...",
        options=[
            discord.SelectOption(label="Funções sobre o Ticket", description="Cargos de suporte e categoria de canal globais", emoji="🛠️", value="functions"),
            discord.SelectOption(label="Logs de Ticket", description="Canal para logs de criação e fechamento de tickets", emoji="📋", value="logs"),
            discord.SelectOption(label="Funções Premium", description="Recursos adicionais premium", emoji="⭐", value="premium"),
            discord.SelectOption(label="Sistema de IA", description="Atendimento automatizado por IA", emoji="🤖", value="ai")
        ]
    )
    async def select_category(self, interaction: discord.Interaction, select: Select):
        val = select.values[0]
        if val == "functions":
            view = GlobalTicketFunctionsView(self.guild_id)
            await interaction.response.edit_message(embed=view.get_embed(), view=view)
        elif val == "logs":
            view = GlobalTicketLogsView(self.guild_id)
            await interaction.response.edit_message(embed=view.get_embed(), view=view)
        elif val in ["premium", "ai"]:
            embed = create_embed(title="⭐ Em breve", description="Esta funcionalidade estará disponível em atualizações futuras.", color=discord.Color.gold())
            view = SingleBackButton(parent_view_factory=lambda: GlobalSettingsView(self.guild_id))
            await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(label="< Voltar", style=discord.ButtonStyle.secondary, row=1)
    async def back(self, interaction: discord.Interaction, button: Button):
        view = RootMenuView(self.guild_id)
        await interaction.response.edit_message(embed=view.get_embed(), view=view)

class GlobalTicketFunctionsView(View):
    def __init__(self, guild_id: int):
        super().__init__(timeout=300)
        self.guild_id = guild_id

    def get_embed(self) -> discord.Embed:
        glob = get_global_ticket_settings(self.guild_id)
        staff_roles = ", ".join([f"<@&{r}>" for r in glob.get("staff_role_ids", [])]) or "*Nenhum*"
        cat_ch = f"<#{glob.get('ticket_category_channel_id')}>" if glob.get("ticket_category_channel_id") else "*Nenhuma*"
        text = f"⚙️ **Funções Globais sobre o Ticket**\n\n• **Cargos de Staff:** {staff_roles}\n• **Categoria de Destino:** {cat_ch}"
        return create_embed(title="🛠️ Funções Globais do Ticket", description=text, color=EMBED_COLOR)

    @discord.ui.select(cls=RoleSelect, placeholder="Selecione os cargos de Staff Globais...", min_values=0, max_values=25, custom_id="global_staff_roles")
    async def select_staff_roles(self, interaction: discord.Interaction, select: RoleSelect):
        try:
            glob = get_global_ticket_settings(self.guild_id)
            glob["staff_role_ids"] = [r.id for r in select.values]
            update_global_ticket_settings(self.guild_id, glob)

            embed = create_embed(title="✅ Sucesso", description="Configurações salvas com sucesso!", color=SUCCESS_COLOR)
            view = SingleBackButton(parent_view_factory=lambda: GlobalTicketFunctionsView(self.guild_id))
            await interaction.response.edit_message(embed=embed, view=view)
        except Exception as e:
            print(f"[TICKET_SYSTEM] erro ao definir cargos de staff globais: {e}", flush=True)

    @discord.ui.select(cls=ChannelSelect, channel_types=[discord.ChannelType.category], placeholder="Selecione a Categoria de Canal Global...", min_values=0, max_values=1, custom_id="global_category_ch")
    async def select_category_channel(self, interaction: discord.Interaction, select: ChannelSelect):
        try:
            glob = get_global_ticket_settings(self.guild_id)
            glob["ticket_category_channel_id"] = select.values[0].id if select.values else None
            update_global_ticket_settings(self.guild_id, glob)

            embed = create_embed(title="✅ Sucesso", description="Configurações salvas com sucesso!", color=SUCCESS_COLOR)
            view = SingleBackButton(parent_view_factory=lambda: GlobalTicketFunctionsView(self.guild_id))
            await interaction.response.edit_message(embed=embed, view=view)
        except Exception as e:
            print(f"[TICKET_SYSTEM] erro ao definir categoria global: {e}", flush=True)

    @discord.ui.button(label="< Voltar", style=discord.ButtonStyle.secondary, row=2)
    async def back(self, interaction: discord.Interaction, button: Button):
        view = GlobalSettingsView(self.guild_id)
        await interaction.response.edit_message(embed=view.get_embed(), view=view)

class GlobalTicketLogsView(View):
    def __init__(self, guild_id: int):
        super().__init__(timeout=300)
        self.guild_id = guild_id

    def get_embed(self) -> discord.Embed:
        cfg = get_guild_config(self.guild_id)
        ch_str = f"<#{cfg.get('ticket_log_channel_id')}>" if cfg.get("ticket_log_channel_id") else "*Não configurado*"
        text = f"📋 **Canal de Logs de Tickets**\n\nCanal Atual: {ch_str}\n\nEscolha um canal existente abaixo ou crie um automaticamente para a Staff."
        return create_embed(title="📋 Logs de Ticket", description=text, color=EMBED_COLOR)

    @discord.ui.select(cls=ChannelSelect, channel_types=[discord.ChannelType.text], placeholder="Selecione o canal de logs de ticket...", min_values=0, max_values=1, row=0)
    async def select_tlog_ch(self, interaction: discord.Interaction, select: ChannelSelect):
        try:
            ch_id = select.values[0].id if select.values else None
            update_guild_config(self.guild_id, "ticket_log_channel_id", ch_id)
            await interaction.response.edit_message(embed=self.get_embed(), view=self)
        except Exception as e:
            print(f"[TICKET_LOG_SELECT_ERROR] {e}", flush=True)

    @discord.ui.button(label="Criar Canal de Logs Automaticamente", style=discord.ButtonStyle.success, row=1)
    async def create_auto_log_ch(self, interaction: discord.Interaction, button: Button):
        try:
            guild = interaction.guild
            glob = get_global_ticket_settings(self.guild_id)
            staff_roles = glob.get("staff_role_ids", [])

            overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False)
            }
            for rid in staff_roles:
                role = guild.get_role(rid)
                if role:
                    overwrites[role] = discord.PermissionOverwrite(view_channel=True, read_message_history=True)

            ch = await guild.create_text_channel(name="📋-logs-tickets", overwrites=overwrites, reason="Canal de logs de ticket automático")
            update_guild_config(self.guild_id, "ticket_log_channel_id", ch.id)

            await interaction.response.send_message(f"✅ Canal de logs de tickets criado com sucesso em {ch.mention}!", ephemeral=True)
            await interaction.edit_original_response(embed=self.get_embed(), view=self)
        except Exception as e:
            print(f"[TICKET_LOG_CREATE_ERROR] {e}", flush=True)
            await interaction.response.send_message("❌ Erro ao criar canal de logs.", ephemeral=True)

    @discord.ui.button(label="< Voltar", style=discord.ButtonStyle.secondary, row=1)
    async def back(self, interaction: discord.Interaction, button: Button):
        view = GlobalSettingsView(self.guild_id)
        await interaction.response.edit_message(embed=view.get_embed(), view=view)

# ============================================================
# ETAPA 7-B — OUTRAS CONFIGURAÇÕES (POR PAINEL)
# ============================================================

class PanelSettingsView(View):
    def __init__(self, guild_id: int, panel_id: int):
        super().__init__(timeout=300)
        self.guild_id = guild_id
        self.panel_id = panel_id

    def get_embed(self) -> discord.Embed:
        return create_embed(title="⚙️ Configurar Outras Opções do Painel", description="Escolha o nível de configuração desejado abaixo:", color=EMBED_COLOR)

    @discord.ui.button(label="Configurar Por Painel", style=discord.ButtonStyle.primary, emoji="📋")
    async def config_by_panel(self, interaction: discord.Interaction, button: Button):
        view = PanelSpecificSettingsView(self.guild_id, self.panel_id)
        await interaction.response.edit_message(embed=view.get_embed(), view=view)

    @discord.ui.button(label="Configurar Por Opção", style=discord.ButtonStyle.primary, emoji="🔗")
    async def config_by_option(self, interaction: discord.Interaction, button: Button):
        view = ConfigByOptionView(self.guild_id, self.panel_id)
        await interaction.response.edit_message(embed=view.get_embed(), view=view)

    @discord.ui.button(label="< Voltar", style=discord.ButtonStyle.secondary)
    async def back(self, interaction: discord.Interaction, button: Button):
        view = PanelOptionsMenuView(self.guild_id, self.panel_id)
        await interaction.response.edit_message(embed=view.get_embed(), view=view)

class PanelSpecificSettingsView(View):
    def __init__(self, guild_id: int, panel_id: int):
        super().__init__(timeout=300)
        self.guild_id = guild_id
        self.panel_id = panel_id

    def get_embed(self) -> discord.Embed:
        panel = get_panel(self.guild_id, self.panel_id)
        s = panel.get("settings", {})
        cs = panel.get("component_settings", {})
        staff = ", ".join([f"<@&{r}>" for r in s.get("staff_role_ids", [])]) or "*Global*"
        cat = f"<#{s.get('ticket_category_channel_id')}>" if s.get("ticket_category_channel_id") else "*Global*"
        mentions = ", ".join([f"<@&{r}>" for r in s.get("mention_role_ids", [])]) or "*Nenhum*"

        text = (
            "⚠ **A configuração do painel se sobrepõe às configurações globais.**\n\n"
            f"• **Cargos de Suporte:** {staff}\n"
            f"• **Categoria de Canal:** {cat}\n"
            f"• **Cargos para Menção:** {mentions}\n"
            f"• **Placeholder Dropdown:** `{cs.get('placeholder', 'Selecione o tipo do atendimento')}`\n"
            f"• **Valores de Seleção (Min/Max):** `{cs.get('min_values', 1)}` a `{cs.get('max_values', 1)}`"
        )
        return create_embed(title=f"⚙️ Configurações do Painel ID {self.panel_id}", description=text, color=EMBED_COLOR)

    @discord.ui.select(
        placeholder="Escolha uma opção...",
        options=[
            discord.SelectOption(label="Configurar Cargo de Suporte", value="staff_roles", emoji="👮"),
            discord.SelectOption(label="Configurar Categoria", value="category", emoji="📁"),
            discord.SelectOption(label="Configurar Placeholder", value="placeholder", emoji="💬"),
            discord.SelectOption(label="Configurar Valores de Seleção", value="min_max", emoji="🔢"),
            discord.SelectOption(label="Selecionar cargos para menção", value="mentions", emoji="🔔")
        ]
    )
    async def select_setting(self, interaction: discord.Interaction, select: Select):
        val = select.values[0]

        if val == "staff_roles":
            view = SelectPanelRolesView(self.guild_id, self.panel_id, "staff_role_ids")
            await interaction.response.edit_message(embed=view.get_embed(), view=view)

        elif val == "category":
            view = SelectPanelCategoryView(self.guild_id, self.panel_id)
            await interaction.response.edit_message(embed=view.get_embed(), view=view)

        elif val == "placeholder":
            panel = get_panel(self.guild_id, self.panel_id)
            ph = panel.get("component_settings", {}).get("placeholder", "Selecione o tipo do atendimento")
            await interaction.response.send_modal(PlaceholderModal(self.guild_id, self.panel_id, ph))

        elif val == "min_max":
            panel = get_panel(self.guild_id, self.panel_id)
            cs = panel.get("component_settings", {})
            total_opts = len(panel.get("options", []))
            await interaction.response.send_modal(MinMaxModal(self.guild_id, self.panel_id, cs.get("min_values", 1), cs.get("max_values", 1), total_opts))

        elif val == "mentions":
            view = SelectPanelRolesView(self.guild_id, self.panel_id, "mention_role_ids")
            await interaction.response.edit_message(embed=view.get_embed(), view=view)

    @discord.ui.button(label="< Voltar", style=discord.ButtonStyle.secondary, row=1)
    async def back(self, interaction: discord.Interaction, button: Button):
        view = PanelSettingsView(self.guild_id, self.panel_id)
        await interaction.response.edit_message(embed=view.get_embed(), view=view)

class SelectPanelRolesView(View):
    def __init__(self, guild_id: int, panel_id: int, setting_key: str):
        super().__init__(timeout=300)
        self.guild_id = guild_id
        self.panel_id = panel_id
        self.setting_key = setting_key

    def get_embed(self) -> discord.Embed:
        label = "Cargos de Suporte" if self.setting_key == "staff_role_ids" else "Cargos para Menção"
        return create_embed(
            title=f"🔔 Configurar {label}",
            description="⚠ A configuração do painel se sobrepõe às configurações globais.\n\nSelecione os cargos no menu abaixo:",
            color=EMBED_COLOR
        )

    @discord.ui.select(cls=RoleSelect, placeholder="Selecione os cargos...", min_values=0, max_values=25)
    async def select_roles(self, interaction: discord.Interaction, select: RoleSelect):
        try:
            panel = get_panel(self.guild_id, self.panel_id)
            panel["settings"][self.setting_key] = [r.id for r in select.values]
            update_panel(self.guild_id, self.panel_id, panel)

            embed = create_embed(title="✅ Sucesso", description="Configurações salvas com sucesso!", color=SUCCESS_COLOR)
            view = SingleBackButton(parent_view_factory=lambda: PanelSpecificSettingsView(self.guild_id, self.panel_id))
            await interaction.response.edit_message(embed=embed, view=view)
        except Exception as e:
            print(f"[TICKET_SYSTEM] erro ao definir cargos do painel: {e}", flush=True)

    @discord.ui.button(label="< Voltar", style=discord.ButtonStyle.secondary, row=1)
    async def back(self, interaction: discord.Interaction, button: Button):
        view = PanelSpecificSettingsView(self.guild_id, self.panel_id)
        await interaction.response.edit_message(embed=view.get_embed(), view=view)

class SelectPanelCategoryView(View):
    def __init__(self, guild_id: int, panel_id: int):
        super().__init__(timeout=300)
        self.guild_id = guild_id
        self.panel_id = panel_id

    def get_embed(self) -> discord.Embed:
        return create_embed(
            title="📁 Configurar Categoria de Canal do Painel",
            description="⚠ A configuração do painel se sobrepõe às configurações globais.\n\nSelecione a categoria de destino dos tickets deste painel:",
            color=EMBED_COLOR
        )

    @discord.ui.select(cls=ChannelSelect, channel_types=[discord.ChannelType.category], placeholder="Selecione a Categoria de Canal...", min_values=0, max_values=1)
    async def select_category(self, interaction: discord.Interaction, select: ChannelSelect):
        try:
            panel = get_panel(self.guild_id, self.panel_id)
            panel["settings"]["ticket_category_channel_id"] = select.values[0].id if select.values else None
            update_panel(self.guild_id, self.panel_id, panel)

            embed = create_embed(title="✅ Sucesso", description="Configurações salvas com sucesso!", color=SUCCESS_COLOR)
            view = SingleBackButton(parent_view_factory=lambda: PanelSpecificSettingsView(self.guild_id, self.panel_id))
            await interaction.response.edit_message(embed=embed, view=view)
        except Exception as e:
            print(f"[TICKET_SYSTEM] erro ao definir categoria do painel: {e}", flush=True)

    @discord.ui.button(label="< Voltar", style=discord.ButtonStyle.secondary, row=1)
    async def back(self, interaction: discord.Interaction, button: Button):
        view = PanelSpecificSettingsView(self.guild_id, self.panel_id)
        await interaction.response.edit_message(embed=view.get_embed(), view=view)

class PlaceholderModal(Modal, title="Configurar Placeholder"):
    placeholder = TextInput(label="Texto do Placeholder", max_length=150, required=True)

    def __init__(self, guild_id: int, panel_id: int, current: str):
        super().__init__()
        self.guild_id = guild_id
        self.panel_id = panel_id
        self.placeholder.default = current

    async def on_submit(self, interaction: discord.Interaction):
        try:
            panel = get_panel(self.guild_id, self.panel_id)
            panel["component_settings"]["placeholder"] = self.placeholder.value.strip()
            update_panel(self.guild_id, self.panel_id, panel)

            embed = create_embed(title="✅ Sucesso", description="Placeholder salvo com sucesso!", color=SUCCESS_COLOR)
            view = SingleBackButton(parent_view_factory=lambda: PanelSpecificSettingsView(self.guild_id, self.panel_id))
            await interaction.response.edit_message(embed=embed, view=view)
        except Exception as e:
            print(f"[TICKET_SYSTEM] erro ao salvar modal de placeholder: {e}", flush=True)

class MinMaxModal(Modal, title="Configurar Min/Max de Seleção"):
    min_val = TextInput(label="Mínimo de Seleções (1 a 5)", max_length=2, required=True)
    max_val = TextInput(label="Máximo de Seleções (1 a 25)", max_length=2, required=True)

    def __init__(self, guild_id: int, panel_id: int, current_min: int, current_max: int, total_opts: int):
        super().__init__()
        self.guild_id = guild_id
        self.panel_id = panel_id
        self.total_opts = total_opts
        self.min_val.default = str(current_min)
        self.max_val.default = str(current_max)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            mn = int(self.min_val.value.strip())
            mx = int(self.max_val.value.strip())
            mn = max(1, min(mn, 5))
            mx = max(mn, min(mx, 25))

            panel = get_panel(self.guild_id, self.panel_id)
            panel["component_settings"]["min_values"] = mn
            panel["component_settings"]["max_values"] = mx
            update_panel(self.guild_id, self.panel_id, panel)

            embed = create_embed(title="✅ Sucesso", description=f"Valores de seleção definidos para Min: `{mn}`, Max: `{mx}`.", color=SUCCESS_COLOR)
            view = SingleBackButton(parent_view_factory=lambda: PanelSpecificSettingsView(self.guild_id, self.panel_id))
            await interaction.response.edit_message(embed=embed, view=view)
        except ValueError:
            await interaction.response.send_message("❌ Insira apenas números inteiros válidos.", ephemeral=True)
        except Exception as e:
            print(f"[TICKET_SYSTEM] erro ao salvar min/max modal: {e}", flush=True)

class ConfigByOptionView(View):
    def __init__(self, guild_id: int, panel_id: int):
        super().__init__(timeout=300)
        self.guild_id = guild_id
        self.panel_id = panel_id
        self._build_components()

    def get_embed(self) -> discord.Embed:
        panel = get_panel(self.guild_id, self.panel_id)
        options = panel.get("options", [])
        text = "Vincule cada opção a uma categoria de atendimento existente no bot:\n\n"
        for o in options:
            cat = o.get("categoria_vinculada") or "*Não vinculada*"
            text += f"• `{o['label']}` (ID {o['id']}) → Categoria: `{cat}`\n"
        return create_embed(title="🔗 Vincular Categoria por Opção", description=text, color=EMBED_COLOR)

    def _build_components(self):
        self.clear_items()
        panel = get_panel(self.guild_id, self.panel_id)
        options = panel.get("options", [])

        if options:
            select_opts = [discord.SelectOption(label=f"ID {o['id']}: {o['label'][:50]}", value=str(o["id"])) for o in options]
            select = Select(placeholder="Selecione a opção para vincular...", options=select_opts)
            select.callback = self.on_select_opt
            self.add_item(select)

        back_btn = Button(label="< Voltar", style=discord.ButtonStyle.secondary)
        back_btn.callback = self.on_back
        self.add_item(back_btn)

    async def on_select_opt(self, interaction: discord.Interaction):
        opt_id = int(interaction.data["values"][0])
        await interaction.response.send_modal(LinkCategoryModal(self.guild_id, self.panel_id, opt_id))

    async def on_back(self, interaction: discord.Interaction):
        view = PanelSettingsView(self.guild_id, self.panel_id)
        await interaction.response.edit_message(embed=view.get_embed(), view=view)

class LinkCategoryModal(Modal, title="Vincular Categoria à Opção"):
    categoria = TextInput(label="Chave da Categoria Vinculada", placeholder="Ex: suporte_geral, denuncias", max_length=100, required=True)

    def __init__(self, guild_id: int, panel_id: int, option_id: int):
        super().__init__()
        self.guild_id = guild_id
        self.panel_id = panel_id
        self.option_id = option_id

    async def on_submit(self, interaction: discord.Interaction):
        try:
            panel = get_panel(self.guild_id, self.panel_id)
            for o in panel.get("options", []):
                if o["id"] == self.option_id:
                    o["categoria_vinculada"] = self.categoria.value.strip().lower().replace(" ", "_")
                    break
            update_panel(self.guild_id, self.panel_id, panel)

            view = ConfigByOptionView(self.guild_id, self.panel_id)
            await interaction.response.edit_message(embed=view.get_embed(), view=view)
        except Exception as e:
            print(f"[TICKET_SYSTEM] erro ao vincular categoria: {e}", flush=True)

# ============================================================
# ETAPA 8 — ENVIAR PAINÉIS
# ============================================================

class SendPanelView(View):
    def __init__(self, guild_id: int):
        super().__init__(timeout=300)
        self.guild_id = guild_id
        self.selected_panel_id = None
        self._build_components()

    def get_embed(self) -> discord.Embed:
        return create_embed(
            title="📢 Enviar ou Reenviar Painel",
            description="Selecione o painel e o canal onde a mensagem pública com os botões/dropdown será enviada.",
            color=EMBED_COLOR
        )

    def _build_components(self):
        self.clear_items()
        panels = get_panels(self.guild_id)

        if panels:
            opts = [discord.SelectOption(label=f"Painel ID {p['id']}: {(p['conteudo'].get('title') or p['conteudo'].get('texto') or 'Sem titulo')[:50]}", value=str(p["id"])) for p in panels]
            select = Select(placeholder="Selecione o Painel...", options=opts)
            select.callback = self.on_select_panel
            self.add_item(select)

        if self.selected_panel_id:
            channel_select = ChannelSelect(channel_types=[discord.ChannelType.text], placeholder="Selecione o Canal de envio...")
            channel_select.callback = self.on_select_channel
            self.add_item(channel_select)

        back_btn = Button(label="< Voltar", style=discord.ButtonStyle.secondary)
        back_btn.callback = self.on_back
        self.add_item(back_btn)

    async def on_select_panel(self, interaction: discord.Interaction):
        self.selected_panel_id = int(interaction.data["values"][0])
        self._build_components()
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

    async def on_select_channel(self, interaction: discord.Interaction):
        try:
            channel = interaction.guild.get_channel(int(interaction.data["values"][0]))
            panel = get_panel(self.guild_id, self.selected_panel_id)

            if not channel or not panel:
                return await interaction.response.send_message("❌ Canal ou painel inválido.", ephemeral=True)

            from systems.views import DynamicPanelPublicView

            content_text = None
            embed_obj = None

            if panel["tipo_conteudo"] == "embed":
                embed_obj = build_panel_embed(panel["conteudo"])
            else:
                content_text = panel["conteudo"].get("texto", "Selecione uma opção para abrir um ticket.")

            public_view = DynamicPanelPublicView(panel)

            sent_msg = None
            old_msg_id = panel.get("message_id")
            old_ch_id = panel.get("channel_id")

            # Tenta editar mensagem existente se possível
            if old_msg_id and old_ch_id:
                try:
                    old_ch = interaction.guild.get_channel(old_ch_id)
                    if old_ch:
                        old_msg = await old_ch.fetch_message(old_msg_id)
                        if old_msg:
                            if embed_obj:
                                sent_msg = await old_msg.edit(embed=embed_obj, view=public_view)
                            else:
                                sent_msg = await old_msg.edit(content=content_text, view=public_view)
                except Exception:
                    sent_msg = None

            if not sent_msg:
                if embed_obj:
                    sent_msg = await channel.send(embed=embed_obj, view=public_view)
                else:
                    sent_msg = await channel.send(content=content_text, view=public_view)

            panel["channel_id"] = channel.id
            panel["message_id"] = sent_msg.id
            update_panel(self.guild_id, self.selected_panel_id, panel)

            embed = create_embed(title="✅ Painel Enviado!", description=f"Painel ID `{self.selected_panel_id}` enviado com sucesso em {channel.mention}!", color=SUCCESS_COLOR)
            view = SingleBackButton(parent_view_factory=lambda: RootMenuView(self.guild_id))
            await interaction.response.edit_message(embed=embed, view=view)

        except Exception as e:
            print(f"[TICKET_SYSTEM] erro ao enviar painel: {e}", flush=True)

    async def on_back(self, interaction: discord.Interaction):
        view = RootMenuView(self.guild_id)
        await interaction.response.edit_message(embed=view.get_embed(), view=view)

# ============================================================
# 🚀 SLASH COMMAND REGISTER & SETUP
# ============================================================

@app_commands.command(name="ticket-system", description="Painel principal de configuração do sistema de tickets")
async def ticket_system_cmd(interaction: discord.Interaction):
    try:
        if not is_admin_or_staff(interaction):
            return await interaction.response.send_message("❌ Permissão insuficiente.", ephemeral=True)

        view = RootMenuView(interaction.guild_id)
        embed = create_embed(
            title="⚙️ Painel do Sistema de Tickets",
            description="Selecione uma opção abaixo para começar a configurar o sistema de tickets deste servidor.",
            color=EMBED_COLOR
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    except Exception as e:
        print(f"[TICKET_SYSTEM] erro na execucao do comando /ticket-system: {e}", flush=True)

async def setup(bot: commands.Bot):
    bot.tree.add_command(ticket_system_cmd)
