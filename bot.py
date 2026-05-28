import telebot
from telebot import types

TOKEN = "8594048221:AAH347Vcdh0haLmEs48yYWwVCIpftfr9JZo"
GROUP_ID = -1003685695007

bot = telebot.TeleBot(TOKEN)

orders = {}
balances = {}


@bot.message_handler(commands=['start'])
def start(message):
    if message.from_user.id not in balances:
        balances[message.from_user.id] = 50000

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🚕 Заказ бериш", "💰 Баланс")

    bot.send_message(
        message.chat.id,
        "Ассалому алайкум",
        reply_markup=kb
    )


@bot.message_handler(func=lambda m: m.text == "💰 Баланс")
def balance(message):
    bot.send_message(
        message.chat.id,
        f"💰 Баланс: {balances.get(message.from_user.id, 0)} сўм"
    )


@bot.message_handler(func=lambda m: m.text == "🚕 Заказ бериш")
def order_start(message):
    msg = bot.send_message(message.chat.id, "📍 Қаердан?")
    bot.register_next_step_handler(msg, get_to)


def get_to(message):
    frm = message.text
    msg = bot.send_message(message.chat.id, "📍 Қаерга?")
    bot.register_next_step_handler(msg, get_seats, frm)


def get_seats(message, frm):
    to = message.text
    msg = bot.send_message(message.chat.id, "👥 Нечта жой?")
    bot.register_next_step_handler(msg, get_phone, frm, to)


def get_phone(message, frm, to):
    seats = message.text
    msg = bot.send_message(message.chat.id, "📞 Телефон номер?")
    bot.register_next_step_handler(msg, send_order, frm, to, seats)


def send_order(message, frm, to, seats):
    phone = message.text
    uid = message.from_user.id

    orders[uid] = {
        "from": frm,
        "to": to,
        "seats": seats,
        "phone": phone
    }

    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(
        "✅ Қабул қилиш",
        callback_data=f"take_{uid}"
    ))

    bot.send_message(
        GROUP_ID,
        f"""🚕 Янги заказ

📍 Қаердан: {frm}
📍 Қаерга: {to}
👥 Жой: {seats}""",
        reply_markup=kb
    )

    bot.send_message(message.chat.id, "✅ Заказ юборилди")


@bot.callback_query_handler(func=lambda c: c.data.startswith("take_"))
def take(call):
    uid = int(call.data.split("_")[1])

    if uid not in orders:
        bot.answer_callback_query(call.id, "Заказ топилмади")
        return

    driver = call.from_user.id

    if balances.get(driver, 0) < 10000:
        bot.answer_callback_query(call.id, "❌ Баланс кам")
        return

    balances[driver] -= 10000
    data = orders[uid]

    bot.send_message(
        driver,
        f"""✅ Заказ қабул қилинди

📞 {data['phone']}
📍 {data['from']}
➡️ {data['to']}
👥 {data['seats']}"""
    )

    bot.edit_message_text(
        f"✅ {call.from_user.first_name} қабул қилди",
        GROUP_ID,
        call.message.message_id
    )

    del orders[uid]

    bot.answer_callback_query(call.id, "Қабул қилинди")


print("Bot ishladi")
bot.infinity_polling(skip_pending=True)
