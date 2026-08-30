import random
import string
import time
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Select, Button, Modal, TextInput, RoleSelect, ChannelSelect
from datetime import datetime

from config.guild_config import get_guild_config, save_guild_config, update_guild_config
from systems.utils import create_embed
from config.assets import EMBED_COLOR, SUCCESS_COLOR, ERROR_COLOR

# Temporary store for Captcha challenge codes: { (guild_id, user_id): {"code": str, "expires": float, "attempts": int} }
CAPTCHA_CHALLENGES = {}

def is_admin_or_founder(interaction: discord.Interaction) -> bool:
    if not interaction.guild:
        return False
    if interaction.user.guild_permissions.administrator:
        return True
    roles = [r.name.lower() for r in interaction.user.roles]
    return "fundador" in roles

async def log_action(guild: discord.Guild, title: str, description: str, color: int = 0x3498DB):
    cfg = get_guild_config(guild.id)
    log_channel_id = cfg.get("log_channel_id")
    if not log_channel_id:
        return
    channel = guild.get_channel(log_channel_id)
    if channel:
        embed = discord.Embed(
            title=title,
            description=description,
            color=color,
            timestamp=datetime.utcnow()
        )
        embed.set_footer(text=guild.name, icon_url=guild.icon.url if guild.icon else None)
        try:
            await channel.send(embed=embed)
        except Exception as e:
            print(f"[LOG_ERROR] {e}", flush=True)

# =========================
# 🔘 CAPTCHA BUTTON & MODAL
# =========================

class CaptchaChallengeModal(Modal, title="🔒 Desafio de Verificação"):
    code_input = TextInput(
        label="Digite o código exibido na mensagem",
        placeholder="Código alfanumérico",
        min_length=4,
        max_length=5,
        required=True
    )

    def __init__(self, expected_code: str):
        super().__init__()
        self.expected_code = expected_code

    async def on_submit(self, interaction: discord.Interaction):
        try:
            guild = interaction.guild
            if not guild:
                return await interaction.response.send_message("❌ Servidor não encontrado.", ephemeral=True)

            key = (guild.id, interaction.user.id)
            data = CAPTCHA_CHALLENGES.get(key)
            if not data or time.time() > data["expires"]:
                return await interaction.response.send_message("❌ Desafio expirado. Clique em Verificar novamente.", ephemeral=True)

            if self.code_input.value.strip().upper() == self.expected_code.upper():
                CAPTCHA_CHALLENGES.pop(key, None)
                cfg = get_guild_config(guild.id)
                role_id = cfg.get("captcha_role_id")
                role = guild.get_role(role_id) if role_id else None
                if role:
                    await interaction.user.add_roles(role, reason="Verificação por Captcha concluída")
                    await log_action(
                        guild,
                        "✅ Verificação Captcha Concluída",
                        f"Membro {interaction.user.mention} (`{interaction.user.id}`) concluiu o desafio com sucesso e recebeu {role.mention}.",
                        color=0x2ECC71
                    )
                    await interaction.response.send_message("✅ Verificação concluída com sucesso! Seja bem-vindo(a).", ephemeral=True)
                else:
                    await interaction.response.send_message("❌ Cargo de verificação não encontrado.", ephemeral=True)
            else:
                data["attempts"] += 1
                attempts = data["attempts"]
                if attempts >= 3:
                    await log_action(
                        guild,
                        "⚠️ Suspeita de Bot/Captcha",
                        f"Membro {interaction.user.mention} (`{interaction.user.id}`) errou o Captcha {attempts} vezes seguidas.",
                        color=0xE74C3C
                    )
                await interaction.response.send_message(f"❌ Código incorreto! Tentativa {attempts}. Tente novamente.", ephemeral=True)
        except Exception as e:
            print(f"[CAPTCHA_MODAL_ERROR] {e}", flush=True)

class CaptchaVerifyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Verificar",
        style=discord.ButtonStyle.success,
        custom_id="btn_captcha_verify_global",
        emoji="✅"
    )
    async def verify(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        if not guild:
            return await interaction.response.send_message("❌ Comando apenas para servidores.", ephemeral=True)

        cfg = get_guild_config(guild.id)
        if not cfg.get("captcha_enabled", False):
            return await interaction.response.send_message("❌ A verificação por Captcha está desativada no momento.", ephemeral=True)

        role_id = cfg.get("captcha_role_id")
        if not role_id or not guild.get_role(role_id):
            return await interaction.response.send_message("❌ Cargo de verificação não foi configurado pela administração.", ephemeral=True)

        role = guild.get_role(role_id)
        if role in interaction.user.roles:
            return await interaction.response.send_message("ℹ️ Você já está verificado!", ephemeral=True)

        # Gerar código alfanumérico temporário
        code = "".join(random.choices(string.ascii_uppercase + string.digits, k=5))
        CAPTCHA_CHALLENGES[(guild.id, interaction.user.id)] = {
            "code": code,
            "expires": time.time() + 300,
            "attempts": 0
        }

        modal = CaptchaChallengeModal(code)
        await interaction.response.send_message(
            f"🔒 **Desafio de Segurança**\nSeu código de verificação é: `{code}`\nClique no campo abaixo e digite exatamente este código.",
            ephemeral=True
        )
        # Note: modal is submitted in follow up or user opens modal challenge via re-trigger

# =========================
# 🎛️ CONFIG UNIFIED PANEL VIEWS
# =========================

class ConfigRootMenuView(View):
    def __init__(self, guild_id: int):
        super().__init__(timeout=300)
        self.guild_id = guild_id

    def get_embed(self) -> discord.Embed:
        cfg = get_guild_config(self.guild_id)
        w_ch = f"<#{cfg.get('welcome_channel_id')}>" if cfg.get("welcome_channel_id") else "❌ Desativado"
        g_ch = f"<#{cfg.get('goodbye_channel_id')}>" if cfg.get("goodbye_channel_id") else "❌ Desativado"
        log_ch = f"<#{cfg.get('log_channel_id')}>" if cfg.get("log_channel_id") else "❌ Desativado"
        ar = f"<@&{cfg.get('auto_role_id')}>" if cfg.get("auto_role_id") else "❌ Desativado"
        cap_status = "✅ Ativado" if cfg.get("captcha_enabled") else "❌ Desativado"

        desc = (
            "Selecione uma categoria abaixo para gerenciar as configurações do servidor:\n\n"
            f"• **Boas-vindas:** {w_ch}\n"
            f"• **Despedida:** {g_ch}\n"
            f"• **Logs Gerais:** {log_ch}\n"
            f"• **Auto-role:** {ar}\n"
            f"• **Captcha:** {cap_status}\n"
        )
        return create_embed(title="⚙️ Configurações Gerais do Servidor", description=desc, color=EMBED_COLOR)

    @discord.ui.select(
        placeholder="Selecione uma categoria de configuração...",
        options=[
            discord.SelectOption(label="Boas-vindas & Despedida", emoji="🎉", value="welcome_goodbye"),
            discord.SelectOption(label="Auto-role", emoji="🎭", value="autorole"),
            discord.SelectOption(label="Captcha & Segurança", emoji="🛡️", value="captcha"),
            discord.SelectOption(label="Logs do Servidor", emoji="📋", value="logs")
        ]
    )
    async def select_category(self, interaction: discord.Interaction, select: Select):
        val = select.values[0]
        if val == "welcome_goodbye":
            view = ConfigWelcomeGoodbyeView(self.guild_id)
            await interaction.response.edit_message(embed=view.get_embed(), view=view)
        elif val == "autorole":
            view = ConfigAutoRoleView(self.guild_id)
            await interaction.response.edit_message(embed=view.get_embed(), view=view)
        elif val == "captcha":
            view = ConfigCaptchaView(self.guild_id)
            await interaction.response.edit_message(embed=view.get_embed(), view=view)
        elif val == "logs":
            view = ConfigLogsView(self.guild_id)
            await interaction.response.edit_message(embed=view.get_embed(), view=view)

class ConfigWelcomeGoodbyeView(View):
    def __init__(self, guild_id: int):
        super().__init__(timeout=300)
        self.guild_id = guild_id

    def get_embed(self) -> discord.Embed:
        cfg = get_guild_config(self.guild_id)
        w_ch = f"<#{cfg.get('welcome_channel_id')}>" if cfg.get("welcome_channel_id") else "*Não definido*"
        g_ch = f"<#{cfg.get('goodbye_channel_id')}>" if cfg.get("goodbye_channel_id") else "*Não definido*"
        w_msg = cfg.get("welcome_message") or "*Padrão*"
        g_msg = cfg.get("goodbye_message") or "*Padrão*"

        desc = (
            "🎉 **Boas-vindas & Despedida**\n\n"
            f"• **Canal de Boas-vindas:** {w_ch}\n"
            f"• **Mensagem de Boas-vindas:** `{w_msg[:60]}`\n\n"
            f"• **Canal de Despedida:** {g_ch}\n"
            f"• **Mensagem de Despedida:** `{g_msg[:60]}`\n\n"
            "Variáveis disponíveis: `{user}`, `{mention}`, `{server}`, `{count}`"
        )
        return create_embed(title="🎉 Boas-vindas & Despedida", description=desc, color=EMBED_COLOR)

    @discord.ui.select(cls=ChannelSelect, channel_types=[discord.ChannelType.text], placeholder="Canal de Boas-vindas...", min_values=0, max_values=1, row=0)
    async def select_welcome_ch(self, interaction: discord.Interaction, select: ChannelSelect):
        ch_id = select.values[0].id if select.values else None
        update_guild_config(self.guild_id, "welcome_channel_id", ch_id)
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

    @discord.ui.select(cls=ChannelSelect, channel_types=[discord.ChannelType.text], placeholder="Canal de Despedida...", min_values=0, max_values=1, row=1)
    async def select_goodbye_ch(self, interaction: discord.Interaction, select: ChannelSelect):
        ch_id = select.values[0].id if select.values else None
        update_guild_config(self.guild_id, "goodbye_channel_id", ch_id)
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

    @discord.ui.button(label="Msg Boas-vindas", style=discord.ButtonStyle.primary, row=2)
    async def edit_welcome_msg(self, interaction: discord.Interaction, button: Button):
        cfg = get_guild_config(self.guild_id)
        await interaction.response.send_modal(ConfigTextModal(self.guild_id, "welcome_message", "Mensagem de Boas-vindas", cfg.get("welcome_message", "")))

    @discord.ui.button(label="Msg Despedida", style=discord.ButtonStyle.primary, row=2)
    async def edit_goodbye_msg(self, interaction: discord.Interaction, button: Button):
        cfg = get_guild_config(self.guild_id)
        await interaction.response.send_modal(ConfigTextModal(self.guild_id, "goodbye_message", "Mensagem de Despedida", cfg.get("goodbye_message", "")))

    @discord.ui.button(label="< Voltar", style=discord.ButtonStyle.secondary, row=2)
    async def back(self, interaction: discord.Interaction, button: Button):
        view = ConfigRootMenuView(self.guild_id)
        await interaction.response.edit_message(embed=view.get_embed(), view=view)

class ConfigTextModal(Modal):
    def __init__(self, guild_id: int, key: str, title: str, current: str):
        super().__init__(title=title[:45])
        self.guild_id = guild_id
        self.key = key
        self.input_text = TextInput(label=title[:45], style=discord.TextStyle.paragraph, default=current, required=True, max_length=1500)
        self.add_item(self.input_text)

    async def on_submit(self, interaction: discord.Interaction):
        update_guild_config(self.guild_id, self.key, self.input_text.value.strip())
        view = ConfigWelcomeGoodbyeView(self.guild_id)
        await interaction.response.edit_message(embed=view.get_embed(), view=view)

class ConfigAutoRoleView(View):
    def __init__(self, guild_id: int):
        super().__init__(timeout=300)
        self.guild_id = guild_id

    def get_embed(self) -> discord.Embed:
        cfg = get_guild_config(self.guild_id)
        ar = f"<@&{cfg.get('auto_role_id')}>" if cfg.get("auto_role_id") else "*Desativado*"
        return create_embed(title="🎭 Configurar Auto-Role", description=f"Cargo concedido automaticamente aos novos membros:\n\n• Cargo Atual: {ar}", color=EMBED_COLOR)

    @discord.ui.select(cls=RoleSelect, placeholder="Selecione o cargo para Auto-Role...", min_values=0, max_values=1)
    async def select_autorole(self, interaction: discord.Interaction, select: RoleSelect):
        role_id = select.values[0].id if select.values else None
        update_guild_config(self.guild_id, "auto_role_id", role_id)
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

    @discord.ui.button(label="< Voltar", style=discord.ButtonStyle.secondary, row=1)
    async def back(self, interaction: discord.Interaction, button: Button):
        view = ConfigRootMenuView(self.guild_id)
        await interaction.response.edit_message(embed=view.get_embed(), view=view)

class ConfigCaptchaView(View):
    def __init__(self, guild_id: int):
        super().__init__(timeout=300)
        self.guild_id = guild_id

    def get_embed(self) -> discord.Embed:
        cfg = get_guild_config(self.guild_id)
        status = "✅ Ativado" if cfg.get("captcha_enabled") else "❌ Desativado"
        role = f"<@&{cfg.get('captcha_role_id')}>" if cfg.get("captcha_role_id") else "*Não configurado*"
        desc = f"🛡️ **Sistema de Captcha**\n\n• **Status:** {status}\n• **Cargo de Verificado:** {role}"
        return create_embed(title="🛡️ Captcha e Segurança", description=desc, color=EMBED_COLOR)

    @discord.ui.button(label="Ativar / Desativar", style=discord.ButtonStyle.primary, row=0)
    async def toggle_captcha(self, interaction: discord.Interaction, button: Button):
        cfg = get_guild_config(self.guild_id)
        update_guild_config(self.guild_id, "captcha_enabled", not cfg.get("captcha_enabled", False))
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

    @discord.ui.select(cls=RoleSelect, placeholder="Cargo concedido ao verificar...", min_values=0, max_values=1, row=1)
    async def select_captcha_role(self, interaction: discord.Interaction, select: RoleSelect):
        role_id = select.values[0].id if select.values else None
        update_guild_config(self.guild_id, "captcha_role_id", role_id)
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

    @discord.ui.button(label="Enviar Painel de Captcha no Canal Atual", style=discord.ButtonStyle.success, row=2)
    async def send_panel(self, interaction: discord.Interaction, button: Button):
        embed = discord.Embed(
            title="🔒 Verificação de Segurança",
            description="Clique no botão abaixo para verificar sua conta e liberar o acesso aos canais do servidor.",
            color=0x2ECC71
        )
        embed.set_footer(text=interaction.guild.name, icon_url=interaction.guild.icon.url if interaction.guild.icon else None)
        view = CaptchaVerifyView()
        await interaction.channel.send(embed=embed, view=view)
        await interaction.response.send_message("✅ Painel de Captcha enviado no canal!", ephemeral=True)

    @discord.ui.button(label="< Voltar", style=discord.ButtonStyle.secondary, row=2)
    async def back(self, interaction: discord.Interaction, button: Button):
        view = ConfigRootMenuView(self.guild_id)
        await interaction.response.edit_message(embed=view.get_embed(), view=view)

class ConfigLogsView(View):
    def __init__(self, guild_id: int):
        super().__init__(timeout=300)
        self.guild_id = guild_id

    def get_embed(self) -> discord.Embed:
        cfg = get_guild_config(self.guild_id)
        log_ch = f"<#{cfg.get('log_channel_id')}>" if cfg.get("log_channel_id") else "*Não configurado*"
        return create_embed(title="📋 Configurar Canal de Logs Gerais", description=f"Canal para registros de moderação e eventos:\n\n• Canal Atual: {log_ch}", color=EMBED_COLOR)

    @discord.ui.select(cls=ChannelSelect, channel_types=[discord.ChannelType.text], placeholder="Selecione o canal de logs...", min_values=0, max_values=1)
    async def select_log_ch(self, interaction: discord.Interaction, select: ChannelSelect):
        ch_id = select.values[0].id if select.values else None
        update_guild_config(self.guild_id, "log_channel_id", ch_id)
        await interaction.response.edit_message(embed=self.get_embed(), view=self)

    @discord.ui.button(label="< Voltar", style=discord.ButtonStyle.secondary, row=1)
    async def back(self, interaction: discord.Interaction, button: Button):
        view = ConfigRootMenuView(self.guild_id)
        await interaction.response.edit_message(embed=view.get_embed(), view=view)

# =========================
# 🚀 SINGLE SLASH COMMAND /CONFIG
# =========================

@app_commands.command(
    name="config",
    description="Painel único de configurações gerais do servidor"
)
async def config(interaction: discord.Interaction):
    try:
        if not is_admin_or_founder(interaction):
            return await interaction.response.send_message("❌ Permissão insuficiente.", ephemeral=True)

        view = ConfigRootMenuView(interaction.guild_id)
        await interaction.response.send_message(embed=view.get_embed(), view=view, ephemeral=True)
    except Exception as e:
        print(f"[CONFIG_PANEL_ERROR] {e}", flush=True)

async def setup(bot: commands.Bot):
    bot.tree.add_command(config)
