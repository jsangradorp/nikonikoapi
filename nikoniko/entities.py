''' Definition of ORM objects for the Nikoniko boards API '''
import os
import logging
import re
from sqlalchemy import Column, Integer, String, Date, DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Table
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.orm import sessionmaker

from marshmallow import Schema, fields

logging.basicConfig(level=logging.DEBUG)
LOGGER = logging.getLogger(__name__)

DB_DRIVER = os.getenv('DB_DRIVER', 'postgresql')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_DBNAME = os.getenv('DB_DBNAME', 'nikoniko')
DB_USERNAME = os.getenv('DB_USERNAME', os.getenv('USER', None))
DB_PASSWORD = os.getenv('DB_PASSWORD', None)
DB_CONNSTRING = '{}://{}{}{}{}:{}/{}'.format(
    DB_DRIVER,
    DB_USERNAME if DB_USERNAME else '',
    ':{}'.format(DB_PASSWORD) if DB_PASSWORD else '',
    '@' if DB_USERNAME else '',
    DB_HOST,
    DB_PORT,
    DB_DBNAME)
# ENGINE = create_engine('sqlite:///:memory:', echo=False)
# ENGINE = create_engine(
#     'postgresql://nikoniko:awesomepassword@localhost:5432/nikoniko',
#     echo=False)
LOGGER.debug(
    'db_connstring: [%s]',
    re.sub(
        r'(:.+?):.*?@',
        r'\1:XXXXXXX@',
        DB_CONNSTRING))
ENGINE = create_engine(
    DB_CONNSTRING,
    echo=False)
BASE = declarative_base()
SESSION = sessionmaker(bind=ENGINE)


class InvalidatedToken(BASE):  # pylint: disable=too-few-public-methods
    ''' Invalidated Token entity definition '''
    __tablename__ = 'invalidatedtokens'
    token = Column(String(180), primary_key=True)
    timestamp_invalidated = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True)


class User(BASE):  # pylint: disable=too-few-public-methods
    ''' User entity definition '''
    __tablename__ = 'users'
    user_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50))
    email = Column(String(50), nullable=False, index=True, unique=True)
    password_hash = Column(String(60))
    person_id = Column(Integer, ForeignKey('people.id'))
    person = relationship('Person', back_populates='user')


class ReportedFeeling(BASE):  # pylint: disable=too-few-public-methods
    ''' Reported Feeling entity definition '''
    __tablename__ = 'reportedfeelings'
    person_id = Column(Integer, ForeignKey('people.id'), primary_key=True)
    board_id = Column(Integer, ForeignKey('boards.id'), primary_key=True)
    date = Column(Date, primary_key=True)
    feeling = Column(String(10))

    person = relationship('Person', back_populates='reported_feelings')
    board = relationship('Board', back_populates='reported_feelings')


class ReportedFeelingSchema(Schema):  # pylint: disable=too-few-public-methods
    ''' Reported Feeling schema definition '''
    person_id = fields.Int(dump_only=True)
    board_id = fields.Int(dump_only=True)
    date = fields.Date()
    feeling = fields.Str()

REPORTEDFEELING_SCHEMA = ReportedFeelingSchema()
REPORTEDFEELINGS_SCHEMA = ReportedFeelingSchema(many=True)


MEMBERSHIP = \
    Table(
        'membership',
        BASE.metadata,
        Column('person_id',
               ForeignKey('people.id'),
               primary_key=True),
        Column('board_id',
               ForeignKey('boards.id'),
               primary_key=True))


class Person(BASE):  # pylint: disable=too-few-public-methods
    ''' Person entity definition '''
    __tablename__ = 'people'
    person_id = Column(Integer, primary_key=True, autoincrement=True)
    label = Column(String(50))

    boards = relationship(
        'Board',
        secondary=MEMBERSHIP,
        back_populates='people')
    reported_feelings = relationship('ReportedFeeling')

    user = relationship('User', back_populates='person', uselist=False)


class PersonSchema(Schema):  # pylint: disable=too-few-public-methods
    ''' Person schema definition '''
    person_id = fields.Int(dump_only=True)
    label = fields.Str()

PERSON_SCHEMA = PersonSchema()
PEOPLE_SCHEMA = PersonSchema(many=True)


class PersonInBoardSchema(Schema):  # pylint: disable=too-few-public-methods
    ''' Person in board schema definition '''
    person_id = fields.Int(dump_only=True)
    label = fields.Str()
    reportedfeelings = fields.Nested(ReportedFeelingSchema, many=True)


class Board(BASE):  # pylint: disable=too-few-public-methods
    ''' Board entity definition '''
    __tablename__ = 'boards'
    board_id = Column(Integer, primary_key=True, autoincrement=True)
    label = Column(String(50))

    people = relationship(
        'Person',
        secondary=MEMBERSHIP,
        back_populates='boards')
    reported_feelings = relationship('ReportedFeeling')


class BoardSchema(Schema):  # pylint: disable=too-few-public-methods
    ''' Board schema definition '''
    board_id = fields.Int(dump_only=True)
    label = fields.Str()
    people = fields.Nested(PersonInBoardSchema, many=True)

BOARD_SCHEMA = BoardSchema()
BOARDS_SCHEMA = BoardSchema(many=True)


class BoardInListSchema(Schema):  # pylint: disable=too-few-public-methods
    ''' Board in list schema definition '''
    board_id = fields.Int(dump_only=True)
    label = fields.Str()


class UserSchema(Schema):  # pylint: disable=too-few-public-methods
    ''' User schema definition '''
    user_id = fields.Int(dump_only=True)
    name = fields.Str()
    email = fields.Str()
    person = fields.Nested(PersonSchema)
    boards = fields.Nested(BoardInListSchema, many=True)

USER_SCHEMA = UserSchema()
USERS_SCHEMA = UserSchema(many=True)


class UserProfileSchema(Schema):  # pylint: disable=too-few-public-methods
    ''' User profile schema definition '''
    user_id = fields.Int(dump_only=True)
    name = fields.Str()
    email = fields.Str()

USERPROFILE_SCHEMA = UserProfileSchema()
USERPROFILES_SCHEMA = UserProfileSchema(many=True)


BASE.metadata.create_all(ENGINE)
