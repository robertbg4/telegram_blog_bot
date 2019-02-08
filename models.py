import logging
import datetime

import geocoder
import telegram
import configparser
from peewee import *

config = configparser.RawConfigParser()
config.read('config.ini')

db = SqliteDatabase(config['main']['DATABASE_PATH'])
logger = logging.getLogger()

class BaseModel(Model):
    class Meta:
        database = db

def create_tables():
    db.create_tables(BaseModel.__subclasses__())

class User(BaseModel):
    telegram_id = IntegerField(primary_key=True)
    first_name = CharField(null=True)
    last_name = CharField(null=True)
    username = CharField(null=True)
    is_bot = BooleanField()
    is_superuser = BooleanField(default=False)
    created = DateTimeField(default=datetime.datetime.now())

    @staticmethod
    def get_from_tg(tg_user: telegram.User):
        user, created = User.get_or_create(telegram_id=tg_user.id,
                                           first_name=tg_user.first_name,
                                           last_name=tg_user.last_name,
                                           username=tg_user.username,
                                           is_bot=tg_user.is_bot)
        if created:
            logger.info(f'{user} id: {user.id} created')
        return user

    def __str__(self):
        return f'{self.username}|{self.first_name} {self.last_name}'

class Message(BaseModel):
    message_id = IntegerField(primary_key=True)
    text = TextField(null=True)
    date = DateTimeField()
    chat_id = IntegerField()

    @staticmethod
    def get_from_tg(tg_message: telegram.Message):
        message, created = Message.get_or_create(
            message_id=tg_message.message_id,
            text=tg_message.text,
            date=tg_message.date,
            chat_id=tg_message.chat.id)
        if created:
            logger.info(f'{message} id: {message.id} created')
        return message

    def __str__(self):
        return f'{self.chat_id} | {self.text}'

class Post(BaseModel):
    text = TextField(null=True)
    created = DateTimeField(default=datetime.datetime.now())
    message = ForeignKeyField(Message, backref='posts', null=True)
    silent_mode = BooleanField(default=True)
    latitude = FloatField(null=True)
    longitude = FloatField(null=True)
    place = CharField(null=True)
    #TODO: only one post can be current
    current = BooleanField(default=True)

    def create_keyboard(self, symbols):
        InlineButton.delete().where(
            InlineButton.id.in_(self.buttons)).execute()
        for symbol in symbols:
            self.add_button(symbol)
        logger.info(f'Keyboard with symbols {symbols} created to {self}')

    def add_button(self, symbol):
        InlineButton.create(symbol=symbol, post=self)
        logger.info(f'Button {symbol} added to {self}')

    def vote(self, symbol, user):
        button = self.buttons.where(InlineButton.symbol == symbol).get()
        button.voters.add(user)
        logger.info(f'{user} voted {symbol} to {self}')

    def set_location_from_tg(self, location: telegram.Location):
        self.latitude = location.latitude
        self.longitude = location.longitude
        geo = geocoder.yandex(
            [self.latitude, self.longitude],
            method='reverse')
        self.place = geo.description or geo.address
        logger.info(f'Added location {self.place}')

    @property
    def location(self):
        return f'{self.latitude} {self.longitude}\n{self.place}'

    @property
    def keyboard(self):
        if not self.buttons.count():
            return None
        tg_buttons = [telegram.InlineKeyboardButton(
            text=button.symbol,
            callback_data=button.id) for button in self.buttons]
        # TODO: split list to matrix
        return telegram.InlineKeyboardMarkup(inline_keyboard=[tg_buttons])

    def send(self, bot, chat_id, posted):
        text = self.text
        if self.latitude and self.longitude:
            text += f'\n\n{self.latitude} {self.longitude}'
        if self.place:
            text += f'\n{self.place}'
        # TODO: don't send if this post already posted
        message = bot.send_message(chat_id=chat_id,
                                   text=text,
                                   parse_mode='Markdown',
                                   disable_notification=self.silent_mode,
                                   reply_markup=self.keyboard)
        if posted:
            self.message = message
            query = Post.update(current=False).where(Post.current == True)
            query.execute()

    def __str__(self):
        return self.text

class InlineButton(BaseModel):
    '''
        Model for reactions under post
    '''
    symbol = CharField(max_length=10)
    voters = ManyToManyField(User, backref='votes')
    post = ForeignKeyField(Post, backref='buttons')

    @property
    def count(self):
        return self.voters.count()

    def __str__(self):
        return f'{self.post} | {self.symbol}'
