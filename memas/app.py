import traceback
import yaml
from flask import Flask
from memas.context_manager import ContextManager
from memas.interface.exceptions import MemasException


def create_app(config_filename, *, first_init=False):
    app = Flask(__name__)

    app.config.from_file(config_filename, load=yaml.safe_load)
    app.ctx: ContextManager = ContextManager(app.config)
    if first_init:
        app.ctx.first_init()
        app.logger.info("Finished first time initialization")
        exit(0)

    app.ctx.init()

    @app.errorhandler(MemasException)
    def handle_memas_exception(e: MemasException):
        app.logger.info(f"{e.__class__.__name__}: {e.return_obj()}")
        # app.logger.info(traceback.format_exc())
        return e.return_obj(), e.status_code.value

    from memas.dataplane import dataplane
    from memas.controlplane import controlplane
    app.register_blueprint(dataplane)
    app.register_blueprint(controlplane)

    app.logger.info("Finished initialization")

    return app
