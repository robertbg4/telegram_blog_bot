# Copyright © 2018
# Author: Robert Rakhmatullin.
# Contacts: <robertbg4@gmail.com>
# License: http://opensource.org/licenses/MIT

import os
import logging

from telegram import ext

from models import User, Message


def get_message(bot, update):
    print(update)
    print()
    user = User.get_from_tg(update.message.from_user)
    message = Message.get_from_tg(update.message)
    print(user)

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO)
logger = logging.getLogger()
updater = ext.Updater(token=os.getenv('TELEGRAM_BOT_TOKEN'))
dispatcher = updater.dispatcher

message_handler = ext.MessageHandler(ext.Filters.text, get_message)
dispatcher.add_handler(message_handler)

updater.start_polling(clean=True)

updater.idle()
