import os
from functools import wraps

from flask import Blueprint, render_template, session, redirect, url_for, flash, request

from webapp import state
from config.assets import ASSETS
from config.owner_notes import get_note, set_note, TAGS
from config.bot_settings import get_bot_settings, update_bot_setting
from systems.command_usage import load_usage

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
        logo_url=ASSETS["logo"],
        guilds=guilds_data,
        tags=TAGS,
    )


@owner_bp.route("/painel-admin/nota/<int:guild_id>", methods=["POST"])
@owner_required
def salvar_nota(guild_id: int):
    tag = request.form.get("tag", "outro")
    note = request.form.get("note", "").strip()
    set_note(guild_id, tag, note)
    flash("Etiqueta / anotação atualizada!")
    return redirect(url_for("owner.painel_admin"))


@owner_bp.route("/painel-admin/remover/<int:guild_id>", methods=["POST"])
@owner_required
def remover_servidor(guild_id: int):
    ok, msg = state.leave_guild(guild_id)
    if ok:
        flash(f"Bot removido do servidor com sucesso: {msg}")
    else:
        flash(f"Não foi possível sair: {msg}")
    return redirect(url_for("owner.painel_admin"))


@owner_bp.route("/painel-admin/usuarios")
@owner_required
def painel_usuarios():
    bot = state.get_bot()
    users_map = {}

    if bot is not None:
        for guild in bot.guilds:
            usage = load_usage(guild.id)

            for uid_str, data in usage.items():
                uid = int(uid_str)
                member = guild.get_member(uid)

                entry = users_map.setdefault(uid, {
                    "id": uid,
                    "name": str(member) if member else f"Usuário {uid} (saiu do servidor)",
                    "avatar_url": member.display_avatar.url if member else None,
                    "is_bot": member.bot if member else False,
                    "guilds": [],
                    "commands": {},
                    "total_usos": 0,
                    "last_used": None,
                })
                entry["guilds"].append(guild.name)
                for cmd_name, count in data.get("commands", {}).items():
                    entry["commands"][cmd_name] = entry["commands"].get(cmd_name, 0) + count
                    entry["total_usos"] += count
                if data.get("last_used") and (
                    entry["last_used"] is None or data["last_used"] > entry["last_used"]
                ):
                    entry["last_used"] = data["last_used"]

    users_list = list(users_map.values())
    for u in users_list:
        u["top_commands"] = sorted(u["commands"].items(), key=lambda x: -x[1])[:3]

    users_list.sort(key=lambda u: (u["is_bot"], -u["total_usos"], u["name"].lower()))

    total_pessoas = sum(1 for u in users_list if not u["is_bot"])
    total_bots = sum(1 for u in users_list if u["is_bot"])

    return render_template(
        "owner_users.html",
        logo_url=ASSETS["logo"],
        users=users_list,
        total_pessoas=total_pessoas,
        total_bots=total_bots,
    )


@owner_bp.route("/painel-admin/configuracoes")
@owner_required
def painel_configuracoes():
    settings = get_bot_settings()
    mensagens = settings.get("mensagens", {})
    sistemas = settings.get("sistemas_ativos", {})
    return render_template(
        "owner_config.html",
        logo_url=ASSETS["logo"],
        mensagens=mensagens,
        sistemas=sistemas,
    )


@owner_bp.route("/painel-admin/configuracoes/salvar", methods=["POST"])
@owner_required
def salvar_configuracoes():
    settings = get_bot_settings()
    mensagens = settings.get("mensagens", {})
    sistemas = settings.get("sistemas_ativos", {})

    mensagens["boas_vindas_padrao"] = request.form.get("msg_boas_vindas", mensagens.get("boas_vindas_padrao", "")).strip()
    mensagens["despedida_padrao"] = request.form.get("msg_despedida", mensagens.get("despedida_padrao", "")).strip()
    mensagens["erro_generico"] = request.form.get("msg_erro", mensagens.get("erro_generico", "")).strip()
    mensagens["rodape_padrao"] = request.form.get("msg_rodape", mensagens.get("rodape_padrao", "")).strip()

    for sistema_key in sistemas.keys():
        sistemas[sistema_key] = request.form.get(f"sistema_{sistema_key}") is not None

    update_bot_setting("mensagens", mensagens)
    update_bot_setting("sistemas_ativos", sistemas)

    flash("Configurações globais salvas com sucesso!")
    return redirect(url_for("owner.painel_configuracoes"))
