# Copyright © 2018
# Author: Robert Rakhmatullin.
# Contacts: <robertbg4@gmail.com>
# License: http://opensource.org/licenses/MIT

import os
import logging

from telegram import ext
from telegram import KeyboardButton, ReplyKeyboardMarkup

from models import User, Message, Post


def set_cancel_keyboard():
    cancel_button = KeyboardButton('Отмена')
    keyboard = ReplyKeyboardMarkup(keyboard=[[cancel_button]],
                                   one_time_keyboard=True,
                                   resize_keyboard=True)
    return keyboard

def set_drafted_keyboard():
    drafted_button = KeyboardButton('Отложенные посты')
    keyboard = ReplyKeyboardMarkup(keyboard=[[drafted_button]],
                                   one_time_keyboard=True,
                                   resize_keyboard=True)
    return keyboard

def set_edit_keyboard():
    send_button = KeyboardButton('/send')
    draft_button = KeyboardButton('/cancel')
    delete_button = KeyboardButton('/delete')
    keyboard = ReplyKeyboardMarkup(keyboard=[[send_button],
                                             [draft_button, delete_button]],
                                   one_time_keyboard=True,
                                   resize_keyboard=True)
    return keyboard

def add_location(bot, update):
    post = Post.get_or_none(Post.current == True)
    if not post:
        update.message.reply_text(text='Пост не выбран. Пришли его или выбери из отложенных', reply_markup=set_drafted_keyboard())
        return
    post.set_location_from_tg(update.message.location)
    post.send(bot, update.chat_id, False)

def send_post(bot, update):
    post = Post.get_or_none(Post.current == True)
    if not post:
        update.message.reply_text(text='Пост не выбран. Пришли его или выбери из отложенных', reply_markup=set_drafted_keyboard())
        return
    post.send(bot, '@robert_blog', True)

def delete_post(bot, update):
    post = Post.get_or_none(Post.current == True)
    if not post:
        update.message.reply_text(text='Пост не выбран. Пришли его или выбери из отложенных', reply_markup=set_drafted_keyboard())
        return
    post.delete_instance()

def draft_post(bot, update):
    post = Post.get_or_none(Post.current == True)
    if not post:
        return
    post.current = False
    #TODO rewrite to atomic update
    post.save()

def get_drafted_posts(bot, update):
    query = Post.select().where(Post.message == None)
    update.message.reply_text(text=query, reply_markup=set_cancel_keyboard())


def get_message(bot, update):
    post = Post.create(text=update.message.text)
    logger.info(f'post created: {post}')
    update.message.reply_text(text=post.text, reply_markup=set_edit_keyboard())


logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO)
logger = logging.getLogger()
updater = ext.Updater(token=os.getenv('TELEGRAM_BOT_TOKEN'))
dispatcher = updater.dispatcher
robert_id = 102622698

message_handler = ext.MessageHandler(ext.MergedFilter(base_filter=ext.Filters.user(robert_id), and_filter=ext.Filters.text), get_message)
location_handler = ext.MessageHandler(ext.MergedFilter(base_filter=ext.Filters.user(robert_id), and_filter=ext.Filters.location), add_location)
delete_command_handler = CommandHandler('delete', delete_post)
send_command_handler = CommandHandler('send', send_post)
draft_command_handler = CommandHandler('draft', draft_post)

dispatcher.add_handler(message_handler)
dispatcher.add_handler(location_handler)
dispatcher.add_handler(delete_command_handler)
dispatcher.add_handler(send_command_handler)
dispatcher.add_handler(draft_command_handler)

updater.start_polling(clean=True)

updater.idle()
