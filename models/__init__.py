from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .user import Role, User
from .product import Category, Supplier, Customer, Product
from .purchase import PurchaseOrder, PurchaseItem
from .sale import Sale, SaleItem
from .inventory import InventoryTransaction, StockAdjustment
from .audit import AuditLog, Notification

__all__ = [
    'db',
    'Role',
    'User',
    'Category',
    'Supplier',
    'Customer',
    'Product',
    'PurchaseOrder',
    'PurchaseItem',
    'Sale',
    'SaleItem',
    'InventoryTransaction',
    'StockAdjustment',
    'AuditLog',
    'Notification'
]
