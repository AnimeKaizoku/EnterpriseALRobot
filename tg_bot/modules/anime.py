import datetime
import html
import textwrap

import bs4
import jikanpy
import requests
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ParseMode
from telegram.ext import run_async, CallbackContext

from lynda import dispatcher
from lynda.modules.disable import DisableAbleCommandHandler

info_btn = "More Information"
kaizoku_btn = "Kaizoku ☠️"
kayo_btn = "Kayo 🏴‍☠️"
prequel_btn = "⬅️ Prequel"
sequel_btn = "Sequel ➡️"
close_btn = "Close ❌"


def shorten(description, info = 'anilist.co'):
    msg = "" 
    if len(description) > 700:
           description = description[0:500] + '....'
           msg += f"\n*Description*: _{description}_[Read More]({info})"
    else:
          msg += f"\n*Description*:_{description}_"
    return msg


#time formatter from uniborg
def t(milliseconds: int) -> str:
    """Inputs time in milliseconds, to get beautified time,
    as string"""
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = ((str(days) + " Days, ") if days else "") + \
        ((str(hours) + " Hours, ") if hours else "") + \
        ((str(minutes) + " Minutes, ") if minutes else "") + \
        ((str(seconds) + " Seconds, ") if seconds else "") + \
        ((str(milliseconds) + " ms, ") if milliseconds else "")
    return tmp[:-2]
    
airing_query = '''
    query ($id: Int,$search: String) { 
        Media (id: $id, type: ANIME,search: $search) { 
            id
            episodes
            title {
                romaji
                english
                native
            }
            nextAiringEpisode {
            airingAt
            timeUntilAiring
            episode
        } 
    }
}
'''

fav_query = """
query ($id: Int) { 
    Media (id: $id, type: ANIME) { 
        id
        title {
            romaji
            english
            native
        }
    }
}
"""

anime_query = '''
    query ($id: Int,$search: String) { 
        Media (id: $id, type: ANIME,search: $search) { 
            id
            title {
            romaji
            english
            native
        }
        description (asHtml: false)
        startDate{
            year
        }
        episodes
        season
        type
        format
        status
        duration
        siteUrl
        studios{
            nodes{
                name
            }
        }
        trailer{
            id
            site 
            thumbnail
        }  
        averageScore
        genres
        bannerImage
    }
}
'''
character_query = """
    query ($query: String) {
        Character (search: $query) {
            id
            name {
                first
                last
                full
            }
            siteUrl
            image {
                large
            }
            description
    }
}
"""

manga_query = """
query ($id: Int,$search: String) { 
    Media (id: $id, type: MANGA,search: $search) { 
        id
        title {
            romaji
            english
            native
        }
        description (asHtml: false)
        startDate{
            year
        }
        type
        format
        status
        siteUrl
        averageScore
        genres
        bannerImage
    }
}
"""


url = 'https://graphql.anilist.co'


@run_async
def anime(update: Update, context: CallbackContext):
    message = update.effective_message
    search = message.text.split(' ', 1)
    if len(search) == 1: return
    else: search = search[1]
    variables = {'search' : search}
    json = requests.post(url, json={'query': anime_query, 'variables': variables}).json()['data'].get('Media', None)
    if json:
        msg = f"*{json['title']['romaji']}*(`{json['title']['native']}`)\n*Type*: {json['format']}\n*Status*: {json['status']}\n*Episodes*: {json.get('episodes', 'N/A')}\n*Duration*: {json.get('duration', 'N/A')} Per Ep.\n*Score*: {json['averageScore']}\n*Genres*: `"
        for x in json['genres']: msg += f"{x}, "
        msg = msg[:-2] + '`\n'
        msg += "*Studios*: `"
        for x in json['studios']['nodes']: msg += f"{x['name']}, " 
        msg = msg[:-2] + '`\n'
        info = json.get('siteUrl')
        trailer = json.get('trailer', None)
        if trailer:
            trailer_id = trailer.get('id', None)
            site = trailer.get('site', None)
            if site == "youtube": trailer = 'https://youtu.be/' + trailer_id
        description = json.get('description', 'N/A').replace('<i>', '').replace('</i>', '').replace('<br>', '')
        msg += shorten(description, info) 
        image = json.get('bannerImage', None)
        if trailer:
            buttons = [
                [InlineKeyboardButton("More Info", url=info),
                InlineKeyboardButton("Trailer 🎬", url=trailer)]
                ]
        else:
            buttons = [
                [InlineKeyboardButton("More Info", url=info)]
            ]
        if image:
            try:
                update.effective_message.reply_photo(photo = image, caption = msg, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(buttons))
            except:
                msg += f" [〽️]({image})"
                update.effective_message.reply_text(msg, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(buttons))
        else: 
            update.effective_message.reply_text(msg, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(buttons))

