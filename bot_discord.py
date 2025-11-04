# -*- coding: utf-8 -*-
from keep_alive import keep_alive

import discord
from discord.ext import commands
import random
import re
import os
import unicodedata

# ==============================
# CONFIGURAÇÕES
# ==============================
TOKEN = os.getenv("DISCORD_TOKEN")
PREFIXO = "!"
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True
bot = commands.Bot(command_prefix=PREFIXO, intents=intents)

# ==============================
# FUNÇÃO AUXILIAR: NORMALIZAR TEXTO
# ==============================
def normalizar(texto):
    """Remove acentos, emojis e converte pra minúsculo"""
    texto = ''.join(
        c for c in unicodedata.normalize("NFKD", texto)
        if not unicodedata.combining(c)
    )
    return texto.encode("ASCII", "ignore").decode("utf-8").lower()

# ==============================
# EVENTOS
# ==============================
@bot.event
async def on_ready():
    print(f"✅ Bot {bot.user.name} está online!")
    await bot.change_presence(activity=discord.Game(name="organizando grupos 💪"))

# ==============================
# COMANDO DE AJUDA
# ==============================
@bot.command(name="ajuda")
async def ajuda(ctx):
    ajuda_msg = (
        "🤖 **Comandos disponíveis:**\n\n"
        "`!div Cargo` → Divide automaticamente os membros do cargo em grupos iguais.\n"
        "`!div Cargo g=5` → Cria exatamente 5 grupos.\n"
        "`!div Cargo p=4` → Cria grupos de 4 pessoas.\n"
        "`!div Cargo g=5 p=3` → Cria 5 grupos de 3 pessoas.\n"
        "`!div Cargo al` → Divide em ordem aleatória.\n"
        "`!div Cargo g=5 al dm` → Cria 5 grupos aleatórios e envia o resultado por **DM apenas para você**.\n\n"
        "🧠 Combine as variáveis conforme desejar!"
    )
    await ctx.send(ajuda_msg)

# ==============================
# COMANDO PRINCIPAL: DIVISÃO DE GRUPOS
# ==============================
@bot.command(name="div")
async def dividir(ctx, *args):
    if not args:
        await ctx.send("❌ Use: `!div Cargo` ou `!div @Cargo`")
        return

    args_texto = " ".join(args)
    cargo_match = re.match(r'<?@?&?(\d+)?>? ?("?([^"]+)"?)?', args_texto)

    cargo_obj = None
    cargo_nome = None

    # Tenta identificar se foi uma menção
    if cargo_match:
        cargo_id = cargo_match.group(1)
        cargo_nome = cargo_match.group(3)
        if cargo_id:
            cargo_obj = ctx.guild.get_role(int(cargo_id))
        elif cargo_nome:
            cargo_obj = discord.utils.find(
                lambda r: normalizar(r.name) == normalizar(cargo_nome),
                ctx.guild.roles
            )

    # Se ainda não encontrou, tenta procurar de forma mais ampla
    if not cargo_obj:
        cargo_obj = discord.utils.find(
            lambda r: normalizar(r.name) in normalizar(args_texto),
            ctx.guild.roles
        )

    if not cargo_obj:
        await ctx.send("❌ Cargo não encontrado! Tente usar o nome exato ou mencionar com @Cargo.")
        return

    membros = [m for m in cargo_obj.members if not m.bot]
    if not membros:
        await ctx.send(f"⚠️ Nenhum membro encontrado no cargo **{cargo_obj.name}**.")
        return

    # Parâmetros opcionais
    g_match = re.search(r"g=(\d+)", args_texto)
    p_match = re.search(r"p=(\d+)", args_texto)
    al = "al" in args_texto
    dm = "dm" in args_texto

    if al:
        random.shuffle(membros)

    # ==============================
    # LÓGICA AJUSTADA: g= e p= combinados
    # ==============================
    grupos = []

    if g_match and p_match:
        num_grupos = int(g_match.group(1))
        tam = int(p_match.group(1))
        grupos = [membros[i * tam:(i + 1) * tam] for i in range(num_grupos)]
    elif g_match:
        num_grupos = int(g_match.group(1))
        grupos = [[] for _ in range(num_grupos)]
        for i, m in enumerate(membros):
            grupos[i % num_grupos].append(m)
    elif p_match:
        tam = int(p_match.group(1))
        grupos = [membros[i:i + tam] for i in range(0, len(membros), tam)]
    else:
        tam = len(membros) // 2 or 1
        grupos = [membros[i:i + tam] for i in range(0, len(membros), tam)]

    # Remove grupos vazios
    grupos = [g for g in grupos if g]

    # ==============================
    # MONTAR RESPOSTA
    # ==============================
    resultado = ""
    for i, grupo in enumerate(grupos, start=1):
        nomes = ", ".join(m.display_name for m in grupo)
        resultado += f"**Grupo {i}:** {nomes}\n"

    embed = discord.Embed(
        title="✅ Grupos criados!",
        description=resultado or "Nenhum grupo criado.",
        color=discord.Color.green()
    )
    embed.set_footer(text=f"Cargo: {cargo_obj.name}")

    await ctx.send(embed=embed)

    # Enviar DM somente para quem usou o comando
    if dm:
        try:
            await ctx.author.send(
                f"✅ Seus grupos foram criados com sucesso!\n\n{resultado}"
            )
        except:
            await ctx.send("⚠️ Não consegui enviar DM (você pode estar com DMs fechadas).")

# ==============================
# EXECUÇÃO
# ==============================
keep_alive()
bot.run(TOKEN)