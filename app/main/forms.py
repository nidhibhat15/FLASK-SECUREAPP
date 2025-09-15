from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField, SelectField, StringField
from wtforms.validators import DataRequired, Optional

class EncryptForm(FlaskForm):
    recipient = SelectField('Recipient', coerce=int, validators=[Optional()])
    message = TextAreaField('Message', validators=[DataRequired()])
    submit = SubmitField('Encrypt')

class DecryptForm(FlaskForm):
    token = StringField('Token', validators=[DataRequired()])
    submit = SubmitField('Decrypt')
