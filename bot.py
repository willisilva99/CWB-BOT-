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
canal_abrir_caixa = 1309181452595757077  # Canal de comando para abrir caixas
canal_rank = 1309181411751886869  # Canal de Rank Automático
canal_premio = 1222717244170174588  # Canal de aviso de prêmios em tempo real

# Dicionário para armazenar o último tempo de sorteio de cada jogador e pontuação de embers
last_attempt_time = {}
player_prizes = {}
player_box_opens = {}
player_embers = {}

# Emojis de reação para adicionar
reacoes = ["🔥", "<:emoji_1:1262824010723365030>", "<:emoji_2:1261377496893489242>", "<:emoji_3:1261374830088032378>", "<:emoji_4:1260945241918279751>"]

# Atualização dos prêmios com chances e descrições
prizes = [
    {"name": "AK47", "image": "https://i.postimg.cc/KYWdMknH/Ak47.webp", "chance": 3, "description": "Uma poderosa AK47, perfeita para dominar o apocalipse com força e precisão."},
    {"name": "VIP", "image": "https://i.postimg.cc/P537gpF5/pngtree-vip-3d-golden-word-element-png-image-240239.png", "chance": 0.05, "description": "Um status VIP especial que te dá acesso a benefícios exclusivos no apocalipse."},
    {"name": "GIROCÓPTERO", "image": "https://i.postimg.cc/fR84MgkZ/Gyrocopter-Placeable.webp", "chance": 2, "description": "O Giroscópio, um meio de transporte aéreo que vai te levar para qualquer lugar do apocalipse rapidamente."},
    {"name": "MOTO", "image": "https://i.postimg.cc/9f060tq9/Motorcycle-Placeable.webp", "chance": 3, "description": "Uma moto resistente, perfeita para desviar de zumbis e explorar os territórios inexplorados."},
    {"name": "SEM SORTE", "image": "https://i.postimg.cc/Y0KZd5DN/DALL-E-2024-11-21-15-18-18-The-same-post-apocalyptic-supply-crate-marked-with-CWB-now-open-reve.webp", "chance": 88, "description": "A sorte não está ao seu lado. Mas a luta continua! Tente novamente, sobrevivente!"},
    {"name": "CWB Coin", "image": "https://imgur.com/n4dqi3d.png", "chance": 1, "description": "A moeda CWB, que pode ser usada para adquirir itens e vantagens especiais no apocalipse."},
    {"name": "Eraser T5", "image": "https://imgur.com/n4dqi3d.png", "chance": 0.8, "description": "O Eraser T5, uma arma potente que pode apagar qualquer ameaça do mapa com um único tiro."},
    {"name": "BullDog T5", "image": "https://imgur.com/n4dqi3d.png", "chance": 0.8, "description": "A BullDog T5, uma espingarda de combate ideal para eliminar hordas de inimigos próximos."},
    {"name": "Pack 5k Munição 9mm Urânio", "image": "https://imgur.com/n4dqi3d.png", "chance": 1.5, "description": "5.000 unidades de munição 9mm, ideal para a sua pistola, com uma poderosa carga de urânio."},
    {"name": "Pack 5k Munição 762mm Urânio", "image": "https://imgur.com/n4dqi3d.png", "chance": 1.5, "description": "5.000 unidades de munição 7.62mm, feitas de urânio, capazes de destruir qualquer inimigo."},
    {"name": "Pack 5k Munição Shot Urânio", "image": "https://imgur.com/n4dqi3d.png", "chance": 1.5, "description": "5.000 unidades de munição para espingarda, com urânio para um impacto devastador."}
]

# Mensagens de falha (Sem sorte)
mensagens_sem_sorte = [
    "O apocalipse não perdoa... O destino não sorriu para você hoje. Mas sua luta não acabou. Tente novamente, sobrevivente!",
    "A escuridão tomou conta da sua sorte. Mas lembre-se, a esperança nunca morre. O amanhã pode ser seu!",
    "Os ventos sombrios do CWB sopram contra você. Mas cada batalha te torna mais forte, continue tentando!",
    "A devastação não te favoreceu... Mas não desista, sobrevivente. Cada queda te leva um passo mais perto da vitória.",
]

# Mensagens de sorte (quando o jogador ganha prêmios)
mensagens_com_sorte = [
    "O apocalipse não conseguiu te derrotar! A sorte está do seu lado, sobrevivente! Você ganhou: **{prize}**.",
    "Você desafiou os mortos e a sorte te recompensou com algo incrível. Prepare-se para sua próxima jornada! Você ganhou: **{prize}**.",
    "O CWB é implacável, mas hoje você venceu. A sorte sorriu para você. Aproveite seu prêmio, herói do apocalipse!",
    "Em meio à destruição, você brilhou como um farol de esperança. O apocalipse não pode te parar! Você ganhou: **{prize}**.",
]

# Função para calcular o tempo restante para o próximo sorteio
def tempo_restante(last_time):
    return max(0, 10800 - (time.time() - last_time))  # 3 horas = 10800 segundos

# Função para selecionar um prêmio com base nas chances ajustadas
def escolher_premio():
    total = sum(item['chance'] for item in prizes)
    rand = random.uniform(0, total)
    current = 0
    for item in prizes:
        current += item['chance']
        if rand <= current:
            return item

