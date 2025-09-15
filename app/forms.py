from flask_wtf import FlaskForm
from wtforms import SelectField, TextAreaField, BooleanField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Optional
from flask_wtf.file import FileField, FileRequired

class ComposeForm(FlaskForm):
    recipient = SelectField('Recipient', coerce=int, validators=[DataRequired()])
    message = TextAreaField('Message', validators=[DataRequired()])
    one_time = BooleanField('One-time read')
    ttl = IntegerField('Expires after (seconds)', validators=[Optional()])
    submit = SubmitField('Send')

class UploadForm(FlaskForm):
    file = FileField('File', validators=[FileRequired()])
    submit = SubmitField('Upload')
