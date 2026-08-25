import json
import os
from copy import deepcopy

# =========================
# ⚙️ CONFIGURAÇÃO DEFAULT POR GUILD
# =========================

DEFAULT_GLOBAL_TICKET_SETTINGS = {
    "staff_role_ids": [],
    "ticket_category_channel_id": None,
    "mention_role_ids": []
}

DEFAULT_GUILD_CONFIG = {
    "prefix": "!",
    "log_channel_id": None,
    "welcome_channel_id": None,
    "welcome_message": "Seja bem-vindo(a) ao **{server}**, {mention}! Atualmente estamos com **{count}** membros.",
    "goodbye_channel_id": None,
    "goodbye_message": "O usuário **{user}** saiu do servidor **{server}**.",
    "auto_role_id": None,
    "captcha_enabled": False,
    "captcha_role_id": None,
    "captcha_channel_id": None,
    "role_levels": {
        "staff": 0,
        "moderador": 1,
        "fundador": 99
    },
    "global_ticket_settings": DEFAULT_GLOBAL_TICKET_SETTINGS,
    "ticket_panels": []
}

DATA_DIR = "data/guilds"

# =========================
# 📂 FUNÇÕES DE ARQUIVO
# =========================

def _get_guild_file_path(guild_id: int) -> str:
    os.makedirs(DATA_DIR, exist_ok=True)
    return os.path.join(DATA_DIR, f"{guild_id}.json")

def _migrate_config(config: dict) -> dict:
    """
    Migra configurações antigas para o novo formato.
    """
    for key, value in DEFAULT_GUILD_CONFIG.items():
        if key not in config:
            config[key] = deepcopy(value)

    if "global_ticket_settings" not in config:
        config["global_ticket_settings"] = deepcopy(DEFAULT_GLOBAL_TICKET_SETTINGS)

    if "ticket_panels" not in config:
        config["ticket_panels"] = []

    # Migração de 'ticket_categories' antigo para um único painel default
    if "ticket_categories" in config and config["ticket_categories"]:
        old_categories = config["ticket_categories"]
        options = []
        opt_id = 1
        for cat_key, cat_data in old_categories.items():
            subcats = cat_data.get("subcategories", {})
            if subcats:
                for sub_key, sub_data in subcats.items():
                    options.append({
                        "id": opt_id,
                        "label": sub_data.get("label", sub_key),
                        "emoji": sub_data.get("emoji", "📄"),
                        "description": f"Categoria: {cat_data.get('label', cat_key)}",
                        "categoria_vinculada": cat_key
                    })
                    opt_id += 1
            else:
                options.append({
                    "id": opt_id,
                    "label": cat_data.get("label", cat_key),
                    "emoji": cat_data.get("emoji", "📂"),
                    "description": None,
                    "categoria_vinculada": cat_key
                })
                opt_id += 1

        migrated_panel = {
            "id": 1,
            "tipo_conteudo": "embed",
            "tipo_componente": "dropdown",
            "conteudo": {
                "title": "Central de Atendimento",
                "description": "Selecione uma opção abaixo para abrir um ticket.",
                "color": "#3D5A80",
                "url": None,
                "timestamp": False,
                "author": {"name": None, "icon_url": None, "url": None},
                "thumbnail_url": None,
                "image_url": None,
                "footer": {"text": None, "icon_url": None},
                "fields": []
            },
            "options": options,
            "component_settings": {
                "placeholder": "Selecione o tipo do atendimento",
                "min_values": 1,
                "max_values": 1
            },
            "channel_id": None,
            "message_id": None,
            "settings": {
                "staff_role_ids": [],
                "ticket_category_channel_id": None,
                "mention_role_ids": []
            }
        }
        config["ticket_panels"].append(migrated_panel)
        del config["ticket_categories"]

    return config

def get_guild_config(guild_id: int) -> dict:
    file_path = _get_guild_file_path(guild_id)
    if not os.path.exists(file_path):
        config = deepcopy(DEFAULT_GUILD_CONFIG)
        save_guild_config(guild_id, config)
        return config

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            migrated_data = _migrate_config(data)
            return migrated_data
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
# 🛠️ PAINÉIS DE TICKET HELPERS
# =========================

def get_panels(guild_id: int) -> list:
    config = get_guild_config(guild_id)
    return config.get("ticket_panels", [])

def get_panel(guild_id: int, panel_id: int) -> dict | None:
    panels = get_panels(guild_id)
    for p in panels:
        if p["id"] == panel_id:
            return p
    return None

def create_panel(guild_id: int, tipo_conteudo: str = "embed", tipo_componente: str = "dropdown") -> dict:
    config = get_guild_config(guild_id)
    panels = config.get("ticket_panels", [])
    
    next_id = max([p["id"] for p in panels], default=0) + 1

    conteudo_default = {
        "title": "Central de Atendimento",
        "description": "Selecione uma opção abaixo para abrir um ticket.",
        "color": "#3D5A80",
        "url": None,
        "timestamp": False,
        "author": {"name": None, "icon_url": None, "url": None},
        "thumbnail_url": None,
        "image_url": None,
        "footer": {"text": None, "icon_url": None},
        "fields": []
    } if tipo_conteudo == "embed" else {"texto": "Selecione uma opção para abrir um ticket."}

    new_panel = {
        "id": next_id,
        "tipo_conteudo": tipo_conteudo,
        "tipo_componente": tipo_componente,
        "conteudo": conteudo_default,
        "options": [],
        "component_settings": {
            "placeholder": "Selecione o tipo do atendimento",
            "min_values": 1,
            "max_values": 1
        },
        "channel_id": None,
        "message_id": None,
        "settings": {
            "staff_role_ids": [],
            "ticket_category_channel_id": None,
            "mention_role_ids": []
        }
    }

    panels.append(new_panel)
    config["ticket_panels"] = panels
    save_guild_config(guild_id, config)
    return new_panel

def update_panel(guild_id: int, panel_id: int, dados: dict):
    config = get_guild_config(guild_id)
    panels = config.get("ticket_panels", [])
    for idx, p in enumerate(panels):
        if p["id"] == panel_id:
            panels[idx] = dados
            break
    config["ticket_panels"] = panels
    save_guild_config(guild_id, config)

def delete_panel(guild_id: int, panel_id: int):
    config = get_guild_config(guild_id)
    panels = [p for p in config.get("ticket_panels", []) if p["id"] != panel_id]
    config["ticket_panels"] = panels
    save_guild_config(guild_id, config)

# =========================
# 🌍 GLOBAL SETTINGS HELPERS
# =========================

def get_global_ticket_settings(guild_id: int) -> dict:
    config = get_guild_config(guild_id)
    return config.get("global_ticket_settings", deepcopy(DEFAULT_GLOBAL_TICKET_SETTINGS))

def update_global_ticket_settings(guild_id: int, dados: dict):
    config = get_guild_config(guild_id)
    config["global_ticket_settings"] = dados
    save_guild_config(guild_id, config)

def get_role_levels(guild_id: int) -> dict:
    config = get_guild_config(guild_id)
    return config.get("role_levels", DEFAULT_GUILD_CONFIG["role_levels"])

def get_prefix(guild_id: int) -> str:
    config = get_guild_config(guild_id)
    return config.get("prefix", DEFAULT_GUILD_CONFIG["prefix"])

def update_guild_config(guild_id: int, key: str, value):
    config = get_guild_config(guild_id)
    config[key] = value
    save_guild_config(guild_id, config)
