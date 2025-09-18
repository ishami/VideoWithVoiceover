from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from sqlalchemy import text
from werkzeug.security import generate_password_hash, check_password_hash
import json

db = SQLAlchemy()

# Free‐tier project limit
FREE_TIER_LIMIT = 3

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id             = db.Column(db.Integer, primary_key=True)
    email          = db.Column(db.String(120), unique=True, nullable=False)
    password_hash  = db.Column(db.String(200), nullable=False)
    created_at     = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Premium flag, never NULL
    is_premium     = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
        server_default=text('FALSE')
    )

    # Project limit, never NULL, defaults to FREE_TIER_LIMIT
    projects_limit = db.Column(
        db.Integer,
        nullable=False,
        default=FREE_TIER_LIMIT,
        server_default=text(str(FREE_TIER_LIMIT))
    )

    # ---- Helper methods for password management ----
    def set_password(self, password: str) -> None:
        """Hash and set the user's password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verify a plain password against the stored hash."""
        return check_password_hash(self.password_hash, password)


class Project(db.Model):
    __tablename__ = 'projects'

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title      = db.Column(db.String(200))
    script     = db.Column(db.Text)
    keywords   = db.Column(db.Text)
    voice      = db.Column(db.String(100))
    manifest   = db.Column(db.Text)  # stored as JSON string
    status     = db.Column(db.String(50), default='draft', nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    def get_manifest(self):
        return json.loads(self.manifest) if self.manifest else {}

    def set_manifest(self, data):
        self.manifest = json.dumps(data)
