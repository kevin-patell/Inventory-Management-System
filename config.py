import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'smart-inventory-super-secret-key-2026'
    
    # SQLite Database
    DB_DIR = os.path.join(basedir, 'database')
    os.makedirs(DB_DIR, exist_ok=True)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f"sqlite:///{os.path.join(DB_DIR, 'inventory.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Uploads
    UPLOAD_FOLDER = os.path.join(basedir, 'static', 'uploads', 'products')
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max limit
    
    # App Settings
    ITEMS_PER_PAGE = 10
    CURRENCY_SYMBOL = '₹'
    PDF_CURRENCY_SYMBOL = 'Rs. '
    COMPANY_NAME = 'Smart Inventory System'
    COMPANY_ADDRESS = '100 Business Tech Blvd, Suite 400, Silicon City, CA'
    COMPANY_PHONE = '+1 (800) 555-0199'
    COMPANY_EMAIL = 'support@smartims.com'
    COMPANY_TAX_ID = 'TAX-US-9847120-X'
