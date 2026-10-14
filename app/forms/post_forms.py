from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms.validators import DataRequired, Length


class PostForm(FlaskForm):
    """Form for creating a post. Field limits mirror the columns in app/models.post.py keep them in sync"""

    title = StringField("Title", validators=[DataRequired(), Length(max=120)])
    body = TextAreaField("Body", validators=[DataRequired()])
