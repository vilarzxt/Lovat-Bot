import discord
from discord import app_commands
from discord.ext import commands

from config.guild_config import (
    get_guild_config,
    save_guild_config,
    get_ticket_categories,
    get_role_levels
)
from systems.permissions import is_ticket_staff
from systems.utils import create_embed
from config.assets import EMBED_COLOR

ticket_config_group = app_commands.Group(
    name="ticket-config",
    description="Configurações do sistema de tickets do servidor"
)

def is_admin_or_founder(interaction: discord.Interaction) -> bool:
    if not interaction.guild:
        return False
    if interaction.user.guild_permissions.administrator:
        return True
    roles = [r.name.lower() for r in interaction.user.roles]
    return "fundador" in roles

# =========================
# 1. CATEGORIA - ADICIONAR
# =========================

@ticket_config_group.command(
    name="categoria-adicionar",
    description="Adiciona uma nova categoria de ticket"
)
@app_commands.describe(
    chave="Identificador único (ex: suporte, denuncias)",
    nome="Nome exibido",
    emoji="Emoji da categoria",
    min_level="Nível mínimo de cargo para atender (default 0)"
)
async def categoria_adicionar(
    interaction: discord.Interaction,
    chave: str,
    nome: str,
    emoji: str,
    min_level: int = 0
):
    if not is_admin_or_founder(interaction):
        return await interaction.response.send_message("❌ Permissão insuficiente.", ephemeral=True)

    guild_id = interaction.guild_id
    config = get_guild_config(guild_id)
    key = chave.lower().strip().replace(" ", "_")

    if key in config["ticket_categories"]:
        return await interaction.response.send_message(f"❌ A categoria `{key}` já existe.", ephemeral=True)

    config["ticket_categories"][key] = {
        "label": nome,
        "emoji": emoji,
        "min_level": min_level,
        "subcategories": {}
    }
    save_guild_config(guild_id, config)

    await interaction.response.send_message(
        f"✅ Categoria `{nome}` ({emoji}) adicionada com sucesso!",
        ephemeral=True
    )

# =========================
# 2. CATEGORIA - REMOVER
# =========================

@ticket_config_group.command(
    name="categoria-remover",
    description="Remove uma categoria de ticket"
)
async def categoria_remover(
    interaction: discord.Interaction,
    chave: str
):
    if not is_admin_or_founder(interaction):
        return await interaction.response.send_message("❌ Permissão insuficiente.", ephemeral=True)

    guild_id = interaction.guild_id
    config = get_guild_config(guild_id)
    key = chave.lower().strip().replace(" ", "_")

    if key not in config["ticket_categories"]:
        return await interaction.response.send_message(f"❌ Categoria `{key}` não encontrada.", ephemeral=True)

    del config["ticket_categories"][key]
    save_guild_config(guild_id, config)

    await interaction.response.send_message(f"✅ Categoria `{key}` removida com sucesso!", ephemeral=True)

# =========================
# 3. SUBCATEGORIA - ADICIONAR
# =========================

@ticket_config_group.command(
    name="subcategoria-adicionar",
    description="Adiciona uma subcategoria a uma categoria existente"
)
@app_commands.describe(
    categoria="Chave da categoria pai",
    chave="Identificador único da subcategoria",
    nome="Nome exibido",
    emoji="Emoji da subcategoria",
    campos="Campos solicitados (separados por vírgula)"
)
async def subcategoria_adicionar(
    interaction: discord.Interaction,
    categoria: str,
    chave: str,
    nome: str,
    emoji: str,
    campos: str
):
    if not is_admin_or_founder(interaction):
        return await interaction.response.send_message("❌ Permissão insuficiente.", ephemeral=True)

    guild_id = interaction.guild_id
    config = get_guild_config(guild_id)
    cat_key = categoria.lower().strip().replace(" ", "_")
    sub_key = chave.lower().strip().replace(" ", "_")

    if cat_key not in config["ticket_categories"]:
        return await interaction.response.send_message(f"❌ Categoria `{cat_key}` não encontrada.", ephemeral=True)

    field_list = [f.strip() for f in campos.split(",") if f.strip()]

    config["ticket_categories"][cat_key]["subcategories"][sub_key] = {
        "label": nome,
        "emoji": emoji,
        "fields": field_list
    }
    save_guild_config(guild_id, config)

    await interaction.response.send_message(
        f"✅ Subcategoria `{nome}` adicionada na categoria `{cat_key}`!",
        ephemeral=True
    )

