from datetime import datetime
from flask import Blueprint, jsonify, request
from models import (
    db, Product, Category, Supplier, PurchaseOrder, PurchaseItem,
    Sale, SaleItem, InventoryTransaction, StockAdjustment
)
from services.inventory_service import record_transaction, process_stock_adjustment
from utils.helpers import generate_sku, generate_invoice_number, generate_po_number
from services.audit_service import log_audit, create_notification

api_bp = Blueprint('api', __name__, url_prefix='/api')

# Error handler helper
def api_error(message, status_code=400):
    return jsonify({'success': False, 'error': message}), status_code

# --- Products API ---

@api_bp.route('/products', methods=['GET'])
def get_products():
    search = request.args.get('search', '').strip()
    category_id = request.args.get('category_id', type=int)
    stock_status = request.args.get('stock_status')

    query = Product.query
    if search:
        query = query.filter(Product.name.ilike(f"%{search}%") | Product.sku.ilike(f"%{search}%"))
    if category_id:
        query = query.filter(Product.category_id == category_id)
    if stock_status == 'low':
        query = query.filter(Product.current_stock > 0, Product.current_stock <= Product.min_stock_level)
    elif stock_status == 'out':
        query = query.filter(Product.current_stock <= 0)

    products = query.order_by(Product.name).all()
    return jsonify({
        'success': True,
        'count': len(products),
        'products': [p.to_dict() for p in products]
    }), 200

@api_bp.route('/products/<int:id>', methods=['GET'])
def get_product(id):
    product = Product.query.get(id)
    if not product:
        return api_error("Product not found", 404)
    return jsonify({'success': True, 'product': product.to_dict()}), 200

