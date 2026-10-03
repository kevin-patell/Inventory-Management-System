from datetime import datetime
from . import db

class InventoryTransaction(db.Model):
    __tablename__ = 'inventory_transactions'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    transaction_type = db.Column(db.String(30), nullable=False, index=True) 
    # 'stock_added', 'stock_removed', 'stock_returned', 'damaged_stock', 'adjustment_add', 'adjustment_sub'
    
    quantity_change = db.Column(db.Integer, nullable=False)
    previous_quantity = db.Column(db.Integer, nullable=False)
    new_quantity = db.Column(db.Integer, nullable=False)
    
    reference_type = db.Column(db.String(30), nullable=True) # 'purchase', 'sale', 'adjustment', 'manual'
    reference_id = db.Column(db.String(64), nullable=True, index=True)
    reason = db.Column(db.String(255))
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    # Relationships
    product = db.relationship('Product', back_populates='inventory_transactions')
    user = db.relationship('User', back_populates='inventory_transactions')

    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else None,
            'product_sku': self.product.sku if self.product else None,
            'transaction_type': self.transaction_type,
            'quantity_change': self.quantity_change,
            'previous_quantity': self.previous_quantity,
            'new_quantity': self.new_quantity,
            'reference_type': self.reference_type,
            'reference_id': self.reference_id,
            'reason': self.reason,
            'user_name': self.user.full_name if self.user else 'System',
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }

    def __repr__(self):
        return f"<InventoryTransaction {self.product_id} ({self.quantity_change})>"

class StockAdjustment(db.Model):
    __tablename__ = 'stock_adjustments'

    id = db.Column(db.Integer, primary_key=True)
    adjustment_number = db.Column(db.String(64), unique=True, nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    adjustment_type = db.Column(db.String(30), nullable=False) # 'add', 'subtract', 'recount', 'damaged'
    quantity = db.Column(db.Integer, nullable=False)
    previous_quantity = db.Column(db.Integer, nullable=False)
    new_quantity = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.Text, nullable=False)
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    product = db.relationship('Product', back_populates='stock_adjustments')
    user = db.relationship('User', back_populates='stock_adjustments')

    def to_dict(self):
        return {
            'id': self.id,
            'adjustment_number': self.adjustment_number,
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else None,
            'product_sku': self.product.sku if self.product else None,
            'adjustment_type': self.adjustment_type,
            'quantity': self.quantity,
            'previous_quantity': self.previous_quantity,
            'new_quantity': self.new_quantity,
            'reason': self.reason,
            'user_name': self.user.full_name if self.user else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else None
        }

    def __repr__(self):
        return f"<StockAdjustment {self.adjustment_number} Product:{self.product_id}>"
