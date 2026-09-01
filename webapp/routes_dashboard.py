from functools import wraps

from flask import Blueprint, render_template, session, redirect, url_for, flash

from webapp import discord_oauth, state
from webapp.routes_public import get_invite_url
from config.assets import ASSETS
from config.guild_config import get_guild_config

dashboard_bp = Blueprint("dashboard", __name__)


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user" not in session or "access_token" not in session:
            flash("Você precisa entrar com o Discord para acessar essa página.")
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)
    return wrapped


@dashboard_bp.route("/servidores")
@login_required
def meus_servidores():
    access_token = session["access_token"]
    admin_guilds = discord_oauth.get_user_guilds(access_token)

    # Guarda os IDs em sessão pra checagem de permissão nas próximas páginas
    # sem precisar bater na API do Discord de novo a cada clique.
    session["admin_guild_ids"] = [g["id"] for g in admin_guilds]

    guilds = []
    for g in admin_guilds:
        icon_url = None
        if g.get("icon"):
            icon_url = f"https://cdn.discordapp.com/icons/{g['id']}/{g['icon']}.png"

        guilds.append({
            "id": g["id"],
            "name": g["name"],
            "icon_url": icon_url,
            "bot_present": state.get_bot_guild(int(g["id"])) is not None,
        })

    return render_template(
        "servidores.html",
        logo_url=ASSETS["logo"],
        guilds=guilds,
        invite_url=get_invite_url(),
    )


@dashboard_bp.route("/painel/<guild_id>")
@login_required
def painel_servidor(guild_id):
    admin_guild_ids = session.get("admin_guild_ids", [])

    if guild_id not in admin_guild_ids:
        flash("Você não tem permissão de administrador nesse servidor.")
        return redirect(url_for("dashboard.meus_servidores"))

    guild = state.get_bot_guild(int(guild_id))
    if guild is None:
        flash("O Lovat Bot ainda não está nesse servidor.")
        return redirect(url_for("dashboard.meus_servidores"))

    cfg = get_guild_config(int(guild_id))

    def channel_name(channel_id):
        if not channel_id:
            return "Não configurado"
        ch = guild.get_channel(channel_id)
        return f"#{ch.name}" if ch else "Canal não encontrado"

    def role_name(role_id):
        if not role_id:
            return "Não configurado"
        role = guild.get_role(role_id)
        return role.name if role else "Cargo não encontrado"

    ticket_panels = [
        {
            "id": p["id"],
            "titulo": p.get("conteudo", {}).get("title", "Sem título"),
            "total_opcoes": len(p.get("options", [])),
        }
        for p in cfg.get("ticket_panels", [])
    ]

    return render_template(
        "painel.html",
        logo_url=ASSETS["logo"],
        guild_name=guild.name,
        log_channel=channel_name(cfg.get("log_channel_id")),
        ticket_log_channel=channel_name(cfg.get("ticket_log_channel_id")),
        welcome_channel=channel_name(cfg.get("welcome_channel_id")),
        goodbye_channel=channel_name(cfg.get("goodbye_channel_id")),
        auto_role=role_name(cfg.get("auto_role_id")),
        captcha_enabled=cfg.get("captcha_enabled", False),
        ticket_panels=ticket_panels,
    )
