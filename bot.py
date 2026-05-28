import telebot
from telebot import types
import json
import os
import re

TOKEN = "8594048221:AAFYSCHGT1GDPydisGWvzj5Z4jSQeKUs06c"
GROUP_ID = -1003875819316
ADMIN_ID = 1794307964
CARD = "9860600409265755"

bot = telebot.TeleBot(TOKEN)

BALANCE_FILE = "balances.json"
DRIVERS_FILE = "drivers.json"


# ================= FILE SAVE =================
def load_json(file):
    if os.path.exists(file):
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f)

user_balance = load_json(BALANCE_FILE)
drivers = load_json(DRIVERS_FILE)

orders = {}
step_data = {}
payment_wait = {}
register_step = {}


# ================= MENU =================
def menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🚕 Заказ бериш")
    kb.add("🚖 Хайдовчи бўлиш", "💰 Хайдовчи Баланси")
    return kb


# ================= START =================
@bot.message_handler(commands=['start'])
def start(message):
    uid = str(message.chat.id)

    if uid not in user_balance:
        user_balance[uid] = 0
        save_json(BALANCE_FILE, user_balance)

    bot.send_message(message.chat.id, "Ассалому алайкум 👋", reply_markup=menu())


# ================= DRIVER REGISTER =================
@bot.message_handler(func=lambda m: m.text == "🚖 Хайдовчи бўлиш")
def become_driver(message):
    uid = str(message.chat.id)

    if uid in drivers:
        bot.send_message(message.chat.id, "✅ Сиз аллақачон рўйхатдан ўтгансиз")
        return

    register_step[message.chat.id] = {"step": "name"}
    bot.send_message(message.chat.id, "👤 Исмингизни киритинг")


@bot.message_handler(func=lambda m: m.chat.id in register_step)
def register_driver(message):
    uid = str(message.chat.id)
    step = register_step[message.chat.id]["step"]

    if step == "name":
        if len(message.text.strip()) < 3:
            bot.send_message(message.chat.id, "❌ Исм камида 3 ҳарф бўлиши керак")
            return

        register_step[message.chat.id]["name"] = message.text
        register_step[message.chat.id]["step"] = "phone"
        bot.send_message(message.chat.id, "📞 Телефон рақамингизни киритинг\nМасалан: +998901234567")
        return

    elif step == "phone":
        phone = message.text.strip()

        if not re.fullmatch(r"\+?\d{12,13}", phone):
            bot.send_message(
                message.chat.id,
                "❌ Телефон рақам нотўғри\nМасалан: +998901234567"
            )
            return

        register_step[message.chat.id]["phone"] = phone
        register_step[message.chat.id]["step"] = "car"
        bot.send_message(message.chat.id, "🚘 Машина маркасини киритинг")
        return

    elif step == "car":
        if len(message.text.strip()) < 2:
            bot.send_message(message.chat.id, "❌ Машина номини тўғри киритинг")
            return

        drivers[uid] = {
            "name": register_step[message.chat.id]["name"],
            "phone": register_step[message.chat.id]["phone"],
            "car": message.text
        }

        save_json(DRIVERS_FILE, drivers)
        del register_step[message.chat.id]

        bot.send_message(
            message.chat.id,
            "✅ Сиз муваффақиятли хайдовчи бўлдингиз",
            reply_markup=menu()
        )


# ================= BALANCE =================
@bot.message_handler(func=lambda m: m.text == "💰 Хайдовчи Баланси")
def balance(message):
    uid = str(message.chat.id)
    bal = user_balance.get(uid, 0)

    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("💳 Баланс тўлдириш", callback_data="send_check"))

    bot.send_message(
        message.chat.id,
        f"💰 Баланс: {bal} сўм\n\n💳 Карта: {CARD}",
        reply_markup=kb
    )


# ================= SEND CHECK =================
@bot.callback_query_handler(func=lambda call: call.data == "send_check")
def send_check(call):
    payment_wait[call.from_user.id] = True
    bot.send_message(call.from_user.id, "📸 Чек расмини юборинг")


