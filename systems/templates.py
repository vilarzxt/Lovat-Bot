import discord

from config.assets import (
    EMBED_COLOR,
    ASSETS
)

from systems.utils import (
    create_embed
)

from config.guild_config import get_ticket_categories

# =========================
# 🎫 TICKET TEMPLATES (DINÂMICO)
# =========================

def get_ticket_template(
    subcategory: str,
    guild_id: int = None,
    category_key: str = None
) -> discord.Embed:

    title = "🎫 Ticket de Atendimento"
    fields = []

    if guild_id and category_key:
        categories = get_ticket_categories(guild_id)
        cat_data = categories.get(category_key, {})
        subcats = cat_data.get("subcategories", {})
        sub_data = subcats.get(subcategory, {})

        if sub_data:
            label = sub_data.get("label", subcategory)
            emoji = sub_data.get("emoji", "📄")
            title = f"{emoji} {label}"
            fields = sub_data.get("fields", [])

    embed = create_embed(
        title=title,
        description="Preencha as informações solicitadas abaixo para dar prosseguimento ao seu atendimento.",
        color=EMBED_COLOR
    )

    if fields:
        field_list = "\n".join([f"• {field}" for field in fields])
        embed.add_field(
            name="📋 Informações Necessárias",
            value=field_list,
            inline=False
        )

    embed.set_image(
        url=ASSETS["banner_ticket"]
    )

    return embed
