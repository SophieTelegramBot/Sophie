import os

import aiohttp
from aiogram.dispatcher import Dispatcher
from aiogram.types import Message
from stfu_tg import Bold, Code, Doc, HList, KeyValue, Section, VList

from src.modules import MODULES
from src.modules.utils.covert import convert_size
from src.modules.utils.message import DISABLE_KEYWORDS, ENABLE_KEYWORDS
from src.services.mongo import db
from src.services.redis import redis
from .start import REGISTERED_OP_COMMANDS


class OPFunctions:
    async def __setup__(self, _: Dispatcher):
        self.ip.only_owner = True
        self.purgecache.only_owner = True

    @staticmethod
    async def help(message: Message, arg_raw: str = ''):
        """Shows the help of OP commands"""
        doc = Doc()
        for module_name in REGISTERED_OP_COMMANDS.keys():
            data = []
            for cmd in REGISTERED_OP_COMMANDS[module_name].items():
                help_string = cmd[1]['help']
                data.append(KeyValue(cmd[0], help_string) if help_string else Bold(cmd[0]))
            doc += Section(VList(*data), title=module_name)

        return await message.reply(doc)

    @staticmethod
    async def stats(message: Message, arg_raw: str = '') -> Message:
        """Shows current stats of the bot"""
        from src import SOPHIE_VERSION

        # Detailed stats
        if arg_raw := arg_raw.lower():
            try:
                module = next(x for x in MODULES if arg_raw in x.__name__)
            except StopIteration:
                return await message.reply(f'Module not found - {arg_raw}!')

            if not hasattr(module, '__detailed_stats__'):
                return await message.reply(f'__detailed_stats__ not found in - {arg_raw}!')

            return await message.reply(str(
                Doc(Section(*(await module.__detailed_stats__()), title=f'Detailed stats of {arg_raw}'))
            ))

        # Normal stats
        if 'fsTotalSize' in (local_db := await db.command("dbstats")):
            mongo_used = local_db['dataSize']
            mongo_free = local_db['fsTotalSize'] - local_db['fsUsedSize']
        else:
            # MongoDB Atlas mode
            mongo_used = local_db['storageSize']
            mongo_free = 536870912 - local_db['storageSize']

        data = [
            Section(
                KeyValue("Version", SOPHIE_VERSION),
                KeyValue("Run mode",
                         f"Webhooks ({os.getenv('WEBHOOKS_PORT')})" if os.getenv('WEBHOOKS') else 'Polling'),
                KeyValue("Loaded modules", Code(len(MODULES))),
                title="General"
            ), Section(
                KeyValue('MongoDB size', f"{convert_size(mongo_used)} / {convert_size(mongo_free)}"),
                KeyValue('Redis keys', Code(len(redis.keys()))),
                title="Database"
            )
        ]

        usage_count = []
        for module in [m for m in MODULES if hasattr(m, '__usage_count__')]:
            usage_data = await module.__usage_count__()
            usage_count.extend(usage_data) if type(usage_data) is list else usage_count.append(usage_data)

        data.append(Section(
            *usage_count,
            title="Usage count"
        ))

        # Appends __stats__ to the end
        for module in [m for m in MODULES if hasattr(m, '__stats__')]:
            data.append(await module.__stats__())

        # TODO: WTF
        str(data[2])

        doc = Doc(
            Section(*data, title="Stats"),
            Section(
                HList(*[x.__name__.split('.')[2] for x in MODULES if hasattr(x, '__detailed_stats__')]),
                title='Detailed stats available for modules')
        )

        return await message.reply(str(doc))

    @staticmethod
    async def purgecache(message: Message) -> Message:
        """Purges reds cache (potentially danger)"""
        redis.flushdb()
        return await message.reply("Redis cache was cleaned.")

    @staticmethod
    async def ip(message: Message) -> Message:
        """Shows public ip"""
        async with aiohttp.ClientSession() as session:
            async with session.get("https://ipinfo.io/ip") as resp:
                await message.reply(Code(await resp.text()))

    @staticmethod
    async def mmode(message: Message, arg_raw: str = '') -> Message:
        if not arg_raw:
            # Status
            return await message.reply(f"maintenance mode is {'on' if redis.get('mmode') else 'off'}")

        if arg_raw in ENABLE_KEYWORDS:
            redis.set('mmode', 1, keepttl=7200)
            return await message.reply(f"maintenance mode is now enabled for 2 hours")
        elif arg_raw in DISABLE_KEYWORDS:
            redis.delete('mmode')
            return await message.reply(f"maintenance mode is now disabled!")
