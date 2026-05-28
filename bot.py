import telebot
from telebot import types

TOKEN = "8594048221:AAH347Vcdh0haLmEs48yYWwVCIpftfr9JZo"
GROUP_ID = -1003875819316
ADMIN_ID = 1794307964
CARD = "9860600409265755"

bot = telebot.TeleBot(TOKEN)

user_balance = {}
orders = {}
step_data = {}
payment_wait = {}


# ================= MENU =================
def menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🚕 Заказ бериш", "💰 Баланс")
    return kb


# ================= START =================
@bot.message_handler(commands=['start'])
def start(message):
    step_data.pop(message.chat.id, None)

    bot.send_message(
        message.chat.id,
        "Ассалому алайкум",
        reply_markup=menu()
    )


# ================= BALANCE =================
@bot.message_handler(func=lambda m: m.text == "💰 Баланс")
def balance(message):
    bal = user_balance.get(message.chat.id, 0)

    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(
        "💳 Баланс тўлдириш",
        callback_data="send_check"
    ))

    bot.send_message(
        message.chat.id,
        f"💰 Баланс: {bal} сўм\n\n"
        f"💳 Карта:\n{CARD}",
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

    bot.send_message(
        ADMIN_ID,
        f"Тўлов келди.\n/pay {uid} 5000"
    )

    bot.send_message(
        uid,
        "✅ Чек админга юборилди"
    )

    del payment_wait[uid]


# ================= ORDER START =================
@bot.message_handler(func=lambda m: m.text == "🚕 Заказ бериш")
def order_start(message):
    step_data[message.chat.id] = {"step": "from"}
    bot.send_message(message.chat.id, "📍 Қаердан йулга чикасиз?")


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
        bot.send_message(uid, "👥 Нечта жой?")

    elif data["step"] == "seat":
        data["seat"] = message.text
        data["step"] = "phone"
        bot.send_message(uid, "📞 Телефон номер?")

    elif data["step"] == "phone":
        data["phone"] = message.text

        order_id = len(orders) + 1
        orders[order_id] = data.copy()

        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(
            "✅ Қабул қилиш",
            callback_data=f"accept_{order_id}"
        ))

        txt = (
            f"🚕 Янги заказ\n\n"
            f"📍 Қаердан: {data['from']}\n"
            f"📍 Қаерга: {data['to']}\n"
            f"👥 Жой: {data['seat']}"
        )

        bot.send_message(GROUP_ID, txt, reply_markup=kb)
        bot.send_message(uid, "✅ Заказ юборилди", reply_markup=menu())

        del step_data[uid]


# ================= ACCEPT ORDER =================
@bot.callback_query_handler(func=lambda call: call.data.startswith("accept_"))
def accept_order(call):
    try:
        order_id = int(call.data.split("_")[1])
    except:
        bot.answer_callback_query(call.id, "Хато")
        return

    if order_id not in orders:
        bot.answer_callback_query(call.id, "Бу эски заказ")
        return

    uid = call.from_user.id
    balance = user_balance.get(uid, 0)

    if balance < 5000:
        bot.answer_callback_query(call.id, "Баланс етарли эмас")

        bot.send_message(
            uid,
            f"❌ Баланс етарли эмас\n\n"
            f"Карта:\n{CARD}"
        )
        return

    user_balance[uid] -= 5000
    data = orders[order_id]

    bot.edit_message_text(
        f"✅ @{call.from_user.username or call.from_user.first_name} қабул қилди",
        call.message.chat.id,
        call.message.message_id
    )

    bot.send_message(
        uid,
        f"✅ Заказ қабул қилинди\n\n"
        f"📞 {data['phone']}\n"
        f"📍 Қаердан: {data['from']}\n"
        f"📍 Қаерга: {data['to']}\n"
        f"👥 Жой: {data['seat']}\n\n"
        f"💰 Қолдиқ: {user_balance[uid]} сўм"
    )

    del orders[order_id]


# ================= ADMIN PAYMENT =================
@bot.message_handler(commands=['pay'])
def pay(message):
    if message.from_user.id != ADMIN_ID:
        return

    try:
        parts = message.text.split()

        uid = int(parts[1])
        amount = int(parts[2])

        user_balance[uid] = user_balance.get(uid, 0) + amount

        bot.send_message(
            uid,
            f"✅ Баланс {amount} сўмга тўлдирилди\n"
            f"💰 Янги баланс: {user_balance[uid]} сўм"
        )

        bot.send_message(
            message.chat.id,
            "✅ Баланс муваффақиятли тўлдирилди"
        )

    except:
        bot.send_message(
            message.chat.id,
            "❌ Формат:\n/pay user_id amount"
        )


print("Bot ishga tushdi...")
bot.infinity_polling()
