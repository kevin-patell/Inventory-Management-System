from datetime import datetime
from . import db

class PurchaseOrder(db.Model):
    __tablename__ = 'purchase_orders'

    id = db.Column(db.Integer, primary_key=True)
    po_number = db.Column(db.String(64), unique=True, nullable=False, index=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    order_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    status = db.Column(db.String(20), default='Received', index=True)  # Pending, Received, Cancelled
    subtotal = db.Column(db.Float, default=0.0, nullable=False)
    tax_amount = db.Column(db.Float, default=0.0, nullable=False)
    discount_amount = db.Column(db.Float, default=0.0, nullable=False)
    shipping_fee = db.Column(db.Float, default=0.0, nullable=False)
    total_amount = db.Column(db.Float, default=0.0, nullable=False)
    payment_status = db.Column(db.String(20), default='Paid')  # Paid, Partial, Unpaid
    notes = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    supplier = db.relationship('Supplier', back_populates='purchases')
    user = db.relationship('User', back_populates='purchases')
    items = db.relationship('PurchaseItem', back_populates='purchase', cascade='all, delete-orphan')

    @property
    def total_quantity(self):
        return sum(item.quantity for item in self.items)

    def to_dict(self):
        return {
            'id': self.id,
            'po_number': self.po_number,
            'supplier_id': self.supplier_id,
            'supplier_name': self.supplier.name if self.supplier else None,
            'user_name': self.user.full_name if self.user else None,
            'order_date': self.order_date.strftime('%Y-%m-%d %H:%M') if self.order_date else None,
            'status': self.status,
            'subtotal': self.subtotal,
            'tax_amount': self.tax_amount,
            'discount_amount': self.discount_amount,
            'shipping_fee': self.shipping_fee,
            'total_amount': self.total_amount,
            'payment_status': self.payment_status,
            'notes': self.notes,
            'item_count': len(self.items),
            'items': [item.to_dict() for item in self.items]
        }

    def __repr__(self):
        return f"<PurchaseOrder {self.po_number} - ₹{self.total_amount}>"

class PurchaseItem(db.Model):
    __tablename__ = 'purchase_items'

    id = db.Column(db.Integer, primary_key=True)
    purchase_id = db.Column(db.Integer, db.ForeignKey('purchase_orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)

    # Relationships
    purchase = db.relationship('PurchaseOrder', back_populates='items')
    product = db.relationship('Product', back_populates='purchase_items')

    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else None,
            'product_sku': self.product.sku if self.product else None,
            'quantity': self.quantity,
            'unit_price': self.unit_price,
            'total_price': self.total_price
        }

    def __repr__(self):
        return f"<PurchaseItem {self.product_id} x{self.quantity}>"
