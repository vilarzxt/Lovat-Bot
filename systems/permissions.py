# =========================
# 🔐 PERMISSIONS ENGINE (GUILD-AWARE)
# LOVAT BOT
# =========================

from typing import List
from config.guild_config import get_role_levels, get_ticket_categories

def resolve_role(role_name: str) -> str:
    return role_name.lower()

def resolve_roles(user_roles: List[str]) -> List[str]:
    return [resolve_role(r) for r in user_roles]

def get_role_level(guild_id: int, role_name: str) -> int:
    resolved = resolve_role(role_name)
    role_levels = get_role_levels(guild_id)
    return role_levels.get(resolved, -1)

def get_user_highest_level(guild_id: int, roles: List[str]) -> int:
    levels = [get_role_level(guild_id, r) for r in roles]
    return max(levels, default=-1)

def can_access_ticket(guild_id: int, user_roles: List[str], category_key: str) -> bool:
    categories = get_ticket_categories(guild_id)
    category = categories.get(category_key)

    if not category:
        return False

    resolved = resolve_roles(user_roles)

    if "fundador" in resolved:
        return True

    user_level = get_user_highest_level(guild_id, user_roles)
    min_level = category.get("min_level", 0)

    return user_level >= min_level

def can_close_ticket(guild_id: int, user_roles: List[str], category_key: str = "generic") -> bool:
    resolved = resolve_roles(user_roles)

    if "fundador" in resolved:
        return True

    user_level = get_user_highest_level(guild_id, user_roles)
    return user_level >= 0

def is_ticket_staff(guild_id: int, user_roles: List[str]) -> bool:
    resolved = resolve_roles(user_roles)

    if "fundador" in resolved:
        return True

    user_level = get_user_highest_level(guild_id, user_roles)
    return user_level >= 0
