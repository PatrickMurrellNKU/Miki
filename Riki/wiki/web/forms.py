"""
    Forms
    ~~~~~
"""
from flask_wtf import Form
from flask_wtf.file import FileRequired
from wtforms import BooleanField, SubmitField, FileField
from wtforms import TextField
from wtforms import TextAreaField
from wtforms import PasswordField
from wtforms.validators import InputRequired
from wtforms.validators import ValidationError

from wiki.core import clean_url
from wiki.web import current_wiki
from wiki.web import current_users


class URLForm(Form):
    url = TextField('', [InputRequired()])

    def validate_url(form, field):
        if current_wiki.exists(field.data):
            raise ValidationError('The URL "%s" exists already.' % field.data)

    def clean_url(self, url):
        return clean_url(url)


class SearchForm(Form):
    term = TextField('', [InputRequired()])
    ignore_case = BooleanField(
        description='Ignore Case',
        # FIXME: default is not correctly populated
        default=True)


class EditorForm(Form):
    title = TextField('', [InputRequired()])
    body = TextAreaField('', [InputRequired()])
    tags = TextField('')


class LoginForm(Form):
    name = TextField('', [InputRequired()])
    password = PasswordField('', [InputRequired()])

    def validate_name(form, field):
        user = current_users.get_user(field.data)
        if not user:
            raise ValidationError('This username does not exist.')

    def validate_password(form, field):
        user = current_users.get_user(form.name.data)
        if not user:
            return
        if not user.check_password(field.data):
            raise ValidationError('Username and password do not match.')

# Form used for registering accounts on the wiki
class RegisterForm(Form):
    name = TextField('', [InputRequired()])
    password = PasswordField('', [InputRequired()])
    confirmpassword = PasswordField('', [InputRequired()])

    # Check that the current user does not already exist so that we can use this username
    def validate_name(form, field):
        user = current_users.get_user(field.data)
        if user:
            raise ValidationError('This username already exists.')

    # make sure the passwords match so the user does not accidentally set the wrong password
    def validate_password(form, field):
        passwordOne = form.password.data
        passwordTwo = form.confirmpassword.data
        if passwordOne == passwordTwo:
            return
        else:
            raise ValidationError('Passwords do not match')


class UploadForm(Form):
    file = FileField('Upload File', validators=[FileRequired()])
    description = TextAreaField(validators=[InputRequired()])
    upload = SubmitField('Upload')