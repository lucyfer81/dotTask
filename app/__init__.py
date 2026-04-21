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
        _migrate_db(db)

    # TODO: uncomment as routes are created
    from .routes import dashboard
    app.register_blueprint(dashboard.bp)
    from .routes import locations
    from .routes import tasks
    app.register_blueprint(tasks.bp)
    app.register_blueprint(locations.bp)
    from .routes import data_io
    app.register_blueprint(data_io.bp)

    return app


def _migrate_db(db):
    """Add columns that db.create_all() won't add to existing tables."""
    import sqlalchemy
    with db.engine.connect() as conn:
        # Check if task_log column exists in task_assignment
        result = conn.execute(sqlalchemy.text(
            "PRAGMA table_info(task_assignment)"
        ))
        columns = {row[1] for row in result}
        if 'task_log' not in columns:
            conn.execute(sqlalchemy.text(
                "ALTER TABLE task_assignment ADD COLUMN task_log TEXT"
            ))
            conn.commit()
