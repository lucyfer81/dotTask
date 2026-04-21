import json
from datetime import datetime, timezone
from app import db


class Location(db.Model):
    __tablename__ = "location_master"

    id = db.Column(db.Integer, primary_key=True)
    location_name = db.Column(db.String(200), nullable=False)
    country = db.Column(db.String(100))
    city = db.Column(db.String(100))
    location_type = db.Column(db.String(50))
    region = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    it_manager = db.Column(db.String(200))
    primary_it_contact = db.Column(db.String(200))
    comments = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    assignments = db.relationship("TaskAssignment", backref="location", lazy="dynamic")

    def __repr__(self):
        return f"<Location {self.location_name}>"


class Task(db.Model):
    __tablename__ = "task_master"

    id = db.Column(db.Integer, primary_key=True)
    task_name = db.Column(db.String(300), nullable=False)
    task_source = db.Column(db.String(200))
    stakeholder = db.Column(db.String(200))
    task_description = db.Column(db.Text)
    scope_country = db.Column(db.String(100))
    scope_location_type = db.Column(db.String(50))
    task_owner = db.Column(db.String(200))
    execution_model = db.Column(db.String(200))
    overall_status = db.Column(db.String(50), default="Not Started")
    start_date = db.Column(db.Date)
    target_date = db.Column(db.Date)
    last_update = db.Column(db.Date)
    link_to_file = db.Column(db.Text)
    link_to_mail = db.Column(db.Text)
    task_priority = db.Column(db.String(50), default="Medium")
    comments = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    assignments = db.relationship("TaskAssignment", backref="task", lazy="dynamic",
                                  cascade="all, delete-orphan")

    @property
    def file_links(self):
        """Return parsed list of {"name": ..., "url": ...} dicts."""
        if self.link_to_file:
            try:
                return json.loads(self.link_to_file)
            except (json.JSONDecodeError, TypeError):
                return []
        return []

    @file_links.setter
    def file_links(self, value):
        self.link_to_file = json.dumps(value, ensure_ascii=False) if value else None

    @property
    def mail_links(self):
        """Return parsed list of {"name": ..., "url": ...} dicts."""
        if self.link_to_mail:
            try:
                return json.loads(self.link_to_mail)
            except (json.JSONDecodeError, TypeError):
                return []
        return []

    @mail_links.setter
    def mail_links(self, value):
        self.link_to_mail = json.dumps(value, ensure_ascii=False) if value else None

    def __repr__(self):
        return f"<Task {self.task_name}>"


class TaskAssignment(db.Model):
    __tablename__ = "task_assignment"

    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey("task_master.id"), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey("location_master.id"), nullable=False)
    it_name = db.Column(db.String(200))
    it_role = db.Column(db.String(200))
    local_responsibility = db.Column(db.String(500))
    local_status = db.Column(db.String(50), default="Pending")
    last_update = db.Column(db.Date)
    issue_blocker = db.Column(db.Text)
    comments = db.Column(db.Text)
    task_log = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        db.UniqueConstraint("task_id", "location_id", name="uq_task_location"),
    )

    def __repr__(self):
        return f"<Assignment task={self.task_id} loc={self.location_id}>"
