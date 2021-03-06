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

import os

import sentry_sdk
from sentry_sdk.integrations.redis import RedisIntegration

from src.utils.logger import log

SENTRY_API_KEY = os.getenv('SENTRY_API_KEY', None)

if SENTRY_API_KEY:
    log.info("Starting sentry.io integraion...")

    sentry_sdk.init(
        SENTRY_API_KEY,
        integrations=[RedisIntegration()]
    )
else:
    log.warn("sentry.io API key not found! Skipping.")
