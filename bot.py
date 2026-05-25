import telebot
from telebot import types

TOKEN = "8594048221:AAE6AgJatafG-vNHiaTtTwfKKpm3n7UMc9g"
GROUP_ID = -1003685695007
ADMIN_ID = 1794307964
CARD = "9860600409265755"

bot = telebot.TeleBot(TOKEN)

user_balance = {}
orders = {}
payment_wait = {}


def menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🚕 Заказ бериш")
    kb.add("💰 Баланс")
    return kb


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "Ассалому алайкум!\nТакси ботга хуш келибсиз.",
        reply_markup=menu()
    )


@bot.message_handler(func=lambda m: m.text == "💰 Баланс")
def balance(message):
    uid = message.from_user.id
    bal = user_balance.get(uid, 0)

    payment_wait[uid] = {"step": "amount"}

    bot.send_message(
        uid,
        f"""💰 Балансингиз: {bal} сўм

💳 Тўлов учун карта:
{CARD}

Қанча тўлдирмоқчисиз?"""
    )


@bot.message_handler(func=lambda m: m.text == "🚕 Заказ бериш")
def order_start(message):
    uid = message.from_user.id
    orders[uid] = {"step": "from"}

    bot.send_message(uid, "📍 Қаердан?")


@bot.message_handler(content_types=['photo'])
def receive_photo(message):
    uid = message.from_user.id

    if uid not in payment_wait:
        return

    if payment_wait[uid]["step"] == "photo":
        amount = payment_wait[uid]["amount"]

        kb = types.InlineKeyboardMarkup()
        kb.add(
            types.InlineKeyboardButton(
                "✅ Тасдиқлаш",
                callback_data=f"approve_{uid}_{amount}"
            )
        )

        bot.send_photo(
            ADMIN_ID,
            message.photo[-1].file_id,
            caption=f"💳 Тўлов чеки\n💰 {amount} сўм",
            reply_markup=kb
        )

        bot.send_message(uid, "✅ Чек админга юборилди")


@bot.message_handler(func=lambda m: True)
def handler(message):
    uid = message.from_user.id
    text = message.text

    if uid in payment_wait:
        if payment_wait[uid]["step"] == "amount":
            try:
                amount = int(text)
                payment_wait[uid]["amount"] = amount
                payment_wait[uid]["step"] = "photo"
                bot.send_message(uid, "📷 Чек расмини юборинг")
            except:
                bot.send_message(uid, "Суммани рақамда киритинг")
            return

    if uid not in orders:
        return

    step = orders[uid]["step"]

    if step == "from":
        orders[uid]["from"] = text
        orders[uid]["step"] = "to"
        bot.send_message(uid, "📍 Қаерга?")

    elif step == "to":
        orders[uid]["to"] = text
        orders[uid]["step"] = "seats"
        bot.send_message(uid, "👥 Нечта жой?")

    elif step == "seats":
        orders[uid]["seats"] = text
        orders[uid]["step"] = "phone"
        bot.send_message(uid, "📞 Телефон рақамингизни киритинг")

    elif step == "phone":
        orders[uid]["phone"] = text

        kb = types.InlineKeyboardMarkup()
        kb.add(
            types.InlineKeyboardButton(
                "✅ Қабул қилиш",
                callback_data=f"take_{uid}"
            )
        )

        bot.send_message(
            GROUP_ID,
            f"""🚕 Янги заказ

📍 Қаердан: {orders[uid]['from']}
📍 Қаерга: {orders[uid]['to']}
👥 Жой: {orders[uid]['seats']}""",
            reply_markup=kb
        )

        bot.send_message(uid, "✅ Заказ группага юборилди")
        del orders[uid]


@bot.callback_query_handler(func=lambda c: True)
def callback(call):

    if call.data.startswith("approve_"):
        _, uid, amount = call.data.split("_")
        uid = int(uid)
        amount = int(amount)

        user_balance[uid] = user_balance.get(uid, 0) + amount

        bot.send_message(
            uid,
            f"✅ Балансингиз {amount} сўмга тўлдирилди"
        )

        bot.answer_callback_query(call.id, "Тасдиқланди")


    elif call.data.startswith("take_"):
        uid = int(call.data.split("_")[1])
        driver = call.from_user.id

        if user_balance.get(driver, 0) < 10000:
            bot.answer_callback_query(call.id, "❌ Баланс етарли эмас")
            return

        user_balance[driver] -= 10000

        data = orders.get(uid)
        if not data:
            bot.answer_callback_query(call.id, "Заказ топилмади")
            return

        bot.send_message(
            driver,
            f"""✅ Заказ қабул қилинди

📍 Қаердан: {data['from']}
📍 Қаерга: {data['to']}
👥 Жой: {data['seats']}
📞 Номер: {data['phone']}"""
        )

        done = types.InlineKeyboardMarkup()
        done.add(
            types.InlineKeyboardButton(
                "✅ Қабул қилинди",
                callback_data="done"
            )
        )

        bot.edit_message_text(
            f"""🚕 Заказ қабул қилинди

📍 Қаердан: {data['from']}
📍 Қаерга: {data['to']}
👥 Жой: {data['seats']}

👤 Хайдовчи: {call.from_user.first_name}""",
            GROUP_ID,
            call.message.message_id,
            reply_markup=done
        )

        bot.answer_callback_query(call.id, "Қабул қилинди")


bot.infinity_polling(skip_pending=True)
