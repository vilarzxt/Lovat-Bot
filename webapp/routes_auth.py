from flask import Blueprint, redirect, request, session, url_for, flash

from webapp import discord_oauth

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login")
def login():
    return redirect(discord_oauth.get_oauth_url())


@auth_bp.route("/callback")
def callback():
    code = request.args.get("code")

    if not code:
        flash("Login cancelado ou inválido.")
        return redirect(url_for("public.home"))

    token_data = discord_oauth.exchange_code(code)

    if not token_data or "access_token" not in token_data:
        flash("Não foi possível concluir o login com o Discord. Tente novamente.")
        return redirect(url_for("public.home"))

    access_token = token_data["access_token"]
    user = discord_oauth.get_current_user(access_token)

    if not user:
        flash("Não foi possível obter seus dados do Discord.")
        return redirect(url_for("public.home"))

    # Guardamos só o essencial na sessão: id/nome do usuário e o token
    # (necessário pra buscar a lista de servidores depois).
    session.permanent = True
    session["user"] = {
        "id": user.get("id"),
        "username": user.get("username"),
        "avatar": user.get("avatar"),
    }
    session["access_token"] = access_token

    return redirect(url_for("dashboard.meus_servidores"))


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("public.home"))
