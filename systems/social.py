import os
import json
import math
from datetime import datetime, timezone, timedelta

DATA_DIR = "data/guilds"

def _get_social_file_path(guild_id: int) -> str:
    guild_folder = os.path.join(DATA_DIR, str(guild_id))
    os.makedirs(guild_folder, exist_ok=True)
    return os.path.join(guild_folder, "social.json")

def load_social(guild_id: int) -> dict:
    file_path = _get_social_file_path(guild_id)
    if not os.path.exists(file_path):
        return {}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[SOCIAL] Erro ao carregar arquivo de {guild_id}: {e}", flush=True)
        return {}

def save_social(guild_id: int, data: dict):
    file_path = _get_social_file_path(guild_id)
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"[SOCIAL] Erro ao salvar arquivo de {guild_id}: {e}", flush=True)

def calc_level(xp: int) -> int:
    return int((xp / 50) ** 0.5) + 1

def get_user_social(guild_id: int, user_id: int) -> dict:
    soc = load_social(guild_id)
    str_id = str(user_id)
    if str_id not in soc:
        soc[str_id] = {
            "xp": 0,
            "nivel": 1,
            "ultima_mensagem": None,
            "bio": "",
            "reputacao": 0,
            "last_rep_given": {}
        }
        save_social(guild_id, soc)
    return soc[str_id]

def add_xp(guild_id: int, user_id: int, xp_amount: int) -> tuple[int, bool]:
    soc = load_social(guild_id)
    str_id = str(user_id)
    user_data = soc.get(str_id, {
        "xp": 0, "nivel": 1, "ultima_mensagem": None, "bio": "", "reputacao": 0, "last_rep_given": {}
    })

    old_lvl = user_data.get("nivel", 1)
    new_xp = user_data.get("xp", 0) + xp_amount
    new_lvl = calc_level(new_xp)

    user_data["xp"] = new_xp
    user_data["nivel"] = new_lvl
    user_data["ultima_mensagem"] = datetime.now(timezone.utc).isoformat()
    soc[str_id] = user_data
    save_social(guild_id, soc)

    leveled_up = new_lvl > old_lvl
    return new_lvl, leveled_up

def set_xp(guild_id: int, user_id: int, xp_amount: int) -> int:
    soc = load_social(guild_id)
    str_id = str(user_id)
    user_data = get_user_social(guild_id, user_id)
    user_data["xp"] = max(0, xp_amount)
    user_data["nivel"] = calc_level(user_data["xp"])
    soc[str_id] = user_data
    save_social(guild_id, soc)
    return user_data["nivel"]


def set_bio(guild_id: int, user_id: int, bio_text: str):
    soc = load_social(guild_id)
    str_id = str(user_id)
    user_data = get_user_social(guild_id, user_id)
    user_data["bio"] = bio_text[:200]
    soc[str_id] = user_data
    save_social(guild_id, soc)

def add_rep(guild_id: int, target_id: int, giver_id: int) -> tuple[bool, str]:
    if target_id == giver_id:
        return False, "Você não pode dar reputação a si mesmo."

    soc = load_social(guild_id)
    giver_data = soc.get(str(giver_id), {})
    last_rep_dict = giver_data.get("last_rep_given", {})

    now = datetime.now(timezone.utc)
    target_str = str(target_id)

    if target_str in last_rep_dict:
        last_date = datetime.fromisoformat(last_rep_dict[target_str])
        if now - last_date < timedelta(hours=24):
            return False, "Você já deu reputação para este usuário nas últimas 24 horas."

    target_data = get_user_social(guild_id, target_id)
    target_data["reputacao"] = target_data.get("reputacao", 0) + 1
    soc[str(target_id)] = target_data

    giver_data = get_user_social(guild_id, giver_id)
    if "last_rep_given" not in giver_data:
        giver_data["last_rep_given"] = {}
    giver_data["last_rep_given"][target_str] = now.isoformat()
    soc[str(giver_id)] = giver_data

    save_social(guild_id, soc)
    return True, "Reputação enviada com sucesso!"
