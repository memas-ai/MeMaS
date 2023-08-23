import yaml
from flask import Flask
from memas.context_manager import ContextManager


def create_app(config_filename, *, first_init=False):
    app = Flask(__name__)

    app.config.from_file(config_filename, load=yaml.safe_load)
    app.ctx: ContextManager = ContextManager(app.config)
    if first_init:
        app.ctx.first_init()
        exit(0)

    app.ctx.init()

    from memas.dataplane import dataplane
    from memas.controlplane import controlplane
    app.register_blueprint(dataplane)
    app.register_blueprint(controlplane)

    app.logger.info("Finished initialization")

    return app
