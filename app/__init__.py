from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config

db = SQLAlchemy()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    with app.app_context():
        from . import models
        db.create_all()

    # TODO: uncomment as routes are created
    from .routes import locations
    # from .routes import dashboard, tasks, data_io
    # app.register_blueprint(dashboard.bp)
    # app.register_blueprint(tasks.bp)
    app.register_blueprint(locations.bp)
    # app.register_blueprint(data_io.bp)

    return app
