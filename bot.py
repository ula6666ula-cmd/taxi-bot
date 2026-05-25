import telebot
from telebot import types

TOKEN = "8594048221:AAE6AgJatafG-vNHiaTtTwfKKpm3n7UMc9g"
GROUP_ID = -1003685695007
ADMIN_ID = 1794307964
CARD = "9860 6004 0926 5755"

bot = telebot.TeleBot(TOKEN)

user_balance = {}
user_step = {}
order_data = {}

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🚕 Заказ бериш", "💰 Баланс")
    bot.send_message(message.chat.id, "Ассалому алайкум!", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "💰 Баланс")
def balance(message):
    bal = user_balance.get(message.from_user.id, 0)
    bot.send_message(message.chat.id, f"💰 Баланс: {bal} сўм\n\nКарта: {CARD}\nЧек расмини юборинг")

@bot.message_handler(content_types=['photo'])
def receive_check(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Тасдиқлаш", callback_data=f"approve_{message.from_user.id}"))

    bot.send_photo(
        ADMIN_ID,
        message.photo[-1].file_id,
        caption=f"💳 Янги чек\n👤 {message.from_user.first_name}\n🆔 {message.from_user.id}",
        reply_markup=markup
    )

    bot.send_message(message.chat.id, "✅ Чек админга юборилди")

@bot.callback_query_handler(func=lambda call: call.data.startswith("approve_"))
def approve(call):
    if call.from_user.id != ADMIN_ID:
        return

    driver_id = int(call.data.split("_")[1])
    user_balance[driver_id] = user_balance.get(driver_id, 0) + 50000

    bot.send_message(driver_id, "✅ 50 000 сўм қўшилди")
    bot.answer_callback_query(call.id, "Тасдиқланди")

@bot.message_handler(func=lambda m: m.text == "🚕 Заказ бериш")
def order_start(message):
    user_step[message.from_user.id] = "from"
    bot.send_message(message.chat.id, "Қайердан?")

@bot.message_handler(func=lambda m: m.from_user.id in user_step)
def process_order(message):
    uid = message.from_user.id

    if user_step[uid] == "from":
        order_data[uid] = {"from": message.text}
        user_step[uid] = "to"
        bot.send_message(message.chat.id, "Қаерга?")
        return

    if user_step[uid] == "to":
        order_data[uid]["to"] = message.text

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("✅ Қабул қилиш", callback_data=f"take_{uid}"))

        bot.send_message(
            GROUP_ID,
            f"🚕 Янги заказ\n\n📍 Қайердан: {order_data[uid]['from']}\n📍 Қаерга: {order_data[uid]['to']}",
            reply_markup=markup
        )

        bot.send_message(message.chat.id, "✅ Заказ юборилди")

        del user_step[uid]
        del order_data[uid]

@bot.callback_query_handler(func=lambda call: call.data.startswith("take_"))
def take(call):
    bal = user_balance.get(call.from_user.id, 0)

    if bal < 10000:
        bot.answer_callback_query(call.id, "Баланс етарли эмас")
        return

    user_balance[call.from_user.id] -= 10000
    bot.send_message(GROUP_ID, f"✅ Заказни {call.from_user.first_name} қабул қилди")

bot.infinity_polling()
