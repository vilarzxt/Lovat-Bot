import discord
import random
from discord import app_commands
from discord.ext import commands
from systems.utils import create_embed
from config.assets import EMBED_COLOR

EIGHT_BALL_RESPONSES = [
    "Com certeza!",
    "Sem dúvidas.",
    "Sim, definitivamente.",
    "Você pode contar com isso.",
    "A meu ver, sim.",
    "Provavelmente.",
    "As perspectivas são boas.",
    "Sim.",
    "Sinais apontam que sim.",
    "Resposta nebulosa, tente novamente.",
    "Pergunte novamente mais tarde.",
    "Melhor não te dizer agora.",
    "Não posso prever agora.",
    "Concentre-se e pergunte novamente.",
    "Não conte com isso.",
    "Minha resposta é não.",
    "Minhas fontes dizem não.",
    "Perspectivas não são tão boas.",
    "Muito duvidoso."
]

@app_commands.command(name="avatar", description="Exibe o avatar em tamanho grande de um usuário")
@app_commands.describe(usuario="Usuário desejado")
async def avatar(interaction: discord.Interaction, usuario: discord.Member = None):
    try:
        target = usuario or interaction.user
        avatar_url = target.display_avatar.url
        embed = create_embed(
            title=f"🖼️ Avatar de {target.display_name}",
            color=EMBED_COLOR,
            image=avatar_url
        )
        await interaction.response.send_message(embed=embed, ephemeral=False)
    except Exception as e:
        print(f"[FUN_AVATAR_ERROR] {e}", flush=True)
        await interaction.response.send_message("❌ Erro ao obter avatar.", ephemeral=True)

@app_commands.command(name="enquete", description="Cria uma enquete pública com opções")
@app_commands.describe(
    pergunta="Pergunta da enquete",
    opcao1="Primeira opção",
    opcao2="Segunda opção",
    opcao3="Terceira opção (opcional)",
    opcao4="Quarta opção (opcional)"
)
async def enquete(
    interaction: discord.Interaction,
    pergunta: str,
    opcao1: str,
    opcao2: str,
    opcao3: str = None,
    opcao4: str = None
):
    try:
        options = [opcao1, opcao2]
        if opcao3:
            options.append(opcao3)
        if opcao4:
            options.append(opcao4)

        number_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]
        desc = f"**{pergunta}**\n\n"
        for idx, opt in enumerate(options):
            desc += f"{number_emojis[idx]} {opt}\n"

        embed = create_embed(
            title="📊 Enquete",
            description=desc,
            color=EMBED_COLOR
        )
        embed.set_footer(text=f"Criada por {interaction.user.display_name}")

        await interaction.response.send_message(embed=embed, ephemeral=False)
        msg = await interaction.original_response()

        for idx in range(len(options)):
            await msg.add_reaction(number_emojis[idx])

    except Exception as e:
        print(f"[FUN_ENQUETE_ERROR] {e}", flush=True)

@app_commands.command(name="moeda", description="Joga uma moeda (Cara ou Coroa)")
async def moeda(interaction: discord.Interaction):
    try:
        resultado = random.choice(["Cara 🪙", "Coroa 🪙"])
        embed = create_embed(
            title="🪙 Cara ou Coroa",
            description=f"Resultado: **{resultado}**",
            color=EMBED_COLOR
        )
        await interaction.response.send_message(embed=embed, ephemeral=False)
    except Exception as e:
        print(f"[FUN_MOEDA_ERROR] {e}", flush=True)

@app_commands.command(name="dado", description="Rola um dado de N lados")
@app_commands.describe(lados="Quantidade de lados do dado (padrão: 6)")
async def dado(interaction: discord.Interaction, lados: int = 6):
    try:
        if lados < 2:
            return await interaction.response.send_message("❌ O dado deve ter no mínimo 2 lados.", ephemeral=True)
        res = random.randint(1, lados)
        embed = create_embed(
            title="🎲 Rolagem de Dado",
            description=f"Dado de **{lados}** lados: Rolou **{res}**!",
            color=EMBED_COLOR
        )
        await interaction.response.send_message(embed=embed, ephemeral=False)
    except Exception as e:
        print(f"[FUN_DADO_ERROR] {e}", flush=True)

@app_commands.command(name="ship", description="Calcula a compatibilidade entre dois usuários")
@app_commands.describe(usuario1="Primeiro usuário", usuario2="Segundo usuário")
async def ship(interaction: discord.Interaction, usuario1: discord.Member, usuario2: discord.Member):
    try:
        pct = random.randint(0, 100)
        bars = int(pct / 10)
        progress_bar = "💖" * bars + "🖤" * (10 - bars)

        frase = "Um par afinado e com ótima sintonia!" if pct >= 50 else "Uma combinação curiosa e cheia de altos e baixos!"

        embed = create_embed(
            title="💘 Teste de Compatibilidade",
            description=f"**{usuario1.display_name}** + **{usuario2.display_name}**\n\n"
                        f"Chance: **{pct}%**\n`[{progress_bar}]`\n\n*{frase}*",
            color=0xFF69B4
        )
        await interaction.response.send_message(embed=embed, ephemeral=False)
    except Exception as e:
        print(f"[FUN_SHIP_ERROR] {e}", flush=True)

@app_commands.command(name="8ball", description="Pergunte algo à Bola 8 Mágica")
@app_commands.describe(pergunta="Sua pergunta")
async def eightball(interaction: discord.Interaction, pergunta: str):
    try:
        resp = random.choice(EIGHT_BALL_RESPONSES)
        embed = create_embed(
            title="🎱 Bola 8 Mágica",
            description=f"**Pergunta:** {pergunta}\n**Resposta:** {resp}",
            color=EMBED_COLOR
        )
        await interaction.response.send_message(embed=embed, ephemeral=False)
    except Exception as e:
        print(f"[FUN_8BALL_ERROR] {e}", flush=True)

async def setup(bot: commands.Bot):
    bot.tree.add_command(avatar)
    bot.tree.add_command(enquete)
    bot.tree.add_command(moeda)
    bot.tree.add_command(dado)
    bot.tree.add_command(ship)
    bot.tree.add_command(eightball)
