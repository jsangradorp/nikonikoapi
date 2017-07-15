from sqlalchemy import Column, Integer, String, Date, Sequence
from sqlalchemy import ForeignKey
from sqlalchemy import Table
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.orm import sessionmaker

from marshmallow import Schema, fields

# engine = create_engine('sqlite:///:memory:', echo=False)
engine = create_engine('postgresql://nikoniko:awesomepassword@localhost/nikoniko', echo=False)
Base = declarative_base()
Session = sessionmaker(bind=engine)


class User(Base):
    __tablename__ = 'users'
    user_id = Column(Integer, Sequence('user_id_seq'), primary_key=True)
    name = Column(String(50))
    email = Column(String(50), nullable=False, index=True, unique=True)
    password_hash = Column(String(50))
    person_id = Column(Integer, ForeignKey('people.id'))
    person = relationship('Person', back_populates='user')

    def __repr__(self):
        return "<User(name='%s',email='%s',person_id=%d>)" % (self.name, self.email, self.person_id)


membership = \
    Table(
        'membership',
        Base.metadata,
        Column('person_id',
               ForeignKey('people.id'),
               primary_key=True),
        Column('board_id',
               ForeignKey('boards.id'),
               primary_key=True))


class Person(Base):
    __tablename__ = 'people'
    id = Column(Integer, Sequence('person_id_seq'), primary_key=True)
    label = Column(String(50))

    boards = relationship('Board', secondary=membership, back_populates='people')
    reported_feelings = relationship('ReportedFeeling')

    user = relationship('User', back_populates='person', uselist=False)

    def __repr__(self):
        return "<Person(label='%s')>" % (self.label)


class PersonSchema(Schema):
    id = fields.Int(dump_only=True)
    label = fields.Str()

person_schema = PersonSchema()
people_schema = PersonSchema(many=True)


class UserSchema(Schema):
    user_id = fields.Int(dump_only=True)
    name = fields.Str()
    email = fields.Str()
    person = fields.Nested(PersonSchema)

user_schema = UserSchema()
users_schema = UserSchema(many=True)


class Board(Base):
    __tablename__ = 'boards'
    id = Column(Integer, Sequence('board_id_seq'), primary_key=True)
    label = Column(String(50))

    people = relationship('Person', secondary=membership, back_populates='boards')
    reported_feelings = relationship('ReportedFeeling')

    def __repr__(self):
        return "<Board(label='%s')>" % (self.label)


class BoardSchema(Schema):
    id = fields.Int(dump_only=True)
    label = fields.Str()
    people = fields.Nested(PersonSchema, many=True)

board_schema = BoardSchema()
boards_schema = BoardSchema(many=True)


class ReportedFeeling(Base):
    __tablename__ = 'reportedfeelings'
    person_id = Column(Integer, ForeignKey('people.id'), primary_key=True)
    board_id = Column(Integer, ForeignKey('boards.id'), primary_key=True)
    date = Column(Date, primary_key=True)
    feeling = Column(String(10))

    person = relationship('Person', back_populates='reported_feelings')
    board = relationship('Board', back_populates='reported_feelings')

    def __repr__(self):
        return "<ReportedFeeling(person_id='%s', board_id='%s', date='%s', feeling='%s')>" % (
            self.label,
            self.board_id,
            self.date,
            self.feeling)


class ReportedFeelingSchema(Schema):
    person_id = fields.Int(dump_only=True)
    board_id = fields.Int(dump_only=True)
    date = fields.Date()
    feeling = fields.Str()

reportedfeeling_schema = ReportedFeelingSchema()
reportedfeelings_schema = ReportedFeelingSchema(many=True)

Base.metadata.create_all(engine)