# =========================
# 4. SUBCATEGORIA - REMOVER
# =========================

@ticket_config_group.command(
    name="subcategoria-remover",
    description="Remove uma subcategoria"
)
async def subcategoria_remover(
    interaction: discord.Interaction,
    categoria: str,
    chave: str
):
    if not is_admin_or_founder(interaction):
        return await interaction.response.send_message("❌ Permissão insuficiente.", ephemeral=True)

    guild_id = interaction.guild_id
    config = get_guild_config(guild_id)
    cat_key = categoria.lower().strip().replace(" ", "_")
    sub_key = chave.lower().strip().replace(" ", "_")

    if cat_key not in config["ticket_categories"]:
        return await interaction.response.send_message(f"❌ Categoria `{cat_key}` não encontrada.", ephemeral=True)

    if sub_key not in config["ticket_categories"][cat_key]["subcategories"]:
        return await interaction.response.send_message(f"❌ Subcategoria `{sub_key}` não encontrada.", ephemeral=True)

    del config["ticket_categories"][cat_key]["subcategories"][sub_key]
    save_guild_config(guild_id, config)

    await interaction.response.send_message(f"✅ Subcategoria `{sub_key}` removida!", ephemeral=True)

# =========================
# 5. CARGO - DEFINIR
# =========================

@ticket_config_group.command(
    name="cargo-definir",
    description="Define o nível de um cargo para a equipe de suporte"
)
async def cargo_definir(
    interaction: discord.Interaction,
    cargo: discord.Role,
    nivel: int
):
    if not is_admin_or_founder(interaction):
        return await interaction.response.send_message("❌ Permissão insuficiente.", ephemeral=True)

    guild_id = interaction.guild_id
    config = get_guild_config(guild_id)

    role_name = cargo.name.lower()
    config["role_levels"][role_name] = nivel
    save_guild_config(guild_id, config)

    await interaction.response.send_message(
        f"✅ Cargo `{cargo.name}` configurado para o nível `{nivel}`.",
        ephemeral=True
    )

# =========================
# 6. LISTAR
# =========================

@ticket_config_group.command(
    name="listar",
    description="Lista as configurações de tickets do servidor"
)
async def listar(interaction: discord.Interaction):
    if not is_admin_or_founder(interaction):
        return await interaction.response.send_message("❌ Permissão insuficiente.", ephemeral=True)

    guild_id = interaction.guild_id
    config = get_guild_config(guild_id)

    embed = create_embed(
        title="⚙️ Configurações de Tickets do Servidor",
        color=EMBED_COLOR
    )

    roles_text = "\n".join([f"• `{r}`: Nível {lvl}" for r, lvl in config.get("role_levels", {}).items()]) or "Nenhum cargo configurado"
    embed.add_field(name="🛡️ Cargos Configurados", value=roles_text, inline=False)

    cats = config.get("ticket_categories", {})
    for key, cat in cats.items():
        subcats = cat.get("subcategories", {})
        sub_text = "\n".join([f"  └ {sdata.get('emoji', '📄')} `{skey}` ({sdata.get('label')})" for skey, sdata in subcats.items()]) or "  └ Nenhuma subcategoria"
        embed.add_field(
            name=f"{cat.get('emoji', '📂')} {cat.get('label', key)} (`{key}` | Nível Min: {cat.get('min_level', 0)})",
            value=sub_text,
            inline=False
        )

    await interaction.response.send_message(embed=embed, ephemeral=True)

# =========================
# 7. PAINEL ENVIAR
# =========================

@ticket_config_group.command(
    name="painel-enviar",
    description="Reenvia o painel de tickets com a configuração atualizada"
)
async def painel_enviar(interaction: discord.Interaction):
    if not is_admin_or_founder(interaction):
        return await interaction.response.send_message("❌ Permissão insuficiente.", ephemeral=True)

    from commands.ticket import ticket as ticket_cmd
    await ticket_cmd.callback(interaction)

# =========================
# 🚀 SETUP
# =========================

async def setup(bot: commands.Bot):
    bot.tree.add_command(ticket_config_group)
