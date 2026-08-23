# =========================
# 🔐 PERMISSIONS ENGINE
# LOVAT BOT
# =========================

from typing import Dict, List, Optional


# =========================
# 🧠 HIERARQUIA BASE (NÍVEIS)
# =========================

ROLE_LEVELS = {

    "staff": 0,

    "moderador": 1,

    "fundador": 99
}


# =========================
# 🎫 CATEGORIAS DE TICKET
# =========================

TICKET_RULES: Dict[str, Dict] = {

    "suporte_geral": {
        "route": "STAFF_TEAM",
        "min_level": 0
    },

    "duvidas": {
        "route": "STAFF_TEAM",
        "min_level": 0
    },

    "sugestoes": {
        "route": "STAFF_TEAM",
        "min_level": 0
    },

    "denuncia_report": {
        "route": "STAFF_TEAM",
        "min_level": 0
    },

    "financeiro_colaboracao": {
        "route": "MOD_TEAM",
        "min_level": 1  # moderador+
    }
}


# =========================
# 🧠 ROLE GROUPS (TIPOS FUNCIONAIS)
# =========================

STAFF_TEAM = [
    "staff"
]

MOD_TEAM = [
    "moderador"
]

FOUNDER_TEAM = [
    "fundador"
]


# =========================
# 🔐 CORE FUNCTIONS
# =========================

def resolve_role(role_name: str) -> str:

    return role_name.lower()


def resolve_roles(user_roles: List[str]) -> List[str]:

    return [
        resolve_role(r)
        for r in user_roles
    ]


def get_role_level(role_name: str) -> int:

    resolved = resolve_role(role_name)

    return ROLE_LEVELS.get(resolved, -1)


def get_user_highest_level(roles: List[str]) -> int:

    return max(
        [get_role_level(r) for r in roles],
        default=-1
    )


def can_access_ticket(user_roles: List[str], ticket_key: str) -> bool:

    rule = TICKET_RULES.get(ticket_key)

    if not rule:
        return False

    resolved = resolve_roles(user_roles)

    user_level = get_user_highest_level(user_roles)

    # 🧠 FUNDADOR OVERRIDE
    if "fundador" in resolved:
        return True

    return user_level >= rule["min_level"]


def can_close_ticket(user_roles: List[str], ticket_key: str) -> bool:

    resolved = resolve_roles(user_roles)

    user_level = get_user_highest_level(user_roles)

    # 🔥 FUNDADOR OVERRIDE
    if "fundador" in resolved:
        return True

    # Staff (nível 0+) pode fechar qualquer ticket
    return user_level >= 0


# =========================
# 🎫 STAFF CHECK (GERENCIAMENTO GERAL)
# =========================
# Usado pelos botões do painel de ticket
# (Fechar, Atender, Configurações) — apenas
# se a pessoa tem QUALQUER cargo reconhecido
# como staff (nível >= 0).
# =========================

def is_ticket_staff(user_roles: List[str]) -> bool:

    resolved = resolve_roles(user_roles)

    # 🧠 FUNDADOR OVERRIDE
    if "fundador" in resolved:
        return True

    user_level = get_user_highest_level(user_roles)

    return user_level >= 0

