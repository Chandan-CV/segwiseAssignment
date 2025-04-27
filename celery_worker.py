from app import create_app
from app.tasks import celery

# Create Flask application context
flask_app = create_app()
app_context = flask_app.app_context()
app_context.push()

# Configure Celery to work with Flask app
class FlaskTask(celery.Task):
    def __call__(self, *args, **kwargs):
        with flask_app.app_context():
            return self.run(*args, **kwargs)

celery.Task = FlaskTask