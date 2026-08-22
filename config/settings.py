# =========================
# 🧠 IDENTIDADE DO BOT
# LOVAT BOT
# =========================

PROJECT_NAME = "Lovat Bot"

VERSION_NAME = "V0.0.1"

VERSION_DESCRIPTION = (
    "Sistema operacional de tickets + "
    "moderação + "
    "utilidades + "
    "social"
)

VERSION_FULL = (
    f"{VERSION_NAME} | "
    f"{VERSION_DESCRIPTION}"
)

# =========================
# 🌐 IDS DO DISCORD
# =========================

GUILD_ID = 1486383328859787515

# =========================
# ⚙️ COMPORTAMENTO DO BOT
# =========================

PREFIX = "!"

SYNC_GLOBAL = True
SYNC_GUILD = True

# =========================
# 🎫 CONFIGURAÇÕES DE TICKETS
# =========================

TICKET_SYSTEM_ENABLED = True

TICKET_CLOSE_ENABLED = True

TICKET_TRANSCRIPT_ENABLED = True

TICKET_AUTO_CLOSE_ENABLED = True

TICKET_PERSISTENT_VIEWS = True

# =========================
# ⏰ AUTO CLOSE
# =========================

AUTO_CLOSE_OPTIONS = [
    30,
    60,
    120,
    360,
    720,
    1440
]

AUTO_CLOSE_WARNING_1 = 30
AUTO_CLOSE_WARNING_2 = 15

# =========================
# 🎛️ FEATURE FLAGS
# =========================

FEATURES = {

    "tickets": True,

    "moderation": True,

    "logs": True,

    "auto_close": True,

    "transcripts": True,

    "dropdowns": True,

    "routing": True,

    "persistent_views": True
}
