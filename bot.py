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

# Lista de prêmios com chance de VIP ajustada para 0.001%
prizes = [
    {"name": "AK47", "image": "https://discordapp.com/channels/1222717244170174585/1309220640556978196/1309221997603196989", "chance": 2},  # Chance baixa
    {"name": "VIP", "image": "https://discordapp.com/channels/1222717244170174585/1309220640556978196/1309224289367228446/vip.png", "chance": 0.001},  # Chance 0.001%
    {"name": "GIROCÓPTERO", "image": "https://discordapp.com/channels/1222717244170174585/1309220640556978196/1309222056348618912", "chance": 2},  # Chance baixa
    {"name": "MOTO", "image": "https://discordapp.com/channels/1222717244170174585/1309220640556978196/1309222023444037714", "chance": 2},  # Chance baixa
    {"name": "SEM SORTE", "image": "https://discordapp.com/channels/1222717244170174585/1309220640556978196/1309221462866923520", "chance": 95},  # Chance alta para falha
]

# Mensagens de falha (Sem sorte)
mensagens_sem_sorte = [
    "O apocalipse não perdoa... o destino não sorriu para você hoje. Tente novamente, sobrevivente!",
    "A escuridão tomou conta da sua sorte. Mas não desista, o amanhã pode ser mais favorável.",
    "Os ventos sombrios do CWB sopram contra você, mas continue tentando. A sorte pode mudar!",
    "A devastação não te favoreceu... mas continue lutando, a esperança é a última que morre.",
]

# Mensagens de sorte (quando o jogador ganha prêmios)
mensagens_com_sorte = [
    "O apocalipse não conseguiu te derrotar. A sorte está do seu lado, sobrevivente! Você ganhou: **{prize}**.",
    "Você desafiou os mortos e a sorte te recompensou. Prepare-se para sua próxima jornada!",
    "O CWB é implacável, mas hoje você venceu. Aproveite seu prêmio, herói do apocalipse!",
    "Em meio à destruição, você brilhou como um farol de esperança. O apocalipse não pode te parar!",
]

# Mensagens apocalípticas (para prêmios valiosos)
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
        mensagem = random.choice(mensagens_com_sorte).format(prize=prize["name"])
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

    # Limpeza do chat (opcional)
    await ctx.channel.purge(limit=10)  # Apaga as últimas 10 mensagens, incluindo o comando

    # Atualiza o tempo da última tentativa do jogador
    last_attempt_time[user.id] = time.time()

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