@run_async
def character(update: Update, _):
    message = update.effective_message
    search = message.text.split(' ', 1)
    if len(search) == 1:
        update.effective_message.reply_text('Format : /character < character name >') 
        return
    search = search[1]
    variables = {'query': search}
    json = requests.post(url, json={'query': character_query, 'variables': variables}).json()['data'].get('Character', None)
    if json:
        msg = f"*{json.get('name').get('full')}*(`{json.get('name').get('native')}`)\n"
        description = f"{json['description']}"
        site_url = json.get('siteUrl')
        msg += shorten(description, site_url)
        image = json.get('image', None)
        if image:
            image = image.get('large')
            update.effective_message.reply_photo(photo = image, caption = msg, parse_mode=ParseMode.MARKDOWN)
        else: update.effective_message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

@run_async
def manga(update: Update, _):
    message = update.effective_message
    search = message.text.split(' ', 1)
    if len(search) == 1:
        update.effective_message.reply_text('Format : /manga < manga name >') 
        return
    search = search[1]
    variables = {'search': search}
    json = requests.post(url, json={'query': manga_query, 'variables': variables}).json()['data'].get('Media', None)
    msg = ''
    if json:
        title, title_native = json['title'].get('romaji', False), json['title'].get('native', False)
        start_date, status, score = json['startDate'].get('year', False), json.get('status', False), json.get('averageScore', False)
        if title:
            msg += f"*{title}*"
            if title_native:
                msg += f"(`{title_native}`)"
        if start_date: msg += f"\n*Start Date* - `{start_date}`"
        if status: msg += f"\n*Status* - `{status}`"
        if score: msg += f"\n*Score* - `{score}`"
        msg += '\n*Genres* - '
        for x in json.get('genres', []): msg += f"{x}, "
        msg = msg[:-2]
        info = json['siteUrl']
        buttons = [
                [InlineKeyboardButton("More Info", url=info)]
            ]
        image = json.get("bannerImage", False)
        msg += f"_{json.get('description', None)}_"
        if image:
            try:
                update.effective_message.reply_photo(photo = image, caption = msg, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(buttons))
            except:
                msg += f" [〽️]({image})"
                update.effective_message.reply_text(msg, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(buttons))
        else: update.effective_message.reply_text(msg, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(buttons))


@run_async
def user(update: Update, _):
    message = update.effective_message
    args = message.text.strip().split(" ", 1)

    try:
        search_query = args[1]
    except:
        if message.reply_to_message:
            search_query = message.reply_to_message.text
        else:
            update.effective_message.reply_text("Format : /user <username>")
            return

    jikan = jikanpy.jikan.Jikan()

    try:
        user = jikan.user(search_query)
    except jikanpy.APIException:
        update.effective_message.reply_text("Username not found.")
        return

    progress_message = update.effective_message.reply_text("Searching.... ")

    date_format = "%Y-%m-%d"
    if user['image_url'] is None:
        img = "https://cdn.myanimelist.net/images/questionmark_50.gif"
    else:
        img = user['image_url']

    try:
        user_birthday = datetime.datetime.fromisoformat(user['birthday'])
        user_birthday_formatted = user_birthday.strftime(date_format)
    except:
        user_birthday_formatted = "Unknown"

    user_joined_date = datetime.datetime.fromisoformat(user['joined'])
    user_joined_date_formatted = user_joined_date.strftime(date_format)

    for entity in user:
        if user[entity] is None:
            user[entity] = "Unknown"

    about = user['about'].split(" ", 60)

    try:
        about.pop(60)
    except IndexError:
        pass

    about_string = ' '.join(about)
    about_string = about_string.replace("<br>", "").strip().replace("\r\n", "\n")

    caption = ""

    caption += textwrap.dedent(f"""
    *Username*: [{user['username']}]({user['url']})
    *Gender*: `{user['gender']}`
    *Birthday*: `{user_birthday_formatted}`
    *Joined*: `{user_joined_date_formatted}`
    *Days wasted watching anime*: `{user['anime_stats']['days_watched']}`
    *Days wasted reading manga*: `{user['manga_stats']['days_read']}`
    """)

    caption += f"*About*: {about_string}"

    buttons = [
        [InlineKeyboardButton(info_btn, url=user['url'])],
        [InlineKeyboardButton(close_btn, callback_data=f"anime_close, {message.from_user.id}")]
    ]

    update.effective_message.reply_photo(photo=img, caption=caption, parse_mode=ParseMode.MARKDOWN,
                                        reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=False)
    progress_message.delete()


