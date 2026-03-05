import json
import random
from datetime import datetime
from itertools import cycle
from pytz import timezone as tz

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.ext import (
    ApplicationBuilder,
    ChatMemberHandler,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

TOKEN = "8279909532:AAGJ0-jAaqBC0erhYm1ZxyxBohbzPBBKNEg"

CHAT_ID = -1003741922832

ARQUIVO = "pagamentos.json"

TEMPO_PAGAMENTO = 1800  # 30 minutos

chaves = [
    "ernaldo.m21@gmail.com",
    "erick.brosso21@gmail.com",
    "Greciafranklin844@gmail.com",
    "rdakonff@icloud.com",
    "rdakonff@gmail.com",
    "rossvlim09@gmail.com",
    "marceloarthemalle@gmail.com"
]

VALOR_BASE = 22.34

manaus = tz("America/Manaus")
FIM = manaus.localize(datetime(2026, 3, 7, 0, 0))

chaves_cycle = cycle(chaves)

# -----------------------
# BANCO DE DADOS
# -----------------------

def carregar_dados():
    try:
        with open(ARQUIVO) as f:
            return json.load(f)
    except:
        return []

def salvar_dados(dados):
    with open(ARQUIVO, "w") as f:
        json.dump(dados, f, indent=4)

# -----------------------
# GERAR VALOR
# -----------------------

def gerar_valor():

    dados = carregar_dados()
    usados = {d["valor"] for d in dados}

    while True:

        variacao = round(random.uniform(0.01, 0.99), 2)
        valor = round(VALOR_BASE + variacao, 2)

        if valor not in usados:
            return valor

def chave_atual():
    return next(chaves_cycle)

# -----------------------
# BOTÕES
# -----------------------

def menu():

    keyboard = [

        [InlineKeyboardButton("💰 Pagar", callback_data="pagar")],

        [InlineKeyboardButton("✅ Já paguei", callback_data="paguei")],

        [InlineKeyboardButton("📊 Ver participantes", callback_data="lista")]

    ]

    return InlineKeyboardMarkup(keyboard)

# -----------------------
# EXPULSAR
# -----------------------

async def expulsar(context: ContextTypes.DEFAULT_TYPE):

    user_id = context.job.data

    dados = carregar_dados()

    for d in dados:

        if d["id"] == user_id and not d["pago"]:

            try:

                await context.bot.ban_chat_member(CHAT_ID, user_id)

                await context.bot.send_message(
                    CHAT_ID,
                    f"⏰ Tempo esgotado.\n\n@{d['username']} não confirmou pagamento e foi removido."
                )

            except:
                pass

            return

# -----------------------
# BOAS VINDAS
# -----------------------

async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat_member = update.chat_member

    if chat_member.new_chat_member.status != "member":
        return

    if chat_member.new_chat_member.user.is_bot:
        return

    user = chat_member.new_chat_member.user

    valor = gerar_valor()

    dados = carregar_dados()

    dados.append({
        "id": user.id,
        "username": user.username or user.first_name,
        "valor": valor,
        "pago": False
    })

    salvar_dados(dados)

    chave = chave_atual()

    texto = f"""
🐐 E aí {user.first_name}, seja bem-vindo!

Aqui é o *Sorteio Carneiro's* 🎉

A ideia é simples: todo mundo entra com uma pequena contribuição e no final **uma pessoa leva o prêmio**.

━━━━━━━━━━━━━━━

💰 Seu valor para participar

R$ {valor}

PIX:
{chave}

━━━━━━━━━━━━━━━

📌 Como participar

1️⃣ Copia a chave PIX acima  
2️⃣ Faz o pagamento exatamente de **R$ {valor}**  
3️⃣ Depois confirma no botão *Já paguei*

⏰ Você tem 30 minutos para confirmar o pagamento.

Boa sorte 🍀
"""

    await context.bot.send_message(
        CHAT_ID,
        texto,
        reply_markup=menu()
    )

    # iniciar contador de expulsão
    context.job_queue.run_once(
        expulsar,
        TEMPO_PAGAMENTO,
        data=user.id
    )

# -----------------------
# BOTÕES
# -----------------------

async def botoes(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    dados = carregar_dados()

    user = query.from_user

    if query.data == "pagar":

        for d in dados:

            if d["id"] == user.id:

                chave = chave_atual()

                await query.message.reply_text(
                    f"💰 Seu valor é:\n\nR$ {d['valor']}\n\nPIX:\n{chave}"
                )

                return

    if query.data == "paguei":

        await query.message.reply_text(
            "Envie o comando:\n\n/confirmar VALOR\n\nExemplo:\n/confirmar 22.56"
        )

    if query.data == "lista":

        texto = "📊 Participantes\n\n"

        for d in dados:

            status = "✅" if d["pago"] else "❌"

            texto += f"{status} @{d['username']} — R$ {d['valor']}\n"

        await query.message.reply_text(texto)

# -----------------------
# CONFIRMAR PAGAMENTO
# -----------------------

async def confirmar(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.args:

        await update.message.reply_text("Use /confirmar valor")

        return

    valor = float(context.args[0])

    dados = carregar_dados()

    for d in dados:

        if d["valor"] == valor:

            d["pago"] = True

            salvar_dados(dados)

            await update.message.reply_text(
                f"✅ Pagamento confirmado de @{d['username']}"
            )

            return

    await update.message.reply_text("Valor não encontrado.")

# -----------------------
# MAIN
# -----------------------

def main():

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(ChatMemberHandler(welcome, ChatMemberHandler.MY_CHAT_MEMBER))

    app.add_handler(CallbackQueryHandler(botoes))

    app.add_handler(CommandHandler("confirmar", confirmar))

    print("Bot rodando...")

    app.run_polling()

if __name__ == "__main__":

    main()
