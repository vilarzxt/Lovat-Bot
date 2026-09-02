import os
import json

DATA_DIR = "data/guilds"

def _get_economy_file_path(guild_id: int) -> str:
    guild_folder = os.path.join(DATA_DIR, str(guild_id))
    os.makedirs(guild_folder, exist_ok=True)
    return os.path.join(guild_folder, "economy.json")

def load_economy(guild_id: int) -> dict:
    file_path = _get_economy_file_path(guild_id)
    if not os.path.exists(file_path):
        return {}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[ECONOMY] Erro ao carregar arquivo de {guild_id}: {e}", flush=True)
        return {}

def save_economy(guild_id: int, data: dict):
    file_path = _get_economy_file_path(guild_id)
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"[ECONOMY] Erro ao salvar arquivo de {guild_id}: {e}", flush=True)

def get_user_data(guild_id: int, user_id: int) -> dict:
    econ = load_economy(guild_id)
    str_id = str(user_id)
    if str_id not in econ:
        econ[str_id] = {"saldo": 0, "ultimo_daily": None}
        save_economy(guild_id, econ)
    return econ[str_id]

def get_saldo(guild_id: int, user_id: int) -> int:
    return get_user_data(guild_id, user_id).get("saldo", 0)

def add_saldo(guild_id: int, user_id: int, valor: int) -> int:
    econ = load_economy(guild_id)
    str_id = str(user_id)
    user_data = econ.get(str_id, {"saldo": 0, "ultimo_daily": None})
    user_data["saldo"] = user_data.get("saldo", 0) + valor
    econ[str_id] = user_data
    save_economy(guild_id, econ)
    return user_data["saldo"]

def remove_saldo(guild_id: int, user_id: int, valor: int) -> bool:
    econ = load_economy(guild_id)
    str_id = str(user_id)
    user_data = econ.get(str_id, {"saldo": 0, "ultimo_daily": None})
    if user_data.get("saldo", 0) < valor:
        return False
    user_data["saldo"] -= valor
    econ[str_id] = user_data
    save_economy(guild_id, econ)
    return True

def set_saldo(guild_id: int, user_id: int, valor: int) -> int:
    econ = load_economy(guild_id)
    str_id = str(user_id)
    user_data = econ.get(str_id, {"saldo": 0, "ultimo_daily": None})
    user_data["saldo"] = max(0, valor)
    econ[str_id] = user_data
    save_economy(guild_id, econ)
    return user_data["saldo"]


def get_ultimo_daily(guild_id: int, user_id: int) -> str | None:
    return get_user_data(guild_id, user_id).get("ultimo_daily")

def set_ultimo_daily(guild_id: int, user_id: int, timestamp_iso: str):
    econ = load_economy(guild_id)
    str_id = str(user_id)
    user_data = econ.get(str_id, {"saldo": 0, "ultimo_daily": None})
    user_data["ultimo_daily"] = timestamp_iso
    econ[str_id] = user_data
    save_economy(guild_id, econ)
