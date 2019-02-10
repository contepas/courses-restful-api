import datetime
import config

from peewee import *
from argon2 import PasswordHasher
from itsdangerous import (TimedJSONWebSignatureSerializer as Serializer,
                            BadSignature, SignatureExpired)

DB = SqliteDatabase('courses.sqlite', pragmas={'foreign_keys': 1})
HASHER = PasswordHasher()


class BaseModel(Model):
    class Meta:
        database = DB


class User(BaseModel):
    username = CharField(unique = True)
    email = CharField(unique = True)
    password = CharField()

    @classmethod
    def create_user(cls, username, email, password, **kwargs):
        email = email.lower()
        try:
            cls.select().where(
                    (cls.email == email) | (cls.username ** username)
                ).get()
        except cls.DoesNotExist:
            user = cls(username = username, email = email)
            user.password = user.set_password(password)
            user.save()
            return user
        else:
            raise Exception('Username or Email already exist')

    @staticmethod
    def verity_auth_token(token):
        serializer = Serializer(config.SECRET_KEY)
        try:
            data = serializer.loads(token)
        except (SignatureExpired, BadSignature):
            return None
        else:
            user = User.get(User.id==data['id'])
            return user
    
    @staticmethod
    def set_password(password):
        return HASHER.hash(password)

    def verify_password(self, password):
        return HASHER.verify(self.password, password)

    def generate_auth_token(self, expired=3600):
        serializer = Serializer(config.SECRET_KEY)
        return serializer.dumps({'id': self.id})


class Course(BaseModel):
    title = CharField()
    url = CharField(unique=True)
    #created_at = DateTimeField(default = datetime.datetime.now())
    accomplished_by = ForeignKeyField(User, related_name='course_set')


class Subject(BaseModel):
    name = CharField(unique=True)


class CourseSubject(BaseModel):
    course = ForeignKeyField(Course, backref='subject_set')
    subject = ForeignKeyField(Subject, backref='course_set')


def initialize():
    DB.connect()
    DB.create_tables([User, Course, Subject, CourseSubject], safe=True)