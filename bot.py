import discord
from discord.ext import commands, tasks
from discord.ui import Button, View
import random
import time
import os
from datetime import datetime

# Definindo intents necessários
intents = discord.Intents.default()
intents.messages = True  # Necessário para ler e reagir a mensagens
intents.guilds = True    # Necessário para interagir com guildas/servidores
intents.message_content = True  # Necessário para acessar o conteúdo das mensagens

# Criando o bot com os intents necessários
bot = commands.Bot(command_prefix="!", intents=intents)

# IDs dos canais
canal_abrir_caixa = 1309181452595757077  # Canal para usar o comando !abrir_caixa
canal_rank = 1309181411751886869  # Canal para comandos de rank
canal_premio = 1222717244170174588  # Canal de aviso de prêmios em tempo real

# Dicionários para armazenar dados
last_attempt_time = {}
player_prizes = {}
player_box_opens = {}
player_embers = {}

# Emojis de reação para prêmios
reacoes = ["🔥", "<:emoji_1:1262824010723365030>", "<:emoji_2:1261377496893489242>", "<:emoji_3:1261374830088032378>", "<:emoji_4:1260945241918279751>"]

# Lista de prêmios
prizes = [
    {"name": "AK47", "image": "https://i.postimg.cc/KYWdMknH/Ak47.webp", "chance": 3, "description": "Uma poderosa AK47, perfeita para dominar o apocalipse com força e precisão."},
    {"name": "VIP", "image": "https://i.postimg.cc/P537gpF5/pngtree-vip-3d-golden-word-element-png-image-240239.png", "chance": 0.05, "description": "Um status VIP especial que te dá acesso a benefícios exclusivos no apocalipse."},
    {"name": "GIROCÓPTERO", "image": "https://i.postimg.cc/fR84MgkZ/Gyrocopter-Placeable.webp", "chance": 2, "description": "Um giroscópio para viagens rápidas pelo apocalipse."},
    {"name": "MOTO", "image": "https://i.postimg.cc/9f060tq9/Motorcycle-Placeable.webp", "chance": 3, "description": "Uma moto resistente para explorar terrenos perigosos."},
    {"name": "SEM SORTE", "image": "https://i.postimg.cc/Y0KZd5DN/DALL-E-2024-11-21-15-18-18-The-same-post-apocalyptic-supply-crate-marked-with-CWB-now-open-reve.webp", "chance": 88, "description": "A sorte não te favoreceu desta vez."},
    {"name": "CWB Coin", "image": "https://imgur.com/n4dqi3d.png", "chance": 1, "description": "Uma moeda CWB para trocar por vantagens únicas."},
    {"name": "Eraser T5", "image": "https://imgur.com/n4dqi3d.png", "chance": 0.8, "description": "Eraser T5, arma poderosa para apagar qualquer ameaça."},
    {"name": "BullDog T5", "image": "https://imgur.com/n4dqi3d.png", "chance": 0.8, "description": "BullDog T5, espingarda de combate implacável."},
    {"name": "Pack 5k Munição 9mm Urânio", "image": "https://imgur.com/n4dqi3d.png", "chance": 1.5, "description": "5k de munição 9mm urânio, destruição garantida."},
    {"name": "Pack 5k Munição 762mm Urânio", "image": "https://imgur.com/n4dqi3d.png", "chance": 1.5, "description": "5k de munição 7.62mm urânio, poder de fogo extremo."},
    {"name": "Pack 5k Munição Shot Urânio", "image": "https://imgur.com/n4dqi3d.png", "chance": 1.5, "description": "5k de munição de espingarda urânio, impacto devastador."}
]

# Mensagens sem sorte
mensagens_sem_sorte = [
    "O apocalipse não perdoa... O destino não sorriu para você hoje. Mas sua luta não acabou. Tente novamente, sobrevivente!",
    "A escuridão tomou conta da sua sorte. Mas lembre-se, a esperança nunca morre. O amanhã pode ser seu!",
    "Os ventos sombrios do CWB sopram contra você. Mas cada batalha te torna mais forte, continue tentando!",
    "A devastação não te favoreceu... Mas não desista, sobrevivente. Cada queda te leva um passo mais perto da vitória.",
]

# Mensagens com sorte
mensagens_com_sorte = [
    "O apocalipse não conseguiu te derrotar! A sorte está do seu lado, sobrevivente! Você ganhou: **{prize}**.",
    "Você desafiou os mortos e a sorte te recompensou com algo incrível. Prepare-se para sua próxima jornada! Você ganhou: **{prize}**.",
    "O CWB é implacável, mas hoje você venceu. A sorte sorriu para você. Aproveite seu prêmio, herói do apocalipse!",
    "Em meio à destruição, você brilhou como um farol de esperança. O apocalipse não pode te parar! Você ganhou: **{prize}**.",
]

