# Copyright © 2018
# Author: Robert Rakhmatullin.
# Contacts: <robertbg4@gmail.com>
# License: http://opensource.org/licenses/MIT

import logging

from telegram import ext
from telegram import KeyboardButton, ReplyKeyboardMarkup

from models import User, Message, Post, config

def set_cancel_keyboard():
    cancel_button = KeyboardButton('Отмена')
    keyboard = ReplyKeyboardMarkup(keyboard=[[cancel_button]],
                                   one_time_keyboard=True,
                                   resize_keyboard=True)
    return keyboard

def set_drafted_keyboard():
    drafted_button = KeyboardButton('/drafted')
    keyboard = ReplyKeyboardMarkup(keyboard=[[drafted_button]],
                                   one_time_keyboard=True,
                                   resize_keyboard=True)
    return keyboard

def set_edit_keyboard():
    send_button = KeyboardButton('/send')
    draft_button = KeyboardButton('/draft')
    delete_button = KeyboardButton('/delete')
    keyboard = ReplyKeyboardMarkup(keyboard=[[send_button],
                                             [draft_button, delete_button]],
                                   one_time_keyboard=True,
                                   resize_keyboard=True)
    return keyboard

def add_location(bot, update):
    post = Post.get_or_none(Post.current == True)
    if not post:
        update.message.reply_text(text='Пост не выбран. Пришли его или выбери из отложенных',
                                  reply_markup=set_drafted_keyboard())
        return
    post.set_location_from_tg(update.message.location)
    post.send(bot, update.message.chat_id, False)
    logger.info(f'location added: {post}')

def send_post(bot, update):
    post = Post.get_or_none(Post.current == True)
    if not post:
        update.message.reply_text(text='Пост не выбран. Пришли его или выбери из отложенных',
                                  reply_markup=set_drafted_keyboard())
        return
    post.send(bot, '@robert_blog', True)
    logger.info(f'post sended: {post}')
    update.message.reply_text(text='Пост отправлен',
                              reply_markup=set_drafted_keyboard())

def delete_post(bot, update):
    post = Post.get_or_none(Post.current == True)
    if not post:
        update.message.reply_text(text='Пост не выбран. Пришли его или выбери из отложенных',
                                  reply_markup=set_drafted_keyboard())
        return
    post.delete_instance()
    logger.info(f'post deleted: {post}')
    update.message.reply_text(text='Пост удален',
                              reply_markup=set_drafted_keyboard())

def draft_post(bot, update):
    query = Post.update(current=False).where(Post.current == True)
    query.execute()
    logger.info(f'posts drafted')
    update.message.reply_text(text='Пост отложен',
                              reply_markup=set_drafted_keyboard())

def get_drafted_posts(bot, update):
    query = Post.select().where(Post.message == None)
    for post in query:
        update.message.reply_text(text=post.text,
                                  reply_markup=set_cancel_keyboard())


def get_message(bot, update):
    post = Post.create(text=update.message.text)
    logger.info(f'post created: {post}')
    update.message.reply_text(text=post.text, 
                              reply_markup=set_edit_keyboard(),
                              parse_mode='Markdown')


logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO)
logger = logging.getLogger()
updater = ext.Updater(token=config['main']['TELEGRAM_BOT_TOKEN'])
dispatcher = updater.dispatcher
robert_id = 102622698

message_handler = ext.MessageHandler(ext.filters.MergedFilter(base_filter=ext.Filters.user(robert_id), and_filter=ext.Filters.text), get_message)
location_handler = ext.MessageHandler(ext.filters.MergedFilter(base_filter=ext.Filters.user(robert_id), and_filter=ext.Filters.location), add_location)
delete_command_handler = ext.CommandHandler('delete', delete_post)
send_command_handler = ext.CommandHandler('send', send_post)
draft_command_handler = ext.CommandHandler('draft', draft_post)
drafted_command_handler = ext.CommandHandler('drafted', get_drafted_posts)

dispatcher.add_handler(message_handler)
dispatcher.add_handler(location_handler)
dispatcher.add_handler(delete_command_handler)
dispatcher.add_handler(send_command_handler)
dispatcher.add_handler(draft_command_handler)
dispatcher.add_handler(drafted_command_handler)

updater.start_polling(clean=True)

updater.idle()
