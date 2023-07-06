from flask import Flask
from memas.context_manager import ctx
import memas.dataplane as dp
import memas.controlplane as cp

app: Flask = Flask(__name__)


@app.route('/hello')
def hello_world():
    return "Hello World"


if __name__ == "__main__":
    ctx.init()
    cp.init_app(app)
    dp.init_app(app)

    app.run(host='127.0.0.1', port=8000, debug=True)