def tempo_restante(last_time):
    return max(0, 10800 - (time.time() - last_time))  # 3h = 10800s

def escolher_premio():
    total = sum(item['chance'] for item in prizes)
    rand = random.uniform(0, total)
    current = 0
    for item in prizes:
        current += item['chance']
        if rand <= current:
            return item

def contar_raros(user_id):
    # Conta quantos prêmios raros (diferentes de SEM SORTE) o jogador possui
    if user_id not in player_prizes:
        return 0
    return sum(1 for p in player_prizes[user_id] if p != "SEM SORTE")

@bot.command()
async def ajuda(ctx):
    ajuda_texto = """
    **Comandos disponíveis:**

    `!abrir_caixa` - Abra uma caixa para ganhar prêmios. Apenas pode ser usado no canal correto.
    `!abrir_admin` - Apenas o criador ou o usuário autorizado pode usar este comando, sem cooldown.
    `!limpar_chat` - Limpa as últimas 100 mensagens do chat atual, só pode ser usado por administradores. (Comando de emergência)
    `!ajuda` - Exibe esta mensagem de ajuda.
    `!rank_premios` - Exibe o ranking dos melhores prêmios.
    `!rank_caixas_abertas` - Exibe o ranking dos jogadores que mais abriram caixas.
    
    **Nota:** O comando `!abrir_caixa` só pode ser usado no canal correto. Consulte o administrador para mais informações.
    """
    embed = discord.Embed(
        title="Comandos Disponíveis",
        description=ajuda_texto,
        color=discord.Color.blue()
    )
    embed.set_image(url="https://i.postimg.cc/rmt7CVjF/DALL-E-2024-11-21-15-22-03-A-rugged-survivor-in-a-post-apocalyptic-setting-wearing-worn-out-cloth.webp")
    await ctx.send(embed=embed)

@bot.command()
async def limpar_chat(ctx):
    # Apenas administradores podem usar
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("Você não tem permissão para usar este comando.")
        return
    deleted = await ctx.channel.purge(limit=100)
    await ctx.send(f"Foram limpas {len(deleted)} mensagens.", delete_after=5)

