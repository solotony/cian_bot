from datetime import date, timedelta
from typing import Tuple

from flask_login import UserMixin
from sqlalchemy.inspection import inspect

from .common import db


class Serializer(object):
    """
    Inherit from this class allows Alchemy Models to be serializable.
    """

    include: Tuple[str] = ()

    def serialize(self) -> dict:
        """
        Serialize particular fields if include is set or
        All fields of a target instance.
        """

        attributes = self.include or inspect(self).attrs.keys()
        return {c: getattr(self, c) for c in attributes}

    @staticmethod
    def serialize_list(lst: list) -> list:
        return [m.serialize() for m in lst]


class BaseModel(db.Model, Serializer):

    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)
    created_on = db.Column(db.DateTime, default=db.func.now())
    updated_on = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())

    def serialize(self) -> dict:
        return Serializer.serialize(self)


class User(UserMixin, BaseModel):

    __tablename__ = 'users'

    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))

    include = ('id', 'username', 'created_on')


class BotSettings(BaseModel):

    __tablename__ = 'settings'

    day_money_limit = db.Column(db.Integer(), default=0)
    money_left = db.Column(db.Integer(), default=0)
    next_update_date = db.Column(db.Date, default=date.today() + timedelta(days=1))

    include = ('day_money_limit', 'money_left')


class Lead(BaseModel):

    # lead unique url stored as integer to id field

    __tablename__ = 'leads'

    include = ('id', 'created_on')
