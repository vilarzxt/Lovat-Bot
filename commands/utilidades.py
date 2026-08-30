import discord
import ast
import operator
import asyncio
from discord import app_commands
from discord.ext import commands
from systems.utils import create_embed
from config.assets import EMBED_COLOR

# Safe AST evaluator for /calcular
OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

def safe_eval(expr: str):
    node = ast.parse(expr, mode='eval').body

    def _eval(node):
        if isinstance(node, ast.Num):
            return node.n
        elif isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        elif isinstance(node, ast.BinOp):
            left = _eval(node.left)
            right = _eval(node.right)
            op_type = type(node.op)
            if op_type in OPERATORS:
                return OPERATORS[op_type](left, right)
        elif isinstance(node, ast.UnaryOp):
            operand = _eval(node.operand)
            op_type = type(node.op)
            if op_type in OPERATORS:
                return OPERATORS[op_type](operand)
        raise ValueError("Expressão inválida")

    return _eval(node)

def parse_time(time_str: str) -> int | None:
    try:
        time_str = time_str.lower().strip()
        if time_str.endswith("s"):
            return int(time_str[:-1])
        elif time_str.endswith("m"):
            return int(time_str[:-1]) * 60
        elif time_str.endswith("h"):
            return int(time_str[:-1]) * 3600
        return int(time_str)
    except ValueError:
        return None

@app_commands.command(name="serverinfo", description="Exibe informações sobre o servidor")
async def serverinfo(interaction: discord.Interaction):
    try:
        guild = interaction.guild
        if not guild:
            return await interaction.response.send_message("❌ Comando apenas para servidores.", ephemeral=True)

        embed = create_embed(
            title=f"🏰 Informações do Servidor: {guild.name}",
            color=EMBED_COLOR
        )
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        embed.add_field(name="🆔 ID", value=str(guild.id), inline=True)
        embed.add_field(name="👑 Dono", value=guild.owner.mention if guild.owner else "Desconhecido", inline=True)
        embed.add_field(name="📅 Criado em", value=guild.created_at.strftime("%d/%m/%Y %H:%M"), inline=True)
        embed.add_field(name="👥 Membros", value=str(guild.member_count), inline=True)
        embed.add_field(name="💬 Canais de Texto", value=str(len(guild.text_channels)), inline=True)
        embed.add_field(name="🔊 Canais de Voz", value=str(len(guild.voice_channels)), inline=True)

        await interaction.response.send_message(embed=embed)
    except Exception as e:
        print(f"[UTIL_SERVERINFO_ERROR] {e}", flush=True)

@app_commands.command(name="userinfo", description="Exibe informações sobre um usuário")
@app_commands.describe(usuario="Usuário desejado")
async def userinfo(interaction: discord.Interaction, usuario: discord.Member = None):
    try:
        user = usuario or interaction.user
        embed = create_embed(
            title=f"👤 Informações de {user.display_name}",
            color=EMBED_COLOR
        )
        embed.set_thumbnail(url=user.display_avatar.url)

        embed.add_field(name="🆔 ID", value=str(user.id), inline=True)
        embed.add_field(name="📅 Conta Criada", value=user.created_at.strftime("%d/%m/%Y %H:%M"), inline=True)
        if isinstance(user, discord.Member) and user.joined_at:
            embed.add_field(name="📥 Entrou no Servidor", value=user.joined_at.strftime("%d/%m/%Y %H:%M"), inline=True)
            roles = [r.mention for r in user.roles if r.name != "@everyone"]
            roles_str = ", ".join(roles) if roles else "*Nenhum cargo*"
            embed.add_field(name="🎭 Cargos", value=roles_str[:1000], inline=False)

        await interaction.response.send_message(embed=embed)
    except Exception as e:
        print(f"[UTIL_USERINFO_ERROR] {e}", flush=True)

@app_commands.command(name="calcular", description="Calcula uma expressão matemática simples")
@app_commands.describe(expressao="Expressão matemática (ex: 10 + (5 * 2))")
async def calcular(interaction: discord.Interaction, expressao: str):
    try:
        res = safe_eval(expressao)
        embed = create_embed(
            title="🧮 Calculadora",
            description=f"**Expressão:** `{expressao}`\n**Resultado:** `{res}`",
            color=EMBED_COLOR
        )
        await interaction.response.send_message(embed=embed)
    except Exception:
        await interaction.response.send_message("❌ Expressão inválida. Use apenas números e operadores +, -, *, /, ( ).", ephemeral=True)

@app_commands.command(name="lembrete", description="Define um lembrete em tempo (ex: 10s, 5m, 1h)")
@app_commands.describe(tempo="Tempo de espera (ex: 30s, 10m)", mensagem="Mensagem do lembrete")
async def lembrete(interaction: discord.Interaction, tempo: str, mensagem: str):
    try:
        seconds = parse_time(tempo)
        if not seconds or seconds <= 0:
            return await interaction.response.send_message("❌ Formato de tempo inválido. Use ex: `10s`, `5m`, `1h`.", ephemeral=True)

        await interaction.response.send_message(f"⏰ Lembrete definido para daqui a **{tempo}**!", ephemeral=True)

        # Lembrete em memória via asyncio (Nota: Lembretes ativos expiram se o bot reiniciar)
        async def _run_reminder():
            await asyncio.sleep(seconds)
            try:
                await interaction.user.send(f"⏰ **Lembrete:** {mensagem}")
            except Exception:
                pass

        asyncio.create_task(_run_reminder())

    except Exception as e:
        print(f"[UTIL_LEMBRETE_ERROR] {e}", flush=True)

async def setup(bot: commands.Bot):
    bot.tree.add_command(serverinfo)
    bot.tree.add_command(userinfo)
    bot.tree.add_command(calcular)
    bot.tree.add_command(lembrete)