# Comando de ajuda com imagem
@bot.command()
async def ajuda(ctx):
    ajuda_texto = """
    **Comandos disponíveis:**

    `!abrir_caixa` - Abra uma caixa para ganhar prêmios. Apenas pode ser usado no canal correto.
    `!abrir_admin` - Apenas o criador ou o usuário autorizado pode usar este comando, sem cooldown.
    `!limpar_chat` - Limpa o chat, só pode ser usado por administradores. (Comando de emergência)
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

# Comando para abrir a caixa com cooldown
@bot.command()
async def abrir_caixa(ctx):
    # Verifica se o comando foi executado no canal correto
    if ctx.channel.id != canal_abrir_caixa:  
        await ctx.send(f"{ctx.author.mention}, você só pode usar o comando neste canal: <#{canal_abrir_caixa}>")
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

    # Incrementa o contador de caixas abertas
    player_box_opens[user.id] = player_box_opens.get(user.id, 0) + 1

    # Cria o embed com a imagem do prêmio ou da mensagem de azar
    embed = discord.Embed(
        title="🎁 Você abriu a Caixa de Presentes!",
        description=f"{user.mention}, {mensagem} Você ganhou: **{prize['name']}**!" if prize["name"] != "SEM SORTE" else f"{user.mention}, {mensagem}",
        color=discord.Color.gold()
    )
    embed.set_image(url=prize['image'])  # A imagem agora usa um link direto válido

    # Envia a mensagem com o embed no canal
    msg = await ctx.send(embed=embed)

    # Reage no post do prêmio valioso apenas
    if prize["name"] != "SEM SORTE":
        await msg.add_reaction(random.choice(reacoes))

    # Envia a mensagem de parabéns no canal de premiação
    if prize["name"] != "SEM SORTE":
        parabens_msg = f"🎉 **Parabéns {user.mention}!** Você ganhou: **{prize['name']}**! Prepare-se para a próxima aventura!"
        await bot.get_channel(canal_premio).send(parabens_msg)

    # Atualiza o tempo da última tentativa do jogador
    last_attempt_time[user.id] = time.time()

# Comando para exibir o ranking de prêmios
@bot.command()
async def rank_premios(ctx):
    # Verifica se o comando foi executado no canal correto
    if ctx.channel.id != canal_rank:
        await ctx.send(f"{ctx.author.mention}, você só pode usar este comando no canal de rank: <#{canal_rank}>")
        return

    # Ordenando os jogadores com base nos prêmios ganhos
    rank = sorted(player_prizes.items(), key=lambda x: len(x[1]), reverse=True)
    mensagem = "🏆 **Ranking dos Melhores Prêmios** 🏆\n\n"

    for i, (user_id, prizes) in enumerate(rank[:10], start=1):
        user = await bot.fetch_user(user_id)
        itens_raros = [p for p in prizes if p != "SEM SORTE"]
        mensagem += f"{i}. **{user.display_name}** - {len(itens_raros)} prêmios raros: {', '.join(itens_raros)}\n"
    
    await ctx.send(mensagem)

# Comando para exibir o ranking de caixas abertas
@bot.command()
async def rank_caixas_abertas(ctx):
    # Verifica se o comando foi executado no canal correto
    if ctx.channel.id != canal_rank:
        await ctx.send(f"{ctx.author.mention}, você só pode usar este comando no canal de rank: <#{canal_rank}>")
        return

    # Ordenando os jogadores com base no número de caixas abertas
    rank = sorted(player_box_opens.items(), key=lambda x: x[1], reverse=True)
    mensagem = "📦 **Ranking de Abertura de Caixas** 📦\n\n"

    for i, (user_id, opens) in enumerate(rank[:5], start=1):
        user = await bot.fetch_user(user_id)
        mensagem += f"{i}. **{user.display_name}** - {opens} caixas abertas\n"
    
    await ctx.send(mensagem)

# Comando de administrador para abrir a caixa sem cooldown
@bot.command()
async def abrir_admin(ctx):
    # Verifica se o autor do comando é o criador ou o usuário autorizado
    criador_id = 470628393272999948  # Seu ID correto
    usuario_autorizado_id = 434531832097144852  # ID autorizado a usar o comando

    if ctx.author.id != criador_id and ctx.author.id != usuario_autorizado_id:
        # Embed de resposta caso o autor não seja o criador nem o autorizado
        embed = discord.Embed(
            title="Acesso Negado",
            description="Somente o criador ou o usuário autorizado podem usar este comando. Caso precise de algo, entre em contato.",
            color=discord.Color.red()
        )
        embed.set_footer(text="Caso tenha dúvidas, entre em contato com o criador do bot.")
        
        # Botão de contato com o link do criador
        button = Button(label="Entrar em Contato", style=discord.ButtonStyle.link, url="https://discord.com/users/470628393272999948")  # URL do criador para contato
        view = View()
        view.add_item(button)
        
        await ctx.send(embed=embed, view=view)
        return

    # Sorteia o prêmio como no comando normal
    prize = escolher_premio()

    embed = discord.Embed(
        title="🎁 Você abriu uma Caixa Especial!",
        description=f"**{ctx.author.mention}** ganhou: **{prize['name']}**!",
        color=discord.Color.gold()
    )
    embed.set_image(url=prize['image'])
    await ctx.send(embed=embed)

# Comando para limpar e zerar os rankings a cada 7 horas
@tasks.loop(hours=7)
async def limpar_rank():
    # Zerando os rankings de prêmios e caixas abertas
    player_prizes.clear()
    player_box_opens.clear()

    # Envia uma mensagem para o canal de rank
    channel = bot.get_channel(canal_rank)
    embed = discord.Embed(
        title="⚡ Zeração de Ranking ⚡",
        description="O ranking foi zerado. Todos os prêmios e caixas abertas foram reiniciados.",
        color=discord.Color.red()
    )
    await channel.send(embed=embed)

# Rodando o bot com o token de ambiente
TOKEN = os.getenv('TOKEN')
bot.run(TOKEN)
