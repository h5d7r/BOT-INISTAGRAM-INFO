import telebot
import instaloader
import sqlite3
import re
from datetime import datetime

API_TOKEN = 'YOUR_BOT_TOKEN_HERE'
bot = telebot.TeleBot(API_TOKEN)
L = instaloader.Instaloader()

con = sqlite3.connect('insta_users.db', check_same_thread=False)
cur = con.cursor()
cur.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT, date TEXT)''')
con.commit()

def save_user(user_id, username):
    cur.execute("INSERT OR IGNORE INTO users (user_id, username, date) VALUES (?, ?, ?)", 
                (user_id, username, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    con.commit()

def extract_username(text):
    match = re.search(r'instagram\.com/([A-Za-z0-9_.]+)', text)
    if match:
        return match.group(1)
    return text.strip().replace('@', '')

@bot.message_handler(commands=['start'])
def send_welcome(message):
    save_user(message.from_user.id, message.from_user.username)
    bot.reply_to(message, "Welcome to Legendary Insta Bot.\nSend Username or Link.\nDev: Mr. Velox (@C2_9H)")

@bot.message_handler(func=lambda message: True)
def analyze_instagram(message):
    target_username = extract_username(message.text)
    wait_msg = bot.reply_to(message, "Analyzing Instagram Database... Please wait.")
    
    try:
        profile = instaloader.Profile.from_username(L.context, target_username)
        
        is_private = "Yes 🔒" if profile.is_private else "No 🔓"
        is_verified = "Yes ☑️" if profile.is_verified else "No"
        is_business = "Yes 💼" if profile.is_business_account else "No"
        
        msg = f"""Instagram Analysis: @{profile.username}

[ User Profile ]
Name: {profile.full_name}
Username: @{profile.username}
ID: {profile.userid}
Bio: {profile.biography}

[ Statistics ]
Followers: {profile.followers:,}
Following: {profile.followees:,}
Posts: {profile.mediacount:,}

[ Account Type ]
Private: {is_private}
Verified: {is_verified}
Business: {is_business}
Category: {profile.business_category_name if profile.business_category_name else 'None'}
External Link: {profile.external_url if profile.external_url else 'None'}

[ Media ]
HD Picture: {profile.profile_pic_url}

Dev: Mr. Velox (@C2_9H)
"""
        bot.delete_message(message.chat.id, wait_msg.message_id)
        bot.send_message(message.chat.id, msg)
        
    except instaloader.ProfileNotExistsException:
        bot.delete_message(message.chat.id, wait_msg.message_id)
        bot.send_message(message.chat.id, "Error: User not found.")
    except Exception as e:
        bot.delete_message(message.chat.id, wait_msg.message_id)
        bot.send_message(message.chat.id, f"Error: {str(e)}")

bot.infinity_polling()
