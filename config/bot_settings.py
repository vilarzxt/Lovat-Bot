import json
import os

# =========================
# ⚙️ CONFIGURAÇÕES GLOBAIS DO BOT
#
# Diferente de config/guild_config.py (que é por servidor), este
# arquivo guarda ajustes que valem para o bot inteiro, em todos os
# servidores — controlado só pelo dono via /painel-admin/config.
# =========================

SETTINGS_FILE = "data/bot_settings.json"

DEFAULT_SETTINGS = {
    "mensagens": {
        "boas_vindas_padrao": "👋 Bem-vindo(a) ao servidor, {usuario}!",
        "despedida_padrao": "👋 {usuario} saiu do servidor.",
    },
    "sistemas_ativos": {
        "economia": True,
        "musica": True,
        "tickets": True,
        "moderacao": True,
        "social": True,
        "diversao": True,
        "utilidades": True,
    },
}


def _ensure_file():
    os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
    if not os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_SETTINGS, f, indent=4, ensure_ascii=False)


def get_settings() -> dict:
    _ensure_file()
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        # garante que chaves novas adicionadas depois não quebrem configs antigas
        merged = {**DEFAULT_SETTINGS, **data}
        merged["mensagens"] = {**DEFAULT_SETTINGS["mensagens"], **data.get("mensagens", {})}
        merged["sistemas_ativos"] = {**DEFAULT_SETTINGS["sistemas_ativos"], **data.get("sistemas_ativos", {})}
        return merged
    except Exception as e:
        print(f"[BOT_SETTINGS] erro ao ler: {e}", flush=True)
        return DEFAULT_SETTINGS


def save_settings(data: dict):
    os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"[BOT_SETTINGS] erro ao salvar: {e}", flush=True)


def is_system_enabled(system_name: str) -> bool:
    return get_settings()["sistemas_ativos"].get(system_name, True)
