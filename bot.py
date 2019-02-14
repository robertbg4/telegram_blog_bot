# Copyright © 2018
# Author: Robert Rakhmatullin.
# Contacts: <robertbg4@gmail.com>
# License: http://opensource.org/licenses/MIT

import logging

from telegram import ext
from telegram import KeyboardButton, ReplyKeyboardMarkup

from models import User, Message, Post, InlineButton, config

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
        error_text = 'Пост не выбран. Пришли его или выбери из отложенных'
        update.message.reply_text(text=error_text,
                                  reply_markup=set_drafted_keyboard())
        return
    post.set_location_from_tg(update.message.location)
    post.send(bot, update.message.chat_id, False)
    logger.info(f'location added: {post}')

def send_post(bot, update):
    post = Post.get_or_none(Post.current == True)
    if not post:
        error_text = 'Пост не выбран. Пришли его или выбери из отложенных'
        update.message.reply_text(text=error_text,
                                  reply_markup=set_drafted_keyboard())
        return
    post.send(bot, blog_id, True)
    logger.info(f'post sended: {post}')
    update.message.reply_text(text='Пост отправлен',
                              reply_markup=set_drafted_keyboard())

def delete_post(bot, update):
    post = Post.get_or_none(Post.current == True)
    if not post:
        error_text = 'Пост не выбран. Пришли его или выбери из отложенных'
        update.message.reply_text(text=error_text,
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
    post = Post.get_or_none(Post.current == True)
    if post:
        post.create_keyboard(update.message.text)
        post.send(bot, update.message.chat_id, False)
        update.message.reply_text(text=None, reply_markup=set_edit_keyboard())
        return
    post = Post.create(text=update.message.text)
    logger.info(f'post created: {post}')
    post.send(bot, update.message.chat_id, False)
    update.message.reply_text(text=None, reply_markup=set_edit_keyboard())

def get_reaction(bot, update):
    callback = update.callback_query
    message_id = callback.message.message_id

    message = Message.get_or_none(Message.message_id == message_id)
    post = message.posts.first()
    button = post.buttons.where(InlineButton.id == callback.data).get()

    result = button.vote(User.get_from_tg(callback.from_user))

    callback.answer(text=f'You {result} {button.symbol}')
    callback.edit_message_reply_markup(reply_markup=post.keyboard)


logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO)
logger = logging.getLogger()
updater = ext.Updater(token=config['main']['TELEGRAM_BOT_TOKEN'])
dispatcher = updater.dispatcher
admin_id = int(config['main']['ADMIN_ID'])
if not admin_id:
    raise ValueError("Couldn't load without admin id")
blog_id = config['main']['BLOG_ID']
if not blog_id:
    raise ValueError("Couldn't load without blog id")

message_handler = ext.MessageHandler(ext.filters.MergedFilter(base_filter=ext.Filters.user(admin_id), and_filter=ext.Filters.text), get_message)
location_handler = ext.MessageHandler(ext.filters.MergedFilter(base_filter=ext.Filters.user(admin_id), and_filter=ext.Filters.location), add_location)
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

callback_handler = ext.CallbackQueryHandler(get_reaction)
dispatcher.add_handler(callback_handler)

updater.start_polling(clean=True)

updater.idle()
