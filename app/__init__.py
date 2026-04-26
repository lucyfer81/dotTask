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

        # Add it_contacts JSON column to location_master
        result = conn.execute(sqlalchemy.text(
            "PRAGMA table_info(location_master)"
        ))
        loc_columns = {row[1] for row in result}
        if 'it_contacts' not in loc_columns:
            conn.execute(sqlalchemy.text(
                "ALTER TABLE location_master ADD COLUMN it_contacts TEXT"
            ))
            conn.commit()

        # Migrate data: it_contact table → location_master.it_contacts JSON
        import json
        result = conn.execute(sqlalchemy.text(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='it_contact'"
        ))
        if result.fetchone():
            rows = conn.execute(sqlalchemy.text(
                "SELECT location_id, name, role, email, phone FROM it_contact ORDER BY id"
            )).fetchall()
            from collections import defaultdict
            grouped = defaultdict(list)
            for r in rows:
                grouped[r[0]].append({
                    "name": r[1] or "", "role": r[2] or "",
                    "email": r[3] or "", "phone": r[4] or "",
                })
            for lid, contacts in grouped.items():
                conn.execute(sqlalchemy.text(
                    "UPDATE location_master SET it_contacts = :json WHERE id = :lid"
                ), {"json": json.dumps(contacts, ensure_ascii=False), "lid": lid})
            conn.commit()

        # Migrate data: legacy it_manager / primary_it_contact → it_contacts JSON
        result = conn.execute(sqlalchemy.text(
            "PRAGMA table_info(location_master)"
        ))
        loc_columns = {row[1] for row in result}
        if 'it_manager' in loc_columns:
            rows = conn.execute(sqlalchemy.text(
                "SELECT id, it_manager, primary_it_contact, it_contacts FROM location_master"
            )).fetchall()
            for r in rows:
                existing = json.loads(r[3]) if r[3] else []
                if existing:
                    continue
                contacts = []
                if r[1]:
                    contacts.append({"name": r[1], "role": "IT Manager", "email": "", "phone": ""})
                if r[2]:
                    contacts.append({"name": r[2], "role": "IT Coordinator", "email": "", "phone": ""})
                if contacts:
                    conn.execute(sqlalchemy.text(
                        "UPDATE location_master SET it_contacts = :json WHERE id = :lid"
                    ), {"json": json.dumps(contacts, ensure_ascii=False), "lid": r[0]})
            conn.commit()