@run_async
def upcoming(update: Update, _):
    jikan = jikanpy.jikan.Jikan()
    upcoming = jikan.top('anime', page=1, subtype="upcoming")

    upcoming_list = [entry['title'] for entry in upcoming['top']]
    upcoming_message = ""

    for entry_num in range(len(upcoming_list)):
        if entry_num == 10:
            break
        upcoming_message += f"{entry_num + 1}. {upcoming_list[entry_num]}\n"

    update.effective_message.reply_text(upcoming_message)


def site_search(update: Update, site: str):
    message = update.effective_message
    args = message.text.strip().split(" ", 1)
    more_results = True

    try:
        search_query = args[1]
    except IndexError:
        message.reply_text("Give something to search")
        return

    if site == "kaizoku":
        search_url = f"https://animekaizoku.com/?s={search_query}"
        html_text = requests.get(search_url).text
        soup = bs4.BeautifulSoup(html_text, "html.parser")
        search_result = soup.find_all("h2", {'class': "post-title"})

        if search_result:
            result = f"<b>Search results for</b> <code>{html.escape(search_query)}</code> <b>on</b> <code>AnimeKaizoku</code>: \n"
            for entry in search_result:
                post_link = entry.a['href']
                post_name = html.escape(entry.text)
                result += f"• <a href='{post_link}'>{post_name}</a>\n"
        else:
            more_results = False
            result = f"<b>No result found for</b> <code>{html.escape(search_query)}</code> <b>on</b> <code>AnimeKaizoku</code>"

    elif site == "kayo":
        search_url = f"https://animekayo.com/?s={search_query}"
        html_text = requests.get(search_url).text
        soup = bs4.BeautifulSoup(html_text, "html.parser")
        search_result = soup.find_all("h2", {'class': "title"})

        result = f"<b>Search results for</b> <code>{html.escape(search_query)}</code> <b>on</b> <code>AnimeKayo</code>: \n"
        for entry in search_result:

            if entry.text.strip() == "Nothing Found":
                result = f"<b>No result found for</b> <code>{html.escape(search_query)}</code> <b>on</b> <code>AnimeKayo</code>"
                more_results = False
                break

            post_link = entry.a['href']
            post_name = html.escape(entry.text.strip())
            result += f"• <a href='{post_link}'>{post_name}</a>\n"

    buttons = [
        [InlineKeyboardButton("See all results", url=search_url)]
    ]

    if more_results:
        message.reply_text(result, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(buttons),
                            disable_web_page_preview=True)
    else:
        message.reply_text(result, parse_mode=ParseMode.HTML, disable_web_page_preview=True)


@run_async
def kaizoku(update: Update, _):
    site_search(update, "kaizoku")


@run_async
def kayo(update: Update, context: CallbackContext):
    site_search(update, "kayo")



ANIME_HANDLER = DisableAbleCommandHandler("anime", anime)
CHARACTER_HANDLER = DisableAbleCommandHandler("character", character)
MANGA_HANDLER = DisableAbleCommandHandler("manga", manga)
USER_HANDLER = DisableAbleCommandHandler("user", user)
UPCOMING_HANDLER = DisableAbleCommandHandler("upcoming", upcoming)
KAIZOKU_SEARCH_HANDLER = DisableAbleCommandHandler("kaizoku", kaizoku)
KAYO_SEARCH_HANDLER = DisableAbleCommandHandler("kayo", kayo)

dispatcher.add_handler(ANIME_HANDLER)
dispatcher.add_handler(CHARACTER_HANDLER)
dispatcher.add_handler(MANGA_HANDLER)
dispatcher.add_handler(USER_HANDLER)
dispatcher.add_handler(KAIZOKU_SEARCH_HANDLER)
dispatcher.add_handler(KAYO_SEARCH_HANDLER)
dispatcher.add_handler(UPCOMING_HANDLER)

__command_list__ = ["anime", "manga", "character", "user", "upcoming", "kaizoku", "kayo"]
__handlers__ = [ANIME_HANDLER, CHARACTER_HANDLER, MANGA_HANDLER, USER_HANDLER, UPCOMING_HANDLER, KAIZOKU_SEARCH_HANDLER,
                KAYO_SEARCH_HANDLER]