@bot.command()
async def abrir_caixa(ctx):
    if ctx.channel.id != canal_abrir_caixa:
        await ctx.send(f"{ctx.author.mention}, você só pode usar o comando neste canal: <#{canal_abrir_caixa}>")
        return

    user = ctx.author
    if user.id in last_attempt_time:
        tempo_rest = tempo_restante(last_attempt_time[user.id])
        if tempo_rest > 0:
            horas = int(tempo_rest // 3600)
            minutos = int((tempo_rest % 3600) // 60)
            segundos = int(tempo_rest % 60)
            await ctx.send(f"{user.mention}, você precisa esperar {horas}h {minutos}m {segundos}s para tentar novamente.")
            return

    prize = escolher_premio()

    if prize["name"] == "SEM SORTE":
        mensagem = random.choice(mensagens_sem_sorte)
    else:
        mensagem = random.choice(mensagens_com_sorte).format(prize=prize["name"])
        player_prizes[user.id] = player_prizes.get(user.id, []) + [prize["name"]]

    player_box_opens[user.id] = player_box_opens.get(user.id, 0) + 1

    embed = discord.Embed(
        title="🎁 Você abriu a Caixa de Presentes!",
        description=f"{user.mention}, {mensagem} Você ganhou: **{prize['name']}**!" if prize["name"] != "SEM SORTE" else f"{user.mention}, {mensagem}",
        color=discord.Color.gold()
    )
    embed.set_image(url=prize['image'])
    msg = await ctx.send(embed=embed)

    if prize["name"] != "SEM SORTE":
        await msg.add_reaction(random.choice(reacoes))
        
        # Novo esquema: avisar em tempo real com mais detalhes no canal de prêmios
        raros = contar_raros(user.id)
        caixas_abertas = player_box_opens[user.id]
        parabens_msg = f"🎉 **Parabéns {user.mention}!** Você ganhou: **{prize['name']}**!"
        parabens_msg += f"\nCaixas Abertas: **{caixas_abertas}** | Prêmios Raros Obtidos: **{raros}**"
        embed_parabens = discord.Embed(
            title="🥳 Ganhador do Sorteio!",
            description=parabens_msg,
            color=discord.Color.green()
        )
        embed_parabens.set_image(url=prize['image'])
        await bot.get_channel(canal_premio).send(embed=embed_parabens)

    last_attempt_time[user.id] = time.time()

@bot.command()
async def rank_premios(ctx):
    if ctx.channel.id != canal_rank:
        await ctx.send(f"{ctx.author.mention}, você só pode usar este comando no canal de rank: <#{canal_rank}>")
        return
    rank = sorted(player_prizes.items(), key=lambda x: sum(1 for p in x[1] if p != "SEM SORTE"), reverse=True)
    mensagem = "🏆 **Ranking dos Melhores Prêmios** 🏆\n\n"
    for i, (user_id, prizes) in enumerate(rank[:10], start=1):
        user = await bot.fetch_user(user_id)
        itens_raros = [p for p in prizes if p != "SEM SORTE"]
        mensagem += f"{i}. **{user.display_name}** - {len(itens_raros)} prêmios raros: {', '.join(itens_raros)}\n"
    await ctx.send(mensagem)

@bot.command()
async def rank_caixas_abertas(ctx):
    if ctx.channel.id != canal_rank:
        await ctx.send(f"{ctx.author.mention}, você só pode usar este comando no canal de rank: <#{canal_rank}>")
        return
    rank = sorted(player_box_opens.items(), key=lambda x: x[1], reverse=True)
    mensagem = "📦 **Ranking de Abertura de Caixas** 📦\n\n"
    for i, (user_id, opens) in enumerate(rank[:5], start=1):
        user = await bot.fetch_user(user_id)
        mensagem += f"{i}. **{user.display_name}** - {opens} caixas abertas\n"
    await ctx.send(mensagem)

@bot.command()
async def abrir_admin(ctx):
    criador_id = 470628393272999948  # ID do criador
    usuario_autorizado_id = 434531832097144852  # ID do usuário autorizado

    if ctx.author.id not in [criador_id, usuario_autorizado_id]:
        embed = discord.Embed(
            title="Acesso Negado",
            description="Somente o criador ou o usuário autorizado podem usar este comando. Caso precise de algo, entre em contato.",
            color=discord.Color.red()
        )
        embed.set_footer(text="Caso tenha dúvidas, entre em contato com o criador do bot.")
        button = Button(label="Entrar em Contato", style=discord.ButtonStyle.link, url="https://discord.com/users/470628393272999948")
        view = View()
        view.add_item(button)
        await ctx.send(embed=embed, view=view)
        return

    # Sem cooldown
    prize = escolher_premio()
    player_box_opens[ctx.author.id] = player_box_opens.get(ctx.author.id, 0) + 1
    if prize["name"] != "SEM SORTE":
        player_prizes[ctx.author.id] = player_prizes.get(ctx.author.id, []) + [prize["name"]]

    mensagem = f"**{ctx.author.mention}** ganhou: **{prize['name']}**!"
    embed = discord.Embed(
        title="🎁 Você abriu uma Caixa Especial!",
        description=mensagem,
        color=discord.Color.gold()
    )
    embed.set_image(url=prize['image'])
    msg = await ctx.send(embed=embed)

    if prize["name"] != "SEM SORTE":
        await msg.add_reaction(random.choice(reacoes))
        # Aviso em tempo real no canal de prêmios
        raros = contar_raros(ctx.author.id)
        caixas_abertas = player_box_opens[ctx.author.id]
        parabens_msg = f"🎉 **Parabéns {ctx.author.mention}!** Você ganhou: **{prize['name']}**!"
        parabens_msg += f"\nCaixas Abertas: **{caixas_abertas}** | Prêmios Raros Obtidos: **{raros}**"
        embed_parabens = discord.Embed(
            title="🥳 Ganhador do Sorteio (Admin)!",
            description=parabens_msg,
            color=discord.Color.green()
        )
        embed_parabens.set_image(url=prize['image'])
        await bot.get_channel(canal_premio).send(embed=embed_parabens)

@tasks.loop(hours=7)
async def limpar_rank():
    player_prizes.clear()
    player_box_opens.clear()
    channel = bot.get_channel(canal_rank)
    embed = discord.Embed(
        title="⚡ Zeração de Ranking ⚡",
        description="O ranking foi zerado. Todos os prêmios e caixas abertas foram reiniciados.",
        color=discord.Color.red()
    )
    await channel.send(embed=embed)

# Inicia a tarefa de limpeza automática do ranking
limpar_rank.start()

TOKEN = os.getenv('TOKEN')
bot.run(TOKEN)
