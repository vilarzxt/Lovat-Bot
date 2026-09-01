import os
from flask import Blueprint, render_template

from webapp import state
from config.command_catalog import COMMAND_CATEGORIES, get_total_command_count
from config.settings import VERSION_FULL
from config.assets import ASSETS

public_bp = Blueprint("public", __name__)


def _format_uptime(seconds: float) -> str:
    seconds = int(seconds)
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)

    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes or not parts:
        parts.append(f"{minutes}m")

    return " ".join(parts)


def get_invite_url() -> str:
    client_id = os.getenv("DISCORD_CLIENT_ID", "")
    # Permissions = Administrator (8). Um bot multifuncional (moderação,
    # tickets, cargos, canais) precisa de bastante acesso; pode ser
    # restringido depois se quiser um set de permissões mais granular.
    return (
        f"https://discord.com/api/oauth2/authorize"
        f"?client_id={client_id}&permissions=8&scope=bot%20applications.commands"
    )


@public_bp.route("/")
def home():
    return render_template(
        "home.html",
        logo_url=ASSETS["logo"],
        invite_url=get_invite_url(),
        guild_count=state.get_guild_count(),
        user_count=state.get_user_count(),
    )


@public_bp.route("/comandos")
def comandos():
    return render_template(
        "comandos.html",
        logo_url=ASSETS["logo"],
        categories=COMMAND_CATEGORIES,
        total_commands=get_total_command_count(),
    )


@public_bp.route("/status")
def status():
    return render_template(
        "status.html",
        logo_url=ASSETS["logo"],
        online=state.is_bot_online(),
        uptime=_format_uptime(state.get_uptime_seconds()),
        guild_count=state.get_guild_count(),
        user_count=state.get_user_count(),
        latency=state.get_latency_ms(),
        version=VERSION_FULL,
    )
