import logging
import datetime

import geocoder
import telegram
from peewee import *

db = SqliteDatabase('bot.db')
logger = logging.getLogger()

class BaseModel(Model):
    class Meta:
        database = db

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
    posted = DateTimeField(null=True)
    silent_mode = BooleanField(default=True)
    latitude = FloatField(null=True)
    longitude = FloatField(null=True)
    place = CharField(null=True)

    def create_keyboard(self, symbols):
        for symbol in symbols:
            InlineButton.create(symbol=symbol, post=self)
        logger.info(f'Keyboard with symbols {symbols} created to {self}')

    def vote(self, symbol, user):
        button = self.buttons.where(InlineButton.symbol == symbol).get()
        button.voters.add(user)
        logger.info(f'{user} voted {symbol} to {self}')

    def set_tg_location(self, location: telegram.Location):
        self.latitude = location.latitude
        self.longitude = location.longitude
        geo = geocoder.yandex(
            [self.latitude, self.longitude],
            method='reverse')
        self.place = geo.description or geo.address
        logger.info(f'Added location {self.location}')

    @property
    def location(self):
        return f'{self.latitude} {self.longitude}\n{self.place}'

    def __str__(self):
        return self.text

class InlineButton(BaseModel):
    symbol = CharField()
    voters = ManyToManyField(User, backref='votes')
    post = ForeignKeyField(Post, backref='buttons')

    @property
    def count(self):
        return self.voters.count()

    def __str__(self):
        return f'{self.post} | {self.symbol}'
