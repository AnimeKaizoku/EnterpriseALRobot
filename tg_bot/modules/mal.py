import aiohttp

from urllib.parse import quote as urlencode
from tg_bot import tg_botbot
from tg_bot.decorator import register
from .utils.disable import disableable_dec
from .utils.message import need_args_dec, get_args_str

@register(cmds='sanime')
@disableable_dec('sanime')
async def manime(message):
   query = get_args_str(message).lower()
   headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:70.0) Gecko/20100101 Firefox/70.0"} 
   query.replace('', '%20')
   surl = f'https://api.jikan.moe/v3/search/anime?q={urlencode(query)}'
   session = aiohttp.ClientSession()
   async with session.get(surl) as resp:
     a = await resp.json()
     if 'results' in a.keys():   
        pic = f'{a["results"][0]["image_url"]}'
        info = f'{a["results"][0]["title"]}\n'
        info += f' • Airing : {a["results"][0]["airing"]}\n'
        info += f' • Type : {a["results"][0]["type"]}\n'
        info += f' • Episodes : {a["results"][0]["episodes"]}\n'
        info += f' • Score : {a["results"][0]["score"]}\n'
        info += f' • Rated : {a["results"][0]["rated"]}\n'
        info += f' • Synopsis : {a["results"][0]["synopsis"]}\n'
        mlink = f'{a["results"][0]["url"]}\n'
        link_btn = InlineKeyboardMarkup()
        link_btn.insert(InlineKeyboardButton("MyAnimeList Link", url=mlink))
        await message.reply_photo(pic, caption=info, reply_markup=link_btn)


@register(cmds='character')
@disableable_dec('character')
async def character(message):
   query = get_args_str(message).lower()
   headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:70.0) Gecko/20100101 Firefox/70.0"} 
   query.replace('', '%20')
   csurl = f'https://api.jikan.moe/v3/search/character?q={urlencode(query)}'
   session = aiohttp.ClientSession()
   async with session.get(csurl) as resp:
    a = await resp.json()
    if 'results' in a.keys():
       info = f'  • Name : {a["results"][0]["name"]}\n'
       pic = f'{a["results"][0]["image_url"]}'
       mclink = f'{a["results"][0]["url"]}\n'
       clink_btn = InlineKeyboardMarkup()
       clink_btn.insert(InlineKeyboardButton("MyAnimeList Link", url=mclink))
       await message.reply_photo(pic, caption=info, reply_markup=clink_btn)
