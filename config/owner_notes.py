import json
import os
from copy import deepcopy

# =========================
# 🗂️ ANOTAÇÕES DO DONO POR SERVIDOR
#
# Isso é só para uso pessoal do dono do bot no painel admin —
# não afeta em nada o funcionamento do bot no Discord. Serve
# apenas para ele organizar visualmente quais servidores são
# de amigos, conhecidos, parcerias etc.
# =========================

NOTES_FILE = "data/owner_notes.json"

TAGS = {
    "amigo": "👥 Amigo",
    "conhecido": "🙂 Conhecido",
    "parceria": "🤝 Parceria",
    "teste": "🧪 Teste",
    "desconhecido": "❓ Desconhecido",
}

DEFAULT_TAG = "desconhecido"


def _ensure_file():
    os.makedirs(os.path.dirname(NOTES_FILE), exist_ok=True)
    if not os.path.exists(NOTES_FILE):
        with open(NOTES_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)


def get_all_notes() -> dict:
    _ensure_file()
    try:
        with open(NOTES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[OWNER_NOTES] erro ao ler: {e}", flush=True)
        return {}


def get_note(guild_id: int) -> dict:
    notes = get_all_notes()
    return notes.get(str(guild_id), {"tag": DEFAULT_TAG, "note": ""})


def set_note(guild_id: int, tag: str, note: str):
    notes = get_all_notes()
    if tag not in TAGS:
        tag = DEFAULT_TAG
    notes[str(guild_id)] = {"tag": tag, "note": note.strip()[:200]}
    try:
        with open(NOTES_FILE, "w", encoding="utf-8") as f:
            json.dump(notes, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"[OWNER_NOTES] erro ao salvar: {e}", flush=True)
