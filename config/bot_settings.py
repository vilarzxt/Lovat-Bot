import json
import os
from copy import deepcopy

# =========================
# ⚙️ CONFIGURAÇÕES GLOBAIS DO BOT
#
# Diferente de config/guild_config.py (que é por servidor), este
# arquivo guarda ajustes que valem para o bot inteiro, em todos os
# servidores — controlado só pelo dono via /painel-admin/configuracoes.
# =========================

SETTINGS_FILE = "data/bot_settings.json"

DEFAULT_SETTINGS = {
    "mensagens": {
        "boas_vindas_padrao": "👋 Bem-vindo(a) ao servidor, {usuario}!",
        "despedida_padrao": "👋 {usuario} saiu do servidor.",
        "erro_generico": "❌ Ocorreu um erro ao processar seu comando. Tente novamente mais tarde.",
        "rodape_padrao": "Lovat Bot — Sistema Oficial",
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


def get_bot_settings() -> dict:
    _ensure_file()
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        merged = deepcopy(DEFAULT_SETTINGS)
        if isinstance(data, dict):
            if "mensagens" in data and isinstance(data["mensagens"], dict):
                merged["mensagens"].update(data["mensagens"])
            if "sistemas_ativos" in data and isinstance(data["sistemas_ativos"], dict):
                merged["sistemas_ativos"].update(data["sistemas_ativos"])
            for k, v in data.items():
                if k not in ["mensagens", "sistemas_ativos"]:
                    merged[k] = v
        return merged
    except Exception as e:
        print(f"[BOT_SETTINGS] erro ao ler: {e}", flush=True)
        return deepcopy(DEFAULT_SETTINGS)


# Alias para compatibilidade
get_settings = get_bot_settings


def save_bot_settings(data: dict):
    os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"[BOT_SETTINGS] erro ao salvar: {e}", flush=True)


save_settings = save_bot_settings


def update_bot_setting(key: str, value):
    settings = get_bot_settings()
    settings[key] = value
    save_bot_settings(settings)


def is_system_enabled(system_name: str) -> bool:
    settings = get_bot_settings()
    return bool(settings.get("sistemas_ativos", {}).get(system_name, True))
