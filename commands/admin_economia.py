import os
import discord
from discord.ext import commands
from discord import app_commands

from config.assets import EMBED_COLOR
from config.bot_settings import is_system_enabled
from systems.utils import create_embed
from systems.economy import get_saldo, set_saldo, add_saldo
from systems.social import get_user_social, set_xp

# =========================
# 👑 ADMIN ECONOMIA (SÓ O DONO)
#
# Funciona em QUALQUER servidor onde o bot esteja, mesmo que o dono
# não tenha permissão de administrador ali — a checagem é pelo ID
# fixo do dono (OWNER