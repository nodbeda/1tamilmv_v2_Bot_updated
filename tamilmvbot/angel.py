import os
import time
from dotenv import load_dotenv
import telebot
from telebot import types
import requests
from bs4 import BeautifulSoup
from flask import Flask, request
import logging

# Load .env variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Environment Variables
TOKEN = os.getenv('TOKEN')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')
TAMILMV_URL = os.getenv('TAMILMV_URL', 'https://www.1tamilmv.ist')
CF_CLEARANCE = os.getenv('CF_CLEARANCE')
PORT = int(os.getenv('PORT', 8080))

# Bot and Flask setup
bot = telebot.TeleBot(TOKEN, parse_mode='HTML')
app = Flask(__name__)

# Global variables
movie_list = []
real_dict = {}

# Headers and cookies for Cloudflare bypass
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36'
}
COOKIES = {
    'cf_clearance': CF_CLEARANCE
}

# /start command
@bot.message_handler(commands=['start'])
def start_cmd(message):
    welcome = """<b>Hello 👋</b>

<blockquote><b>🎬 Get latest Movies from 1Tamilmv</b></blockquote>

⚙️ <b>How to use me??</b> 🤔

✯ Enter /view to get magnet links & torrent files

<blockquote><b>🔗 Share and Support 💝</b></blockquote>"""
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton('🔗 GitHub 🔗', url='https://github.com/SudoR2spr'),
        types.InlineKeyboardButton('⚡ Powered By', url='https://t.me/Opleech_WD')
    )
    bot.send_photo(
        chat_id=message.chat.id,
        photo='https://graph.org/file/4e8a1172e8ba4b7a0bdfa.jpg',
        caption=welcome,
        reply_markup=keyboard
    )

# /view command
@bot.message_handler(commands=['view'])
def view_cmd(message):
    bot.send_message(message.chat.id, "<b>🧲 Please wait for 10 ⏰ seconds</b>")
    global movie_list, real_dict
    movie_list, real_dict = tamilmv()

    if not movie_list:
        bot.send_message(message.chat.id, "<b>❌ Failed to fetch movie list.</b>")
        return

    keyboard = make_keyboard(movie_list)
    bot.send_photo(
        chat_id=message.chat.id,
        photo='https://graph.org/file/4e8a1172e8ba4b7a0bdfa.jpg',
        caption="<b><blockquote>🔗 Select a Movie from the list 🎬</blockquote></b>\n\n🔘 Please select a movie:",
        reply_markup=keyboard
    )

# Inline keyboard builder
def make_keyboard(movies):
    markup = types.InlineKeyboardMarkup()
    for key, title in enumerate(movies):
        markup.add(types.InlineKeyboardButton(text=title, callback_data=f"{key}"))
    return markup

# Callback handler
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    global real_dict
    idx = int(call.data)
    movie = movie_list[idx]
    if movie in real_dict:
        for msg in real_dict[movie]:
            bot.send_message(call.message.chat.id, text=msg)

# Main scraping logic
def tamilmv():
    try:
        r = requests.get(TAMILMV_URL, headers=HEADERS, cookies=COOKIES, timeout=20)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'lxml')
        items = soup.find_all('div', {'class': 'ipsType_break ipsContained'})

        if len(items) < 15:
            return [], {}

        movie_list = []
        real_dict = {}

        for i in range(15):
            title = items[i].find('a').text.strip()
            link = items[i].find('a')['href']
            movie_list.append(title)
            real_dict[title] = get_movie_details(link)

        return movie_list, real_dict
    except Exception as e:
        logger.error(f"Error in tamilmv(): {e}")
        return [], {}

# Get details (magnet/torrent)
def get_movie_details(url):
    try:
        r = requests.get(url, headers=HEADERS, cookies=COOKIES, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'lxml')

        title = soup.find('h1').text.strip() if soup.find('h1') else "Unknown Title"
        magnets = [a['href'] for a in soup.find_all('a', href=True) if 'magnet:' in a['href']]
        torrents = [a['href'] for a in soup.find_all('a', {"data-fileext": "torrent"}, href=True)]

        messages = []
        for i, mag in enumerate(magnets):
            tfile = torrents[i] if i < len(torrents) else None
            if tfile and not tfile.startswith("http"):
                tfile = f"{TAMILMV_URL}{tfile}"

            msg = f"<b>📂 Movie Title:</b>\n<blockquote>{title}</blockquote>\n\n<b>🧲 Magnet Link:</b>\n<pre>{mag}</pre>\n"
            msg += f"📥 <b>Download Torrent:</b>\n<a href=\"{tfile}\">🔗 Click Here</a>\n" if tfile else "📥 <b>Torrent File:</b> Not Available"
            messages.append(msg)
        return messages
    except Exception as e:
        logger.error(f"Error in get_movie_details(): {e}")
        return []

# Flask routes
@app.route('/')
def health_check():
    return "Angel Bot Healthy", 200

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_str = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_str)
        bot.process_new_updates([update])
        return ''
    return 'Invalid content type', 403

# Webhook Setup
if __name__ == "__main__":
    bot.remove_webhook()
    time.sleep(1)
    bot.set_webhook(url=f"https://combative-ardella-karthikpro12737-7a90b660.koyeb.app/webhook")
    app.run(host='0.0.0.0', port=PORT)
