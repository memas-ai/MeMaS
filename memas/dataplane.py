from flask import Flask, Blueprint

dataplane = Blueprint("dp", __name__, url_prefix="/dp")


@dataplane.route('/recall', methods=["GET"])
def recall():
    return "World Hello"


@dataplane.route('/remember', methods=["POST"])
def remember():
    return "World Hello"
