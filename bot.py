import discord
from discord.ext import commands, tasks
from discord.ui import Button, View
import random
import time
import os
from datetime import datetime

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# IDs dos canais
canal_abrir_caixa = 1309181452595757077
canal_rank = 1309181411751886869
canal_premio = 1222717244170174588

last_attempt_time = {}
player_prizes = {}
player_box_opens = {}
player_embers = {}

reacoes = ["🔥", "<:emoji_1:1262824010723365030>", "<:emoji_2:1261377496893489242>", "<:emoji_3:1261374830088032378>", "<:emoji_4:1260945241918279751>"]

prizes = [
    {"name": "AK47", "image": "https://i.postimg.cc/KYWdMknH/Ak47.webp", "chance": 3, "description": "Uma poderosa AK47, perfeita para dominar o apocalipse com força e precisão."},
    {"name": "VIP", "image": "https://i.postimg.cc/P537gpF5/pngtree-vip-3d-golden-word-element-png-image-240239.png", "chance": 0.05, "description": "Um status VIP especial que te dá acesso a benefícios exclusivos no apocalipse."},
    {"name": "GIROCÓPTERO", "image": "https://i.postimg.cc/fR84MgkZ/Gyrocopter-Placeable.webp", "chance": 2, "description": "Um giroscópio para viagens rápidas pelo apocalipse."},
    {"name": "MOTO", "image": "https://i.postimg.cc/9f060tq9/Motorcycle-Placeable.webp", "chance": 3, "description": "Uma moto resistente para explorar terrenos perigosos."},
    {"name": "SEM SORTE", "image": "https://i.postimg.cc/Y0KZd5DN/DALL-E-2024-11-21-15-18-18-The-same-post-apocalyptic-supply-crate-marked-with-CWB-now-open-reve.webp", "chance": 88, "description": "A sorte não está ao seu lado hoje."},
    {"name": "CWB Coin", "image": "https://imgur.com/n4dqi3d.png", "chance": 1, "description": "A moeda CWB, para adquirir itens e vantagens únicas."},
    {"name": "Eraser T5", "image": "https://imgur.com/n4dqi3d.png", "chance": 0.8, "description": "Eraser T5, arma potente para apagar ameaças."},
    {"name": "BullDog T5", "image": "https://imgur.com/n4dqi3d.png", "chance": 0.8, "description": "BullDog T5, espingarda implacável."},
    {"name": "Pack 5k Munição 9mm Urânio", "image": "https://imgur.com/n4dqi3d.png", "chance": 1.5, "description": "5k munição 9mm urânio, poder de fogo intenso."},
    {"name": "Pack 5k Munição 762mm Urânio", "image": "https://imgur.com/n4dqi3d.png", "chance": 1.5, "description": "5k munição 7.62mm urânio, destruição garantida."},
    {"name": "Pack 5k Munição Shot Urânio", "image": "https://imgur.com/n4dqi3d.png", "chance": 1.5, "description": "5k munição Shot urânio, impacto devastador."}
]

mensagens_sem_sorte = [
    "O apocalipse não perdoa... o destino não sorriu para você hoje. Mas sua luta não acabou. Tente novamente, sobrevivente!",
    "A escuridão tomou conta da sua sorte. Mas lembre-se, a esperança nunca morre. O amanhã pode ser seu!",
    "Os ventos sombrios do CWB sopram contra você. Mas cada batalha te torna mais forte, continue tentando!",
    "A devastação não te favoreceu... mas não desista, sobrevivente. Cada queda te leva um passo mais perto da vitória.",
]

mensagens_com_sorte = [
    "O apocalipse não conseguiu te derrotar! A sorte está do seu lado, sobrevivente! Você ganhou: **{prize}**.",
    "Você desafiou os mortos e a sorte te recompensou com algo incrível. Prepare-se para sua próxima jornada! Você ganhou: **{prize}**.",
    "O CWB é implacável, mas hoje você venceu. A sorte sorriu para você. Aproveite seu prêmio, herói do apocalipse!",
    "Em meio à destruição, você brilhou como um farol de esperança. O apocalipse não pode te parar! Você ganhou: **{prize}**.",
]

def tempo_restante(last_time):
    return max(0, 10800 - (time.time() - last_time))  # 3 horas = 10800s

