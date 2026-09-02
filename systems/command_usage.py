import os
import json
from datetime import datetime, timezone

# =========================
# 📊 REGISTRO DE USO DE COMANDOS
#
# Toda vez que alguém usa QUALQUER slash command do bot, isso fica
# registrado aqui: quem usou, qual comando, em qual servidor, quando.
# Usado só para o painel admin do dono ver quem realmente interage
# com o bot (diferente da lista de membros, que inclui quem nunca
# usou nada).
# =========================

DATA_DIR = "data/guilds"


def _get_usage_file_path(guild_id: int) -> str:
    guild_folder = os.path.join(DATA_DIR, str(guild_id))
    os.makedirs(guild_folder, exist_ok=True)
    return os.path.join(guild_folder, "command_usage.json")


def load_usage(guild_id: int) -> dict:
    file_path = _get_usage_file_path(guild_id)
    if not os.path.exists(file_path):
        return {}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[COMMAND_USAGE] Erro ao carregar arquivo de {guild_id}: {e}", flush=True)
        return {}


def save_usage(guild_id: int, data: dict):
    file_path = _get_usage_file_path(guild_id)
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"[COMMAND_USAGE] Erro ao salvar arquivo de {guild_id}: {e}", flush=True)


def log_command_use(guild_id: int, user_id: int, command_name: str):
    """Registra que um usuário usou um comando. Chamado automaticamente
    pelo bot para todo slash command, sem precisar mexer em cada comando."""
    if guild_id is None:
        return  # comandos usados em DM não são rastreados por servidor

    usage = load_usage(guild_id)
    str_id = str(user_id)

    user_entry = usage.get(str_id, {"commands": {}, "last_used": None})
    user_entry["commands"][command_name] = user_entry["commands"].get(command_name, 0) + 1
    user_entry["last_used"] = datetime.now(timezone.utc).isoformat()

    usage[str_id] = user_entry
    save_usage(guild_id, usage)
