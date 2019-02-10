from flask import jsonify, Blueprint, abort
from flask_restful import (Resource, Api, reqparse, 
                            inputs, fields, marshal,
                            marshal_with, url_for)
from auth import auth
import models

############
#### Marshal
############

subject_fields = {
    'id': fields.Integer,
    'name': fields.String,
    'courses': fields.List(fields.String)
}

#############
#### HELP_FUN
#############

def findCourses(subject):
    subject.courses = [url_for('resources.courses.course', name = course.title)
                        for course in subject.course_set]
    return subject

def subject_or_404(subject_id):
    try:
        subject = models.Subject.get(models.Subject.id == subject_id)
    except models.Course.DoesNotExist:
        abort(404)
    else:
        return subject

##############
#### RESOURCES
##############

class SubjectBase(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument(
            'name',
            required=True,
            help='No subject name provided',
            location=['form', 'json']
        )
        super().__init__()

class SubjectList(SubjectBase):

    def get(self):
        subjects = [marshal(findCourses(subject), subject_fields)
                    for subject in models.Subject.select()]
        return {'subjects': subjects}
    
    @marshal_with(subject_fields)
    @auth.login_required
    def post(self):
        args = self.reqparse.parse_args()
        subject = models.Subject.create(**args)
        return (findCourses(subject), 201,
                {'Location': url_for('resources.subjects.subject', id=subject.id)})


class Subject(SubjectBase):
    @marshal_with(subject_fields)
    def get(self, id):
        return subject_or_404(id)
    
    @marshal_with(subject_fields)
    @auth.login_required
    def put(self, id):
        args = self.reqparse.parse_args()
        query = models.Subject.update(**args).where(models.Subject.id == id)
        query.execute()
        return (findCourses(models.Subject.get(models.Subject.id==id)),
                200,
                {'Location': url_for('resources.subjects.subject', id=id)})
    
    @auth.login_required
    def delete(self, id):
        query = models.Subject.delete().where(models.Subject.id == id)
        query.execute()
        return ('', 204, {'Location': url_for('resources.subjects.subjects')})


##############
#### EndPoints
##############

subjects_api = Blueprint('resources.subjects', __name__)
api = Api(subjects_api)
api.add_resource(
    SubjectList,
    '/subjects',
    endpoint='subjects'
)
api.add_resource(
    Subject,
    '/subjects/<int:id>',
    endpoint='subject'
)