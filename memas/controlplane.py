from flask import Flask, Blueprint
from memas.context_manager import ctx

controlplane = Blueprint("cp", __name__, url_prefix="/cp")


@controlplane.route('/create_user', methods=["POST"])
def create_user():
    return ""


@controlplane.route('/create_corpus', methods=["POST"])
def create_corpus():
    ctx.memas_metadata.create_knowledge_corpus()


def init_app(app: Flask):
    app.register_blueprint(controlplane)
