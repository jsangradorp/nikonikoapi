from sqlalchemy import Column, Integer, String, Date, Sequence
from sqlalchemy import ForeignKey
from sqlalchemy import Table
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.orm import sessionmaker

from marshmallow import Schema, fields

engine = create_engine('sqlite:///:memory:', echo=True)
Base = declarative_base()
Session = sessionmaker(bind=engine)

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

    def __repr__(self):
        return "<Person(label='%s')>" % (self.label)


class PersonSchema(Schema):
    id = fields.Int(dump_only=True)
    label = fields.Str()

person_schema = PersonSchema()
people_schema = PersonSchema(many=True)


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

Base.metadata.create_all(engine)