@api_bp.route('/products', methods=['POST'])
def create_product():
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    category_id = data.get('category_id')

    if not name or not category_id:
        return api_error("Name and category_id are required fields.", 400)

    sku = data.get('sku', '').strip().upper() or generate_sku()
    if Product.query.filter_by(sku=sku).first():
        return api_error(f"SKU '{sku}' already exists.", 400)

    try:
        product = Product(
            sku=sku,
            name=name,
            description=data.get('description', ''),
            category_id=category_id,
            supplier_id=data.get('supplier_id'),
            purchase_price=float(data.get('purchase_price', 0.0)),
            selling_price=float(data.get('selling_price', 0.0)),
            current_stock=int(data.get('current_stock', 0)),
            min_stock_level=int(data.get('min_stock_level', 10)),
            status=data.get('status', 'Active')
        )
        db.session.add(product)
        db.session.commit()

        if product.current_stock > 0:
            record_transaction(
                product_id=product.id,
                quantity_change=product.current_stock,
                transaction_type='stock_added',
                reference_type='api',
                reason='Initial stock setup via REST API'
            )
            db.session.commit()

        return jsonify({'success': True, 'message': 'Product created successfully', 'product': product.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return api_error(str(e), 500)

@api_bp.route('/products/<int:id>', methods=['PUT'])
def update_product(id):
    product = Product.query.get(id)
    if not product:
        return api_error("Product not found", 404)

    data = request.get_json() or {}
    if 'name' in data:
        product.name = data['name'].strip()
    if 'description' in data:
        product.description = data['description']
    if 'category_id' in data:
        product.category_id = data['category_id']
    if 'supplier_id' in data:
        product.supplier_id = data['supplier_id']
    if 'purchase_price' in data:
        product.purchase_price = float(data['purchase_price'])
    if 'selling_price' in data:
        product.selling_price = float(data['selling_price'])
    if 'min_stock_level' in data:
        product.min_stock_level = int(data['min_stock_level'])
    if 'status' in data:
        product.status = data['status']

    try:
        db.session.commit()
        return jsonify({'success': True, 'product': product.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return api_error(str(e), 500)

@api_bp.route('/products/<int:id>', methods=['DELETE'])
def delete_product(id):
    product = Product.query.get(id)
    if not product:
        return api_error("Product not found", 404)

    if product.purchase_items or product.sale_items:
        product.status = 'Discontinued'
        db.session.commit()
        return jsonify({'success': True, 'message': 'Product marked as Discontinued due to existing transaction history'}), 200

    db.session.delete(product)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Product deleted successfully'}), 200

# --- Categories API ---

@api_bp.route('/categories', methods=['GET'])
def get_categories():
    categories = Category.query.order_by(Category.name).all()
    return jsonify({'success': True, 'categories': [c.to_dict() for c in categories]}), 200

@api_bp.route('/categories', methods=['POST'])
def create_category():
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    if not name:
        return api_error("Name is required", 400)

    category = Category(
        name=name,
        description=data.get('description', ''),
        parent_id=data.get('parent_id')
    )
    db.session.add(category)
    db.session.commit()
    return jsonify({'success': True, 'category': category.to_dict()}), 201

# --- Suppliers API ---

@api_bp.route('/suppliers', methods=['GET'])
def get_suppliers():
    suppliers = Supplier.query.order_by(Supplier.name).all()
    return jsonify({'success': True, 'suppliers': [s.to_dict() for s in suppliers]}), 200

@api_bp.route('/suppliers', methods=['POST'])
def create_supplier():
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    if not name:
        return api_error("Supplier name is required", 400)

    supplier = Supplier(
        name=name,
        contact_person=data.get('contact_person', ''),
        email=data.get('email', ''),
        phone=data.get('phone', ''),
        address=data.get('address', ''),
        tax_number=data.get('tax_number', '')
    )
    db.session.add(supplier)
    db.session.commit()
    return jsonify({'success': True, 'supplier': supplier.to_dict()}), 201

# --- Stock Adjustments API ---

@api_bp.route('/stock/adjust', methods=['POST'])
def adjust_stock_api():
    data = request.get_json() or {}
    product_id = data.get('product_id')
    adjustment_type = data.get('adjustment_type')
    quantity = data.get('quantity')
    reason = data.get('reason', 'API adjustment')

    if not all([product_id, adjustment_type, quantity is not None]):
        return api_error("product_id, adjustment_type, and quantity are required", 400)

    try:
        adj = process_stock_adjustment(
            product_id=product_id,
            adjustment_type=adjustment_type,
            quantity=int(quantity),
            reason=reason,
            user_id=None
        )
        return jsonify({'success': True, 'adjustment': adj.to_dict()}), 200
    except ValueError as ve:
        return api_error(str(ve), 400)
    except Exception as e:
        return api_error(str(e), 500)

# --- Purchases API ---

@api_bp.route('/purchases', methods=['GET'])
def get_purchases():
    purchases = PurchaseOrder.query.order_by(PurchaseOrder.order_date.desc()).limit(50).all()
    return jsonify({'success': True, 'purchases': [p.to_dict() for p in purchases]}), 200

@api_bp.route('/purchases', methods=['POST'])
def create_purchase_api():
    data = request.get_json() or {}
    supplier_id = data.get('supplier_id')
    items = data.get('items', [])

    if not supplier_id or not items:
        return api_error("supplier_id and at least one item required", 400)

    try:
        po_num = generate_po_number()
        subtotal = sum(float(item['quantity']) * float(item['unit_price']) for item in items)
        tax = float(data.get('tax_amount', 0.0))
        discount = float(data.get('discount_amount', 0.0))
        shipping = float(data.get('shipping_fee', 0.0))
        total = max(0.0, subtotal - discount + tax + shipping)

        purchase = PurchaseOrder(
            po_number=po_num,
            supplier_id=supplier_id,
            user_id=1,
            order_date=datetime.utcnow(),
            status=data.get('status', 'Received'),
            payment_status=data.get('payment_status', 'Paid'),
            subtotal=subtotal,
            discount_amount=discount,
            tax_amount=tax,
            shipping_fee=shipping,
            total_amount=total,
            notes=data.get('notes', '')
        )
        db.session.add(purchase)
        db.session.flush()

        for item_data in items:
            p_id = int(item_data['product_id'])
            qty = int(item_data['quantity'])
            price = float(item_data['unit_price'])

            po_item = PurchaseItem(
                purchase_id=purchase.id,
                product_id=p_id,
                quantity=qty,
                unit_price=price,
                total_price=qty * price
            )
            db.session.add(po_item)

            if purchase.status == 'Received':
                record_transaction(
                    product_id=p_id,
                    quantity_change=qty,
                    transaction_type='stock_added',
                    reference_type='purchase',
                    reference_id=po_num,
                    reason=f"PO {po_num} received via API"
                )

        db.session.commit()
        return jsonify({'success': True, 'purchase': purchase.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return api_error(str(e), 500)

# --- Sales API ---

@api_bp.route('/sales', methods=['GET'])
def get_sales():
    sales = Sale.query.order_by(Sale.sale_date.desc()).limit(50).all()
    return jsonify({'success': True, 'sales': [s.to_dict() for s in sales]}), 200

@api_bp.route('/sales', methods=['POST'])
def create_sale_api():
    data = request.get_json() or {}
    items = data.get('items', [])
    if not items:
        return api_error("At least one sale item is required", 400)

    try:
        inv_num = generate_invoice_number()
        subtotal = 0.0

        for item in items:
            p = Product.query.get(item['product_id'])
            if not p:
                return api_error(f"Product {item['product_id']} not found", 404)
            if p.current_stock < int(item['quantity']):
                return api_error(f"Insufficient stock for {p.name}. In stock: {p.current_stock}", 400)
            subtotal += (int(item['quantity']) * float(item['unit_price']))

        discount = float(data.get('discount_amount', 0.0))
        tax = float(data.get('tax_amount', 0.0))
        total = max(0.0, subtotal - discount + tax)

        sale = Sale(
            invoice_number=inv_num,
            customer_id=data.get('customer_id'),
            customer_name=data.get('customer_name', 'Walk-in Customer'),
            customer_phone=data.get('customer_phone', ''),
            user_id=1,
            sale_date=datetime.utcnow(),
            status='Completed',
            payment_method=data.get('payment_method', 'Cash'),
            subtotal=subtotal,
            discount_amount=discount,
            tax_amount=tax,
            total_amount=total,
            notes=data.get('notes', '')
        )
        db.session.add(sale)
        db.session.flush()

        for item in items:
            p_id = int(item['product_id'])
            qty = int(item['quantity'])
            price = float(item['unit_price'])
            p = Product.query.get(p_id)

            s_item = SaleItem(
                sale_id=sale.id,
                product_id=p_id,
                quantity=qty,
                unit_price=price,
                cost_price=p.purchase_price,
                total_price=qty * price
            )
            db.session.add(s_item)

            record_transaction(
                product_id=p_id,
                quantity_change=-qty,
                transaction_type='stock_removed',
                reference_type='sale',
                reference_id=inv_num,
                reason=f"Sale {inv_num} via API"
            )

        db.session.commit()
        return jsonify({'success': True, 'sale': sale.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return api_error(str(e), 500)

# --- Summary KPI Report API ---

@api_bp.route('/reports/summary', methods=['GET'])
def get_summary_report():
    all_products = Product.query.all()
    total_val = sum(p.inventory_value for p in all_products)
    total_retail = sum(p.retail_value for p in all_products)
    low_stock = sum(1 for p in all_products if p.is_low_stock)
    out_of_stock = sum(1 for p in all_products if p.is_out_of_stock)

    completed_sales = Sale.query.filter_by(status='Completed').all()
    total_revenue = sum(s.total_amount for s in completed_sales)
    total_profit = sum(s.gross_profit for s in completed_sales)

    return jsonify({
        'success': True,
        'summary': {
            'total_products': len(all_products),
            'total_stock_units': sum(p.current_stock for p in all_products),
            'inventory_valuation': total_val,
            'retail_valuation': total_retail,
            'low_stock_count': low_stock,
            'out_of_stock_count': out_of_stock,
            'total_completed_sales': len(completed_sales),
            'total_sales_revenue': round(total_revenue, 2),
            'total_gross_profit': round(total_profit, 2)
        }
    }), 200
