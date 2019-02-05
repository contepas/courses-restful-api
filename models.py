import datetime

from peewee import *

DB = SqliteDatabase('courses.sqlite')

class Course(Model):
    title = CharField()
    url = CharField(unique=True)
    created_at = DateTimeField(default=datetime.datetime.now)

    class Meta:
        database = DB

def initialize():
    DB.connect()
    DB.create_tables([Course], safe=True)