def escolher_premio():
    total = sum(item['chance'] for item in prizes)
    rand = random.uniform(0, total)
    current = 0
    for item in prizes:
        current += item['chance']
        if rand <= current:
            return item

def contar_raros(user_id):
    if user_id not in player_prizes:
        return 0
    return sum(1 for p in player_prizes[user_id] if p != "SEM SORTE")

# Lista de status rotativos do bot
status_list = [
    "Jogando 7 Days to Die",
    "Falando com Willi",
    "Conversando com Willi",
    "Dormindo"
]
status_index = 0  # Definição no escopo global

@tasks.loop(minutes=5)
async def mudar_status():
    global status_index  # Use global ao invés de nonlocal
    await bot.change_presence(activity=discord.Game(name=status_list[status_index]))
    status_index = (status_index + 1) % len(status_list)

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

@bot.event
async def on_ready():
    limpar_rank.start()
    mudar_status.start()
    print(f"Bot conectado como {bot.user}")

@bot.command()
async def ajuda(ctx):
    ajuda_texto = """
    **Comandos disponíveis:**

    `!abrir_caixa` - Abra uma caixa para ganhar prêmios (apenas no canal correto).
    `!abrir_admin` - Apenas o criador ou o usuário autorizado podem usar sem cooldown.
    `!limpar_chat` - Limpa as últimas 100 mensagens (apenas admin).
    `!ajuda` - Exibe esta mensagem de ajuda.
    `!rank_premios` - Exibe o ranking dos melhores prêmios.
    `!rank_caixas_abertas` - Exibe o ranking dos jogadores que mais abriram caixas.
    """
    embed = discord.Embed(
        title="Comandos Disponíveis",
        description=ajuda_texto,
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed)

