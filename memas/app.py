import sys
import traceback
import yaml
from celery import Celery, Task
from flask import Flask
from memas.context_manager import read_env, ContextManager
from memas.interface.exceptions import MemasException


def celery_init_app(app: Flask) -> Celery:
    class FlaskTask(Task):
        def __call__(self, *args: object, **kwargs: object) -> object:
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(app.name, task_cls=FlaskTask)
    celery_app.config_from_object(app.config["CELERY"])
    celery_app.set_default()
    app.extensions["celery"] = celery_app
    return celery_app


def create_app(*, config_filename=None, first_init=False):
    app = Flask(__name__)

    if config_filename is None:
        config_filename = read_env("MEMAS_CONF_FILE")
    app.config.from_file(config_filename, load=yaml.safe_load)
    app.ctx: ContextManager = ContextManager(app.config)
    if first_init:
        app.ctx.first_init()
        app.logger.info("Finished first time initialization")
        sys.exit(0)

    app.ctx.init()

    @app.errorhandler(MemasException)
    def handle_memas_exception(e: MemasException):
        app.logger.info(f"{e.__class__.__name__}: {e.return_obj()}")
        # app.logger.info(traceback.format_exc())
        return e.return_obj(), e.status_code.value

    celery_init_app(app)

    from memas.dataplane import dataplane
    from memas.controlplane import controlplane
    app.register_blueprint(dataplane)
    app.register_blueprint(controlplane)

    app.logger.info("Finished initialization")

    return app
