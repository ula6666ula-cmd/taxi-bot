import telebot
from telebot import types

TOKEN = "8594048221:AAE6AgJatafG-vNHiaTtTwfKKpm3n7UMc9g"
GROUP_ID = -1003685695007
ADMIN_ID = 1794307964
CARD = "9860 6004 0926 5755"

bot = telebot.TeleBot(TOKEN)

user_balance = {}
orders = {}
payment_wait = {}


def menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🚕 Заказ бериш", "💰 Баланс")
    return kb


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "Ассалому алайкум!",
        reply_markup=menu()
    )


@bot.message_handler(func=lambda m: m.text == "💰 Баланс")
def balance(message):
    bal = user_balance.get(message.from_user.id, 0)

    payment_wait[message.from_user.id] = {"step": "amount"}

    bot.send_message(
        message.chat.id,
        f"""💰 Баланс: {bal} сўм

💳 Карта:
{CARD}

Қанча тўлдирмоқчисиз?"""
    )


@bot.message_handler(func=lambda m: m.text == "🚕 Заказ бериш")
def order_start(message):
    orders[message.from_user.id] = {"step": "from"}
    bot.send_message(message.chat.id, "📍 Қаердан йўлга чиқасиз?")


@bot.message_handler(content_types=['photo'])
def receive_check(message):
    uid = message.from_user.id

    if uid not in payment_wait:
        return

    amount = payment_wait[uid]["amount"]

    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(
        "✅ Тасдиқлаш",
        callback_data=f"approve_{uid}_{amount}"
    ))

    bot.send_photo(
        ADMIN_ID,
        message.photo[-1].file_id,
        caption=f"💳 Чек\n💰 {amount} сўм",
        reply_markup=kb
    )

    bot.send_message(uid, "✅ Чек админга юборилди")
    del payment_wait[uid]


@bot.message_handler(func=lambda m: True)
def handler(message):
    uid = message.from_user.id
    text = message.text

    if uid in payment_wait:
        if payment_wait[uid]["step"] == "amount":
            payment_wait[uid]["amount"] = int(text)
            payment_wait[uid]["step"] = "photo"
            bot.send_message(uid, "📷 Чек расмини юборинг")
            return

    if uid not in orders:
        return

    step = orders[uid]["step"]

    if step == "from":
        orders[uid]["from"] = text
        orders[uid]["step"] = "to"
        bot.send_message(uid, "📍 Қаерга борасиз?")

    elif step == "to":
        orders[uid]["to"] = text
        orders[uid]["step"] = "seats"
        bot.send_message(uid, "👥 Нечта жой?")

    elif step == "seats":
        orders[uid]["seats"] = text
        orders[uid]["step"] = "phone"
        bot.send_message(uid, "📞 Телефон рақамингиз?")

    elif step == "phone":
        orders[uid]["phone"] = text

        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(
            "✅ Қабул қилиш",
            callback_data=f"take_{uid}"
        ))

        bot.send_message(
            GROUP_ID,
            f"""🚕 Янги заказ

📍 Қаердан: {orders[uid]['from']}
📍 Қаерга: {orders[uid]['to']}
👥 Жой: {orders[uid]['seats']}""",
            reply_markup=kb
        )

        bot.send_message(uid, "✅ Заказ юборилди")


@bot.callback_query_handler(func=lambda c: True)
def callbacks(call):

    if call.data.startswith("approve_"):
        _, uid, amount = call.data.split("_")

        uid = int(uid)
        amount = int(amount)

        user_balance[uid] = user_balance.get(uid, 0) + amount

        bot.send_message(
            uid,
            f"✅ Баланс {amount} сўмга тўлдирилди"
        )

        bot.answer_callback_query(call.id, "Тасдиқланди")

    elif call.data.startswith("take_"):
        uid = int(call.data.split("_")[1])
        driver = call.from_user.id

        if user_balance.get(driver, 0) < 10000:
            bot.answer_callback_query(call.id, "❌ Баланс етарли эмас")
            return

        user_balance[driver] -= 10000

        data = orders[uid]

        bot.send_message(
            driver,
            f"""✅ Заказ қабул қилинди

📍 Қаердан: {data['from']}
📍 Қаерга: {data['to']}
👥 Жой: {data['seats']}
📞 Номер: {data['phone']}"""
        )

        bot.send_message(
            GROUP_ID,
            f"✅ {call.from_user.first_name} заказни қабул қилди"
        )

        bot.answer_callback_query(call.id, "Қабул қилинди")


bot.infinity_polling()
