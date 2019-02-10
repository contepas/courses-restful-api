from flask import jsonify, Blueprint, abort, g, make_response
from flask_restful import (Resource, Api, reqparse, 
                            inputs, fields, marshal,
                            marshal_with, url_for)

from auth import auth
import models
import json

############
#### Marshal
############

course_fields = {
    'id': fields.Integer,
    'title': fields.String,
    'url': fields.String,
    'subjects': fields.String
}

#############
#### HELP_FUN
#############

def findSubjects(course):
    words = course.title.split()
    course_subjects = set()

    for subject in models.Subject.select():
        if subject.name in words:
            course_subjects.add(subject.name)

    course.subjects = ', '.join(course_subjects)

    return course

def course_or_404(course_id):
    try:
        course = models.Course.get(models.Course.id == course_id)
    except models.Course.DoesNotExist:
        abort(404)
    else:
        return course

##############
#### RESOURCES
##############

class CourseBase(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument(
            'title',
            required=True,
            help='No course title provided',
            location=['form', 'json']
        )
        self.reqparse.add_argument(
            'url',
            required=True,
            help='No course url provided',
            location=['form','json'],
            type=inputs.url
        )
        super().__init__()


class CourseList(CourseBase):

    def get(self):
        courses = [marshal(findSubjects(course), course_fields)
                    for course in models.Course.select()]
        return {'courses': courses}
    
    @marshal_with(course_fields)
    @auth.login_required
    def post(self):
        args = self.reqparse.parse_args()
        course = models.Course.create(
            accomplished_by = g.user,
            **args)
        return (findSubjects(course), 201,
                {'Location': url_for('resources.courses.course', id=course.id)})
        

class Course(CourseBase):
    @marshal_with(course_fields)
    def get(self, id):
        return course_or_404(id)
    
    @marshal_with(course_fields)
    @auth.login_required
    def put(self, id):
        args = self.reqparse.parse_args()
        try:
            course = models.Course.select().where(
                models.Course.accomplished_by == g.user,
                models.Course.id == id
            ).get()
        except models.Course.DoesNotExist:
            return make_response(json.dumps(
                {'error': 'That course does not exist or is not editable'}
            ), 403)
        query = course.update(**args)
        query.execute()
        return (findSubjects(course), 200,
                {'Location': url_for('resources.courses.course', id=id)})
    
    @auth.login_required
    def delete(self, id):
        try:
            course = models.Course.select().where(
                models.Course.accomplished_by == g.user,
                models.Course.id == id
            ).get()
        except models.Course.DoesNotExist:
            return make_response(json.dumps(
                {'error': 'That course does not exist or is not editable'}
            ), 403)
        query = course.delete()
        query.execute()
        return ('', 204, {'Location': url_for('resources.courses.courses')})

##############
#### EndPoints
##############

courses_api = Blueprint('resources.courses', __name__)
api = Api(courses_api)
api.add_resource(
    CourseList,
    '/courses',
    endpoint='courses'
)
api.add_resource(
    Course,
    '/courses/<int:id>',
    endpoint='course'
)