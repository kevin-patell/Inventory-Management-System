from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from . import db

class Role(db.Model):
    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255))
    
    users = db.relationship('User', back_populates='role', lazy='dynamic')

    def __repr__(self):
        return f"<Role {self.name}>"

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(25))
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    role = db.relationship('Role', back_populates='users')
    purchases = db.relationship('PurchaseOrder', back_populates='user', lazy='dynamic')
    sales = db.relationship('Sale', back_populates='user', lazy='dynamic')
    inventory_transactions = db.relationship('InventoryTransaction', back_populates='user', lazy='dynamic')
    stock_adjustments = db.relationship('StockAdjustment', back_populates='user', lazy='dynamic')
    audit_logs = db.relationship('AuditLog', back_populates='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def has_role(self, *role_names):
        if not self.role:
            return False
        return self.role.name in role_names

    @property
    def is_admin(self):
        return self.role and self.role.name == 'Admin'

    @property
    def is_manager(self):
        return self.role and self.role.name == 'Manager'

    @property
    def is_staff(self):
        return self.role and self.role.name == 'Staff'

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'phone': self.phone,
            'role': self.role.name if self.role else None,
            'is_active': self.is_active,
            'last_login': self.last_login.strftime('%Y-%m-%d %H:%M') if self.last_login else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else None
        }

    def __repr__(self):
        return f"<User {self.username} ({self.role.name if self.role else 'No Role'})>"
