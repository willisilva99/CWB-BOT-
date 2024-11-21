import discord
from discord.ext import commands, tasks
import random
import time
import os
from datetime import datetime, timedelta

# Definindo intents necessários
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True

# Criando o bot com os intents necessários
bot = commands.Bot(command_prefix="!", intents=intents)

# IDs dos canais
canal_rank = 1309181411751886869
canal_admin = 1309181452595757077

# Dicionário para armazenar o último tempo de sorteio de cada jogador e pontuação de embers
last_attempt_time = {}
player_prizes = {}
player_box_opens = {}
player_embers = {}

# Emojis de reação para adicionar
reacoes = ["🔥", "<:emoji_1:1262824010723365030>", "<:emoji_2:1261377496893489242>", "<:emoji_3:1261374830088032378>", "<:emoji_4:1260945241918279751>"]

# Mensagens apocalípticas
mensagens_apocalipticas = [
    "As nuvens negras se abrem, e o poder está ao seu alcance, {user}!",
    "Os espíritos do apocalipse sussurram seu nome... você foi escolhido, {user}!",
    "Hoje, os mortos levantaram-se para saudar {user}. A sorte está ao seu lado!",
    "Nas trevas do apocalipse, um brilho de esperança aparece para {user}.",
    "Você venceu o apocalipse e emergiu como um verdadeiro guerreiro, {user}!",
    "{user}, a devastação não é párea para sua sorte. Domine a vitória!",
    "Os ventos da destruição carregam seu nome, {user}. Hoje, você é imbatível!",
    "A terra treme sob seus pés, {user}, enquanto o apocalipse se curva diante de sua vitória!",
    "{user}, você foi agraciado pelas forças do além. Este é o seu dia de sorte!",
    "Com os olhos da noite sobre você, {user}, a fortuna finalmente lhe sorriu!"
]

# Comando para abrir a caixa com restrição de canal
@bot.command()
async def abrir_caixa(ctx):
    if ctx.channel.id == canal_admin and ctx.author.guild_permissions.administrator:
        # Admin pode abrir sem cooldown
        pass
    elif ctx.channel.id != canal_rank:
        await ctx.send(f"{ctx.author.mention}, você só pode usar o comando neste canal: <#{canal_rank}>")
        return

    user = ctx.message.author

    # Verifica se o jogador já tentou nos últimos 3 horas
    if user.id in last_attempt_time:
        tempo_rest = tempo_restante(last_attempt_time[user.id])
        if tempo_rest > 0:
            horas = int(tempo_rest // 3600)
            minutos = int((tempo_rest % 3600) // 60)
            segundos = int(tempo_rest % 60)
            await ctx.send(f"{user.mention}, você precisa esperar {horas}h {minutos}m {segundos}s para tentar novamente.")
            return

    # Sorteia um prêmio com base nas chances ajustadas
    prize = escolher_premio()

    # Mensagem diferente dependendo se ganhou ou não
    if prize["name"] == "SEM SORTE":
        mensagem = random.choice(mensagens_sem_sorte)
    else:
        mensagem = random.choice(mensagens_com_sorte)
        player_prizes[user.id] = player_prizes.get(user.id, []) + [prize["name"]]  # Armazena o prêmio

        # Envia uma mensagem apocalíptica mencionando o apelido do jogador para prêmios valiosos
        mensagem_apocaliptica = random.choice(mensagens_apocalipticas).format(user=user.display_name)
        await ctx.send(mensagem_apocaliptica)

    # Incrementa o contador de caixas abertas
    player_box_opens[user.id] = player_box_opens.get(user.id, 0) + 1

    # Cria o embed com a imagem do prêmio ou da mensagem de azar
    embed = discord.Embed(
        title="🎁 Você abriu a Caixa de Presentes!",
        description=f"{user.mention}, {mensagem} Você ganhou: **{prize['name']}**!" if prize["name"] != "SEM SORTE" else f"{user.mention}, {mensagem}",
        color=discord.Color.gold()
    )
    embed.set_image(url=prize['image'])

    # Envia a mensagem com o embed no canal
    msg = await ctx.send(embed=embed)

    # Reage no post do prêmio valioso apenas
    if prize["name"] != "SEM SORTE":
        await msg.add_reaction(random.choice(reacoes))

    # Atualiza o tempo da última tentativa do jogador
    last_attempt_time[user.id] = time.time()

# Comando para abrir o admin (restrito ao criador)
@bot.command()
async def abrir_admin(ctx):
    if ctx.author.id == 470628393272999948:
        # Apenas o criador pode mencionar o nome e reagir com emojis
        await ctx.send(f"{ctx.author.mention} você pode reagir com emojis e mencionar meu nome, pois é o criador do bot.")
        await ctx.message.add_reaction("🔥")
    else:
        # Caso outra pessoa tente usar o comando
        await ctx.send(f"{ctx.author.mention}, somente o criador pode usar esse comando! Um grande líder do apocalipse não deve ser desafiado!")
        embed = discord.Embed(
            title="⚡Mensagem Apocalíptica⚡",
            description="A terra treme sob o peso do seu erro. Apenas um ser superior pode invocar o poder do apocalipse.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

# Função para selecionar um prêmio com base nas chances ajustadas
def escolher_premio():
    total = sum(item['chance'] for item in prizes)
    rand = random.uniform(0, total)
    current = 0
    for item in prizes:
        current += item['chance']
        if rand <= current:
            return item

# Função para calcular o tempo restante para o próximo sorteio
def tempo_restante(last_time):
    return max(0, 10800 - (time.time() - last_time))  # 3 horas = 10800 segundos

# Rodando o bot com o token de ambiente
TOKEN = os.getenv('TOKEN')
bot.run(TOKEN)
