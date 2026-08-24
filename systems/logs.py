import os
import json
from datetime import datetime, timezone
import discord
from config.guild_config import get_guild_config
from config.assets import EMBED_COLOR
from systems.utils import create_embed

DATA_DIR = "data/guilds"

def _get_logs_file_path(guild_id: int) -> str:
    guild_folder = os.path.join(DATA_DIR, str(guild_id))
    os.makedirs(guild_folder, exist_ok=True)
    return os.path.join(guild_folder, "logs.json")

async def log_action(bot, guild_id: int, tipo: str, autor, alvo, motivo: str = None, extra: dict = None):
    try:
        now_iso = datetime.now(timezone.utc).isoformat()

        autor_id = getattr(autor, "id", str(autor))
        autor_nome = str(autor)
        alvo_id = getattr(alvo, "id", str(alvo)) if alvo else None
        alvo_nome = str(alvo) if alvo else None

        log_entry = {
            "tipo": tipo,
            "autor_id": autor_id,
            "autor_nome": autor_nome,
            "alvo_id": alvo_id,
            "alvo_nome": alvo_nome,
            "motivo": motivo,
            "extra": extra or {},
            "timestamp": now_iso
        }

        file_path = _get_logs_file_path(guild_id)
        logs = []
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    logs = json.load(f)
            except Exception as e:
                print(f"[LOGS] erro ao carregar arquivo de logs de {guild_id}: {e}", flush=True)

        logs.append(log_entry)

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(logs, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"[LOGS] erro ao salvar registro no JSON de {guild_id}: {e}", flush=True)

        # Envio de mensagem no canal de logs se configurado
        config = get_guild_config(guild_id)
        log_channel_id = config.get("log_channel_id")

        if log_channel_id and bot:
            channel = bot.get_channel(int(log_channel_id))
            if channel:
                embed = create_embed(
                    title=f"📋 Registro de Log — {tipo.upper()}",
                    color=EMBED_COLOR
                )
                embed.add_field(name="🛡️ Autor", value=f"{autor_nome} ({autor_id})", inline=True)
                if alvo_nome:
                    embed.add_field(name="👤 Alvo", value=f"{alvo_nome} ({alvo_id})", inline=True)
                if motivo:
                    embed.add_field(name="📝 Motivo", value=motivo, inline=False)
                if extra:
                    extra_str = "\n".join([f"• **{k}**: {v}" for k, v in extra.items()])
                    embed.add_field(name="📌 Informações Extras", value=extra_str, inline=False)
                
                embed.set_footer(text=f"Guild ID: {guild_id} | Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
                
                await channel.send(embed=embed)

    except Exception as e:
        print(f"[LOGS] erro geral em log_action: {e}", flush=True)

def get_historico(guild_id: int, alvo_id: int = None, tipo: str = None, limite: int = 20) -> list:
    try:
        file_path = _get_logs_file_path(guild_id)
        if not os.path.exists(file_path):
            return []

        with open(file_path, "r", encoding="utf-8") as f:
            logs = json.load(f)

        filtrados = []
        for log in reversed(logs):
            if alvo_id and str(log.get("alvo_id")) != str(alvo_id):
                continue
            if tipo and log.get("tipo") != tipo:
                continue
            filtrados.append(log)
            if len(filtrados) >= limite:
                break

        return filtrados
    except Exception as e:
        print(f"[LOGS] erro em get_historico para {guild_id}: {e}", flush=True)
        return []