@bot.command()
async def limpar_chat(ctx):
    if not ctx.author.guild_permissions.administrator:
        embed = discord.Embed(
            title="Acesso Negado",
            description="Você não tem permissão para usar este comando.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return
    deleted = await ctx.channel.purge(limit=100)
    embed = discord.Embed(
        title="Limpeza de Chat",
        description=f"Foram limpas {len(deleted)} mensagens.",
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed, delete_after=5)

@bot.command()
async def abrir_caixa(ctx):
    if ctx.channel.id != canal_abrir_caixa:
        embed = discord.Embed(
            title="Canal Incorreto",
            description=f"{ctx.author.mention}, você só pode usar este comando no canal correto.",
            color=discord.Color.red()
        )
        embed.add_field(name="Canal Correto", value=f"<#{canal_abrir_caixa}>", inline=False)
        await ctx.send(embed=embed)
        return

    user = ctx.author
    if user.id in last_attempt_time:
        tempo_rest = tempo_restante(last_attempt_time[user.id])
        if tempo_rest > 0:
            horas = int(tempo_rest // 3600)
            minutos = int((tempo_rest % 3600) // 60)
            segundos = int(tempo_rest % 60)
            embed = discord.Embed(
                title="Aguarde o Cooldown",
                description=f"{user.mention}, você precisa esperar {horas}h {minutos}m {segundos}s para tentar novamente.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return

    prize = escolher_premio()
    if prize["name"] == "SEM SORTE":
        mensagem = random.choice(mensagens_sem_sorte)
        desc = f"{ctx.author.mention}, {mensagem}"
    else:
        mensagem = random.choice(mensagens_com_sorte).format(prize=prize["name"])
        desc = f"{ctx.author.mention}, {mensagem} Você ganhou: **{prize['name']}**!"
        player_prizes[user.id] = player_prizes.get(user.id, []) + [prize["name"]]

    player_box_opens[user.id] = player_box_opens.get(user.id, 0) + 1

    embed = discord.Embed(
        title="🎁 Resultado da Caixa",
        description=desc,
        color=discord.Color.gold()
    )
    embed.set_image(url=prize['image'])
    msg = await ctx.send(embed=embed)

    if prize["name"] != "SEM SORTE":
        await msg.add_reaction(random.choice(reacoes))
        raros = contar_raros(user.id)
        caixas_abertas = player_box_opens[user.id]
        parabens_msg = (f"🎉 **Parabéns {ctx.author.mention}!** Você ganhou: **{prize['name']}**!"
                        f"\nCaixas Abertas: **{caixas_abertas}** | Prêmios Raros: **{raros}**")
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
        embed = discord.Embed(
            title="Canal Incorreto",
            description=f"{ctx.author.mention}, use este comando no canal de rank.",
            color=discord.Color.red()
        )
        embed.add_field(name="Canal Correto", value=f"<#{canal_rank}>", inline=False)
        await ctx.send(embed=embed)
        return

    rank = sorted(player_prizes.items(), key=lambda x: sum(1 for p in x[1] if p != "SEM SORTE"), reverse=True)
    embed = discord.Embed(
        title="🏆 Ranking dos Melhores Prêmios",
        description="Top 10 jogadores que mais ganharam prêmios raros.",
        color=discord.Color.purple()
    )
    for i, (user_id, prizes) in enumerate(rank[:10], start=1):
        user = await bot.fetch_user(user_id)
        itens_raros = [p for p in prizes if p != "SEM SORTE"]
        valor = f"**Prêmios Raros:** {len(itens_raros)}"
        if itens_raros:
            valor += f"\n{', '.join(itens_raros)}"
        embed.add_field(
            name=f"{i}. {user.display_name}",
            value=valor,
            inline=False
        )
    await ctx.send(embed=embed)

@bot.command()
async def rank_caixas_abertas(ctx):
    if ctx.channel.id != canal_rank:
        embed = discord.Embed(
            title="Canal Incorreto",
            description=f"{ctx.author.mention}, use este comando no canal de rank.",
            color=discord.Color.red()
        )
        embed.add_field(name="Canal Correto", value=f"<#{canal_rank}>", inline=False)
        await ctx.send(embed=embed)
        return

    rank = sorted(player_box_opens.items(), key=lambda x: x[1], reverse=True)
    embed = discord.Embed(
        title="📦 Ranking de Abertura de Caixas",
        description="Top 5 jogadores que mais abriram caixas.",
        color=discord.Color.purple()
    )
    for i, (user_id, opens) in enumerate(rank[:5], start=1):
        user = await bot.fetch_user(user_id)
        embed.add_field(
            name=f"{i}. {user.display_name}",
            value=f"**Caixas Abertas:** {opens}",
            inline=False
        )
    await ctx.send(embed=embed)

@bot.command()
async def abrir_admin(ctx):
    criador_id = 470628393272999948
    usuario_autorizado_id = 434531832097144852

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

    prize = escolher_premio()
    player_box_opens[ctx.author.id] = player_box_opens.get(ctx.author.id, 0) + 1
    if prize["name"] != "SEM SORTE":
        player_prizes[ctx.author.id] = player_prizes.get(ctx.author.id, []) + [prize["name"]]

    desc = f"**{ctx.author.mention}** ganhou: **{prize['name']}**!"
    embed = discord.Embed(
        title="🎁 Caixa Especial Aberta!",
        description=desc,
        color=discord.Color.gold()
    )
    embed.set_image(url=prize['image'])
    msg = await ctx.send(embed=embed)

    if prize["name"] != "SEM SORTE":
        await msg.add_reaction(random.choice(reacoes))
        raros = contar_raros(ctx.author.id)
        caixas_abertas = player_box_opens[ctx.author.id]
        parabens_msg = (f"🎉 **Parabéns {ctx.author.mention}!** Você ganhou: **{prize['name']}**!"
                        f"\nCaixas Abertas: **{caixas_abertas}** | Prêmios Raros: **{raros}**")
        embed_parabens = discord.Embed(
            title="🥳 Ganhador do Sorteio (Admin)!",
            description=parabens_msg,
            color=discord.Color.green()
        )
        embed_parabens.set_image(url=prize['image'])
        await bot.get_channel(canal_premio).send(embed=embed_parabens)

# Lista de status rotativos do bot
status_list = [
    "Jogando 7 Days to Die",
    "Falando com Willi",
    "Conversando com Willi",
    "Dormindo"
]
status_index = 0

@tasks.loop(minutes=5)
async def mudar_status():
    global status_index
    await bot.change_presence(activity=discord.Game(name=status_list[status_index]))
    status_index = (status_index + 1) % len(status_list)

TOKEN = os.getenv('TOKEN')
bot.run(TOKEN)
