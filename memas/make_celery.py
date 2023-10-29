from app import create_app

# This is the necessary entry point for initiating the celery worker
flask_app = create_app()
celery_app = flask_app.extensions["celery"]
