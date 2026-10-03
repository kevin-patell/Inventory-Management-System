from datetime import datetime
from . import db

class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    description = db.Column(db.Text)
    parent_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    parent = db.relationship('Category', remote_side=[id], backref=db.backref('children', lazy='dynamic'))
    products = db.relationship('Product', back_populates='category', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'parent_id': self.parent_id,
            'parent_name': self.parent.name if self.parent else None,
            'product_count': self.products.count(),
            'is_active': self.is_active
        }

    def __repr__(self):
        return f"<Category {self.name}>"

class Supplier(db.Model):
    __tablename__ = 'suppliers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, index=True)
    contact_person = db.Column(db.String(100))
    email = db.Column(db.String(120), index=True)
    phone = db.Column(db.String(30))
    address = db.Column(db.Text)
    tax_number = db.Column(db.String(50))
    notes = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    products = db.relationship('Product', back_populates='supplier', lazy='dynamic')
    purchases = db.relationship('PurchaseOrder', back_populates='supplier', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'contact_person': self.contact_person,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'tax_number': self.tax_number,
            'product_count': self.products.count(),
            'is_active': self.is_active
        }

    def __repr__(self):
        return f"<Supplier {self.name}>"

class Customer(db.Model):
    __tablename__ = 'customers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, index=True)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(30))
    address = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    sales = db.relationship('Sale', back_populates='customer', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'total_orders': self.sales.count()
        }

    def __repr__(self):
        return f"<Customer {self.name}>"

class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(64), unique=True, nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False, index=True)
    description = db.Column(db.Text)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=True)
    
    purchase_price = db.Column(db.Float, default=0.0, nullable=False)
    selling_price = db.Column(db.Float, default=0.0, nullable=False)
    current_stock = db.Column(db.Integer, default=0, nullable=False)
    min_stock_level = db.Column(db.Integer, default=10, nullable=False)
    
    image_url = db.Column(db.String(255), default='default_product.png')
    status = db.Column(db.String(20), default='Active', index=True)  # Active, Inactive, Discontinued
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    category = db.relationship('Category', back_populates='products')
    supplier = db.relationship('Supplier', back_populates='products')
    purchase_items = db.relationship('PurchaseItem', back_populates='product', cascade='all, delete-orphan')
    sale_items = db.relationship('SaleItem', back_populates='product', cascade='all, delete-orphan')
    inventory_transactions = db.relationship('InventoryTransaction', back_populates='product', cascade='all, delete-orphan')
    stock_adjustments = db.relationship('StockAdjustment', back_populates='product', cascade='all, delete-orphan')

    @property
    def is_low_stock(self):
        return 0 < self.current_stock <= self.min_stock_level

    @property
    def is_out_of_stock(self):
        return self.current_stock <= 0

    @property
    def stock_status(self):
        if self.current_stock <= 0:
            return 'Out of Stock'
        elif self.current_stock <= self.min_stock_level:
            return 'Low Stock'
        return 'In Stock'

    @property
    def inventory_value(self):
        return round(self.current_stock * self.purchase_price, 2)

    @property
    def retail_value(self):
        return round(self.current_stock * self.selling_price, 2)

    @property
    def profit_margin(self):
        if self.selling_price > 0:
            return round(((self.selling_price - self.purchase_price) / self.selling_price) * 100, 1)
        return 0.0

    def to_dict(self):
        return {
            'id': self.id,
            'sku': self.sku,
            'name': self.name,
            'description': self.description,
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else None,
            'supplier_id': self.supplier_id,
            'supplier_name': self.supplier.name if self.supplier else None,
            'purchase_price': self.purchase_price,
            'selling_price': self.selling_price,
            'current_stock': self.current_stock,
            'min_stock_level': self.min_stock_level,
            'image_url': self.image_url,
            'status': self.status,
            'stock_status': self.stock_status,
            'inventory_value': self.inventory_value,
            'retail_value': self.retail_value,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else None
        }

    def __repr__(self):
        return f"<Product {self.sku} - {self.name}>"
