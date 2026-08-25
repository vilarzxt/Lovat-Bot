import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime

from config.guild_config import get_guild_config, save_guild_config

config_group = app_commands.Group(
    name="config",
    description="Configurações gerais do servidor"
)

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
# 🔘 CAPTCHA BUTTON VIEW
# =========================

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
            await log_action(
                guild,
                "⚠️ Tentativa de Verificação Captcha",
                f"O membro {interaction.user.mention} ({interaction.user.id}) tentou verificar, mas o captcha está desativado.",
                color=0xE74C3C
            )
            return await interaction.response.send_message("❌ A verificação por Captcha está desativada no momento.", ephemeral=True)

        role_id = cfg.get("captcha_role_id")
        if not role_id:
            await log_action(
                guild,
                "⚠️ Erro no Captcha",
                f"Cargo de verificação não configurado no servidor durante clique de {interaction.user.mention}.",
                color=0xE74C3C
            )
            return await interaction.response.send_message("❌ Cargo de verificação não foi configurado pela administração.", ephemeral=True)

        role = guild.get_role(role_id)
        if not role:
            await log_action(
                guild,
                "⚠️ Erro no Captcha",
                f"Cargo de ID `{role_id}` não foi encontrado no servidor.",
                color=0xE74C3C
            )
            return await interaction.response.send_message("❌ Cargo de verificação não encontrado no servidor.", ephemeral=True)

        if role in interaction.user.roles:
            return await interaction.response.send_message("ℹ️ Você já está verificado!", ephemeral=True)

        try:
            await interaction.user.add_roles(role, reason="Verificação por Captcha concluída com sucesso")
            await log_action(
                guild,
                "✅ Verificação Captcha Concluída",
                f"Membro {interaction.user.mention} (`{interaction.user.id}`) foi verificado e recebeu o cargo {role.mention}.",
                color=0x2ECC71
            )
            await interaction.response.send_message("✅ Verificação concluída com sucesso! Seja bem-vindo(a).", ephemeral=True)
        except Exception as e:
            await log_action(
                guild,
                "❌ Erro ao atribuir cargo Captcha",
                f"Falha ao dar cargo para {interaction.user.mention}: `{e}`",
                color=0xE74C3C
            )
            await interaction.response.send_message("❌ Erro ao atribuir o cargo de verificação. Fale com a equipe.", ephemeral=True)

# =========================
# 📋 CANAL DE LOGS - DEFINIR
# =========================

@config_group.command(
    name="log-canal",
    description="Define o canal onde os logs de moderação/sistema serão enviados"
)
@app_commands.describe(canal="Canal de texto para os registros")
async def log_canal(interaction: discord.Interaction, canal: discord.TextChannel):
    if not is_admin_or_founder(interaction):
        return await interaction.response.send_message("❌ Permissão insuficiente.", ephemeral=True)

    guild_id = interaction.guild_id
    cfg = get_guild_config(guild_id)
    cfg["log_channel_id"] = canal.id
    save_guild_config(guild_id, cfg)

    await interaction.response.send_message(
        f"✅ Canal de logs definido para {canal.mention} com sucesso!",
        ephemeral=True
    )
    await log_action(interaction.guild, "⚙️ Configuração Alterada", f"Canal de logs alterado para {canal.mention} por {interaction.user.mention}.")

# =========================
# 🎉 BOAS-VINDAS
# =========================

@config_group.command(
    name="boas-vindas-canal",
    description="Define o canal para mensagens de boas-vindas"
)
@app_commands.describe(canal="Canal para as boas-vindas")
async def boas_vindas_canal(interaction: discord.Interaction, canal: discord.TextChannel):
    if not is_admin_or_founder(interaction):
        return await interaction.response.send_message("❌ Permissão insuficiente.", ephemeral=True)

    cfg = get_guild_config(interaction.guild_id)
    cfg["welcome_channel_id"] = canal.id
    save_guild_config(interaction.guild_id, cfg)

    await interaction.response.send_message(f"✅ Canal de boas-vindas definido para {canal.mention}.", ephemeral=True)
    await log_action(interaction.guild, "⚙️ Configuração Alterada", f"Canal de boas-vindas definido para {canal.mention} por {interaction.user.mention}.")

@config_group.command(
    name="boas-vindas-mensagem",
    description="Define a mensagem de boas-vindas. Variáveis: {user}, {mention}, {server}, {count}"
)
@app_commands.describe(mensagem="Mensagem de boas-vindas")
async def boas_vindas_mensagem(interaction: discord.Interaction, mensagem: str):
    if not is_admin_or_founder(interaction):
        return await interaction.response.send_message("❌ Permissão insuficiente.", ephemeral=True)

    cfg = get_guild_config(interaction.guild_id)
    cfg["welcome_message"] = mensagem
    save_guild_config(interaction.guild_id, cfg)

    await interaction.response.send_message("✅ Mensagem de boas-vindas atualizada!", ephemeral=True)
    await log_action(interaction.guild, "⚙️ Configuração Alterada", f"Mensagem de boas-vindas atualizada por {interaction.user.mention}.")

# =========================
# 👋 DESPEDIDA
# =========================

