import os
from functools import wraps

from flask import Blueprint, render_template, session, redirect, url_for, flash, request

from webapp import state
from config.assets import ASSETS
from config.owner_notes import get_note, set_note, TAGS
from config.bot_settings import get_bot_settings, update_bot_setting

owner_bp = Blueprint("owner", __name__)


def get_owner_id() -> str:
    return os.getenv("OWNER_DISCORD_ID", "")


def is_owner_session() -> bool:
    user = session.get("user")
    owner_id = get_owner_id()
    return bool(user and owner_id and str(user.get("id")) == owner_id)


def owner_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user" not in session:
            flash("Você precisa entrar com o Discord para acessar essa página.")
            return redirect(url_for("auth.login"))
        if not is_owner_session():
            flash("Essa página é restrita ao dono do bot.")
            return redirect(url_for("public.home"))
        return view(*args, **kwargs)
    return wrapped


@owner_bp.route("/painel-admin")
@owner_required
def painel_admin():
    bot = state.get_bot()
    guilds_data = []

    if bot is not None:
        for guild in sorted(
            bot.guilds,
            key=lambda g: g.me.joined_at or 0,
            reverse=True,
        ):
            note = get_note(guild.id)

            owner_name = None
            if guild.owner:
                owner_name = guild.owner.display_name

            guilds_data.append({
                "id": guild.id,
                "name": guild.name,
                "icon_url": guild.icon.url if guild.icon else None,
                "member_count": guild.member_count,
                "owner_name": owner_name,
                "joined_at": guild.me.joined_at.strftime("%d/%m/%Y") if guild.me.joined_at else "—",
                "tag": note["tag"],
                "note": note["note"],
            })

    return render_template(
        "owner_panel.html",