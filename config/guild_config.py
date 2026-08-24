import json
import os
from copy import deepcopy

# =========================
# ⚙️ CONFIGURAÇÃO DEFAULT POR GUILD
# =========================

DEFAULT_GUILD_CONFIG = {
    "prefix": "!",
    "log_channel_id": None,
    "role_levels": {
        "staff": 0,
        "moderador": 1,
        "fundador": 99
    },
    "ticket_categories": {
        "suporte_geral": {
            "label": "Suporte Geral",
            "emoji": "🛠️",
            "min_level": 0,
            "subcategories": {
                "duvidas_gerais": {
                    "label": "Dúvidas Gerais",
                    "emoji": "❓",
                    "fields": ["Descrição da Dúvida"]
                },
                "suporte_tecnico": {
                    "label": "Suporte Técnico",
                    "emoji": "🛠️",
                    "fields": ["Plataforma", "Descrição do Problema", "Prints ou Vídeos"]
                }
            }
        },
        "sugestoes": {
            "label": "Sugestões",
            "emoji": "💡",
            "min_level": 0,
            "subcategories": {
                "sugestao_geral": {
                    "label": "Sugestão Geral",
                    "emoji": "💡",
                    "fields": ["Sua Sugestão", "Motivo/Justificativa"]
                }
            }
        },
        "denuncias": {
            "label": "Denúncia/Report",
            "emoji": "🚨",
            "min_level": 0,
            "subcategories": {
                "denuncia_membro": {
                    "label": "Denúncia de Membro",
                    "emoji": "👤",
                    "fields": ["Nome/ID do membro", "Motivo", "Data e horário", "Provas"]
                },
                "denuncia_staff": {
                    "label": "Denúncia de Staff",
                    "emoji": "👮",
                    "fields": ["Nome/ID do membro da staff", "Motivo", "Data e horário", "Provas"]
                }
            }
        }
    }
}

DATA_DIR = "data/guilds"

# =========================
# 📂 FUNÇÕES DE ARQUIVO
# =========================

def _get_guild_file_path(guild_id: int) -> str:
    os.makedirs(DATA_DIR, exist_ok=True)
    return os.path.join(DATA_DIR, f"{guild_id}.json")

def get_guild_config(guild_id: int) -> dict:
    file_path = _get_guild_file_path(guild_id)
    if not os.path.exists(file_path):
        config = deepcopy(DEFAULT_GUILD_CONFIG)
        save_guild_config(guild_id, config)
        return config

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[GUILD_CONFIG] erro ao ler config de {guild_id}: {e}", flush=True)
        return deepcopy(DEFAULT_GUILD_CONFIG)

def save_guild_config(guild_id: int, config: dict):
    file_path = _get_guild_file_path(guild_id)
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"[GUILD_CONFIG] erro ao salvar config de {guild_id}: {e}", flush=True)

# =========================
# 🛠️ HELPERS
# =========================

def get_role_levels(guild_id: int) -> dict:
    config = get_guild_config(guild_id)
    return config.get("role_levels", DEFAULT_GUILD_CONFIG["role_levels"])

def get_ticket_categories(guild_id: int) -> dict:
    config = get_guild_config(guild_id)
    return config.get("ticket_categories", DEFAULT_GUILD_CONFIG["ticket_categories"])

def get_prefix(guild_id: int) -> str:
    config = get_guild_config(guild_id)
    return config.get("prefix", DEFAULT_GUILD_CONFIG["prefix"])

def update_guild_config(guild_id: int, key: str, value):
    config = get_guild_config(guild_id)
    config[key] = value
    save_guild_config(guild_id, config)
