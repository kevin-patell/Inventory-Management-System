import os
import random
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from config import Config

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

def save_product_image(file_storage):
    """
    Saves an uploaded product image safely with unique filename.
    Returns relative filename or default if invalid.
    """
    if not file_storage or file_storage.filename == '':
        return 'default_product.png'

    if allowed_file(file_storage.filename):
        ext = file_storage.filename.rsplit('.', 1)[1].lower()
        unique_name = f"{uuid.uuid4().hex[:12]}_{int(datetime.utcnow().timestamp())}.{ext}"
        filepath = os.path.join(Config.UPLOAD_FOLDER, unique_name)
        file_storage.save(filepath)
        return unique_name

    return 'default_product.png'

def generate_sku(prefix="PRD"):
    """
    Generates a unique SKU code like PRD-82914
    """
    random_digits = random.randint(10000, 99999)
    return f"{prefix.upper()}-{random_digits}"

def generate_invoice_number():
    date_str = datetime.utcnow().strftime('%Y%m%d')
    rand = random.randint(1000, 9999)
    return f"INV-{date_str}-{rand}"

def generate_po_number():
    date_str = datetime.utcnow().strftime('%Y%m%d')
    rand = random.randint(1000, 9999)
    return f"PO-{date_str}-{rand}"

def format_currency(value):
    try:
        val = float(value or 0)
        return f"{Config.CURRENCY_SYMBOL}{val:,.2f}"
    except (ValueError, TypeError):
        return f"{Config.CURRENCY_SYMBOL}0.00"

def format_datetime(value, fmt='%b %d, %Y %H:%M'):
    if not value:
        return ''
    if isinstance(value, str):
        try:
            value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return value
    return value.strftime(fmt)

def format_date(value, fmt='%b %d, %Y'):
    if not value:
        return ''
    if isinstance(value, str):
        try:
            value = datetime.strptime(value, '%Y-%m-%d')
        except ValueError:
            return value
    return value.strftime(fmt)