@config_group.command(
    name="despedida-canal",
    description="Define o canal para mensagens de despedida"
)
@app_commands.describe(canal="Canal para as mensagens de saída")
async def despedida_canal(interaction: discord.Interaction, canal: discord.TextChannel):
    if not is_admin_or_founder(interaction):
        return await interaction.response.send_message("❌ Permissão insuficiente.", ephemeral=True)

    cfg = get_guild_config(interaction.guild_id)
    cfg["goodbye_channel_id"] = canal.id
    save_guild_config(interaction.guild_id, cfg)

    await interaction.response.send_message(f"✅ Canal de despedida definido para {canal.mention}.", ephemeral=True)
    await log_action(interaction.guild, "⚙️ Configuração Alterada", f"Canal de despedida definido para {canal.mention} por {interaction.user.mention}.")

@config_group.command(
    name="despedida-mensagem",
    description="Define a mensagem de despedida. Variáveis: {user}, {server}, {count}"
)
@app_commands.describe(mensagem="Mensagem de despedida")
async def despedida_mensagem(interaction: discord.Interaction, mensagem: str):
    if not is_admin_or_founder(interaction):
        return await interaction.response.send_message("❌ Permissão insuficiente.", ephemeral=True)

    cfg = get_guild_config(interaction.guild_id)
    cfg["goodbye_message"] = mensagem
    save_guild_config(interaction.guild_id, cfg)

    await interaction.response.send_message("✅ Mensagem de despedida atualizada!", ephemeral=True)
    await log_action(interaction.guild, "⚙️ Configuração Alterada", f"Mensagem de despedida atualizada por {interaction.user.mention}.")

# =========================
# 🎭 AUTO ROLE
# =========================

@config_group.command(
    name="auto-role",
    description="Define o cargo atribuído automaticamente a novos membros"
)
@app_commands.describe(cargo="Cargo de entrada automática (ou deixe em branco para desativar)")
async def auto_role(interaction: discord.Interaction, cargo: discord.Role = None):
    if not is_admin_or_founder(interaction):
        return await interaction.response.send_message("❌ Permissão insuficiente.", ephemeral=True)

    cfg = get_guild_config(interaction.guild_id)
    cfg["auto_role_id"] = cargo.id if cargo else None
    save_guild_config(interaction.guild_id, cfg)

    msg = f"✅ Auto-role definido para {cargo.mention}." if cargo else "✅ Auto-role desativado."
    await interaction.response.send_message(msg, ephemeral=True)
    await log_action(interaction.guild, "⚙️ Configuração Alterada", f"Auto-role atualizado por {interaction.user.mention}: {cargo.name if cargo else 'Desativado'}.")

# =========================
# 🛡️ CAPTCHA
# =========================

@config_group.command(
    name="captcha-ativar",
    description="Ativa ou desativa a verificação de membros por Captcha"
)
@app_commands.describe(ativo="True para ativar, False para desativar")
async def captcha_ativar(interaction: discord.Interaction, ativo: bool):
    if not is_admin_or_founder(interaction):
        return await interaction.response.send_message("❌ Permissão insuficiente.", ephemeral=True)

    cfg = get_guild_config(interaction.guild_id)
    cfg["captcha_enabled"] = ativo
    save_guild_config(interaction.guild_id, cfg)

    status = "ativado" if ativo else "desativado"
    await interaction.response.send_message(f"✅ Sistema de Captcha **{status}**.", ephemeral=True)
    await log_action(interaction.guild, "⚙️ Configuração Alterada", f"Captcha {status} por {interaction.user.mention}.")

@config_group.command(
    name="captcha-cargo",
    description="Define o cargo concedido ao concluir o Captcha"
)
@app_commands.describe(cargo="Cargo concedido após verificação")
async def captcha_cargo(interaction: discord.Interaction, cargo: discord.Role):
    if not is_admin_or_founder(interaction):
        return await interaction.response.send_message("❌ Permissão insuficiente.", ephemeral=True)

    cfg = get_guild_config(interaction.guild_id)
    cfg["captcha_role_id"] = cargo.id
    save_guild_config(interaction.guild_id, cfg)

    await interaction.response.send_message(f"✅ Cargo do Captcha definido para {cargo.mention}.", ephemeral=True)
    await log_action(interaction.guild, "⚙️ Configuração Alterada", f"Cargo do Captcha definido para {cargo.name} por {interaction.user.mention}.")

@config_group.command(
    name="captcha-painel",
    description="Envia o painel com botão de verificação por Captcha no canal atual"
)
async def captcha_painel(interaction: discord.Interaction):
    if not is_admin_or_founder(interaction):
        return await interaction.response.send_message("❌ Permissão insuficiente.", ephemeral=True)

    cfg = get_guild_config(interaction.guild_id)
    cfg["captcha_channel_id"] = interaction.channel_id
    save_guild_config(interaction.guild_id, cfg)

    embed = discord.Embed(
        title="🔒 Verificação de Segurança",
        description="Clique no botão abaixo para verificar sua conta e liberar o acesso aos canais do servidor.",
        color=0x2ECC71
    )
    embed.set_footer(text=interaction.guild.name, icon_url=interaction.guild.icon.url if interaction.guild.icon else None)

    view = CaptchaVerifyView()
    await interaction.channel.send(embed=embed, view=view)
    await interaction.response.send_message("✅ Painel de verificação enviado com sucesso!", ephemeral=True)
    await log_action(interaction.guild, "⚙️ Painel de Captcha Enviado", f"Painel enviado em {interaction.channel.mention} por {interaction.user.mention}.")

# =========================
# 🚀 SETUP
# =========================

async def setup(bot: commands.Bot):
    bot.tree.add_command(config_group)
