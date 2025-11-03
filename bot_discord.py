# -*- coding: utf-8 -*-
from keep_alive import keep_alive

import discord
from discord.ext import commands
import random
import re

# ==============================
# CONFIGURAÇÕES
# ==============================
import os
TOKEN = os.getenv("DISCORD_TOKEN")
PREFIXO = "!"
intents = discord.Intents.all()
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True
bot = commands.Bot(command_prefix=PREFIXO, intents=intents)

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
        "`!div Cargo g=5 al dm` → Cria 5 grupos aleatórios e envia por DM.\n\n"
        "🧠 Combine as variáveis conforme desejar!"
    )
    await ctx.send(ajuda_msg)


# ==============================
# FUNÇÃO PRINCIPAL: DIVISÃO DE GRUPOS
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
            cargo_obj = discord.utils.find(lambda r: r.name.lower() == cargo_nome.lower(), ctx.guild.roles)

    # Se ainda não encontrou, tenta pelo texto inteiro
    if not cargo_obj:
        cargo_obj = discord.utils.find(lambda r: r.name.lower() in args_texto.lower(), ctx.guild.roles)

    if not cargo_obj:
        await ctx.send("❌ Cargo não encontrado! Tente usar o nome exato ou mencionar com @Cargo.")
        return

    membros = [m for m in cargo_obj.members if not m.bot]
    if not membros:
        await ctx.send(f"⚠️ Nenhum membro encontrado no cargo {cargo_obj.mention}.")
        return

    g_match = re.search(r"g=(\d+)", args_texto)
    p_match = re.search(r"p=(\d+)", args_texto)
    al = "al" in args_texto
    dm = "dm" in args_texto

    grupos = []
    if al:
        random.shuffle(membros)

    if g_match:
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

    msg_final = f"✅ **Grupos criados para {cargo_obj.mention}:**\n\n"
    for i, g in enumerate(grupos, start=1):
        nomes = ", ".join(m.display_name for m in g)
        msg_final += f"**Grupo {i}:** {nomes}\n"

        if dm:
            for m in g:
                try:
                    await m.send(f"📢 Você está no **Grupo {i}** com: {', '.join(x.name for x in g if x != m)}")
                except:
                    pass

    await ctx.send(msg_final)


# ==============================
# EXECUÇÃO
# ==============================
keep_alive()
bot.run(TOKEN)