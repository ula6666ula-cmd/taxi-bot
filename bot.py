import telebot
from telebot import types

TOKEN = "8594048221:AAFNfcm676ZM8s9qUxEJ6z9u66QcujPp1ww"

bot = telebot.TeleBot(TOKEN)

GROUP_ID = -1003877062196

user_data = {}


@bot.message_handler(commands=['start'])
def start(message):

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    btn = types.KeyboardButton("🚕 Заказ бериш")
    markup.add(btn)

    bot.send_message(
        message.chat.id,
        "Ассалому алайкум!\n🚕 Заказ бериш тугмасини босинг",
        reply_markup=markup
    )


@bot.message_handler(func=lambda m: m.text == "🚕 Заказ бериш")
def order_start(message):

    user_data[message.chat.id] = {}

    msg = bot.send_message(
        message.chat.id,
        "📍 Қаердан йўлга чиқасиз?"
    )

    bot.register_next_step_handler(msg, get_from)


def get_from(message):

    user_data[message.chat.id]['from'] = message.text

    msg = bot.send_message(
        message.chat.id,
        "📍 Қаерга борасиз?"
    )

    bot.register_next_step_handler(msg, get_to)


def get_to(message):

    user_data[message.chat.id]['to'] = message.text

    msg = bot.send_message(
        message.chat.id,
        "👥 Нечта жой керак?"
    )

    bot.register_next_step_handler(msg, get_seat)


def get_seat(message):

    user_data[message.chat.id]['seat'] = message.text

    msg = bot.send_message(
        message.chat.id,
        "📞 Телефон рақамингизни юборинг"
    )

    bot.register_next_step_handler(msg, get_phone)


def get_phone(message):

    user_data[message.chat.id]['phone'] = message.text

    send_order(message)


def send_order(message):

    user = user_data[message.chat.id]

    inline = types.InlineKeyboardMarkup()

    btn = types.InlineKeyboardButton(
        "✅ Заказни олиш",
        callback_data=f"accept_{message.chat.id}"
    )

    inline.add(btn)

    username = message.from_user.username

    if username:
        username_text = f"@{username}"
    else:
        username_text = "Йўқ"

    # ҚИСҚА ЗАКАЗ
    short_text = f"""
🔥 <b>ЯНГИ КЛИЕНТ!!!</b>

🚕 Йўналиш:
📍 {user['from']}
➡️ {user['to']}

👥 Йўловчи сони: {user['seat']}

👇 Заказни олиш учун тугмани босинг
"""

    bot.send_message(
        GROUP_ID,
        short_text,
        parse_mode="HTML",
        reply_markup=inline,
        disable_web_page_preview=True
    )

    # ТЎЛИҚ МАЪЛУМОТ САҚЛАШ
    user_data[message.chat.id]['full_name'] = message.from_user.first_name
    user_data[message.chat.id]['username'] = username_text

    bot.send_message(
        message.chat.id,
        "✅ Заказ группага юборилди"
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith("accept_"))
def accept_order(call):

    chat_id = int(call.data.split("_")[1])

    driver = call.from_user.first_name

    user = user_data.get(chat_id)

    if not user:
        return

    username = call.from_user.username

    if username:
        driver_username = f"@{username}"
    else:
        driver_username = "Йўқ"

    # ХАЙДОВЧИГА ТЎЛИҚ МАЪЛУМОТ
    full_text = f"""
✅ Сиз заказни қабул қилдингиз

📞 Тел: {user['phone']}

👤 Исми: {user['full_name']}

📨 Username: {user['username']}

🚕 Йўналиш:
📍 {user['from']}
➡️ {user['to']}
"""

    bot.send_message(
        call.from_user.id,
        full_text
    )

    # КЛИЕНТГА ХАЙДОВЧИ МАЪЛУМОТИ
    client_text = f"""
✅ Заказ қабул қилинди

🚕 Ҳайдовчи: {driver}

📨 Username: {driver_username}
"""

    bot.send_message(
        chat_id,
        client_text
    )

    bot.answer_callback_query(
        call.id,
        "Заказ сизга бириктирилди"
    )

    # ТУГМАНИ ЎЧИРИШ
    bot.edit_message_reply_markup(
        call.message.chat.id,
        call.message.message_id,
        reply_markup=None
    )

    # ГРУППАГА ХАБАР
    bot.send_message(
        GROUP_ID,
        f"✅ Заказни {driver} қабул қилди"
    )


print("Bot ishladi...")
bot.infinity_polling()
