import logging
import datetime

import hug
from sqlalchemy.orm import aliased

from nikoniko.entities import Session
from nikoniko.entities import Person, person_schema, people_schema
from nikoniko.entities import Board, board_schema, boards_schema
from nikoniko.entities import ReportedFeeling, reportedfeeling_schema, reportedfeelings_schema

from hug_middleware_cors import CORSMiddleware

logger = logging.getLogger(__name__)
session = Session()

api = hug.API(__name__)
api.http.add_middleware(CORSMiddleware(api))


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


@hug.get('/boards')
def boards():
    '''Returns all boards'''
    res = session.query(Board).all()
    return boards_schema.dump(res).data


@hug.put('/reportedfeelings')
def create_reportedFeeling(
        board_id: hug.types.number,
        person_id: hug.types.number,
        feeling: hug.types.text,
        date: hug.types.text):
    '''Creates a new reportedFeeling'''
    try:
        reportedFeeling = session.query(ReportedFeeling).filter_by(board_id=board_id, person_id=person_id, date=date).one()
        reportedFeeling.feeling = feeling
    except:
        reportedFeeling = ReportedFeeling(person_id=person_id, board_id=board_id, date=datetime.datetime.strptime(date, "%Y-%m-%d").date(), feeling=feeling)
        session.add(reportedFeeling)
    session.commit()
    return reportedfeeling_schema.dump(reportedFeeling).data


@hug.get('/reportedfeelings/{board_id}')
def get_reportedFeeling(board_id: hug.types.number, person_id: hug.types.number, date: hug.types.text):
    '''Returns a specific reported feeling for a board, person and date'''
    res = session.query(ReportedFeeling).filter_by(board_id=board_id, person_id=person_id, date=date).one()
    return reportedfeeling_schema.dump(res).data
