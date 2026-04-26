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
        import os
        db_path = app.config["SQLALCHEMY_DATABASE_URI"]
        db_dir = os.path.dirname(db_path.replace("sqlite:///", ""))
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
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
    from .routes import workbench
    app.register_blueprint(workbench.bp)

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

        # Check if comments column exists in location_master
        result = conn.execute(sqlalchemy.text(
            "PRAGMA table_info(location_master)"
        ))
        loc_columns = {row[1] for row in result}
        if 'comments' not in loc_columns:
            conn.execute(sqlalchemy.text(
                "ALTER TABLE location_master ADD COLUMN comments TEXT"
            ))
            conn.commit()

        # Migrate it_manager / primary_it_contact → it_contact rows
        result = conn.execute(sqlalchemy.text(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='it_contact'"
        ))
        if result.fetchone():
            from app.models import Location, ItContact
            locations = Location.query.all()
            for loc in locations:
                existing = ItContact.query.filter_by(location_id=loc.id).count()
                if existing > 0:
                    continue
                if loc.it_manager:
                    conn.execute(sqlalchemy.text(
                        "INSERT INTO it_contact (location_id, name, role) VALUES (:lid, :name, :role)"
                    ), {"lid": loc.id, "name": loc.it_manager, "role": "IT Manager"})
                if loc.primary_it_contact:
                    conn.execute(sqlalchemy.text(
                        "INSERT INTO it_contact (location_id, name, role) VALUES (:lid, :name, :role)"
                    ), {"lid": loc.id, "name": loc.primary_it_contact, "role": "IT Coordinator"})
            conn.commit()
