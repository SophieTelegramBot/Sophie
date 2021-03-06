# Copyright (C) 2018 - 2020 MrYacha. All rights reserved. Source code available under the AGPL.
# Copyright (C) 2019 Aiogram
#
# This file is part of SophieBot.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from aiogram.dispatcher.filters import BoundFilter

from src.modules.utils.language import get_strings_dec
from src.modules.utils.user_details import is_user_admin


class IsAdmin(BoundFilter):
    key = 'is_admin'

    def __init__(self, is_admin):
        self.is_admin = is_admin

    @get_strings_dec('global')
    async def check(self, event, strings):

        if hasattr(event, 'message'):
            chat_id = event.message.chat.id
        else:
            chat_id = event.chat.id

        if not await is_user_admin(chat_id, event.from_user.id):
            task = event.answer if hasattr(event, 'message') else event.reply
            await task(strings['u_not_admin'])
            return False
        return True
