import discord

from config.assets import (
    ASSETS,
    EMBED_COLOR,
    FOOTER_TEXT
)

# =========================
# 🎨 EMBED FACTORY
# LOVAT BOT
# =========================

def create_embed(
    title: str,
    description: str = None,
    color: int = EMBED_COLOR,
    image: str = None
):

    embed = discord.Embed(
        title=title,
        description=description,
        color=color
    )

    embed.set_thumbnail(
        url=ASSETS["logo"]
    )

    if image:

        embed.set_image(
            url=image
        )

    embed.set_footer(
        text=FOOTER_TEXT,
        icon_url=ASSETS["logo"]
    )

    return embed
