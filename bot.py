import telebot
from telebot import types

TOKEN = "8594048221:AAE6AgJatafG-vNHiaTtTwfKKpm3n7UMc9g"
GROUP_ID = -1003685695007
ADMIN_ID = 1794307964
CARD = "9860 6004 0926 5755"

bot = telebot.TeleBot(TOKEN)

user_balance = {}
step_data = {}
payment_amount = {}


@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🚕 Заказ бериш", "💰 Баланс")
    bot.send_message(message.chat.id, "Ассалому алайкум!", reply_markup=markup)


@bot.message_handler(func=lambda m: m.text == "💰 Баланс")
def balance(message):
    bal = user_balance.get(message.from_user.id, 0)
    bot.send_message(
        message.chat.id,
        f"💰 Баланс: {bal} сўм\n\n💳 Карта:\n{CARD}\n\nАввал сумма ёзинг\nМисол: 50000"
    )
    payment_amount[message.from_user.id] = "wait"


@bot.message_handler(func=lambda m: m.from_user.id in payment_amount and payment_amount[m.from_user.id] == "wait")
def set_payment(message):
    payment_amount[message.from_user.id] = message.text
    bot.send_message(message.chat.id, "Энди чек расмини юборинг")


@bot.message_handler(content_types=['photo'])
def receive_check(message):
    amount = payment_amount.get(message.from_user.id, "номаълум")

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(
        "✅ Тасдиқлаш",
        callback_data=f"approve:{message.from_user.id}:{amount}"
    ))

    bot.send_photo(
        ADMIN_ID,
        message.photo[-1].file_id,
        caption=f"💳 Чек\n👤 {message.from_user.first_name}\n💰 {amount} сўм",
        reply_markup=markup
    )

    bot.send_message(message.chat.id, "✅ Чек админга юборилди")


@bot.message_handler(func=lambda m: m.text == "🚕 Заказ бериш")
def order_start(message):
    step_data[message.from_user.id] = {}
    bot.send_message(message.chat.id, "📍 Қаердан йўлга чиқасиз?")


@bot.message_handler(func=lambda m: m.from_user.id in step_data and "from" not in step_data[m.from_user.id])
def get_from(message):
    step_data[message.from_user.id]["from"] = message.text
    bot.send_message(message.chat.id, "📍 Қаерга борасиз?")


@bot.message_handler(func=lambda m: m.from_user.id in step_data and "to" not in step_data[m.from_user.id])
def get_to(message):
    step_data[message.from_user.id]["to"] = message.text
    bot.send_message(message.chat.id, "👥 Нечта жой?")


@bot.message_handler(func=lambda m: m.from_user.id in step_data and "seats" not in step_data[m.from_user.id])
def get_seats(message):
    step_data[message.from_user.id]["seats"] = message.text
    bot.send_message(message.chat.id, "📞 Телефон рақам?")


@bot.message_handler(func=lambda m: m.from_user.id in step_data and "phone" not in step_data[m.from_user.id])
def get_phone(message):
    step_data[message.from_user.id]["phone"] = message.text
    data = step_data[message.from_user.id]

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(
        "✅ Қабул қилиш",
        callback_data=f"take:{message.from_user.id}"
    ))

    bot.send_message(
        GROUP_ID,
        f"""🚕 Янги заказ

📍 Қаердан: {data['from']}
📍 Қаерга: {data['to']}
👥 Жой: {data['seats']}
📞 Номер: {data['phone']}""",
        reply_markup=markup
    )

    bot.send_message(message.chat.id, "✅ Заказ юборилди")
    del step_data[message.from_user.id]


@bot.callback_query_handler(func=lambda call: True)
def callbacks(call):

    if call.data.startswith("approve:"):
        _, user_id, amount = call.data.split(":")
        user_id = int(user_id)
        amount = int(amount)

        user_balance[user_id] = user_balance.get(user_id, 0) + amount

        bot.send_message(
            user_id,
            f"✅ Баланс {amount} сўмга тўлдирилди"
        )

        bot.answer_callback_query(call.id, "Тасдиқланди")


    elif call.data.startswith("take:"):
        driver_id = call.from_user.id
        bal = user_balance.get(driver_id, 0)

        if bal < 10000:
            bot.answer_callback_query(call.id, "❌ Баланс етарли эмас")
            return

        user_balance[driver_id] -= 10000

        bot.send_message(
            GROUP_ID,
            f"✅ {call.from_user.first_name} заказни қабул қилди"
        )

        bot.send_message(
            driver_id,
            "✅ Сиз заказни қабул қилдингиз"
        )

        bot.answer_callback_query(call.id, "Қабул қилинди")


bot.infinity_polling()