# ================= RECEIVE CHECK =================
@bot.message_handler(content_types=['photo'])
def receive_check(message):
    uid = message.chat.id

    if uid not in payment_wait:
        return

    bot.forward_message(ADMIN_ID, uid, message.message_id)
    bot.send_message(ADMIN_ID, f"💳 Янги тўлов\n/pay {uid} 5000")
    bot.send_message(uid, "✅ Чек админга юборилди")

    del payment_wait[uid]


# ================= ORDER START =================
@bot.message_handler(func=lambda m: m.text == "🚕 Заказ бериш")
def order_start(message):
    step_data[message.chat.id] = {"step": "from"}
    bot.send_message(message.chat.id, "📍 Қаердан йўлга чиқасиз?")


# ================= ORDER PROCESS =================
@bot.message_handler(func=lambda m: m.chat.id in step_data)
def process_order(message):
    uid = message.chat.id
    data = step_data[uid]

    if data["step"] == "from":
        data["from"] = message.text
        data["step"] = "to"
        bot.send_message(uid, "📍 Қаерга борасиз?")

    elif data["step"] == "to":
        data["to"] = message.text
        data["step"] = "seat"
        bot.send_message(uid, "👥 Нечта жой оласиз?")

    elif data["step"] == "seat":
        data["seat"] = message.text
        data["step"] = "phone"
        bot.send_message(uid, "📞 Телефон номер?")

    elif data["step"] == "phone":
        data["phone"] = message.text

        order_id = len(orders) + 1
        orders[order_id] = {"customer_id": uid, **data.copy()}

        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("✅ Қабул қилиш", callback_data=f"accept_{order_id}"))

        txt = f"""🚕 Янги заказ

📍 Қаердан: {data['from']}
📍 Қаерга: {data['to']}
👥 Жой: {data['seat']}"""

        bot.send_message(GROUP_ID, txt, reply_markup=kb)
        bot.send_message(uid, "✅ Заказ юборилди", reply_markup=menu())

        del step_data[uid]


# ================= ACCEPT ORDER =================
@bot.callback_query_handler(func=lambda call: call.data.startswith("accept_"))
def accept_order(call):
    order_id = int(call.data.split("_")[1])

    if order_id not in orders:
        return

    uid = str(call.from_user.id)

    if uid not in drivers:
        bot.send_message(call.from_user.id, "❌ Аввал рўйхатдан ўтинг")
        return

    if user_balance.get(uid, 0) < 5000:
        bot.send_message(call.from_user.id, "❌ Баланс етарли эмас")
        return

    user_balance[uid] -= 5000
    save_json(BALANCE_FILE, user_balance)

    data = orders[order_id]
    customer_id = data["customer_id"]

    bot.edit_message_text(
        f"✅ {drivers[uid]['name']} заказни қабул қилди",
        call.message.chat.id,
        call.message.message_id
    )

    bot.send_message(
        customer_id,
        f"""✅ Заказ қабул қилинди

👤 Ҳайдовчи: {drivers[uid]['name']}
📞 {drivers[uid]['phone']}
🚘 Машина: {drivers[uid]['car']}"""
    )

    del orders[order_id]


# ================= ADMIN PAYMENT =================
@bot.message_handler(commands=['pay'])
def pay(message):
    if message.from_user.id != ADMIN_ID:
        return

    try:
        _, uid, amount = message.text.split()

        user_balance[uid] = user_balance.get(uid, 0) + int(amount)
        save_json(BALANCE_FILE, user_balance)

        bot.send_message(int(uid), f"✅ Баланс {amount} сўмга тўлдирилди")
        bot.reply_to(message, "✅ Тасдиқланди")

    except:
        bot.reply_to(message, "❌ Формат: /pay user_id amount")


print("Bot ishga tushdi...")
bot.infinity_polling()
