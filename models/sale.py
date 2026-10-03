from datetime import datetime
from . import db

class Sale(db.Model):
    __tablename__ = 'sales'

    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(64), unique=True, nullable=False, index=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=True)
    customer_name = db.Column(db.String(150), default='Walk-in Customer')
    customer_phone = db.Column(db.String(30))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    sale_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    status = db.Column(db.String(20), default='Completed', index=True)  # Completed, Returned, Cancelled
    payment_method = db.Column(db.String(30), default='Cash')  # Cash, Card, Bank Transfer, UPI
    subtotal = db.Column(db.Float, default=0.0, nullable=False)
    discount_amount = db.Column(db.Float, default=0.0, nullable=False)
    tax_amount = db.Column(db.Float, default=0.0, nullable=False)
    total_amount = db.Column(db.Float, default=0.0, nullable=False)
    notes = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    customer = db.relationship('Customer', back_populates='sales')
    user = db.relationship('User', back_populates='sales')
    items = db.relationship('SaleItem', back_populates='sale', cascade='all, delete-orphan')

    @property
    def total_quantity(self):
        return sum(item.quantity for item in self.items)

    @property
    def total_cost(self):
        return sum(item.cost_price * item.quantity for item in self.items)

    @property
    def gross_profit(self):
        if self.status != 'Completed':
            return 0.0
        return round(self.total_amount - self.total_cost, 2)

    def to_dict(self):
        return {
            'id': self.id,
            'invoice_number': self.invoice_number,
            'customer_id': self.customer_id,
            'customer_name': self.customer_name or (self.customer.name if self.customer else 'Walk-in Customer'),
            'customer_phone': self.customer_phone,
            'user_name': self.user.full_name if self.user else None,
            'sale_date': self.sale_date.strftime('%Y-%m-%d %H:%M') if self.sale_date else None,
            'status': self.status,
            'payment_method': self.payment_method,
            'subtotal': self.subtotal,
            'discount_amount': self.discount_amount,
            'tax_amount': self.tax_amount,
            'total_amount': self.total_amount,
            'gross_profit': self.gross_profit,
            'item_count': len(self.items),
            'items': [item.to_dict() for item in self.items]
        }

    def __repr__(self):
        return f"<Sale {self.invoice_number} - ${self.total_amount}>"

class SaleItem(db.Model):
    __tablename__ = 'sale_items'

    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sales.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    cost_price = db.Column(db.Float, default=0.0, nullable=False)
    total_price = db.Column(db.Float, nullable=False)

    # Relationships
    sale = db.relationship('Sale', back_populates='items')
    product = db.relationship('Product', back_populates='sale_items')

    @property
    def profit(self):
        return round((self.unit_price - self.cost_price) * self.quantity, 2)

    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else None,
            'product_sku': self.product.sku if self.product else None,
            'quantity': self.quantity,
            'unit_price': self.unit_price,
            'cost_price': self.cost_price,
            'total_price': self.total_price,
            'profit': self.profit
        }

    def __repr__(self):
        return f"<SaleItem {self.product_id} x{self.quantity}>"
