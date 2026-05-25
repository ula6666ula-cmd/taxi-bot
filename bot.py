import telebot
from telebot import types

TOKEN = "8594048221:AAH347Vcdh0haLmEs48yYWwVCIpftfr9JZo"
GROUP_ID = -1003685695007
ADMIN_ID = 1794307964

bot = telebot.TeleBot(TOKEN)

user_balance = {}
orders = {}
user_step = {}

def menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🚕 Заказ бериш")
    kb.add("💰 Баланс")
    return kb

@bot.message_handler(commands=['start'])
def start(message):
    if message.from_user.id not in user_balance:
        user_balance[message.from_user.id] = 50000
    bot.send_message(message.chat.id, "Хуш келибсиз", reply_markup=menu())

@bot.message_handler(func=lambda m: m.text == "💰 Баланс")
def balance(message):
    bal = user_balance.get(message.from_user.id, 0)
    bot.send_message(message.chat.id, f"💰 Баланс: {bal} сўм")

@bot.message_handler(func=lambda m: m.text == "🚕 Заказ бериш")
def order_start(message):
    user_step[message.from_user.id] = {}
    bot.send_message(message.chat.id, "📍 Қаердан?")

@bot.message_handler(func=lambda m: m.from_user.id in user_step)
def process_order(message):
    uid = message.from_user.id
    step = user_step[uid]

    if "from" not in step:
        step["from"] = message.text
        bot.send_message(message.chat.id, "📍 Қаерга?")
    elif "to" not in step:
        step["to"] = message.text
        bot.send_message(message.chat.id, "👥 Жой сони?")
    elif "seats" not in step:
        step["seats"] = message.text
        bot.send_message(message.chat.id, "📞 Телефон номер?")
    else:
        step["phone"] = message.text
        orders[uid] = step

        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("✅ Қабул қилиш", callback_data=f"take_{uid}"))

        bot.send_message(
            GROUP_ID,
            f"""🚕 Янги заказ

📍 Қаердан: {step['from']}
📍 Қаерга: {step['to']}
👥 Жой: {step['seats']}""",
            reply_markup=kb
        )

        bot.send_message(message.chat.id, "✅ Заказ юборилди")
        del user_step[uid]

@bot.callback_query_handler(func=lambda call: call.data.startswith("take_"))
def take_order(call):
    uid = int(call.data.split("_")[1])
    driver = call.from_user.id

    if uid not in orders:
        bot.answer_callback_query(call.id, "Заказ топилмади")
        return

    if user_balance.get(driver, 0) < 10000:
        bot.answer_callback_query(call.id, "Баланс етарли эмас")
        return

    data = orders[uid]
    user_balance[driver] -= 10000

    bot.send_message(
        driver,
        f"""✅ Сиз заказни қабул қилдингиз

📍 Қаердан: {data['from']}
📍 Қаерга: {data['to']}
👥 Жой: {data['seats']}
📞 Номер: {data['phone']}"""
    )

    bot.edit_message_text(
        f"""✅ Заказ қабул қилинди

📍 Қаердан: {data['from']}
📍 Қаерга: {data['to']}
👥 Жой: {data['seats']}

👤 Хайдовчи: {call.from_user.first_name}""",
        GROUP_ID,
        call.message.message_id
    )

    del orders[uid]
    bot.answer_callback_query(call.id, "Қабул қилинди")

print("Bot ishga tushdi")
bot.infinity_polling()
