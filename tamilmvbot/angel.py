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
# ============ WOODctaft =================
TOKEN = os.getenv('TOKEN')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')
TAMILMV_URL = os.getenv('TAMILMV_URL', 'https://www.1tamilmv.ist')
CF_CLEARANCE = os.getenv('CF_CLEARANCE', 'RlgHIeuzpe902MYx0vc_ZOtur9EpJ3WVUF9W20SBNXw-1747980033-1.2.1.1-vn86D89aC3ILph66naLWlmkwGr0Y8yWyjbNprhfHY1vk6sb0MLz6Ce2BsKuxUpjizefU0yuu4YOrBiCsxpF2szBZTzuxoQIL4iu57wQm6H5Cm5jp8YNiEBfeqAC9UUV9Nf_FQiUZ1jZMO8Kaha3ri_94ZIi7rYIS6aC9qZQBnrX21qAyA2smUgxGMlx7iJnm5gl2bCQ.aBUaMZyzIEcBTEOs96LuT48XQ.UBBLnhwHLd65Uu59YwD606qPHDquC3o7jgfjZ4AFpjm8g4zzSESoyjjw7DxnS7BKqV0ttkI34Q8mxbNxXmJJ.JFr2QsmZK2llDVPdoAFdD6r7GJE0UvHCxsykEJ1QPr9LGCUEugDc')  # <<< Added line
PORT = int(os.getenv('PORT', 8080))
# ========================================
bot = telebot.TeleBot(TOKEN, parse_mode='HTML')

# Flask app
app = Flask(__name__)

# Global variables
movie_list = []
real_dict = {}

# Reusable headers + cookies
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36'
}
COOKIES = {
    'cf_clearance': CF_CLEARANCE
}

# /start command
@bot.message_handler(commands=['start'])
def random_answer(message):
    text_message = """<b>Hello 👋</b>

<blockquote><b>🎬 Get latest Movies from 1Tamilmv</b></blockquote>

⚙️ <b>How to use me??</b> 🤔

✯ Please enter /view command and you'll get magnet link as well as link to torrent file 😌

<blockquote><b>🔗 Share and Support 💝</b></blockquote>"""

    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton(
            '🔗 GitHub 🔗',
            url='https://github.com/SudoR2spr'),
        types.InlineKeyboardButton(
            text="⚡ Powered By",
            url='https://t.me/Opleech_WD'))

    bot.send_photo(
        chat_id=message.chat.id,
        photo='https://graph.org/file/4e8a1172e8ba4b7a0bdfa.jpg',
        caption=text_message,
        reply_markup=keyboard
    )

# /view command
@bot.message_handler(commands=['view'])
def start(message):
    bot.send_message(message.chat.id, "<b>🧲 Please wait for 10 ⏰ seconds</b>")
    global movie_list, real_dict
    movie_list, real_dict = tamilmv()

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
    for key, value in enumerate(movie_list):
        if call.data == f"{key}":
            if value in real_dict.keys():
                for i in real_dict[value]:
                    bot.send_message(call.message.chat.id, text=i)

def makeKeyboard(movie_list):
    markup = types.InlineKeyboardMarkup()
    for key, value in enumerate(movie_list):
        markup.add(
            types.InlineKeyboardButton(
                text=value,
                callback_data=f"{key}"))
    return markup

def tamilmv():
    mainUrl = TAMILMV_URL

    movie_list = []
    real_dict = {}

    try:
        web = requests.get(mainUrl, headers=HEADERS, cookies=COOKIES)
        web.raise_for_status()
        soup = BeautifulSoup(web.text, 'lxml')

        temps = soup.find_all('div', {'class': 'ipsType_break ipsContained'})

        if len(temps) < 15:
            logger.warning("Not enough movies found on the page")
            return [], {}

        for i in range(15):
            title = temps[i].findAll('a')[0].text.strip()
            link = temps[i].find('a')['href']
            movie_list.append(title)

            movie_details = get_movie_details(link)
            real_dict[title] = movie_details

        return movie_list, real_dict
    except Exception as e:
        logger.error(f"Error in tamilmv function: {e}")
        return [], {}

def get_movie_details(url):
    try:
        html = requests.get(url, headers=HEADERS, cookies=COOKIES, timeout=15)
        html.raise_for_status()
        soup = BeautifulSoup(html.text, 'lxml')

        mag = [a['href'] for a in soup.find_all(
            'a', href=True) if 'magnet:' in a['href']]
        filelink = [a['href'] for a in soup.find_all(
            'a', {"data-fileext": "torrent", 'href': True})]

        movie_details = []
        movie_title = soup.find('h1').text.strip(
        ) if soup.find('h1') else "Unknown Title"

        for p in range(len(mag)):
            torrent_link = filelink[p] if p < len(filelink) else None
            if torrent_link and not torrent_link.startswith('http'):
                torrent_link = f'{TAMILMV_URL}{torrent_link}'

            message = f"""
<b>📂 Movie Title:</b>
<blockquote>{movie_title}</blockquote>

🧲 <b>Magnet Link:</b>
<pre>{mag[p]}</pre>
"""
            if torrent_link:
                message += f"""
📥 <b>Download Torrent:</b>
<a href="{torrent_link}">🔗 Click Here</a>
"""
            else:
                message += """
📥 <b>Torrent File:</b> Not Available
"""

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
    bot.set_webhook(url=f"{WEBHOOK_URL}/webhook")
    app.run(host='0.0.0.0', port=PORT)
