# Last.fm module by @TheRealPhoenix - https://github.com/rsktg

import requests

from telegram import Bot, Update, Message, Chat, ParseMode
from telegram.ext import run_async, CommandHandler

from tg_bot import dispatcher, LASTFM_API_KEY
from tg_bot.modules.disable import DisableAbleCommandHandler

import tg_bot.modules.sql.last_fm_sql as sql


@run_async
def set_user(bot: Bot, update: Update, args):
    msg = update.effective_message
    if args:
        user = update.effective_user.id
        username = " ".join(args)
        sql.set_user(user, username)
        msg.reply_text(f"Username set as {username}!")
    else:
        msg.reply_text("That's not how this works...\nRun /setuser followed by your username!")
        

@run_async
def clear_user(bot: Bot, update: Update):
    user = update.effective_user.id
    sql.set_user(user, "")
    update.effective_message.reply_text("Last.fm username successfully cleared from my database!")
    
  
@run_async
def last_fm(bot: Bot, update: Update):
    msg = update.effective_message
    user = update.effective_user.first_name
    user_id = update.effective_user.id
    username = sql.get_user(user_id)
    if not username:
        msg.reply_text("You haven't set your username yet!")
        return
    
    base_url = "http://ws.audioscrobbler.com/2.0"
    res = requests.get(f"{base_url}?method=user.getrecenttracks&limit=3&extended=1&user={username}&api_key={LASTFM_API_KEY}&format=json")
    if not res.status_code == 200:
        msg.reply_text("Hmm... something went wrong.\nPlease ensure that you've set the correct username!")
        return
        
    try:
        first_track = res.json().get("recenttracks").get("track")[0]
    except IndexError:
        msg.reply_text("You don't seem to have scrobbled any songs...")
        return
    if first_track.get("@attr"):
        # Ensures the track is now playing
        image = first_track.get("image")[3].get("#text") # Grab URL of 300x300 image
        artist = first_track.get("artist").get("name")
        song = first_track.get("name")
        loved = int(first_track.get("loved"))
        rep = f"{user} is currently listening to:\n"
        if not loved:
            rep += f"🎧  <code>{artist} - {song}</code>"
        else:
            rep += f"🎧  <code>{artist} - {song}</code> (♥️, loved)"
        if image:
            rep += f"<a href='{image}'>\u200c</a>"
    else:
        tracks = res.json().get("recenttracks").get("track")
        track_dict = {tracks[i].get("artist").get("name"): tracks[i].get("name") for i in range(3)}
        rep = f"{user} was listening to:\n"
        for artist, song in track_dict.items():
            rep += f"🎧  <code>{artist} - {song}</code>\n"
        last_user = requests.get(f"{base_url}?method=user.getinfo&user={username}&api_key={LASTFM_API_KEY}&format=json").json().get("user")
        scrobbles = last_user.get("playcount")
        rep += f"\n(<code>{scrobbles}</code> scrobbles so far)"
        
    msg.reply_text(rep, parse_mode=ParseMode.HTML)
    
    
__help__ = """
Share what you're what listening to with the help of this module!
*Available commands:*
 - /setuser <username>: sets your last.fm username.
 - /clearuser: removes your last.fm username from the bot's database.
 - /lastfm: returns what you're scrobbling on last.fm.
"""

__mod_name__ = "Last.FM"
    

SET_USER_HANDLER = CommandHandler("setuser", set_user, pass_args=True)
CLEAR_USER_HANDLER = CommandHandler("clearuser", clear_user)
LASTFM_HANDLER = DisableAbleCommandHandler("lastfm", last_fm)

dispatcher.add_handler(SET_USER_HANDLER)
dispatcher.add_handler(CLEAR_USER_HANDLER)
dispatcher.add_handler(LASTFM_HANDLER)