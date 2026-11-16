from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(16), nullable=False)
    active = db.Column(db.Boolean, default=True, nullable=False)

    def set_password(self, p):
        self.password_hash = generate_password_hash(p, method="pbkdf2:sha256")

    def check_password(self, p):
        return check_password_hash(self.password_hash, p)

    @property
    def is_active(self):
        return self.active


class Category(db.Model):
    __tablename__ = "categories"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)


class Ticket(db.Model):
    __tablename__ = "tickets"
    id = db.Column(db.Integer, primary_key=True)
    source_id = db.Column(db.Integer, unique=True, nullable=False)
    date = db.Column(db.Date, nullable=False)
    room = db.Column(db.String(16), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)
    subject = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(16), nullable=False, default="Новая")
    executor_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    service_down = db.Column(db.Boolean, nullable=False, default=False)
    affected_count = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    category = db.relationship("Category")
    executor = db.relationship("User")

    @property
    def priority(self):
        if self.service_down and self.affected_count >= 5:
            return "Критический"
        if self.service_down or self.affected_count >= 5:
            return "Высокий"
        return "Обычный"

    @property
    def priority_reason(self):
        if self.service_down and self.affected_count >= 5:
            return "Сервис недоступен и затронуто 5+ пользователей"
        if self.service_down:
            return "Сервис недоступен"
        if self.affected_count >= 5:
            return "Затронуто 5+ пользователей"
        return "Стандартный случай"


class StatusHistory(db.Model):
    __tablename__ = "status_history"
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey("tickets.id"), nullable=False)
    old_status = db.Column(db.String(16))
    new_status = db.Column(db.String(16), nullable=False)
    changed_at = db.Column(db.DateTime, default=datetime.utcnow)
    changed_by = db.Column(db.Integer, db.ForeignKey("users.id"))

    user = db.relationship("User")


ALLOWED_TRANSITIONS = {
    ("Новая", "В работе"),
    ("В работе", "Закрыта"),
}