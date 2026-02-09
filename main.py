import telebot
import requests
import sqlite3
import re
from datetime import datetime

API_TOKEN = 'YOUR_BOT_TOKEN_HERE'
bot = telebot.TeleBot(API_TOKEN)

con = sqlite3.connect('tiktok_users.db', check_same_thread=False)
cur = con.cursor()
cur.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT, date TEXT)''')
con.commit()

def save_user(user_id, username):
    cur.execute("INSERT OR IGNORE INTO users (user_id, username, date) VALUES (?, ?, ?)", 
                (user_id, username, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    con.commit()

def extract_username(text):
    match = re.search(r'tiktok\.com/@?([\w\.]+)', text)
    if match:
        return match.group(1)
    if text.startswith('@'):
        return text[1:]
    return text

def format_timestamp(ts):
    if not ts:
        return "N/A"
    try:
        return datetime.fromtimestamp(int(ts)).strftime('%Y-%m-%d %H:%M:%S')
    except:
        return "N/A"

def get_tiktok_data(username):
    url = "https://www.tikwm.com/api/user/info"
    params = {"unique_id": username}
    try:
        response = requests.get(url, params=params)
        data = response.json()
        if data.get('code') == 0:
            return data.get('data')
        return None
    except:
        return None

@bot.message_handler(commands=['start'])
def send_welcome(message):
    save_user(message.from_user.id, message.from_user.username)
    bot.reply_to(message, "Welcome. Send TikTok username or link.")

@bot.message_handler(func=lambda message: True)
def analyze_user(message):
    username = extract_username(message.text)
    wait_msg = bot.reply_to(message, "Please wait...")
    
    data = get_tiktok_data(username)
    
    if not data:
        bot.delete_message(message.chat.id, wait_msg.message_id)
        bot.send_message(message.chat.id, "Error: User not found or invalid link.")
        return

    user = data.get('user', {})
    stats = data.get('stats', {})
    
    is_private = "Yes" if user.get('is_secret') else "No"
    is_verified = "Yes" if user.get('verified') else "No"
    can_see_following = "No" if user.get('is_secret') else "Yes"
    open_favorite = "Yes" if user.get('openFavorite') else "No"
    
    msg = f"""Account Analysis: {user.get('uniqueId')}

[ User Details ]
Username: {user.get('uniqueId')}
Nickname: {user.get('nickname')}
User ID: {user.get('id')}
Region: {user.get('region', 'N/A').upper()}
Language: {user.get('language', 'N/A').upper()}
Bio: {user.get('signature', 'None')}

[ Statistics ]
Followers: {stats.get('followerCount', 0)}
Following: {stats.get('followingCount', 0)}
Friends: {stats.get('friendCount', 0)}
Likes: {stats.get('heartCount', 0)}
Videos: {stats.get('videoCount', 0)}

[ Status & Privacy ]
Verified: {is_verified}
Private Account: {is_private}
Can See Following: {can_see_following}
Open Favorites: {open_favorite}

[ History ]
Created At: {format_timestamp(user.get('createTime'))}
Last Nickname Change: {format_timestamp(user.get('last_change_nickname_time', 0))}
Last Username Change: {format_timestamp(user.get('last_change_unique_id_time', 0))}

[ Avatar ]
{user.get('avatarLarger')}
"""

    bot.delete_message(message.chat.id, wait_msg.message_id)
    bot.send_message(message.chat.id, msg)

bot.infinity_polling()
