"""Flask application factory."""

from flask import Flask
from flask_cors import CORS
from .routes import bp


def create_app() -> Flask:
    app = Flask(
        __name__,
        static_folder="../frontend",
        static_url_path="",
    )
    CORS(app)
    app.register_blueprint(bp)
    return app


if __name__ == "__main__":
    create_app().run(debug=True, port=5000)
