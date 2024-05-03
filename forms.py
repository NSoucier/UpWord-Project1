from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, TextAreaField, EmailField
from wtforms.validators import InputRequired, Length

class AddUserForm(FlaskForm):
    """ User signup form """
    
    username = StringField('Username', validators=[InputRequired()])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=8)])
    email = EmailField('Email', validators=[InputRequired()])
    
    
class LoginForm(FlaskForm):
    """ User login form """
    
    username = StringField('Username', validators=[InputRequired()])
    password = PasswordField('Password', validators=[InputRequired()])
    
class EditUserForm(FlaskForm):
    """ Edit user details """
    username = StringField('Username', validators=[InputRequired()])
    email = EmailField('Email', validators=[InputRequired()])
    first_name = StringField('First name', validators=[InputRequired()])
    last_name = StringField('Last name', validators=[InputRequired()])
    fav_translation = SelectField('Default translation', validators=[InputRequired()])
    
