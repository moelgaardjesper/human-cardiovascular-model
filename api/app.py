"""Flask application factory."""

from flask import Flask
from flask_cors import CORS
from .routes import bp
from .live import live_bp


def create_app() -> Flask:
    app = Flask(
        __name__,
        static_folder="../frontend",
        static_url_path="",
    )
    CORS(app)
    app.register_blueprint(bp)
    app.register_blueprint(live_bp)
    return app


if __name__ == "__main__":
    # use_reloader=False: the reloader spawns a child process and may kill the
    # background LiveSimulator thread when it does its first file-stat check (~2s).
    create_app().run(debug=True, use_reloader=False, port=5000)
