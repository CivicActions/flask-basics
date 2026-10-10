from flask_wtf import FlaskForm


class LogoutForm(FlaskForm):
    """Field-less form whose only job is carrying a CSRF token, so logout can
    be a POST that another site can't trigger on a user's behalf."""
