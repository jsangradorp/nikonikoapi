import logging

import hug
from sqlalchemy.orm import aliased

from nikoniko.entities import Session
from nikoniko.entities import Person, person_schema, people_schema
from nikoniko.entities import Board, board_schema, boards_schema

logger = logging.getLogger(__name__)
session = Session()


@hug.get('/people/{id}')
def person(id: hug.types.number):
    '''Returns a person'''
    res = session.query(Person).filter_by(id=id).one()
    return person_schema.dump(res).data


@hug.get('/people')
def people():
    '''Returns all the people'''
    res = session.query(Person).all()
    return people_schema.dump(res).data


@hug.get('/boards/{id}')
def board(id: hug.types.number):
    '''Returns a board'''
    res = session.query(Board).filter_by(id=id).one()
    return board_schema.dump(res).data
