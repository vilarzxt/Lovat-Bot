import re
import discord
from systems.permissions import is_ticket_staff
from commands.config import log_action

INVITE_REGEX = re.compile(r"(discord\.(gg|io|me|li)|discordapp\.com\/invite|discord\.com\/invite)\/[a-zA-Z0-9]+", re.IGNORECASE)

async def handle_anti_invite(message: discord.Message):
    try:
        if not message.guild or message.author.bot:
            return

        if not INVITE_REGEX.search(message.content):
            return

        user_roles = [r.name.lower() for r in getattr(message.author, "roles", [])]
        is_staff = message.author.guild_permissions.administrator or is_ticket_staff(message.guild.id, user_roles)

        if is_staff:
            return

        try:
            await message.delete()
        except Exception as e:
            print(f"[ANTI_INVITE] Falha ao apagar mensagem: {e}", flush=True)

        try:
            await message.channel.send(
                f"⚠️ {message.author.mention}, não é permitido enviar convites de outros servidores aqui!",
                delete_after=6
            )
        except Exception:
            pass

        await log_action(
            message.guild,
            "🛡️ Anti-Invite",
            f"Mensagem de {message.author.mention} (`{message.author.id}`) foi removida por conter convite.\n**Canal:** {message.channel.mention}",
            color=0xE74C3C
        )

    except Exception as e:
        print(f"[ANTI_INVITE_ERROR] {e}", flush=True)

def setup_anti_invite(bot):
    @bot.listen("on_message")
    async def on_message_invite_check(message):
        await handle_anti_invite(message)
