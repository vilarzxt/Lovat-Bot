import os
import requests
from urllib.parse import urlencode

# =========================
# 🔐 DISCORD OAUTH2
#
# Requer estas variáveis no .env:
#   DISCORD_CLIENT_ID      -> Application ID (Discord Developer Portal)
#   DISCORD_CLIENT_SECRET  -> Client Secret (aba OAuth2 do Developer Portal)
#   DISCORD_REDIRECT_URI   -> ex: https://lovatbot.wispbyte.com/callback
#                              (precisa estar cadastrada no Developer Portal,
#                              aba OAuth2 > Redirects)
# =========================

DISCORD_API = "https://discord.com/api"

CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI")

# "identify" -> dados básicos do usuário (id, nome, avatar)
# "guilds"   -> lista de servidores em que o usuário está
SCOPES = "identify guilds"


def get_oauth_url() -> str:
    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": SCOPES,
        "prompt": "consent",
    }
    return f"{DISCORD_API}/oauth2/authorize?{urlencode(params)}"


def exchange_code(code: str) -> dict | None:
    """Troca o código de autorização por um access_token."""
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    try:
        resp = requests.post(
            f"{DISCORD_API}/oauth2/token",
            data=data,
            headers=headers,
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"[OAUTH_TOKEN_ERROR] {e}", flush=True)
        return None


def get_current_user(access_token: str) -> dict | None:
    try:
        resp = requests.get(
            f"{DISCORD_API}/users/@me",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"[OAUTH_USER_ERROR] {e}", flush=True)
        return None


def get_user_guilds(access_token: str) -> list:
    """Retorna os servidores do usuário logado onde ele tem permissão de Administrador."""
    try:
        resp = requests.get(
            f"{DISCORD_API}/users/@me/guilds",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )
        resp.raise_for_status()
        guilds = resp.json()
    except Exception as e:
        print(f"[OAUTH_GUILDS_ERROR] {e}", flush=True)
        return []

    admin_guilds = []
    for g in guilds:
        try:
            permissions = int(g.get("permissions", 0))
        except (TypeError, ValueError):
            permissions = 0

        is_owner = g.get("owner", False)
        is_admin = is_owner or (permissions & 0x8) == 0x8  # 0x8 = ADMINISTRATOR

        if is_admin:
            admin_guilds.append(g)

    return admin_guilds
