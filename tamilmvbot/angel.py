import os
import time
from dotenv import load_dotenv
import telebot
from telebot import types
import requests
from bs4 import BeautifulSoup
from flask import Flask, request
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

TOKEN = os.getenv('TOKEN')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')
TAMILMV_URL = os.getenv('TAMILMV_URL', 'https://www.1tamilmv.ist')
CF_CLEARANCE = os.getenv('CF_CLEARANCE')
PORT = int(os.getenv('PORT', 8080))

bot = telebot.TeleBot(TOKEN, parse_mode='HTML')
app = Flask(__name__)

movie_list = []
real_dict = {}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
}
COOKIES = {
    'cf_clearance': CF_CLEARANCE
}

@bot.message_handler(commands=['start'])
def start_command(message):
    text_message = """<b>Hello 👋</b>

<blockquote><b>🎬 Get latest Movies from 1Tamilmv</b></blockquote>

⚙️ <b>How to use me??</b> 🤔

✯ Please enter /view command and you'll get magnet link as well as link to torrent file 😌

<blockquote><b>🔗 Share and Support 💝</b></blockquote>"""

    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton('🔗 GitHub 🔗', url='https://github.com/SudoR2spr'),
        types.InlineKeyboardButton(text="⚡ Powered By", url='https://t.me/Opleech_WD')
    )

    bot.send_photo(
        chat_id=message.chat.id,
        photo='https://graph.org/file/4e8a1172e8ba4b7a0bdfa.jpg',
        caption=text_message,
        reply_markup=keyboard
    )

@bot.message_handler(commands=['view'])
def view_command(message):
    bot.send_message(message.chat.id, "<b>🧲 Please wait for 10 ⏰ seconds</b>")
    global movie_list, real_dict
    movie_list, real_dict = tamilmv()

    if not movie_list:
        bot.send_message(message.chat.id, "⚠️ Sorry, could not fetch movie list. Please try again later.")
        return

    combined_caption = """<b><blockquote>🔗 Select a Movie from the list 🎬</blockquote></b>\n\n🔘 Please select a movie:"""
    keyboard = makeKeyboard(movie_list)

    bot.send_photo(
        chat_id=message.chat.id,
        photo='https://graph.org/file/4e8a1172e8ba4b7a0bdfa.jpg',
        caption=combined_caption,
        reply_markup=keyboard
    )

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    global real_dict
    try:
        idx = int(call.data)
        movie_name = movie_list[idx]
        if movie_name in real_dict:
            for msg in real_dict[movie_name]:
                bot.send_message(call.message.chat.id, text=msg)
    except Exception as e:
        logger.error(f"Callback error: {e}")

def makeKeyboard(movies):
    markup = types.InlineKeyboardMarkup()
    for idx, title in enumerate(movies):
        markup.add(types.InlineKeyboardButton(text=title, callback_data=str(idx)))
    return markup

def tamilmv():
    try:
        time.sleep(3)  # small delay to avoid rate limits
        response = requests.get(TAMILMV_URL, headers=HEADERS, cookies=COOKIES, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'lxml')

        movie_list = []
        real_dict = {}

        temps = soup.find_all('div', {'class': 'ipsType_break ipsContained'})

        if len(temps) < 15:
            logger.warning("Not enough movies found on the page")
            return [], {}

        for i in range(15):
            title_tag = temps[i].find('a')
            if not title_tag:
                continue
            title = title_tag.text.strip()
            link = title_tag['href']
            movie_list.append(title)
            movie_details = get_movie_details(link)
            real_dict[title] = movie_details

        return movie_list, real_dict
    except Exception as e:
        logger.error(f"Error in tamilmv(): {e}")
        return [], {}

def get_movie_details(url):
    try:
        time.sleep(1)
        html = requests.get(url, headers=HEADERS, cookies=COOKIES, timeout=15)
        html.raise_for_status()
        soup = BeautifulSoup(html.text, 'lxml')

        mags = [a['href'] for a in soup.find_all('a', href=True) if 'magnet:' in a['href']]
        torrents = [a['href'] for a in soup.find_all('a', {"data-fileext": "torrent"}, href=True)]

        movie_details = []
        movie_title = soup.find('h1').text.strip() if soup.find('h1') else "Unknown Title"

        for idx, mag_link in enumerate(mags):
            torrent_link = torrents[idx] if idx < len(torrents) else None
            if torrent_link and not torrent_link.startswith('http'):
                torrent_link = f'{TAMILMV_URL}{torrent_link}'

            message = f"""
<b>📂 Movie Title:</b>
<blockquote>{movie_title}</blockquote>

🧲 <b>Magnet Link:</b>
<pre>{mag_link}</pre>
"""
            if torrent_link:
                message += f"""
📥 <b>Download Torrent:</b>
<a href="{torrent_link}">🔗 Click Here</a>
"""
            else:
                message += "\n📥 <b>Torrent File:</b> Not Available\n"

            movie_details.append(message)

        return movie_details
    except Exception as e:
        logger.error(f"Error retrieving movie details: {e}")
        return []

@app.route('/')
def health_check():
    return "Angel Bot Healthy", 200

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    else:
        return 'Invalid content type', 403

if __name__ == "__main__":
    bot.remove_webhook()
    time.sleep(1)
    bot.set_webhook(url=f"https://combative-ardella-karthikpro12737-7a90b660.koyeb.app/bot7818048200:AAE5Z_QLMibVhfT-lMD3RHfJ2O-ja3L1x8k")
    app.run(host='0.0.0.0', port=PORT)
