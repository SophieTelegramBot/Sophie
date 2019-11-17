# Copyright (C) 2019 The Raphielscape Company LLC.
# Copyright (C) 2018 - 2019 MrYacha
#
# This file is part of SophieBot.
#
# SophieBot is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# Licensed under the Raphielscape Public License, Version 1.c (the "License");
# you may not use this file except in compliance with the License.

import os
import yaml

from babel.core import Locale

from sophie_bot.utils.logger import log
from sophie_bot.services.mongo import db
from sophie_bot.services.redis import redis


LANGUAGES = {}


log.info("Loading localizations...")

for filename in os.listdir('sophie_bot/localization'):
    log.debug('Loading language file ' + filename)
    f = open('sophie_bot/localization/' + filename, "r")
    lang = yaml.load(f, Loader=yaml.CLoader)

    lang_code = lang['language_info']['code']
    lang['language_info']['babel'] = Locale(lang_code)

    LANGUAGES[lang_code] = lang

log.info("Languages loaded: {}".format(
    [l['language_info']['name'] for l in LANGUAGES.values()]))


async def get_chat_lang(chat_id):
    r = redis.get('lang_cache_{}'.format(chat_id))
    if r:
        return r
    else:
        db_lang = await db.lang.find_one({'chat_id': chat_id})
        if db_lang:
            # Rebuild lang cache
            redis.set('lang_cache_{}'.format(chat_id), db_lang['lang'])
            return db_lang['lang']
        user_lang = await db.user_list.find_one({'user_id': chat_id})
        if user_lang and user_lang['user_lang'] in LANGUAGES:
            # Add telegram language in lang cache
            redis.set('lang_cache_{}'.format(chat_id), user_lang['user_lang'])
            return user_lang['user_lang']
        else:
            return 'en'


async def change_chat_lang(chat_id, lang):
    redis.set('lang_cache_{}'.format(chat_id), lang)
    await db.lang.update_one({'chat_id': chat_id}, {"$set": {'chat_id': chat_id, 'lang': lang}}, upsert=True)


async def get_strings(chat_id, module, mas_name="STRINGS"):
    chat_lang = await get_chat_lang(chat_id)
    if chat_lang not in LANGUAGES:
        change_chat_lang(chat_id, 'en')

    data = LANGUAGES[chat_lang][mas_name][module]
    if mas_name == 'STRINGS':
        data['language_info'] = LANGUAGES[chat_lang]['language_info']
    return data


def get_strings_dec(module, mas_name="STRINGS"):
    def wrapped(func):
        async def wrapped_1(*args, **kwargs):
            message = args[0]
            if hasattr(message, 'chat'):
                chat_id = message.chat.id
            elif hasattr(message, 'message'):
                chat_id = message.message.chat.id
            else:
                chat_id = None

            str = await get_strings(chat_id, module, mas_name=mas_name)
            return await func(*args, str, **kwargs)
        return wrapped_1
    return wrapped


async def get_chat_lang_info(chat_id):
    chat_lang = await get_chat_lang(chat_id)
    return LANGUAGES[chat_lang]['language_info']
